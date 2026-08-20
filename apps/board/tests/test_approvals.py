from aios.approvals import ApprovalQueue, Approval, ApprovalStatus


def test_enqueue_returns_pending():
    q = ApprovalQueue()
    appr = q.enqueue(action_key="marketing.social.publish_post",
                     actor="marketing_agent", payload={"caption": "ciao"})
    assert isinstance(appr, Approval)
    assert appr.status == ApprovalStatus.PENDING
    assert q.pending()[0].id == appr.id


def test_approve_removes_from_pending_and_is_clean():
    q = ApprovalQueue()
    appr = q.enqueue(action_key="a.b", actor="x", payload={})
    resolved = q.approve(appr.id)
    assert resolved.status == ApprovalStatus.APPROVED
    assert resolved.clean is True
    assert q.pending() == []


def test_edit_then_approve_is_not_clean():
    q = ApprovalQueue()
    appr = q.enqueue(action_key="a.b", actor="x", payload={"caption": "ciao"})
    resolved = q.approve(appr.id, edited_payload={"caption": "ciao corretto"})
    assert resolved.status == ApprovalStatus.APPROVED
    assert resolved.clean is False
    assert resolved.payload == {"caption": "ciao corretto"}


def test_reject_is_not_clean():
    q = ApprovalQueue()
    appr = q.enqueue(action_key="a.b", actor="x", payload={})
    resolved = q.reject(appr.id, reason="off-brand")
    assert resolved.status == ApprovalStatus.REJECTED
    assert resolved.clean is False
    assert resolved.reason == "off-brand"


# ---- com'è finita resta scritto sulla riga ----
# «APPROVED» dice solo che l'owner ha cliccato: in produzione le 86 righe approvate
# hanno reason a NULL e dal cockpit non si distingue un'esecuzione riuscita da una
# che l'attuatore ha rifiutato.

def test_esito_riuscito_scritto_sulla_riga():
    from aios.autonomy import ActionType, AutonomyLevel
    from aios.kernel import Kernel
    from aios.tools import Tool
    az = ActionType("legal", "azione")
    k = Kernel()
    k.register_tool(Tool(name="azione", action_type=az, run=lambda **kw: {
        "attuatore": {"ok": True, "tabella": "board_tasks", "op": "insert",
                      "righe": [{"id": 1}]}}))
    k.policy.set_level(az, AutonomyLevel.L1_PROPOSE)
    res = k.execute("azione", actor="legal_agent", args={"titolo": "t"})
    k.resolve_approval(res.approval_id, approve=True)
    assert k.approvals.get(res.approval_id).reason == "eseguita — insert su board_tasks (1 righe)"


def test_esito_fallito_scritto_sulla_riga_con_la_causa():
    from aios.autonomy import ActionType, AutonomyLevel
    from aios.kernel import Kernel
    from aios.tools import Tool
    az = ActionType("legal", "azione")
    k = Kernel()
    k.register_tool(Tool(name="azione", action_type=az, run=lambda **kw: {
        "attuatore": {"ok": False, "errore": "nessuna riga di policy_register corrisponde"}}))
    k.policy.set_level(az, AutonomyLevel.L1_PROPOSE)
    res = k.execute("azione", actor="legal_agent", args={"titolo": "t"})
    k.resolve_approval(res.approval_id, approve=True)
    motivo = k.approvals.get(res.approval_id).reason
    assert motivo.startswith("NON eseguita")
    assert "policy_register" in motivo


def test_esito_testo_riassume_i_casi():
    from aios.kernel import esito_testo
    assert esito_testo(None) == "eseguita"
    assert esito_testo({"ok": True, "canale": "n8n", "workflow": "send_email"}) == (
        "eseguita — inviata a n8n, workflow «send_email»")
    assert esito_testo({"ok": False}) == "NON eseguita — causa non riportata"
