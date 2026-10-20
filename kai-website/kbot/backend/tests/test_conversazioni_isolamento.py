"""Conversazioni e titoli: ogni utente vede e modifica solo le proprie (verifica richiesta dall'audit del 20/10/2026)."""
import itertools

import pytest
from fastapi import HTTPException

from app.api import conversations as C
from app.lib.auth import AuthUser


class _Q:
    def __init__(self, db):
        self.db, self.filtri, self.op, self.payload, self.lim = db, [], "select", None, None

    def select(self, *a, **k): self.op = "select"; return self
    def insert(self, row): self.op, self.payload = "insert", row; return self
    def update(self, patch): self.op, self.payload = "update", patch; return self
    def eq(self, k, v): self.filtri.append(lambda r: str(r.get(k)) == str(v)); return self
    def is_(self, k, v): self.filtri.append(lambda r: r.get(k) is None); return self
    def order(self, *a, **k): return self
    def limit(self, n): self.lim = n; return self

    def execute(self):
        righe = [r for r in self.db.righe if all(f(r) for f in self.filtri)]
        if self.op == "insert":
            r = {"id": f"c{next(self.db.n)}", "created_at": "2026-10-20T10:00:00+00:00", "deleted_at": None, **self.payload}
            self.db.righe.append(r)
            return type("R", (), {"data": [r]})()
        if self.op == "update":
            for r in righe:
                r.update(self.payload)
            return type("R", (), {"data": righe})()
        return type("R", (), {"data": righe[: self.lim] if self.lim else righe})()


class _DB:
    def __init__(self):
        self.righe, self.n = [], itertools.count(1)

    def table(self, nome): return _Q(self)


@pytest.fixture
def db(monkeypatch):
    d = _DB()
    monkeypatch.setattr(C, "get_admin_client", lambda: d)
    return d


A = AuthUser(id="utente-A", email="a@example.com", has_paid=False, raw={})
B = AuthUser(id="utente-B", email="b@example.com", has_paid=False, raw={})


def _crea(utente, titolo):
    return C.create_conversation(C.CreateConversationBody(title=titolo), utente)["conversation"]


def test_la_lista_mostra_solo_le_proprie_pratiche(db):
    _crea(A, "Ammortamento computer")
    _crea(B, "Recupero fattura")
    assert [c["title"] for c in C.list_conversations(A)["conversations"]] == ["Ammortamento computer"]
    assert [c["title"] for c in C.list_conversations(B)["conversations"]] == ["Recupero fattura"]


def test_un_altro_utente_non_puo_rinominare_ne_cancellare(db):
    c = _crea(A, "Ammortamento computer")
    with pytest.raises(HTTPException) as e:
        C.update_conversation(c["id"], C.UpdateConversationBody(title="Rubato"), B)
    assert e.value.status_code in (403, 404)
    with pytest.raises(HTTPException):
        C.delete_conversation(c["id"], B)
    assert db.righe[0]["title"] == "Ammortamento computer" and db.righe[0]["deleted_at"] is None


def test_il_titolo_si_salva_e_resta_nella_lista(db):
    c = _crea(A, "Nuova pratica")
    C.update_conversation(c["id"], C.UpdateConversationBody(title="Ammortamento computer"), A)
    assert C.list_conversations(A)["conversations"][0]["title"] == "Ammortamento computer"


def test_il_titolo_e_limitato_e_non_puo_essere_vuoto(db):
    c = _crea(A, "x" * 500)
    assert len(c["title"]) <= 120
    C.update_conversation(c["id"], C.UpdateConversationBody(title="   "), A)
    assert db.righe[0]["title"]                                    # mai stringa vuota


def test_la_cancellazione_e_logica_e_sparisce_dalla_lista(db):
    c = _crea(A, "Server aziendale lento")
    C.delete_conversation(c["id"], A)
    assert C.list_conversations(A)["conversations"] == [] and db.righe[0]["deleted_at"]
