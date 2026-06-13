"""Prospecting qualificato: ricerca → valutazione fit → bozza (mai inviata)."""
from aios.prospecting import Prospector, prospects_tool
from aios.llm import FakeLLM
from aios.founder import default_founder_model

_RESEARCH = "Studio Rossi Ingegneria (rossi.it) — PMI servizi tecnici. BigCorp SpA — multinazionale."
_STRUCT = (
    '{"prospects":['
    '{"company":"Studio Rossi Ingegneria","website":"rossi.it","sector":"ingegneria",'
    '"in_target":true,"fit_score":85,"fit_reason":"PMI servizi tecnici, onboarding manuale",'
    '"contact_email":"info@rossi.it","contact_role":"ufficio","email_source":"sito",'
    '"draft_subject":"Recupera ore sulle email","draft_body":"Ciao, ti diamo un agente che..."},'
    '{"company":"BigCorp SpA","in_target":false,"fit_score":15,'
    '"fit_reason":"multinazionale, fuori target"}]}'
)


def _prospector():
    return Prospector(llm_web=FakeLLM([_RESEARCH]), llm_struct=FakeLLM([_STRUCT]),
                      founder=default_founder_model(),
                      suite_reader=lambda: [{"Servizio": "Agenti email & CRM"}])


def test_find_returns_evaluated_prospects():
    out = _prospector().find(n=2)
    assert len(out) == 2
    rossi = out[0]
    assert rossi["in_target"] is True and rossi["fit_score"] == 85
    assert rossi["contact_email"] == "info@rossi.it"
    assert rossi["draft_subject"] and rossi["draft_body"]  # bozza presente
    assert out[1]["in_target"] is False  # fuffa marcata, non in target


def test_to_row_maps_and_is_draft_only():
    p = _prospector().find(n=2)[0]
    row = Prospector.to_row(p)
    assert row["company"] == "Studio Rossi Ingegneria"
    assert row["status"] == "nuovo"
    assert row["draft_body"] and row["contact_email"] == "info@rossi.it"
    # nessun campo/azione di invio: la bozza resta tale
    assert "sent" not in row and "inviato" not in row and "send" not in row


def test_context_includes_icp_and_services():
    ctx = _prospector()._context()
    assert "PMI" in ctx and "Agenti email" in ctx  # ICP founder + catalogo suite


def test_prospects_tool_readonly_and_graceful():
    class C:
        def select(self, t, p): return [{"company": "X", "status": "nuovo"}]
    tool = prospects_tool(C())
    assert tool.action_type is None and tool.readonly is True
    assert tool.run()[0]["company"] == "X"

    class Bad:
        def select(self, t, p): raise RuntimeError("no table")
    assert prospects_tool(Bad()).run() == []  # degrada a []
