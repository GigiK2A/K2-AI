"""Chiusura consulenza → generazione report (spec Luca 18 lug).

Backstop deterministico della 'regola hard': se il bot fornisce analisi/raccomandazioni per
>= 2 turni consecutivi, la soglia per il report è superata → forced-summary. Il prompt porta
le regole (bloccanti vs approfondimento, mai promettere, report != executive summary,
incrementale); l'ENFORCEMENT è deterministico perché il modello locale non obbedisce da solo.
"""
from __future__ import annotations

import types
import sys

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
from app.lib.prompts import build_system_prompt_v2  # noqa: E402


_ANALISI = ("Ecco come muoverti: 1. raccogli contratto e comunicazioni; 2. invia una risposta "
            "formale; 3. valuta la mediazione. Il rischio principale è la perdita del credito.")
_ANALISI2 = ("In sintesi, ti conviene formalizzare il recupero. Ti consiglio di procedere con "
             "una diffida e, se non paga, con il decreto ingiuntivo. Dovresti muoverti presto.")
_DOMANDA = "Di che importo parliamo e da quanto tempo la fattura è scaduta?"
_NOTREADY = ("Non ho ancora informazioni sufficienti per una diagnosi attendibile: prima devo "
             "chiarire la natura del contenzioso e gli importi in gioco.")


# ── detector: il turno fornisce analisi? ─────────────────────────────────────────────────
def test_provides_analysis_positivo_negativo():
    assert signals.provides_analysis(_ANALISI)
    assert signals.provides_analysis(_ANALISI2)
    assert not signals.provides_analysis(_DOMANDA)         # semplice domanda
    assert not signals.provides_analysis(_NOTREADY)        # dichiara gap bloccante
    assert not signals.provides_analysis("Ok, grazie.")    # troppo corto


# ── streak: 2 turni consecutivi di analisi → soglia superata ─────────────────────────────
def _streak(merged, raw):
    from app.api.message import _analysis_streak_reached
    return _analysis_streak_reached(merged, raw)


def test_streak_due_turni_consecutivi_raggiunge_soglia():
    merged = [
        {"role": "user", "content": "Un cliente non mi paga una fattura."},
        {"role": "assistant", "content": _ANALISI},           # turno precedente: analisi
        {"role": "user", "content": "Sì, ho già sollecitato una volta."},
    ]
    assert _streak(merged, _ANALISI2) is True                 # corrente analisi + precedente analisi


def test_streak_un_solo_turno_non_basta():
    merged = [
        {"role": "user", "content": "Un cliente non mi paga."},
        {"role": "assistant", "content": _DOMANDA},           # turno precedente: domanda
        {"role": "user", "content": "4000 euro, tre mesi fa."},
    ]
    assert _streak(merged, _ANALISI) is False                 # corrente analisi, ma precedente NO


def test_streak_interrotto_da_turno_non_analisi():
    merged = [
        {"role": "assistant", "content": _ANALISI},
        {"role": "user", "content": "ok"},
        {"role": "assistant", "content": _DOMANDA},           # interrompe la sequenza
        {"role": "user", "content": "rispondo"},
    ]
    assert _streak(merged, _ANALISI2) is False


# ── prompt: le regole di chiusura sono presenti ──────────────────────────────────────────
def _prompt():
    return build_system_prompt_v2([], {"messages": [{"role": "user", "content": "ciao"}],
                                       "collected_data": {}}, required_fields_hint="")


def test_prompt_regole_di_chiusura():
    p = _prompt()
    assert "CHIUSURA DELLA CONSULENZA" in p
    assert "BLOCCANTI" in p and "APPROFONDIMENTO" in p
    assert "MAI PROMETTERE AL FUTURO" in p and "consegnalo" in p.lower()
    assert "non è un Executive Summary" in p or "NON è un Executive Summary" in p
    assert "INCREMENTALE" in p.upper()
    # POLICY AGGIORNATA (review calo ordini): la quantità di dati/turni NON è più criterio
    # sufficiente. Il prompt cita ancora i "due turni" ma per NEGARLI come readiness.
    assert "DUE tuoi turni consecutivi" in p and "NON significa «pronto»" in p
