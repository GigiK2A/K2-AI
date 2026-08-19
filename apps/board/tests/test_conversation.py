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
    # L'invio prenota (status='inviato') PRIMA di uscire, per non mandare due mail allo
    # stesso cliente, e ripristina se l'invio non parte: conta l'effetto NETTO, cioè che
    # la bozza resti disponibile e non risulti inviata.
    assert client.updates[-1][2] == {"status": "bozza"}
    assert not any(u[2].get("status") == "inviato" for u in client.updates[1:])


def test_discard_marks_scartata():
    draft = {"id": "d1", "direction": "out", "status": "bozza"}
    m, client = _mgr([draft], FakeLLM(["{}"]))
    assert m.discard("d1")["ok"] is True
    assert client.updates and client.updates[0][2] == {"status": "scartata"}


# ---- follow-up vendite sui lead del K-BOT ----
class LeadClient(FakeClient):
    def __init__(self, email_rows, leads):
        super().__init__(email_rows)
        self.leads = leads

    def select(self, table, params=None):
        if table == "kbot_sessions":
            return list(self.leads)
        return super().select(table, params)


def _lead_mgr(email_rows, leads, llm):
    platform = SimpleNamespace(kernel=SimpleNamespace(_supabase=LeadClient(email_rows, leads),
                              audit=SimpleNamespace(append=lambda **k: None)),
                              agents={}, _founder=None)
    m = ConversationManager(platform, llm)
    return m, m.client


_LEAD = {"id": "s1", "nome": "Studio Rossi", "email": "info@studiorossi.it",
         "sector": "ingegneria", "status": "completed", "messages": "[...]",
         "collected_data": "{}", "paid_at": None}


def test_followup_drafts_outbound_for_kbot_lead():
    llm = FakeLLM([json.dumps({"subject": "Dopo la diagnosi K2-AI",
                               "body": "Ciao Studio Rossi, ti propongo una call di 20 min.",
                               "needs_human": False})])
    m, client = _lead_mgr([], [dict(_LEAD)], llm)
    res = m.draft_lead_followups(limit=5)
    assert res["bozze_create"] == 1
    t, row = client.inserts[0]
    assert t == "email_messages" and row["direction"] == "out" and row["status"] == "bozza"
    assert row["conversation_id"] == "kbot:s1" and row["to_email"] == "info@studiorossi.it"


def test_followup_skips_lead_already_drafted():
    existing = {"id": "e1", "conversation_id": "kbot:s1", "direction": "out", "status": "bozza"}
    m, client = _lead_mgr([existing], [dict(_LEAD)], FakeLLM(["{}"]))
    assert m.draft_lead_followups()["bozze_create"] == 0
    assert client.inserts == []


def test_followup_thread_shows_lead_email_without_inbound():
    out_draft = {"id": "e1", "conversation_id": "kbot:s1", "direction": "out",
                 "to_email": "info@studiorossi.it", "from_name": "K2-AI",
                 "subject": "Follow-up", "body": "ciao", "status": "bozza", "created_at": "2026-06-12"}
    m, _ = _lead_mgr([out_draft], [], FakeLLM(["{}"]))
    th = m.threads()
    assert len(th) == 1 and th[0]["email"] == "info@studiorossi.it"
    assert th[0]["bozza"] is not None and th[0]["da_rispondere"] is False
