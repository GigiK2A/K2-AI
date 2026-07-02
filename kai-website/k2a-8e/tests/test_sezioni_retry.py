"""Regression: generate_sezioni (voci-shape LegalBoost/FiscoBoost) NON deve consegnare
[BOZZA OFFLINE] quando la filiera anthropic risponde ma TRONCA il JSON.

Bug reale (QA): 9 voci ricche in UNA risposta > max_tokens=16000 → JSON illeggibile →
ogni voce cadeva su _offline() = '[BOZZA OFFLINE]' pur con mode=anthropic → report
PAGATO pieno di segnaposto. Fix: le voci mancanti/mozzate si RIGENERANO in batch più
piccoli; se restano, `degraded_voci` è valorizzato → il gate blocca il job.
"""
import json as _json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("K2A_ENTITLEMENT_SECRET", "test-secret")

import app.llm as L  # noqa: E402


def _fake_client(script):
    """script: lista di (json_text, output_tokens, stop_reason) per chiamata successiva."""
    state = {"i": 0}

    class Msgs:
        def create(self, **kw):
            i = state["i"]; state["i"] += 1
            text, tok, stop = script[min(i, len(script) - 1)]
            resp = type("R", (), {})()
            resp.content = [type("B", (), {"type": "text", "text": text})()]
            resp.usage = type("U", (), {"output_tokens": tok})()
            resp.stop_reason = stop
            return resp

    return type("C", (), {"messages": Msgs()})()


def _patch_anthropic(monkeypatch, script):
    import anthropic
    monkeypatch.setattr(L, "ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setattr(anthropic, "Anthropic", lambda *a, **k: _fake_client(script), raising=False)


BP = {"voci": [{"id": "a", "titolo": "A"}, {"id": "b", "titolo": "B"}, {"id": "c", "titolo": "C"}]}


def test_truncated_first_response_regenerates_missing_voci(monkeypatch):
    full = _json.dumps({v: ("Prosa reale " + v.upper() + " ") * 12 for v in ("a", "b", "c")})
    _patch_anthropic(monkeypatch, [
        ('{"a":"prosa troncata a meta sen', 16000, "max_tokens"),   # illeggibile
        (full, 4000, "end_turn"),                                    # retry: tutte valide
    ])
    out, meta = L.generate_sezioni(BP, {}, {"ragione_sociale": "Test Srl"})
    assert meta["mode"] == "anthropic"
    assert meta["degraded_voci"] == []
    assert all("BOZZA OFFLINE" not in v for v in out.values())
    assert all(len(v) >= 60 for v in out.values())


def test_persistent_failure_flags_degraded(monkeypatch):
    # sempre tronco → dopo i retry restano voci non generate → degraded_voci valorizzato
    _patch_anthropic(monkeypatch, [('{"a":"tron', 16000, "max_tokens")])
    out, meta = L.generate_sezioni(BP, {}, {"ragione_sociale": "Test Srl"})
    assert meta["degraded_voci"], "voci non generate devono essere flaggate per il gate"
    # la bozza resta come ultima spiaggia, ma il flag fa bloccare il job a valle
    assert any("BOZZA OFFLINE" in v for v in out.values())
