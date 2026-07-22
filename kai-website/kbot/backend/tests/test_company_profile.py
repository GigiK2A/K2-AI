"""Dati azienda sull'account (review): ragione sociale/P.IVA/ATECO ecc. impostati una volta
(dashboard/signup) e presi dall'account — iniettati nel prompt, non richiesti in ogni chat.
"""
import os
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("KBOT_PROFILE_MEMORY", "1")

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

import pytest  # noqa: E402
from app.lib import profile as P  # noqa: E402


# ── store Supabase finto (in-memory), patchato dove profile.py lo usa ────────────────────
class _Row:
    def __init__(self, data):
        self.data = data


class _Table:
    def __init__(self, store):
        self._store, self._eq, self._row = store, None, None

    def select(self, _c):
        return self

    def eq(self, _k, v):
        self._eq = v
        return self

    def limit(self, _n):
        return self

    def upsert(self, row):
        self._row = row
        return self

    def execute(self):
        if self._row is not None:
            self._store[self._row["user_id"]] = self._row["profile"]
            return _Row([self._row])
        rows = [{"profile": self._store[self._eq]}] if self._eq in self._store else []
        return _Row(rows)


class _Client:
    def __init__(self, store):
        self._store = store

    def table(self, _t):
        return _Table(self._store)


@pytest.fixture()
def fake_store(monkeypatch):
    store: dict = {}
    monkeypatch.setattr(P, "get_admin_client", lambda: _Client(store))
    return store


def test_save_and_load_roundtrip(fake_store):
    assert P.load_anagrafica("u1") == {}
    saved = P.save_anagrafica("u1", {
        "ragione_sociale": "Rossi Impianti Srl", "partita_iva": "03655920548",
        "codice_ateco": "43.21.01", "settore": "impianti elettrici", "dipendenti": "12"})
    assert saved["ragione_sociale"] == "Rossi Impianti Srl"
    assert saved["partita_iva"] == "03655920548" and saved["codice_ateco"] == "43.21.01"
    assert P.load_anagrafica("u1") == saved


def test_empty_field_removes_value(fake_store):
    P.save_anagrafica("u2", {"ragione_sociale": "ACME Srl", "dipendenti": "10"})
    P.save_anagrafica("u2", {"dipendenti": ""})           # vuoto → rimuove
    ana = P.load_anagrafica("u2")
    assert "dipendenti" not in ana and ana["ragione_sociale"] == "ACME Srl"


def test_partial_update_keeps_other_fields(fake_store):
    P.save_anagrafica("u3", {"ragione_sociale": "Beta Srl", "settore": "edilizia"})
    P.save_anagrafica("u3", {"codice_ateco": "41.20.00"})  # aggiunge senza toccare gli altri
    ana = P.load_anagrafica("u3")
    assert ana["ragione_sociale"] == "Beta Srl" and ana["settore"] == "edilizia"
    assert ana["codice_ateco"] == "41.20.00"


def test_injected_into_prompt_block(fake_store):
    P.save_anagrafica("u4", {"ragione_sociale": "Gamma Spa", "partita_iva": "12345678901",
                             "codice_ateco": "62.01.00"})
    block = P.render_block(P.load("u4"))
    assert "PROFILO CLIENTE" in block
    assert "Gamma Spa" in block and "Partita IVA" in block and "Codice ATECO" in block


def test_only_known_fields_saved(fake_store):
    # campi ignoti non finiscono nell'anagrafica
    P.save_anagrafica("u5", {"ragione_sociale": "Delta Srl", "hacked": "x", "role": "admin"})
    ana = P.load_anagrafica("u5")
    assert ana == {"ragione_sociale": "Delta Srl"}


def test_disabled_load_returns_empty(monkeypatch):
    monkeypatch.setenv("KBOT_PROFILE_MEMORY", "0")
    assert P.load_anagrafica("u6") == {}


def test_seed_from_signup_metadata(fake_store):
    # primo accesso: anagrafica vuota → seed da company_name/work_sector del signup
    seeded = P.seed_from_metadata("u7", {"company_name": "Nuova Impresa Srl",
                                         "work_sector": "logistica"})
    assert seeded == {"ragione_sociale": "Nuova Impresa Srl", "settore": "logistica"}
    assert P.load_anagrafica("u7") == seeded


def test_seed_does_not_overwrite_existing(fake_store):
    P.save_anagrafica("u8", {"ragione_sociale": "Già Impostata Srl"})
    # con anagrafica già presente il seed NON sovrascrive
    out = P.seed_from_metadata("u8", {"company_name": "Altro Nome Srl"})
    assert out["ragione_sociale"] == "Già Impostata Srl"


def test_seed_no_metadata_noop(fake_store):
    assert P.seed_from_metadata("u9", {}) == {}
    assert P.load_anagrafica("u9") == {}
