"""Stile conversazionale — consulente senior, non generatore di checklist (review dialogo
lungo B&B): meno liste, sintesi periodiche, gerarchizzare i rischi, dialettica, numeri come
esempi, lunghezza proporzionata.
"""
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

for _name, _attrs in (("dotenv", {"load_dotenv": lambda *a, **k: False}),):
    if _name not in sys.modules:
        _m = types.ModuleType(_name)
        [setattr(_m, k, v) for k, v in _attrs.items()]
        sys.modules[_name] = _m
try:  # pragma: no cover
    from supabase import Client as _ProbeClient  # noqa: F401
except Exception:  # pragma: no cover
    _m = types.ModuleType("supabase")
    _m.Client, _m.create_client = object, (lambda *a, **k: None)
    sys.modules["supabase"] = _m

from app.lib.prompts import build_system_prompt_v2  # noqa: E402


def _conv(nturns: int) -> dict:
    msgs = []
    for i in range(nturns):
        msgs.append({"role": "user", "content": f"messaggio {i} con contenuto reale del cliente"})
        msgs.append({"role": "assistant", "content": "risposta"})
    return {"messages": msgs, "collected_data": {}}


def _p(nturns: int) -> str:
    return build_system_prompt_v2([], _conv(nturns), required_fields_hint="")


# ── la sezione di stile è sempre presente (regola generale) ──────────────────────────────
def test_conversational_style_section_present():
    p = _p(2)
    assert "STILE CONVERSAZIONALE" in p
    for frag in ("NON ogni risposta è una lista", "SINTETIZZA OGNI TANTO",
                 "GERARCHIZZA I RISCHI", "SII DIALETTICO", "PERSONALITÀ CONSULENZIALE",
                 "NON RIPETERE", "NUMERI COME ESEMPI", "LUNGHEZZA"):
        assert frag in p, frag


def test_numbers_as_examples_framing():
    p = _p(2)
    assert "soglie arbitrarie come fatti" in p
    assert "se una quota significativa" in p.lower()


# ── nudge deterministico di sintesi periodica nelle conversazioni lunghe ──────────────────
def test_synthesis_nudge_fires_periodically_only_when_long():
    assert "SINTESI PERIODICA (turno" not in _p(2)     # conversazione breve → no nudge
    assert "SINTESI PERIODICA (turno" not in _p(3)
    assert "SINTESI PERIODICA (turno" in _p(5)          # da 5, ogni 4 turni
    assert "SINTESI PERIODICA (turno" not in _p(6)
    assert "SINTESI PERIODICA (turno" not in _p(8)
    assert "SINTESI PERIODICA (turno" in _p(9)
    assert "SINTESI PERIODICA (turno" in _p(13)


def test_synthesis_nudge_asks_to_hierarchize_risk():
    p = _p(5)
    assert "il vero nodo sia" in p
    assert "rischio è ormai predominante" in p or "RISCHIO/nodo PRINCIPALE" in p
