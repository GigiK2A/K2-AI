"""Test provenienza metriche (app/provenance.py) — spec §2/§3, Test 2 — e la
root-cause del 'placeholder verde' (_enum_placeholder in app/llm.py)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import provenance as PROV  # noqa: E402
from app.quality_gate import run_report_quality_gate  # noqa: E402


# ── evidence store ──────────────────────────────────────────────────────────────
def test_build_evidence_collects_numbers_and_strings():
    ev = PROV.build_evidence({"fatturato": 44000, "azienda": "K2A", "note": {"x": [12, 13]}})
    assert 44000.0 in ev and 12.0 in ev and 13.0 in ev
    assert "k2a" in ev


def test_value_in_evidence_numeric_and_tolerance():
    ev = PROV.build_evidence({"a": 1000})
    assert PROV.value_in_evidence(1000, ev)
    assert PROV.value_in_evidence("1.000", ev)      # formato IT
    assert PROV.value_in_evidence(1003, ev)         # entro tolleranza 0.5%
    assert not PROV.value_in_evidence(2000, ev)


def test_empty_evidence_cannot_verify():
    assert PROV.value_in_evidence(100, set()) is False


# ── Test 2 spec: valore user_provided non nell'evidence → bloccante ─────────────
def test_ungrounded_user_provided_blocks():
    ev = PROV.build_evidence({"altro": 10})
    metric = {"label": "EBITDA", "value": 44000, "source": "user_provided"}
    findings = PROV.validate_metric(metric, ev)
    assert any(f["code"] == "ungrounded_metric" and f["severity"] == "block" for f in findings)


def test_grounded_user_provided_passes():
    ev = PROV.build_evidence({"fatturato": 44000})
    metric = {"label": "Fatturato", "value": 44000, "source": "user_provided"}
    assert PROV.validate_metric(metric, ev) == []


def test_assumption_and_benchmark_not_required_in_evidence():
    ev = PROV.build_evidence({"x": 1})
    assert PROV.validate_metric({"label": "Soglia", "value": 10, "source": "assumption"}, ev) == []
    assert PROV.validate_metric({"label": "Media settore", "value": 30, "source": "benchmark"}, ev) == []


def test_missing_with_value_warns():
    findings = PROV.validate_metric({"label": "Cassa", "value": 999, "source": "missing"}, set())
    assert any(f["code"] == "missing_con_valore" for f in findings)


def test_metric_without_source_not_validated():
    # nessuna source dichiarata → non validata (retro-compatibile)
    assert PROV.validate_metric({"label": "X", "value": 123}, set()) == []


def test_invalid_source_blocks():
    findings = PROV.validate_metric({"label": "X", "value": 1, "source": "inventata"}, set())
    assert any(f["code"] == "source_non_valida" for f in findings)


# ── gate integra la provenienza (Test 2 end-to-end) ─────────────────────────────
def test_gate_flags_ungrounded_metric_when_evidence_given():
    deliverable = {"kpi": [{"nome": "EBITDA", "valore": 44000, "semaforo": "rosso",
                            "source": "user_provided"}]}
    evidence = PROV.build_evidence({"fatturato": 10000})
    res = run_report_quality_gate(deliverable, evidence=evidence)
    assert res["ok"] is False
    assert any(f["code"] == "ungrounded_metric" for f in res["blocking"])


def test_gate_without_evidence_skips_provenance():
    deliverable = {"kpi": [{"nome": "EBITDA", "valore": 44000, "semaforo": "rosso",
                            "source": "user_provided"}]}
    res = run_report_quality_gate(deliverable)   # evidence=None → salta provenienza
    assert all(f["code"] != "ungrounded_metric" for f in res["findings"])


# ── root-cause C: placeholder di un semaforo non è mai verde ────────────────────
def test_enum_placeholder_semaforo_never_green():
    from app.llm import _enum_placeholder
    assert _enum_placeholder(["verde", "giallo", "rosso"]) == "giallo"
    # enum non semaforico → invariato (primo)
    assert _enum_placeholder(["alta", "media", "bassa"]) == "alta"
