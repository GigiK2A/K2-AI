"""Autonomia interna: cosa può partire da solo e cosa resta all'owner.

Regola dell'owner (ago 2026): «non voglio dare autorizzazioni su cose banali; se qualcosa
legalmente è sbagliata l'agente la sistema in automatico senza chiedermelo, ma
dicendomelo». Il confine è quello: dentro l'azienda si fa e si riporta, fuori si chiede.
"""
import pytest

from aios.actuator import is_autonomous_internal
from aios.agents import esecuzione
from aios.autonomy import ActionType, AutonomyLevel
from aios.kernel import ExecOutcome, Kernel
from aios.tools import Tool

AZIONE = ActionType("legal", "azione")


def _kernel(risultato=None):
    k = Kernel()
    k.register_tool(Tool(name="azione", action_type=AZIONE,
                         run=lambda **kw: risultato or {"accettata": True}))
    k.policy.set_level(AZIONE, AutonomyLevel.L1_PROPOSE)
    return k


# ---- il confine ----
@pytest.mark.parametrize("azione", [
    {"tabella": "board_tasks", "op": "insert", "dati": {"title": "t"}},
    {"tabella": "pipeline_leads", "op": "update", "match": {"id": 1}, "dati": {"status": "won"}},
    {"tabella": "privacy_registro_trattamenti", "op": "insert", "dati": {"trattamento": "x"}},
])
def test_scritture_interne_sono_autonome(azione):
    assert is_autonomous_internal(azione) is True


@pytest.mark.parametrize("azione", [
    {"canale": "n8n", "workflow": "send_email", "payload": {"to": "a@b.it"}},
    {"canale": "instagram", "op": "publish"},
    {"tabella": "pipeline_leads", "op": "delete", "match": {"id": 1}},
    {"tipo": "ddl", "sql": "alter table board_tasks add column x text"},
    {"sql": "create index i on board_tasks(title)"},
])
def test_esterno_delete_e_ddl_restano_all_owner(azione):
    assert is_autonomous_internal(azione) is False


# ---- esecuzione immediata ----
def test_execute_now_salta_la_coda_ma_registra_in_audit():
    k = _kernel({"attuatore": {"ok": True, "tabella": "board_tasks", "op": "insert",
                               "righe": [{"id": 1}]}})
    res = k.execute_now("azione", actor="legal_agent", args={"titolo": "t"})
    assert res.outcome == ExecOutcome.EXECUTED
    assert res.eseguita_davvero is True
    assert k.approvals.pending() == []               # niente in coda
    assert k.audit.records()[-1].event == "executed"  # ma tracciato


def test_execute_now_rispetta_il_killswitch():
    k = _kernel()
    k.killswitch.engage(reason="stop")
    res = k.execute_now("azione", actor="legal_agent", args={"titolo": "t"})
    assert res.outcome == ExecOutcome.DENIED
    assert k.audit.records()[-1].event == "blocked_killswitch"


# ---- smistamento (interruttore spento/accesso) ----
def _proposta(azione):
    return {"tipo": "task", "titolo": "Titolo", "contenuto": "c", "motivo": "m",
            "azione": azione}


def test_senza_interruttore_tutto_va_in_coda(monkeypatch):
    monkeypatch.delenv("AIOS_INTERNAL_AUTONOMY", raising=False)
    k = _kernel()
    modo, out = esecuzione.applica_o_accoda(
        k, "azione", "legal_agent",
        _proposta({"tabella": "board_tasks", "op": "insert", "dati": {"title": "t"}}))
    assert modo == "in_coda" and out is not None
    assert len(k.approvals.pending()) == 1


def test_con_interruttore_l_interno_parte_e_si_riporta(monkeypatch):
    monkeypatch.setenv("AIOS_INTERNAL_AUTONOMY", "1")
    k = _kernel({"attuatore": {"ok": True, "tabella": "board_tasks", "op": "insert",
                               "righe": [{"id": 1}]}})
    modo, out = esecuzione.applica_o_accoda(
        k, "azione", "legal_agent",
        _proposta({"tabella": "board_tasks", "op": "insert", "dati": {"title": "t"}}))
    assert modo == "eseguita"
    assert out["ok"] is True and out["tabella"] == "board_tasks"
    assert k.approvals.pending() == []


def test_con_interruttore_l_esterno_resta_in_coda(monkeypatch):
    """Anche in autonomia piena, una email al cliente la decide l'owner."""
    monkeypatch.setenv("AIOS_INTERNAL_AUTONOMY", "1")
    k = _kernel()
    modo, _out = esecuzione.applica_o_accoda(
        k, "azione", "legal_agent",
        _proposta({"canale": "n8n", "workflow": "send_email", "payload": {"to": "a@b.it"}}))
    assert modo == "in_coda"
    assert len(k.approvals.pending()) == 1


def test_fallimento_autonomo_viene_riportato_non_nascosto(monkeypatch):
    monkeypatch.setenv("AIOS_INTERNAL_AUTONOMY", "1")
    k = _kernel({"attuatore": {"ok": False, "errore": "nessun campo riconosciuto",
                               "tabella": "policy_register"}})
    _modo, out = esecuzione.applica_o_accoda(
        k, "azione", "legal_agent",
        _proposta({"tabella": "policy_register", "op": "update",
                   "match": {"policy_name": "Privacy"}, "dati": {"version": "2"}}))
    assert out["ok"] is False and "nessun campo" in out["errore"]
    assert k.audit.records()[-1].event == "failed"


# ---- riepilogo per l'owner ----
def test_riepilogo_raggruppa_i_successi_e_dettaglia_i_fallimenti():
    testo = esecuzione.riepilogo([
        {"titolo": "A", "tabella": "board_tasks", "op": "insert", "ok": True},
        {"titolo": "B", "tabella": "board_tasks", "op": "insert", "ok": True},
        {"titolo": "C", "tabella": "pipeline_leads", "op": "update", "ok": True},
        {"titolo": "Registro AI Act", "tabella": "policy_register", "op": "update",
         "ok": False, "errore": "nessuna riga corrisponde al match"},
    ])
    assert "3 scritture interne fatte da sole" in testo
    assert "board_tasks×2" in testo and "pipeline_leads" in testo
    assert "Registro AI Act" in testo and "nessuna riga" in testo


def test_riepilogo_vuoto_se_non_c_e_niente_da_dire():
    assert esecuzione.riepilogo([]) == ""
