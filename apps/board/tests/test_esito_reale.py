"""Un'azione approvata deve riportare quello che è successo DAVVERO.

Il caso che questi test bloccano: l'attuatore non solleva mai — incapsula i suoi
fallimenti nel valore di ritorno. Prima, chi leggeva solo ExecOutcome.EXECUTED
concludeva "riuscito" e scriveva "✅ Approvato ed eseguito" su Telegram anche
quando non era partito nulla.
"""
from aios.autonomy import ActionType, AutonomyLevel
from aios.kernel import Kernel, ExecOutcome, esito_effettivo
from aios.notify import telegram
from aios.tools import Tool

AZIONE = ActionType("finance", "azione")


def _kernel_con_esito(esito):
    """Kernel con un tool che imita agents/domain.py: ritorna l'esito dell'attuatore
    dentro il risultato invece di sollevare."""
    k = Kernel()
    k.register_tool(Tool(name="proponi", action_type=AZIONE,
                         run=lambda **kw: {"accettata": True, "attuatore": esito}))
    k.policy.set_level(AZIONE, AutonomyLevel.L1_PROPOSE)
    k.policy.set_cap(AZIONE, AutonomyLevel.L1_PROPOSE)
    return k


# ─── estrazione esito ────────────────────────────────────────────────────────

def test_esito_none_se_il_tool_non_riporta_nulla():
    assert esito_effettivo({"accettata": True}) is None
    assert esito_effettivo("non un dict") is None


def test_esito_estrae_fallimento_con_causa():
    es = esito_effettivo({"attuatore": {"ok": False, "errore": "tabella non in allowlist: x"}})
    assert es == {"ok": False, "errore": "tabella non in allowlist: x"}


def test_esito_estrae_scrittura_riuscita():
    es = esito_effettivo({"attuatore": {"ok": True, "tabella": "board_tasks",
                                        "op": "insert", "righe": [{"id": 1}]}})
    assert es["ok"] is True and es["tabella"] == "board_tasks" and es["righe"] == 1


# ─── il kernel distingue eseguito da riuscito ────────────────────────────────

def test_attuatore_fallito_non_e_eseguito_davvero():
    k = _kernel_con_esito({"ok": False, "errore": "n8n non configurato"})
    appr_id = k.execute("proponi", actor="finance_agent", args={}).approval_id
    res = k.resolve_approval(appr_id, approve=True)
    # il kernel ha "eseguito" il tool, ma l'azione non è arrivata a destinazione
    assert res.outcome == ExecOutcome.EXECUTED
    assert res.eseguita_davvero is False
    assert res.esito["errore"] == "n8n non configurato"


def test_attuatore_riuscito_e_eseguito_davvero():
    k = _kernel_con_esito({"ok": True, "tabella": "board_tasks", "op": "insert"})
    appr_id = k.execute("proponi", actor="finance_agent", args={}).approval_id
    res = k.resolve_approval(appr_id, approve=True)
    assert res.eseguita_davvero is True


def test_azione_senza_attuatore_resta_eseguita():
    """Un tool che non usa l'attuatore (es. lettura) non deve risultare fallito."""
    k = Kernel()
    k.register_tool(Tool(name="semplice", action_type=AZIONE, run=lambda **kw: {"ok": True}))
    k.policy.set_level(AZIONE, AutonomyLevel.L2_ROUTINE)
    res = k.execute("semplice", actor="x", args={})
    assert res.eseguita_davvero is True


# ─── l'audit conserva la prova ───────────────────────────────────────────────

def test_audit_registra_il_fallimento_come_failed():
    k = _kernel_con_esito({"ok": False, "errore": "colonna inesistente"})
    appr_id = k.execute("proponi", actor="finance_agent", args={}).approval_id
    k.resolve_approval(appr_id, approve=True)
    ultimo = k.audit.records()[-1]
    assert ultimo.event == "failed"
    assert ultimo.detail["esito"]["errore"] == "colonna inesistente"


def test_audit_registra_il_successo_come_executed():
    k = _kernel_con_esito({"ok": True, "tabella": "invoices", "op": "insert"})
    appr_id = k.execute("proponi", actor="finance_agent", args={}).approval_id
    k.resolve_approval(appr_id, approve=True)
    ultimo = k.audit.records()[-1]
    assert ultimo.event == "executed"
    assert ultimo.detail["esito"]["ok"] is True


# ─── il messaggio all'umano non mente ────────────────────────────────────────

def test_riga_fallimento_non_dice_mai_eseguito():
    riga = telegram.esito_riga({"ok": False, "errore": "n8n non configurato"})
    assert "NON eseguito" in riga
    assert "n8n non configurato" in riga


def test_riga_fallimento_senza_causa_lo_ammette():
    riga = telegram.esito_riga({"ok": False})
    assert "NON eseguito" in riga and "non riportata" in riga


def test_riga_successo_dice_cosa_ha_scritto():
    riga = telegram.esito_riga({"ok": True, "tabella": "board_tasks", "op": "insert", "righe": 1})
    assert "insert su board_tasks" in riga and "1 righe" in riga


def test_riga_successo_esterno_nomina_il_workflow():
    riga = telegram.esito_riga({"ok": True, "canale": "n8n", "workflow": "send_email"})
    assert "n8n" in riga and "send_email" in riga
