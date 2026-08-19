"""Autonomia interna cablata: l'interno parte da solo, l'esterno resta in coda.

Autorizzata dall'owner il 19 ago 2026: «non voglio dare autorizzazioni su cose banali;
se qualcosa legalmente è sbagliata l'agente la sistema e me lo dice».
"""
from aios.agents.domain import DomainAgent, DomainConfig
from aios.autonomy import ActionType
from aios.founder import default_founder_model
from aios.kernel import Kernel
from aios.llm import FakeLLM

INTERNA = ('{"proposte":[{"tipo":"task","titolo":"Registro trattamenti K-BOT",'
           '"contenuto":"c","motivo":"m","azione":{"tabella":"board_tasks","op":"insert",'
           '"dati":{"title":"Registro trattamenti K-BOT","priority":"media"}}}]}')
ESTERNA = ('{"proposte":[{"tipo":"email","titolo":"Scrivi al lead","contenuto":"c",'
           '"motivo":"m","azione":{"canale":"n8n","workflow":"send_email",'
           '"payload":{"to":"cliente@example.it","subject":"s","body":"b"}}}]}')


class FakeClient:
    def __init__(self):
        self.inserts = []

    def insert(self, table, row):
        self.inserts.append((table, row))
        return [{"id": len(self.inserts) + 1, **row}]

    def update(self, table, filters, patch):
        return [{"id": 1, **patch}]

    def select(self, table, params):
        return []


def _agente(risposta):
    k = Kernel()
    cfg = DomainConfig(name="legal", action=ActionType("legal", "azione"),
                       tool_name="azione_legal", sensors=[], system="Sei il legale.")
    return k, DomainAgent(kernel=k, llm=FakeLLM(responses=[risposta]),
                          founder=default_founder_model(), config=cfg,
                          deliverable_client=FakeClient())


def test_interno_parte_da_solo_e_viene_riportato(monkeypatch):
    monkeypatch.setenv("AIOS_INTERNAL_AUTONOMY", "1")
    k, ag = _agente(INTERNA)
    res = ag.run()
    assert k.approvals.pending() == []            # niente da approvare
    assert len(res.eseguite) == 1                 # ...ma qualcosa è stato fatto
    assert res.eseguite[0]["ok"] is True
    assert res.eseguite[0]["tabella"] == "board_tasks"
    assert k.audit.records()[-1].event == "executed"


def test_esterno_resta_all_owner_anche_in_autonomia(monkeypatch):
    monkeypatch.setenv("AIOS_INTERNAL_AUTONOMY", "1")
    k, ag = _agente(ESTERNA)
    res = ag.run()
    assert len(k.approvals.pending()) == 1        # una email la decide l'owner
    assert res.eseguite == []


def test_senza_interruttore_niente_cambia(monkeypatch):
    monkeypatch.delenv("AIOS_INTERNAL_AUTONOMY", raising=False)
    k, ag = _agente(INTERNA)
    res = ag.run()
    assert len(k.approvals.pending()) == 1
    assert res.eseguite == []
