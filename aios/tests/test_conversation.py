"""Conversazioni email L1: thread, bozza di risposta, invio solo via n8n (esterno)."""
import json
from types import SimpleNamespace

from aios.conversation import ConversationManager
from aios.llm import FakeLLM


class FakeClient:
    def __init__(self, rows):
        self.rows = rows
        self.inserts = []
        self.updates = []

    def select(self, table, params=None):
        if table == "email_messages":
            # filtro per id (eq.<id>) se presente
            idf = (params or {}).get("id")
            if idf and idf.startswith("eq."):
                return [r for r in self.rows if str(r.get("id")) == idf[3:]]
            return list(self.rows)
        return []

    def insert(self, table, row):
        self.inserts.append((table, row)); self.rows.append({**row, "id": "new"}); return [row]

    def update(self, table, filters, patch):
        self.updates.append((table, filters, patch)); return [patch]


def _mgr(rows, llm):
    platform = SimpleNamespace(kernel=SimpleNamespace(_supabase=FakeClient(rows),
                              audit=SimpleNamespace(append=lambda **k: None)),
                              agents={}, _founder=None)
    m = ConversationManager(platform, llm)
    return m, m.client


_INBOUND = {"id": "m1", "conversation_id": "c1", "message_id": "out-1", "direction": "in",
            "from_email": "mario@studio.it", "from_name": "Mario", "subject": "Info agenti AI",
            "body": "Mi spiegate come funziona?", "status": "ricevuto", "created_at": "2026-06-01"}


def test_threads_groups_and_flags_to_answer():
    m, _ = _mgr([dict(_INBOUND)], FakeLLM(["{}"]))
    th = m.threads()
    assert len(th) == 1 and th[0]["da_rispondere"] is True and th[0]["bozza"] is None
    assert th[0]["cliente"] == "Mario" and th[0]["email"] == "mario@studio.it"


def test_draft_reply_inserts_out_bozza():
    llm = FakeLLM([json.dumps({"reply_subject": "Re: Info agenti AI",
                               "reply_body": "Ciao Mario, ti diamo un agente che...",
                               "needs_human": False})])
    m, client = _mgr([dict(_INBOUND)], llm)
    res = m.draft_replies(limit=5)
    assert res["bozze_create"] == 1
    t, row = client.inserts[0]
    assert t == "email_messages" and row["direction"] == "out" and row["status"] == "bozza"
    assert row["to_email"] == "mario@studio.it" and row["reply_to_message_id"] == "out-1"
    assert "agente" in row["body"]


def test_draft_flags_needs_human_on_pricing():
    llm = FakeLLM([json.dumps({"reply_subject": "Re: prezzo",
                               "reply_body": "Ti risponde a breve Luigi coi dettagli.",
                               "needs_human": True})])
    m, client = _mgr([dict(_INBOUND, subject="Quanto costa?")], llm)
    m.draft_replies()
    _, row = client.inserts[0]
    assert row["needs_human"] is True


def test_send_requires_n8n_and_marks_sent(monkeypatch):
    monkeypatch.delenv("N8N_WEBHOOK_URL", raising=False)  # n8n non configurato
    draft = {"id": "d1", "conversation_id": "c1", "direction": "out", "to_email": "mario@studio.it",
             "subject": "Re", "body": "ciao", "status": "bozza", "reply_to_message_id": "out-1"}
    m, client = _mgr([draft], FakeLLM(["{}"]))
    out = m.send("d1")
    assert out["ok"] is False                 # senza webhook non parte
    assert client.updates == []               # quindi non marca 'inviato'


def test_discard_marks_scartata():
    draft = {"id": "d1", "direction": "out", "status": "bozza"}
    m, client = _mgr([draft], FakeLLM(["{}"]))
    assert m.discard("d1")["ok"] is True
    assert client.updates and client.updates[0][2] == {"status": "scartata"}
