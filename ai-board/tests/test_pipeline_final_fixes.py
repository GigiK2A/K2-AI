import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

from core.approval import is_actionable_approval_draft
import core.scheduler as scheduler_mod
from core.scheduler import job_approval_reminder, job_daily_brief, job_kpi_update, job_task_deadline_reminder
from interfaces.telegram import assistant
from interfaces.telegram.notifier import notify_informational
import interfaces.telegram.notifier as notifier_mod


class ApprovalFilteringTests(unittest.TestCase):
    def test_is_actionable_approval_draft_filters_legacy_and_informational(self) -> None:
        valid = {
            "id": "11111111-1111-1111-1111-111111111111",
            "status": "draft",
            "task_id": "t-1",
            "content_type": "linkedin_post",
            "content_preview": "Post pronto",
            "title": "Content Engine · linkedin_post",
        }
        informational = {
            **valid,
            "id": "22222222-2222-2222-2222-222222222222",
            "content_type": "kpi_update",
        }
        wrong_status = {
            **valid,
            "id": "33333333-3333-3333-3333-333333333333",
            "status": "review",
        }
        dirty_legacy = {
            **valid,
            "id": "44444444-4444-4444-4444-444444444444",
            "task_id": None,
        }
        briefing_title = {
            **valid,
            "id": "55555555-5555-5555-5555-555555555555",
            "title": "Chief of Staff · daily_brief briefing operativo",
        }

        self.assertTrue(is_actionable_approval_draft(valid))
        self.assertFalse(is_actionable_approval_draft(informational))
        self.assertFalse(is_actionable_approval_draft(wrong_status))
        self.assertFalse(is_actionable_approval_draft(dirty_legacy))
        self.assertFalse(is_actionable_approval_draft(briefing_title))


class DraftBatchCommandTests(unittest.TestCase):
    def test_shortcut_routes_to_close_all_drafts(self) -> None:
        action = assistant.operational_shortcut("cancella tutti i draft")
        self.assertEqual(action, {"action": "close_all_approvals"})

    def test_close_all_drafts_no_pending(self) -> None:
        with patch.object(assistant, "get_pending_approvals_fallback", return_value=([], "primary")):
            response = assistant.execute_action({"action": "close_all_approvals"}, confirmed=False)
        self.assertIn("Non ci sono draft attivi", response.text)

    def test_close_all_drafts_success(self) -> None:
        with patch.object(assistant, "close_all_pending_approvals", return_value=(3, 3, "primary")):
            response = assistant.execute_action({"action": "close_all_approvals"}, confirmed=True)
        self.assertIn("3 draft chiusi", response.text)

    def test_close_all_drafts_storage_unavailable(self) -> None:
        with patch.object(assistant, "close_all_pending_approvals", return_value=(0, 0, "unavailable")):
            response = assistant.execute_action({"action": "close_all_approvals"}, confirmed=True)
        self.assertIn("non riesco a completare la pulizia", response.text.lower())


class InformationalDeliveryTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        notifier_mod._recent_informational_hashes.clear()

    async def test_notify_informational_is_idempotent_for_duplicate_payload(self) -> None:
        sent = []

        async def fake_send_message(text, keyboard=None, parse_mode=None):
            sent.append(text)
            return True

        with (
            patch("interfaces.telegram.notifier.send_message", new=fake_send_message),
            patch("interfaces.telegram.notifier.get_service_client", side_effect=RuntimeError("no-db")),
        ):
            first = await notify_informational("chief_of_staff", "daily_brief", "Contenuto briefing")
            second = await notify_informational("chief_of_staff", "daily_brief", "Contenuto briefing")

        self.assertTrue(first)
        self.assertTrue(second)
        self.assertEqual(len(sent), 1)


class ReminderCountTests(unittest.IsolatedAsyncioTestCase):
    async def test_approval_reminder_counts_only_old_pending(self) -> None:
        pending = [
            {
                "agent": "chief_of_staff",
                "content_preview": "Draft 1",
                "created_at": (datetime.now(timezone.utc) - timedelta(hours=9)).isoformat(),
            },
            {
                "agent": "content_engine",
                "content_preview": "Draft recente",
                "created_at": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
            },
        ]
        sent = {}

        async def passthrough(func, *args, **kwargs):
            return func(*args, **kwargs)

        def fake_notify_informational(agent_name, content_type, text, **kwargs):
            sent["text"] = text
            return True

        def fake_notify_sync(payload):
            sent["payload"] = payload
            return True

        weekday = scheduler_mod.ROME.localize(datetime(2026, 4, 17, 12, 0, 0))
        with (
            patch("core.scheduler._now_rome", return_value=weekday),
            patch("core.scheduler._run_sync", new=passthrough),
            patch("core.approval.expire_stale_approvals", return_value=0),
            patch("core.approval.get_pending_approvals", return_value=pending),
            patch("interfaces.telegram.notifier.notify_informational", new=fake_notify_informational),
            patch("interfaces.telegram.notifier.notify_sync", new=fake_notify_sync),
        ):
            result = await job_approval_reminder()

        self.assertTrue(result)
        self.assertIn("1 draft in attesa", sent["text"])


class WeekendAndDedupSchedulerTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        scheduler_mod._RUNNING_JOBS.clear()
        scheduler_mod._LAST_JOB_RUN_TS.clear()

    async def test_kpi_weekday_single_send(self) -> None:
        sent: list[str] = []
        weekday = scheduler_mod.ROME.localize(datetime(2026, 4, 17, 18, 0, 0))

        async def passthrough(func, *args, **kwargs):
            return func(*args, **kwargs)

        def fake_notify_informational(agent_name, content_type, text, **kwargs):
            sent.append(text)
            return True

        with (
            patch("core.scheduler._now_rome", return_value=weekday),
            patch("core.scheduler._run_sync", new=passthrough),
            patch("core.scheduler._collect_kpi_inputs", return_value={
                "today_label": "17/04/2026",
                "leads_total": 1,
                "leads_this_week": 1,
                "active_pipeline": 1,
                "approved_this_month": 1,
                "lead_counts": {"qualified": 1},
                "active_leads": [{"name": "Lead A", "status": "qualified", "score": 8, "next_action": "Call"}],
                "mrr_available": False,
            }),
            patch("interfaces.telegram.notifier.notify_informational", new=fake_notify_informational),
            patch("interfaces.telegram.notifier.notify_sync", return_value=True),
        ):
            result = await job_kpi_update()

        self.assertTrue(result)
        self.assertEqual(len(sent), 1)

    async def test_weekend_skips_routine_jobs(self) -> None:
        saturday = scheduler_mod.ROME.localize(datetime(2026, 4, 18, 10, 0, 0))
        sunday = scheduler_mod.ROME.localize(datetime(2026, 4, 19, 10, 0, 0))

        async def passthrough(func, *args, **kwargs):
            return func(*args, **kwargs)

        with (
            patch("core.scheduler._run_sync", new=passthrough),
            patch("core.scheduler._collect_kpi_inputs", return_value={}),
            patch("core.scheduler._collect_daily_brief_inputs", return_value={}),
            patch("core.scheduler._collect_task_reminder_inputs", return_value={}),
            patch("core.orchestrator.run_agent") as run_agent,
            patch("interfaces.telegram.notifier.notify_informational") as notify_info,
        ):
            with patch("core.scheduler._now_rome", return_value=saturday):
                self.assertTrue(await job_kpi_update())
                self.assertTrue(await job_daily_brief())
                self.assertTrue(await job_task_deadline_reminder())
                self.assertTrue(await job_approval_reminder())
            scheduler_mod._RUNNING_JOBS.clear()
            scheduler_mod._LAST_JOB_RUN_TS.clear()
            with patch("core.scheduler._now_rome", return_value=sunday):
                self.assertTrue(await job_kpi_update())
                self.assertTrue(await job_daily_brief())
                self.assertTrue(await job_task_deadline_reminder())
                self.assertTrue(await job_approval_reminder())

        run_agent.assert_not_called()
        notify_info.assert_not_called()

    async def test_double_trigger_sends_once(self) -> None:
        sent: list[str] = []
        weekday = scheduler_mod.ROME.localize(datetime(2026, 4, 17, 18, 0, 0))

        async def passthrough(func, *args, **kwargs):
            return func(*args, **kwargs)

        def fake_notify_informational(agent_name, content_type, text, **kwargs):
            sent.append(text)
            return True

        with (
            patch("core.scheduler._now_rome", return_value=weekday),
            patch("core.scheduler._run_sync", new=passthrough),
            patch("core.scheduler._collect_kpi_inputs", return_value={
                "today_label": "17/04/2026",
                "leads_total": 1,
                "leads_this_week": 1,
                "active_pipeline": 1,
                "approved_this_month": 1,
                "lead_counts": {"qualified": 1},
                "active_leads": [{"name": "Lead A", "status": "qualified", "score": 8, "next_action": "Call"}],
                "mrr_available": False,
            }),
            patch("interfaces.telegram.notifier.notify_informational", new=fake_notify_informational),
            patch("interfaces.telegram.notifier.notify_sync", return_value=True),
        ):
            self.assertTrue(await job_kpi_update())
            self.assertTrue(await job_kpi_update())

        self.assertEqual(len(sent), 1)


class BriefingContextSanitizationTests(unittest.TestCase):
    """Verifica che i task dello scheduler non contaminino il context del briefing."""

    def test_scheduler_tasks_excluded_from_active_tasks(self) -> None:
        """Task con requested_by=scheduler:* non devono comparire in active_tasks."""
        fake_tasks = [
            {
                "id": "t1",
                "title": "Task operativo reale",
                "status": "running",
                "priority": 2,
                "assigned_to": "chief_of_staff",
                "requested_by": "founder",
                "description": "descrizione normale",
            },
            {
                "id": "t2",
                "title": "Genera il briefing operativo del giorno per il fondatore.\n\nData: 18/04/2026",
                "status": "running",
                "priority": 3,
                "assigned_to": "chief_of_staff",
                "requested_by": "scheduler:daily_brief",
                "description": "Genera il briefing operativo del giorno per il fondatore.\n\nData: 18/04/2026\n\nDRAFT IN ATTESA: 0...",
            },
        ]

        with (
            patch("core.scheduler._safe_list_tasks", return_value=fake_tasks),
            patch("core.scheduler._safe_list_pipeline_leads", return_value=[]),
            patch("core.approval.get_pending_approvals", return_value=[]),
        ):
            from core.scheduler import _collect_daily_brief_inputs
            result = _collect_daily_brief_inputs()

        titles = [t["title"] for t in result["active_tasks"]]
        self.assertEqual(len(result["active_tasks"]), 1)
        self.assertIn("Task operativo reale", titles)
        self.assertFalse(any("18/04/2026" in t for t in titles))

    def test_active_tasks_stripped_to_display_fields_only(self) -> None:
        """I task passati al context agente devono contenere solo campi display."""
        fake_tasks = [
            {
                "id": "t1",
                "title": "Follow up lead",
                "status": "pending",
                "priority": 1,
                "assigned_to": "sales_enablement",
                "requested_by": "founder",
                "description": "PROMPT LUNGO CON DATI SENSIBILI " * 100,
                "input_data": {"secret": "non deve arrivare all'agente"},
            }
        ]

        with (
            patch("core.scheduler._safe_list_tasks", return_value=fake_tasks),
            patch("core.scheduler._safe_list_pipeline_leads", return_value=[]),
            patch("core.approval.get_pending_approvals", return_value=[]),
        ):
            from core.scheduler import _collect_daily_brief_inputs
            result = _collect_daily_brief_inputs()

        task = result["active_tasks"][0]
        self.assertNotIn("description", task)
        self.assertNotIn("input_data", task)
        self.assertNotIn("id", task)
        self.assertEqual(set(task.keys()), {"title", "status", "priority", "assigned_to"})

    def test_old_pending_stripped_to_display_fields_only(self) -> None:
        """Le approvazioni pending non devono esporre full_content nel context."""
        from datetime import datetime, timedelta, timezone
        old_ts = (datetime.now(timezone.utc) - timedelta(hours=5)).isoformat()
        fake_pending = [
            {
                "id": "ap1",
                "agent": "content_engine",
                "content_preview": "Post LinkedIn",
                "created_at": old_ts,
                "full_content": {"task": "prompt lungo", "output": "output lungo " * 200},
                "status": "draft",
            }
        ]

        with (
            patch("core.scheduler._safe_list_tasks", return_value=[]),
            patch("core.scheduler._safe_list_pipeline_leads", return_value=[]),
            patch("core.approval.get_pending_approvals", return_value=fake_pending),
        ):
            from core.scheduler import _collect_daily_brief_inputs
            result = _collect_daily_brief_inputs()

        self.assertEqual(len(result["old_pending"]), 1)
        item = result["old_pending"][0]
        self.assertNotIn("full_content", item)
        self.assertNotIn("id", item)
        self.assertEqual(set(item.keys()), {"agent", "content_preview", "created_at"})


if __name__ == "__main__":
    unittest.main()
