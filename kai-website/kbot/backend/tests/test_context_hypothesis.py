"""Gestione del contesto + aggiornamento delle ipotesi (review): il contesto ha priorità
(un «Prova SRLS» a metà consulenza è la ragione sociale, non «come apro una SRLS») e nessuna
diagnosi è definitiva (no confirmation bias, peso alle novità).
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

from app.lib import signals  # noqa: E402


# ── looks_like_identifier: nome/ragione sociale/P.IVA/CF vs richiesta ─────────────────────
def test_identifiers_recognized():
    for t in ["Prova SRLS", "Beta Engineering Srl", "K2 Consulting Srl", "Rossi Impianti",
              "K2A S.r.l.s.", "ACME SpA", "Bianchi & C. snc",
              "03655920548", "IT03655920548", "RSSMRA80A01H501U", "Alfa"]:
        assert signals.looks_like_identifier(t), t


def test_requests_not_identifiers():
    for t in ["Come apro una SRLS?", "Voglio aprire una SRL",
              "Sto analizzando il turnover della mia azienda",
              "meglio SRL o ditta individuale?", "aprire una srl conviene?",
              "Ho un problema col mio socio", "Analizza il fatturato",
              "perché le vendite calano", "prova a spiegarmi il DCF"]:
        assert not signals.looks_like_identifier(t), t


# ── iniezione dell'interpretazione contestuale nel prompt ────────────────────────────────
def _prompt(messages):
    from app.lib.prompts import build_system_prompt_v2
    return build_system_prompt_v2([], {"messages": messages, "collected_data": {}},
                                  required_fields_hint="")


def test_mid_conversation_identifier_injected():
    p = _prompt([
        {"role": "user", "content": "Sto analizzando il turnover, se ne vanno in troppi."},
        {"role": "assistant", "content": "Da quanto succede?"},
        {"role": "user", "content": "Prova SRLS"}])
    assert "INTERPRETAZIONE CONTESTUALE" in p and "Prova SRLS" in p
    assert "NON cambiare argomento" in p


def test_real_new_request_not_injected():
    p = _prompt([
        {"role": "user", "content": "turnover alto"},
        {"role": "assistant", "content": "ok"},
        {"role": "user", "content": "Come apro una SRL?"}])
    assert "INTERPRETAZIONE CONTESTUALE" not in p


def test_first_turn_bare_name_no_dynamic_injection():
    # al primo turno non c'è un contesto da preservare: la regola generale nel prompt basta,
    # niente iniezione dinamica specifica
    p = _prompt([{"role": "user", "content": "Beta Engineering Srl"}])
    assert "INTERPRETAZIONE CONTESTUALE" not in p


# ── sezioni prompt sempre presenti (regole generali) ─────────────────────────────────────
def test_prompt_general_rules_present():
    p = _prompt([{"role": "user", "content": "ciao"}])
    assert "GERARCHIA DI INTERPRETAZIONE" in p          # il contesto ha priorità
    assert "NESSUNA DIAGNOSI È DEFINITIVA" in p          # no confirmation bias
    assert "DAI PIÙ PESO ALLE NOVITÀ" in p               # il dato appena emerso è prioritario
    assert "confirmation bias" in p.lower()
    assert "Prova SRLS" in p                             # esempio del caso reale
