"""Test del quality gate pre-consegna (app/quality_gate.py) — spec §12 + Test 3/4/8."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.quality_gate import run_report_quality_gate  # noqa: E402


def _codes(res, severity=None):
    return {f["code"] for f in res["findings"]
            if severity is None or f["severity"] == severity}


def test_clean_report_passes():
    deliverable = {
        "executive_summary": "Sintesi pulita del report senza problemi.",
        "kpi_finanziaria": [{"nome": "Ritardi", "valore": 22, "target": 10, "semaforo": "rosso"}],
    }
    res = run_report_quality_gate(deliverable)
    assert res["ok"] is True
    assert res["blocking"] == []


# ── Test 8 spec: nessun placeholder tecnico ─────────────────────────────────────
def test_blocks_leaked_wrapper_string():
    deliverable = {"executive_summary": '{"type": "string", "$value": "Rischio medio"}'}
    res = run_report_quality_gate(deliverable)
    assert res["ok"] is False
    assert "leaked_wrapper" in _codes(res, "block")


def test_blocks_wrapper_dict_value():
    deliverable = {"meta": {"nota": {"type": "string", "$value": "x"}}}
    res = run_report_quality_gate(deliverable)
    assert res["ok"] is False
    assert "wrapper_dict" in _codes(res, "block")


def test_blocks_object_object_and_undefined():
    assert not run_report_quality_gate({"x": "valore [object Object] qui"})["ok"]
    assert not run_report_quality_gate({"x": "campo undefined"})["ok"]


# ── Test 3 spec: dato mancante non deve avere semaforo verde ────────────────────
def test_blocks_missing_value_with_green():
    deliverable = {"kpi": [{"nome": "Fatturato", "valore": None, "target": None, "semaforo": "verde"}]}
    res = run_report_quality_gate(deliverable)
    assert res["ok"] is False
    assert "missing_green" in _codes(res, "block")


def test_blocks_nd_string_with_green():
    deliverable = {"kpi": [{"nome": "DSO", "valore": "N/D", "semaforo": "verde"}]}
    assert "missing_green" in _codes(run_report_quality_gate(deliverable), "block")


def test_blocks_placeholder_1_1_green():
    deliverable = {"kpi": [{"nome": "Clienti", "valore": 1, "target": 1, "semaforo": "verde"}]}
    assert "placeholder_green" in _codes(run_report_quality_gate(deliverable), "block")


def test_missing_value_without_green_is_ok():
    # dato mancante SENZA verde (grigio/neutro) non è bloccante
    deliverable = {"kpi": [{"nome": "Fatturato", "valore": None, "semaforo": None}]}
    res = run_report_quality_gate(deliverable)
    assert "missing_green" not in _codes(res, "block")


# ── Test 4 spec: KPI duplicati → warning ────────────────────────────────────────
def test_duplicate_kpi_warns_not_blocks():
    deliverable = {
        "kpi_processi": [{"nome": "Commesse in ritardo", "valore": 22, "semaforo": "rosso"}],
        "alert": [{"nome": "Commesse in ritardo", "valore": 22, "semaforo": "rosso"}],
    }
    res = run_report_quality_gate(deliverable)
    assert "duplicate_kpi" in _codes(res, "warn")
    assert res["ok"] is True   # i duplicati non bloccano


def test_report_is_human_readable():
    deliverable = {"x": '{"$value": "y"}'}
    res = run_report_quality_gate(deliverable)
    assert "BLOCCANTE" in res["report"]
    assert "correzione" in res["report"]


# ── Test 6 spec: nessuna serie storica inventata ────────────────────────────────
def test_blocks_invented_time_series():
    from app import provenance as PROV
    # l'utente ha dato UN mese; il modello ha "inventato" 12 mesi di fatturato
    deliverable = {"trend_12_mesi": {"fatturato": [98, 101, 97, 105, 110, 99,
                                                   102, 104, 100, 103, 108, 100000]}}
    evidence = PROV.build_evidence({"fatturato": 100000})
    res = run_report_quality_gate(deliverable, evidence=evidence)
    assert any(f["code"] == "serie_storica_inventata" for f in res["blocking"])


def test_short_real_series_passes():
    from app import provenance as PROV
    # il binder deterministico emette il SOLO mese corrente → nessun blocco
    deliverable = {"trend_12_mesi": {"fatturato": [100000]}}
    evidence = PROV.build_evidence({"fatturato": 100000})
    res = run_report_quality_gate(deliverable, evidence=evidence)
    assert all(f["code"] != "serie_storica_inventata" for f in res["findings"])


def test_grounded_long_series_passes():
    from app import provenance as PROV
    mesi = [100, 102, 98, 105, 103, 99]
    deliverable = {"serie_mensile": {"ricavi": list(mesi)}}
    evidence = PROV.build_evidence({"ricavi_mensili": mesi})
    res = run_report_quality_gate(deliverable, evidence=evidence)
    assert all(f["code"] != "serie_storica_inventata" for f in res["findings"])
