"""La coda di approvazione resta gestibile: niente doppioni, tetto per reparto.

Regressione vera: gli agenti hanno accumulato 646 decisioni in attesa per una quarantina
di intenzioni reali, riproposte ad ogni heartbeat con parole diverse. Una coda così non si
decide: si annulla in blocco (ed è quello che è successo il 18 ago 2026).
"""
from aios.autonomy import ActionType, AutonomyLevel
from aios.kernel import ExecOutcome, Kernel
from aios.tools import Tool

AZIONE = ActionType("finance", "azione")


def _kernel(coda_max=20):
    k = Kernel(coda_max=coda_max)
    k.register_tool(Tool(name="azione", action_type=AZIONE, run=lambda **kw: {"ok": True}))
    k.policy.set_level(AZIONE, AutonomyLevel.L1_PROPOSE)
    return k


def _proposta(titolo, tabella="board_tasks", op="insert"):
    return {"tipo": "task", "titolo": titolo, "contenuto": "c", "motivo": "m",
            "azione": {"tabella": tabella, "op": op, "dati": {"title": titolo}}}


def test_stessa_proposta_non_si_accoda_due_volte():
    k = _kernel()
    a = k.execute("azione", actor="finance_agent", args=_proposta("Fatture scadute > 30 gg"))
    b = k.execute("azione", actor="finance_agent", args=_proposta("Fatture scadute > 30 gg"))
    assert a.approval_id == b.approval_id
    assert len(k.approvals.pending()) == 1
    assert k.audit.records()[-1].event == "duplicate"


def test_regge_la_riformulazione_dell_llm():
    """Titoli diversi, stessa cosa: è il caso che ha gonfiato la coda."""
    k = _kernel()
    a = k.execute("azione", actor="finance_agent", args=_proposta("Fatture scadute > 30 gg"))
    b = k.execute("azione", actor="finance_agent",
                  args=_proposta("Solleciti fatture scadute >30 gg"))
    assert a.approval_id == b.approval_id
    assert len(k.approvals.pending()) == 1


def test_intenzioni_diverse_restano_due():
    k = _kernel()
    k.execute("azione", actor="finance_agent", args=_proposta("Fatture scadute > 30 gg"))
    k.execute("azione", actor="finance_agent", args=_proposta("Promemoria scadenze IVA"))
    assert len(k.approvals.pending()) == 2


def test_stesso_titolo_ma_altra_tabella_non_e_un_doppione():
    k = _kernel()
    k.execute("azione", actor="finance_agent", args=_proposta("Costo hosting mensile"))
    k.execute("azione", actor="finance_agent",
              args=_proposta("Costo hosting mensile", tabella="board_cost_items"))
    assert len(k.approvals.pending()) == 2


def test_tetto_per_reparto_ferma_l_accumulo():
    k = _kernel(coda_max=2)
    for titolo in ("Sollecito fatture insolute", "Chiusura contabile mensile"):
        assert k.execute("azione", actor="finance_agent",
                         args=_proposta(titolo)).outcome == ExecOutcome.QUEUED
    terza = k.execute("azione", actor="finance_agent",
                      args=_proposta("Analisi margini per tier"))
    assert terza.outcome == ExecOutcome.DENIED
    assert terza.approval_id is None
    assert len(k.approvals.pending()) == 2
    ultimo = k.audit.records()[-1]
    assert ultimo.event == "queue_full"
    assert ultimo.detail["tetto"] == 2


def test_il_tetto_si_riapre_quando_decidi():
    k = _kernel(coda_max=1)
    prima = k.execute("azione", actor="finance_agent",
                      args=_proposta("Sollecito fatture insolute"))
    assert k.execute("azione", actor="finance_agent",
                     args=_proposta("Chiusura contabile mensile")).outcome == ExecOutcome.DENIED
    k.resolve_approval(prima.approval_id, approve=False, reason="non serve")
    assert k.execute("azione", actor="finance_agent",
                     args=_proposta("Chiusura contabile mensile")).outcome == ExecOutcome.QUEUED
