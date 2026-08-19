"""Ogni sensore configurato deve esistere davvero tra i tool registrati.

Bug reale, fatto e corretto il 19 ago 2026: nella lista sensori del marketing erano
finiti `leggi_prospect` e `leggi_competitor`, mentre i tool si chiamano `leggi_prospects`
e `leggi_competitor_trovati`. Due voci morte: `if opt in names` era semplicemente falso,
l'agente non leggeva quei dati e nessuno se ne accorgeva — né un errore, né un log.

Questo test rende quel refuso impossibile: confronta i nomi che gli agenti CHIEDONO con
quelli che le factory dei sensori REGISTRANO.
"""
import re
from pathlib import Path

import pytest

from aios.agents.finance_config import FINANCE_CONFIG
from aios.agents.hr_config import HR_CONFIG
from aios.agents.legal_config import LEGAL_CONFIG
from aios.agents.operations_config import OPERATIONS_CONFIG
from aios.agents.sales_config import SALES_CONFIG

SRC = Path(__file__).resolve().parents[1] / "src" / "aios"
CONFIGS = [SALES_CONFIG, FINANCE_CONFIG, OPERATIONS_CONFIG, LEGAL_CONFIG, HR_CONFIG]


def _nomi_registrati() -> set[str]:
    """Tutti i nomi di tool che il codice registra, letti dai sorgenti.

    Si guarda il testo e non il registry vivo perché costruire la piattaforma vera
    richiede credenziali (Supabase, Anthropic, Instagram) che i test non hanno."""
    nomi: set[str] = set()
    for f in SRC.rglob("*.py"):
        if f.parts[-2:] == ("agents", "marketing.py") or "agents" in f.parts:
            continue        # gli agenti CHIEDONO i sensori, non li registrano
        testo = f.read_text(encoding="utf-8")
        # Tool(name="x", ...) diretto
        nomi |= set(re.findall(r'Tool\(\s*name="([a-z_]+)"', testo))
        # helper table-driven: _ro("leggi_x", "tabella"), _sensor("leggi_y", ...)
        nomi |= set(re.findall(r'_(?:ro|sensor|sensore|tool)\(\s*"([a-z_]+)"', testo))
        # registrazioni con nome in variabile: name=<nome>, preceduto da "leggi_..."
        nomi |= set(re.findall(r'name="([a-z_]+)",\s*action_type=None', testo))
    return nomi


def _sensori_marketing() -> set[str]:
    """I nomi che MarketingAgent._gather chiede, estratti dal sorgente."""
    testo = (SRC / "agents" / "marketing.py").read_text(encoding="utf-8")
    corpo = testo.split("def _gather")[1].split("def _stato_fonti")[0]
    return set(re.findall(r'"(leggi_[a-z_]+)"', corpo)) | set(
        re.findall(r'"(analizza_competitor)"', corpo))


def test_almeno_i_sensori_noti_sono_registrati():
    """Guardia sul metodo di estrazione: se questo salta, il test sotto è inutile."""
    nomi = _nomi_registrati()
    for atteso in ("leggi_lead", "leggi_prospects", "leggi_suite", "leggi_profilo_ig"):
        assert atteso in nomi, f"estrazione rotta: {atteso} non trovato nei sorgenti"


@pytest.mark.parametrize("cfg", CONFIGS, ids=[c.name for c in CONFIGS])
def test_i_sensori_dei_reparti_esistono(cfg):
    nomi = _nomi_registrati()
    mancanti = sorted({t for t, _a in cfg.sensors} - nomi)
    assert not mancanti, (
        f"il reparto {cfg.name} chiede sensori che nessuno registra: {mancanti}. "
        "Non darebbero errore: `if tool in names` sarebbe falso e quei dati non "
        "arriverebbero mai all'agente, in silenzio.")


def test_i_sensori_del_marketing_esistono():
    nomi = _nomi_registrati()
    chiesti = _sensori_marketing()
    # guardia anti-vacuità: se l'estrazione non trovasse nulla, il test passerebbe
    # senza controllare niente
    assert "leggi_prospects" in chiesti and len(chiesti) >= 15, \
        f"estrazione dei sensori chiesti sospetta: {sorted(chiesti)}"
    mancanti = sorted(chiesti - nomi)
    assert not mancanti, (
        f"il marketing chiede sensori inesistenti: {mancanti} — è esattamente il refuso "
        "leggi_prospect/leggi_prospects del 19 ago 2026.")
