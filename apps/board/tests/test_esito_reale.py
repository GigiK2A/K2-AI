"""L'approvazione riporta l'esito REALE: 'executed' dal kernel non vuol dire riuscito.

Regressione vera (verificata su Supabase, ago 2026): 10 insert approvati su
privacy_registro_trattamenti, 6 update su policy_register e 3 su pipeline_leads non
avevano scritto NIENTE, e Telegram aveva risposto "✅ Approvato ed eseguito" a tutti.
Questi test bloccano il ritorno di quel silenzio.
"""
import pytest

from aios.actuator import ActuatorError, apply_action, preflight, segnaposto, validate
from aios.autonomy import ActionType, AutonomyLevel
from aios.kernel import ExecOutcome, Kernel, esito_effettivo
from aios.notify import telegram
from aios.tools import Tool

AZIONE = ActionType("vendite", "azione")


def _kernel_in_coda(risultato):
    """Kernel con un tool di dominio che ritorna `risultato`, azione in coda L1."""
    k = Kernel()
    k.register_tool(Tool(name="azione", action_type=AZIONE, run=lambda **kw: risultato))
    k.policy.set_level(AZIONE, AutonomyLevel.L1_PROPOSE)
    return k


class ClientVuoto:
    """Supabase che non trova niente: update/delete a vuoto, come una tabella vuota."""

    def insert(self, table, row):
        return [{"id": 1, **row}]

    def update(self, table, filters, patch):
        return []

    def delete(self, table, filters):
        return []


# ---- lettura dell'esito ----
def test_esito_effettivo_legge_l_attuatore():
    es = esito_effettivo({"accettata": True, "attuatore": {
        "ok": False, "errore": "colonna inesistente", "tabella": "pipeline_leads",
        "op": "insert"}})
    assert es == {"ok": False, "errore": "colonna inesistente",
                  "tabella": "pipeline_leads", "op": "insert"}


def test_esito_effettivo_none_se_il_tool_non_ne_riporta():
    assert esito_effettivo({"accettata": True}) is None
    assert esito_effettivo("non un dict") is None


def test_righe_lista_diventa_conteggio():
    es = esito_effettivo({"attuatore": {"ok": True, "op": "update", "tabella": "t",
                                        "righe": [{"id": 1}, {"id": 2}]}})
    assert es["righe"] == 2


# ---- kernel: EXECUTED ≠ eseguita ----
def test_approvazione_con_attuatore_fallito_non_e_eseguita():
    k = _kernel_in_coda({"accettata": True,
                         "attuatore": {"ok": False, "errore": "colonna inesistente"}})
    q = k.execute("azione", actor="vendite_agent", args={"titolo": "t"})
    res = k.resolve_approval(q.approval_id, approve=True)
    assert res.outcome == ExecOutcome.EXECUTED      # il kernel ha girato…
    assert res.eseguita_davvero is False            # …ma l'azione non è arrivata
    assert res.esito["errore"] == "colonna inesistente"


def test_il_fallimento_finisce_in_audit_come_failed():
    k = _kernel_in_coda({"attuatore": {"ok": False, "errore": "boom"}})
    q = k.execute("azione", actor="vendite_agent", args={"titolo": "t"})
    k.resolve_approval(q.approval_id, approve=True)
    ultimo = k.audit.records()[-1]
    assert ultimo.event == "failed"
    assert ultimo.detail["esito"]["ok"] is False


def test_successo_resta_executed_ed_eseguita():
    k = _kernel_in_coda({"attuatore": {"ok": True, "tabella": "board_tasks",
                                       "op": "insert", "righe": [{"id": 1}]}})
    q = k.execute("azione", actor="vendite_agent", args={"titolo": "t"})
    res = k.resolve_approval(q.approval_id, approve=True)
    assert res.eseguita_davvero is True
    assert k.audit.records()[-1].event == "executed"


# ---- frase riportata all'umano ----
def test_riga_telegram_distingue_i_casi():
    assert telegram.esito_riga(None).startswith("✅")
    fallita = telegram.esito_riga({"ok": False, "errore": "N8N_WEBHOOK_URL mancante"})
    assert "NON eseguito" in fallita and "N8N_WEBHOOK_URL" in fallita
    assert "send_email" in telegram.esito_riga(
        {"ok": True, "canale": "n8n", "workflow": "send_email"})
    assert telegram.esito_riga({"ok": True, "op": "insert", "tabella": "board_tasks",
                                "righe": 1}).startswith("✅ Eseguito")


def test_zero_righe_non_e_un_successo():
    riga = telegram.esito_riga({"ok": True, "op": "update",
                                "tabella": "policy_register", "righe": 0})
    assert "NULLA cambiato" in riga and "policy_register" in riga


def test_il_toast_riporta_la_stringa_del_gestore(monkeypatch):
    """Il testo del bottone non è più fisso: arriva dal gestore."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "t")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "42")
    toast = []

    def fake_post(method, payload, timeout=35):
        if method == "getUpdates":
            return {"result": [{"update_id": 1, "callback_query": {
                "id": "cq1", "data": "approve:7",
                "message": {"chat": {"id": 42}}}}]}
        if method == "answerCallbackQuery":
            toast.append(payload["text"])
        return {}

    monkeypatch.setattr(telegram, "_post", fake_post)
    telegram.poll_decisions(lambda aid: "⚠️ Approvato ma NON eseguito — tabella vuota",
                            lambda aid: None, once=True)
    assert toast == ["⚠️ Approvato ma NON eseguito — tabella vuota"]


# ---- attuatore: le cause a monte ----
def test_update_a_vuoto_e_un_fallimento():
    out = apply_action(ClientVuoto(), {"tabella": "policy_register", "op": "update",
                                       "match": {"policy_name": "Privacy"},
                                       "dati": {"version": "2"}})
    assert out["ok"] is False and "nessuna riga" in out["errore"]


def test_delete_a_vuoto_e_un_fallimento():
    out = apply_action(ClientVuoto(), {"tabella": "pipeline_leads", "op": "delete",
                                       "match": {"id": "L1"}})
    assert out["ok"] is False


def test_segnaposto_trovato_anche_annidato():
    assert segnaposto("Ciao {{nome}}") == "{{nome}}"
    assert segnaposto({"a": {"b": ["x", "${data}"]}}) == "${data}"
    assert segnaposto({"a": "tutto risolto"}) is None


def test_merge_field_da_mail_merge():
    """Caso reale trovato in coda: una email pronta a partire con 'Ciao [Name],'."""
    assert segnaposto("Ciao [Name],\n\nRileggere un contratto…") == "[Name]"
    assert segnaposto({"body": "Buongiorno [Azienda]"}) == "[Azienda]"
    # testo legittimo tra parentesi quadre: non è un segnaposto
    assert segnaposto("vedi allegato [1] e la nota [ndr]") is None


def test_segnaposto_non_diventa_una_riga():
    with pytest.raises(ActuatorError):
        validate({"tabella": "performance_reviews", "op": "insert",
                  "dati": {"period": "{{now_iso}}", "score": 3}})


def test_segnaposto_non_parte_verso_n8n():
    out = apply_action(ClientVuoto(), {"canale": "n8n", "workflow": "send_email",
                                       "payload": {"to": "a@b.it",
                                                   "body": "Buongiorno {{nome}}"}})
    assert out["ok"] is False and "segnaposto" in out["errore"]


def test_campi_tutti_inventati_non_diventano_riga_fantasma():
    """Il caso reale di performance_reviews: nessun campo mappato, note piene, tutto
    il resto null. Non si scrive: il chiamante ripiega su un task."""
    with pytest.raises(ActuatorError):
        apply_action(ClientVuoto(), {"tabella": "performance_reviews", "op": "insert",
                                     "dati": {"review_id": "R1", "stato": "draft",
                                              "period_end": "2026-07-31"}})


def test_preflight_boccia_a_monte_cosi_diventa_un_task():
    with pytest.raises(ActuatorError):
        preflight({"tabella": "performance_reviews", "op": "insert",
                   "dati": {"review_id": "R1", "period_end": "2026-07-31"}})
    # una proposta sana passa
    preflight({"tabella": "board_tasks", "op": "insert",
               "dati": {"title": "Chiamare il lead", "priority": "media"}})
