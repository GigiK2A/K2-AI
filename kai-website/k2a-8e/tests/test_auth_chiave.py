"""Chiave API del motore 8e: la chiave predefinita nel codice non deve aprire un servizio con dominio pubblico (test 31)."""
import pytest
from fastapi import HTTPException

from app import auth

PRED = "k2a-8e-internal-loopback"


def prova(token, monkeypatch, api="chiave-vera-lunga", nxt=None, rifiuta=False):
    monkeypatch.setattr(auth, "API_KEY", api)
    monkeypatch.setattr(auth, "API_KEY_NEXT", nxt)
    monkeypatch.setenv("K2A_8E_REJECT_DEFAULT", "1" if rifiuta else "0")
    try:
        auth.require_bearer(f"Bearer {token}" if token is not None else None)
        return 200
    except HTTPException as e:
        return e.status_code


def test_comportamento_attuale_invariato_finche_l_interruttore_e_spento(monkeypatch):
    assert prova(PRED, monkeypatch) == 200                                   # compatibilità: il backend oggi manda il valore predefinito
    assert prova("chiave-vera-lunga", monkeypatch) == 200 and prova("sbagliata", monkeypatch) == 403 and prova(None, monkeypatch) == 401


def test_con_l_interruttore_acceso_la_chiave_predefinita_e_rifiutata(monkeypatch):
    assert prova(PRED, monkeypatch, rifiuta=True) == 403
    assert prova("chiave-vera-lunga", monkeypatch, rifiuta=True) == 200
    assert prova(PRED, monkeypatch, api=PRED, rifiuta=True) == 403           # nemmeno se è quella configurata: ci vuole una chiave vera
    assert prova(None, monkeypatch, rifiuta=True) == 401


def test_rotazione_senza_interruzione_la_vecchia_e_la_nuova_insieme(monkeypatch):
    assert prova("nuova", monkeypatch, api="vecchia", nxt="nuova", rifiuta=True) == 200
    assert prova("vecchia", monkeypatch, api="vecchia", nxt="nuova", rifiuta=True) == 200
    assert prova("altra", monkeypatch, api="vecchia", nxt="nuova", rifiuta=True) == 403


def test_il_confronto_e_a_tempo_costante():
    import inspect
    assert "compare_digest" in inspect.getsource(auth.require_bearer)
