"""
Eval suite per Giuseppina — 20 scenari fissi.

Obiettivo: verificare che il sistema non peggiori dopo ogni modifica.
Non testano il risultato LLM (non deterministico), ma:
- routing: risposta diretta vs piano JSON
- tool selection: quale funzione notion_tools deve essere chiamata
- validazione: dati mancanti → errore chiaro, non write parziale
- risk level: azioni sensibili → livello corretto
- undo: push/pop corretto per ogni tipo di operazione
- action_guard: L3 detection + pending confirmation flow

Esecuzione: python -m pytest tests/test_eval_scenarios.py -v
"""
from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from core.action_guard import (
    ActionRisk,
    cancel_pending_confirmation,
    get_action_risk,
    has_pending_confirmation,
    pop_pending_confirmation,
    store_pending_confirmation,
)
from core.undo import (
    describe_undo,
    has_undo,
    peek_undo,
    pop_undo,
    push_undo,
)


# ─────────────────────────────────────────────────────────────────────────────
# GRUPPO 1: Risk levels — classificazione corretta
# ─────────────────────────────────────────────────────────────────────────────
class TestActionRiskLevels(unittest.TestCase):
    """Verifica che ogni funzione abbia il livello di rischio atteso."""

    def test_read_ops_are_l1(self):
        """Operazioni di lettura → READ."""
        for fn in ("list_open_tasks", "list_pipeline_status", "list_clients", "search_client"):
            with self.subTest(fn=fn):
                self.assertEqual(get_action_risk(fn), ActionRisk.READ)

    def test_write_simple_ops_are_l2(self):
        """Operazioni di scrittura semplice → WRITE_SIMPLE senza kwargs sensibili."""
        for fn in ("add_lead_to_pipeline", "create_board_task", "save_to_memory", "create_or_update_client"):
            with self.subTest(fn=fn):
                self.assertEqual(get_action_risk(fn), ActionRisk.WRITE_SIMPLE)

    def test_update_lead_normal_status_is_l2(self):
        """update_pipeline_lead con status normale → WRITE_SIMPLE."""
        for status in ("identified", "qualified", "contacted", "call_scheduled", "proposal_sent"):
            with self.subTest(status=status):
                risk = get_action_risk("update_pipeline_lead", {"status": status})
                self.assertEqual(risk, ActionRisk.WRITE_SIMPLE)

    def test_update_lead_final_status_is_l3(self):
        """update_pipeline_lead con status won/lost → WRITE_SENSITIVE (richiede conferma)."""
        for status in ("won", "lost"):
            with self.subTest(status=status):
                risk = get_action_risk("update_pipeline_lead", {"status": status})
                self.assertEqual(risk, ActionRisk.WRITE_SENSITIVE)

    def test_update_task_normal_status_is_l2(self):
        """update_board_task con status normale → WRITE_SIMPLE."""
        for status in ("pending", "running", "review"):
            with self.subTest(status=status):
                risk = get_action_risk("update_board_task", {"status": status})
                self.assertEqual(risk, ActionRisk.WRITE_SIMPLE)

    def test_update_task_final_status_is_l3(self):
        """update_board_task con done/rejected → WRITE_SENSITIVE."""
        for status in ("done", "rejected"):
            with self.subTest(status=status):
                risk = get_action_risk("update_board_task", {"status": status})
                self.assertEqual(risk, ActionRisk.WRITE_SENSITIVE)

    def test_unknown_function_defaults_to_write_simple(self):
        """Funzione sconosciuta → default WRITE_SIMPLE (fail safe)."""
        risk = get_action_risk("some_unknown_function")
        self.assertEqual(risk, ActionRisk.WRITE_SIMPLE)


# ─────────────────────────────────────────────────────────────────────────────
# GRUPPO 2: Action guard — pending confirmation flow
# ─────────────────────────────────────────────────────────────────────────────
class TestActionGuardConfirmationFlow(unittest.TestCase):
    """Verifica il flusso conferma/annulla per azioni L3."""

    def setUp(self):
        self.chat_id = "test_chat_999"
        cancel_pending_confirmation(self.chat_id)

    def tearDown(self):
        cancel_pending_confirmation(self.chat_id)

    def test_no_pending_on_fresh_session(self):
        """Sessione pulita → nessuna conferma pendente."""
        self.assertFalse(has_pending_confirmation(self.chat_id))

    def test_store_and_detect_pending(self):
        """store_pending_confirmation → has_pending_confirmation True."""
        store_pending_confirmation(
            self.chat_id,
            "update_pipeline_lead",
            {"name_or_id": "Mario Rossi", "status": "won"},
            "Segna Mario Rossi come vinto",
        )
        self.assertTrue(has_pending_confirmation(self.chat_id))

    def test_pop_returns_and_removes(self):
        """pop_pending_confirmation → ritorna record e rimuove pending."""
        store_pending_confirmation(
            self.chat_id,
            "update_pipeline_lead",
            {"name_or_id": "Acme", "status": "lost"},
            "Chiudi lead Acme",
        )
        record = pop_pending_confirmation(self.chat_id)
        self.assertIsNotNone(record)
        self.assertEqual(record["func_name"], "update_pipeline_lead")
        self.assertFalse(has_pending_confirmation(self.chat_id))

    def test_cancel_clears_pending(self):
        """cancel_pending_confirmation → rimuove e ritorna True."""
        store_pending_confirmation(self.chat_id, "update_board_task", {"task_id": "abc", "status": "done"}, "")
        result = cancel_pending_confirmation(self.chat_id)
        self.assertTrue(result)
        self.assertFalse(has_pending_confirmation(self.chat_id))

    def test_cancel_nothing_returns_false(self):
        """cancel su sessione pulita → ritorna False."""
        result = cancel_pending_confirmation("chat_non_esiste_mai_123")
        self.assertFalse(result)

    def test_pop_on_empty_returns_none(self):
        """pop su sessione pulita → None."""
        record = pop_pending_confirmation("chat_vuota_xyz")
        self.assertIsNone(record)


# ─────────────────────────────────────────────────────────────────────────────
# GRUPPO 3: Undo stack — push/pop/peek corretto
# ─────────────────────────────────────────────────────────────────────────────
class TestUndoStack(unittest.TestCase):
    """Verifica comportamento stack undo per-sessione."""

    def setUp(self):
        self.session = "undo_test_session_42"
        # Pulisci stack se esistente
        while pop_undo(self.session):
            pass

    def test_empty_stack_has_no_undo(self):
        """Stack vuoto → has_undo False."""
        self.assertFalse(has_undo(self.session))

    def test_push_makes_undo_available(self):
        """Dopo push → has_undo True."""
        push_undo(self.session, "create", "task", "page_id_123", "Test Task")
        self.assertTrue(has_undo(self.session))

    def test_pop_returns_last_pushed(self):
        """pop → ritorna record più recente."""
        push_undo(self.session, "create", "task", "id_1", "Task A")
        push_undo(self.session, "create", "lead", "id_2", "Lead B")
        record = pop_undo(self.session)
        self.assertIsNotNone(record)
        self.assertEqual(record["entity_name"], "Lead B")
        self.assertEqual(record["entity_type"], "lead")

    def test_pop_exhausts_stack(self):
        """Dopo pop di tutti i record → has_undo False."""
        push_undo(self.session, "create", "client", "id_1", "Cliente X")
        pop_undo(self.session)
        self.assertFalse(has_undo(self.session))

    def test_peek_does_not_remove(self):
        """peek → record disponibile ma non rimosso."""
        push_undo(self.session, "update", "task", "id_3", "Task C", pre_state={"status": "pending"})
        peeked = peek_undo(self.session)
        self.assertIsNotNone(peeked)
        self.assertTrue(has_undo(self.session))

    def test_stack_depth_limit(self):
        """Stack non supera MAX_UNDO_DEPTH (5)."""
        from core.undo import _MAX_UNDO_DEPTH
        for i in range(_MAX_UNDO_DEPTH + 3):
            push_undo(self.session, "create", "task", f"id_{i}", f"Task {i}")

        # Pop tutti
        count = 0
        while pop_undo(self.session):
            count += 1

        self.assertLessEqual(count, _MAX_UNDO_DEPTH)

    def test_describe_undo_create(self):
        """describe_undo per create → messaggio leggibile."""
        push_undo(self.session, "create", "lead", "id_1", "Mario Bianchi")
        record = peek_undo(self.session)
        desc = describe_undo(record)
        self.assertIn("Mario Bianchi", desc)
        self.assertIn("lead", desc.lower())

    def test_describe_undo_update_with_pre_state(self):
        """describe_undo per update con pre_state → mostra campi."""
        push_undo(self.session, "update", "task", "id_5", "Task Importante", pre_state={"status": "pending"})
        record = peek_undo(self.session)
        desc = describe_undo(record)
        self.assertIn("status", desc.lower())


# ─────────────────────────────────────────────────────────────────────────────
# GRUPPO 4: notion_tools — validazione campi obbligatori
# ─────────────────────────────────────────────────────────────────────────────
class TestNotionToolsValidation(unittest.TestCase):
    """Verifica che validation block write quando mancano campi obbligatori."""

    def test_add_lead_without_name_returns_error(self):
        """add_lead_to_pipeline senza name → errore, non write."""
        from core.notion_tools import add_lead_to_pipeline
        result = add_lead_to_pipeline(name="", company="Acme")
        self.assertIn("Campo obbligatorio mancante", result)
        self.assertIn("nome del lead", result.lower())

    def test_create_task_without_title_returns_error(self):
        """create_board_task senza title → errore, non write."""
        from core.notion_tools import create_board_task
        result = create_board_task(title="")
        self.assertIn("Campo obbligatorio mancante", result)

    def test_create_client_without_company_returns_error(self):
        """create_or_update_client senza company_name → errore, non write."""
        from core.notion_tools import create_or_update_client
        result = create_or_update_client(company_name="")
        self.assertIn("Campo obbligatorio mancante", result)

    def test_update_task_without_id_returns_error(self):
        """update_board_task senza task_id → errore chiaro."""
        from core.notion_tools import update_board_task
        with patch("core.notion_tools.notion_board.notion_enabled", return_value=True):
            result = update_board_task(task_id="")
        self.assertIn("ID task mancante", result)


# ─────────────────────────────────────────────────────────────────────────────
# GRUPPO 5: Session context — thread-local corretto
# ─────────────────────────────────────────────────────────────────────────────
class TestSessionContext(unittest.TestCase):
    """Verifica che set/get/clear session funzionino correttamente."""

    def test_set_and_get_session(self):
        from core.notion_tools import get_current_session, set_current_session
        set_current_session("telegram_chat_123")
        self.assertEqual(get_current_session(), "telegram_chat_123")

    def test_clear_session(self):
        from core.notion_tools import clear_current_session, get_current_session, set_current_session
        set_current_session("session_xyz")
        clear_current_session()
        self.assertIsNone(get_current_session())

    def test_session_coerces_int_to_str(self):
        from core.notion_tools import get_current_session, set_current_session
        set_current_session(987654)
        self.assertEqual(get_current_session(), "987654")


# ─────────────────────────────────────────────────────────────────────────────
# GRUPPO 6: notion_tools — Notion disabled fallback
# ─────────────────────────────────────────────────────────────────────────────
class TestNotionToolsDisabledFallback(unittest.TestCase):
    """Verifica comportamento quando Notion è disabilitato."""

    def test_add_lead_notion_disabled(self):
        from core.notion_tools import add_lead_to_pipeline
        with patch("core.notion_tools.notion_board.notion_enabled", return_value=False):
            result = add_lead_to_pipeline(name="Test Lead")
        self.assertIn("Notion non abilitato", result)

    def test_create_task_notion_disabled(self):
        from core.notion_tools import create_board_task
        with patch("core.notion_tools.notion_board.notion_enabled", return_value=False):
            result = create_board_task(title="Test Task")
        self.assertIn("Notion non abilitato", result)

    def test_list_tasks_notion_disabled(self):
        from core.notion_tools import list_open_tasks
        with patch("core.notion_tools.notion_board.notion_enabled", return_value=False):
            result = list_open_tasks()
        self.assertIn("Notion non abilitato", result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
