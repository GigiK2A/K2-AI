import unittest
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import Mock, patch

from core.orchestrator import AGENT_REGISTRY, resolve_agent_name
from core.scheduler import (
    ROME,
    job_approval_reminder,
    job_cleanup_logs,
    job_daily_brief,
    job_kpi_update,
    job_market_pulse,
    job_task_deadline_reminder,
    job_weekly_plan,
    scheduler,
    setup_scheduler,
)
from db.models import AgentName
from interfaces.telegram.handlers import schedule_handler, start_handler


class SchedulerSetupTests(unittest.TestCase):
    def tearDown(self) -> None:
        scheduler.remove_all_jobs()

    def test_setup_scheduler_registers_expected_jobs(self) -> None:
        sched = setup_scheduler()

        self.assertEqual(
            {job.id for job in sched.get_jobs()},
            {
                "approval_reminder",
                "cleanup_logs",
                "daily_brief",
                "kpi_update",
                "market_pulse",
                "task_deadline_reminder",
                "weekly_plan",
            },
        )

    def test_market_intelligence_is_real_agent(self) -> None:
        self.assertIn(AgentName.MARKET_INTELLIGENCE, AGENT_REGISTRY)
        self.assertEqual(resolve_agent_name(AgentName.MARKET_INTELLIGENCE), AgentName.MARKET_INTELLIGENCE)


class SchedulerJobTests(unittest.IsolatedAsyncioTestCase):
    async def asyncTearDown(self) -> None:
        scheduler.remove_all_jobs()

    async def test_job_daily_brief_uses_chief_of_staff(self) -> None:
        inputs = {
            "today_label": "07/04/2026",
            "pending_count": 3,
            "old_pending": [{"id": "a"}],
            "active_tasks": [{"title": "Follow up pipeline"}],
            "active_leads": [{"name": "Hotel Roma", "status": "qualified"}],
            "due_leads": [{"name": "Studio Alfa"}],
        }

        async def passthrough(func, *args, **kwargs):
            return func(*args, **kwargs)

        with (
            patch("core.scheduler._run_sync", new=passthrough),
            patch("core.scheduler._collect_daily_brief_inputs", return_value=inputs),
            patch("core.orchestrator.run_agent", return_value={"status": "draft", "approval_id": "draft-1"}) as run_agent,
        ):
            result = await job_daily_brief()

        self.assertTrue(result)
        agent_name, task, context = run_agent.call_args.args
        self.assertEqual(agent_name, AgentName.CHIEF_OF_STAFF)
        self.assertIn("briefing operativo", task.lower())
        self.assertEqual(context["__board"]["requested_by"], "scheduler:daily_brief")
        self.assertEqual(context["__board"]["content_type"], "daily_brief")

    async def test_job_weekly_plan_uses_orchestrator(self) -> None:
        inputs = {
            "week_start": "07/04",
            "week_end": "11/04/2026",
            "lead_counts": {"qualified": 4},
            "approved_assets_count": 2,
            "focus_leads": [{"name": "Ristorante Blu", "status": "qualified", "score": 9}],
        }

        async def passthrough(func, *args, **kwargs):
            return func(*args, **kwargs)

        with (
            patch("core.scheduler._run_sync", new=passthrough),
            patch("core.scheduler._collect_weekly_plan_inputs", return_value=inputs),
            patch("core.orchestrator.run_agent", return_value={"status": "draft", "approval_id": "draft-2"}) as run_agent,
        ):
            result = await job_weekly_plan()

        self.assertTrue(result)
        agent_name, task, context = run_agent.call_args.args
        self.assertEqual(agent_name, AgentName.ORCHESTRATOR)
        self.assertIn("piano operativo", task.lower())
        self.assertEqual(context["__board"]["requested_by"], "scheduler:weekly_plan")

    async def test_job_kpi_update_uses_finance_kpi(self) -> None:
        inputs = {
            "today_label": "07/04/2026",
            "leads_total": 10,
            "leads_this_week": 4,
            "active_pipeline": 7,
            "approved_this_month": 5,
            "runs_today": 6,
            "lead_counts": {"qualified": 3, "proposal_sent": 2},
            "mrr_available": False,
        }

        async def passthrough(func, *args, **kwargs):
            return func(*args, **kwargs)

        with (
            patch("core.scheduler._run_sync", new=passthrough),
            patch("core.scheduler._collect_kpi_inputs", return_value=inputs),
            patch("core.orchestrator.run_agent", return_value={"status": "draft", "approval_id": "draft-3"}) as run_agent,
        ):
            result = await job_kpi_update()

        self.assertTrue(result)
        agent_name, task, context = run_agent.call_args.args
        self.assertEqual(agent_name, AgentName.FINANCE_KPI)
        self.assertIn("report kpi serale", task.lower())
        self.assertEqual(context["__board"]["requested_by"], "scheduler:kpi_update")

    async def test_job_market_pulse_uses_market_intelligence(self) -> None:
        async def passthrough(func, *args, **kwargs):
            return func(*args, **kwargs)

        with (
            patch("core.scheduler._run_sync", new=passthrough),
            patch("core.orchestrator.run_agent", return_value={"status": "draft", "approval_id": "draft-4"}) as run_agent,
        ):
            result = await job_market_pulse()

        self.assertTrue(result)
        agent_name, task, context = run_agent.call_args.args
        self.assertEqual(agent_name, AgentName.MARKET_INTELLIGENCE)
        self.assertIn("mercato italiano", task.lower())
        self.assertEqual(context["__board"]["requested_by"], "scheduler:market_pulse")

    async def test_job_approval_reminder_sends_summary_for_old_pending(self) -> None:
        pending = [
            {
                "agent": "chief_of_staff",
                "content_preview": "Briefing operativo del giorno",
                "created_at": (datetime.now(UTC) - timedelta(hours=9)).isoformat(),
            }
        ]
        sent = {}

        async def passthrough(func, *args, **kwargs):
            return func(*args, **kwargs)

        def fake_send_message(text):
            sent["text"] = text
            return text

        def fake_notify_sync(payload):
            sent["payload"] = payload
            return True

        with (
            patch("core.scheduler._run_sync", new=passthrough),
            patch("core.approval.get_pending_approvals", return_value=pending),
            patch("interfaces.telegram.notifier.send_message", new=fake_send_message),
            patch("interfaces.telegram.notifier.notify_sync", new=fake_notify_sync),
        ):
            result = await job_approval_reminder()

        self.assertTrue(result)
        self.assertIn("oltre 8 ore", sent["text"])
        self.assertIn("chief of staff", sent["text"])

    async def test_job_task_deadline_reminder_sends_summary(self) -> None:
        reminder_inputs = {
            "today_label": "13/04/2026",
            "active_count": 5,
            "urgent_tasks": [
                {"title": "Contatta lead caldo", "priority": 1, "due_date": datetime(2026, 4, 14).date()}
            ],
            "due_week_tasks": [
                {"title": "Revisione proposta", "priority": 2, "due_date": datetime(2026, 4, 18).date()}
            ],
            "overdue_tasks": [],
            "no_due_date_count": 2,
        }
        sent = {}

        async def passthrough(func, *args, **kwargs):
            return func(*args, **kwargs)

        def fake_send_message(text):
            sent["text"] = text
            return text

        def fake_notify_sync(payload):
            sent["payload"] = payload
            return True

        with (
            patch("core.scheduler._run_sync", new=passthrough),
            patch("core.scheduler._collect_task_reminder_inputs", return_value=reminder_inputs),
            patch("interfaces.telegram.notifier.send_message", new=fake_send_message),
            patch("interfaces.telegram.notifier.notify_sync", new=fake_notify_sync),
        ):
            result = await job_task_deadline_reminder()

        self.assertTrue(result)
        self.assertIn("promemoria task automatico", sent["text"].lower())
        self.assertIn("Task con scadenza entro 7 giorni", sent["text"])

    async def test_job_cleanup_logs_archives_multiple_batches(self) -> None:
        async def passthrough(func, *args, **kwargs):
            return func(*args, **kwargs)

        first_batch = [{"id": str(idx)} for idx in range(500)]
        second_batch = [{"id": "tail"}]

        with (
            patch("core.scheduler._run_sync", new=passthrough),
            patch(
                "core.scheduler._collect_logs_to_archive",
                Mock(side_effect=[first_batch, second_batch, []]),
            ) as collect_logs,
            patch("core.scheduler._archive_logs", Mock(side_effect=[500, 1])) as archive_logs,
        ):
            result = await job_cleanup_logs()

        self.assertTrue(result)
        self.assertEqual(collect_logs.call_count, 2)
        self.assertEqual(archive_logs.call_count, 2)


class FakeSentMessage:
    def __init__(self, text: str):
        self.text = text
        self.edits: list[dict] = []

    async def edit_text(self, text: str, parse_mode=None):
        self.edits.append({"text": text, "parse_mode": parse_mode})


class FakeMessage:
    def __init__(self):
        self.replies: list[dict] = []

    async def reply_text(self, text: str, parse_mode=None, reply_markup=None):
        sent = FakeSentMessage(text)
        self.replies.append(
            {
                "text": text,
                "parse_mode": parse_mode,
                "reply_markup": reply_markup,
                "message": sent,
            }
        )
        return sent


class TelegramScheduleHandlerTests(unittest.IsolatedAsyncioTestCase):
    def _authorized_update(self) -> SimpleNamespace:
        message = FakeMessage()
        return SimpleNamespace(
            effective_user=SimpleNamespace(id="123456789"),
            message=message,
        )

    async def test_start_handler_mentions_schedule_command(self) -> None:
        update = self._authorized_update()
        context = SimpleNamespace(args=[], user_data={})

        with patch("interfaces.telegram.handlers.settings.telegram_chat_id", "123456789"):
            await start_handler(update, context)

        self.assertIn("/schedule", update.message.replies[0]["text"])

    async def test_schedule_handler_lists_jobs(self) -> None:
        update = self._authorized_update()
        context = SimpleNamespace(args=[], user_data={})
        fake_scheduler = SimpleNamespace(
            get_jobs=lambda: [
                SimpleNamespace(
                    id="daily_brief",
                    name="Briefing giornaliero",
                    next_run_time=datetime(2026, 4, 8, 8, 0, tzinfo=ROME),
                )
            ]
        )

        with (
            patch("interfaces.telegram.handlers.settings.telegram_chat_id", "123456789"),
            patch("core.scheduler.scheduler", new=fake_scheduler),
        ):
            await schedule_handler(update, context)

        self.assertIn("daily_brief", update.message.replies[0]["text"])
        self.assertIn("/schedule run <id>", update.message.replies[0]["text"])

    async def test_schedule_handler_runs_job_immediately(self) -> None:
        update = self._authorized_update()
        context = SimpleNamespace(args=["run", "daily_brief"], user_data={})
        called = {"count": 0}

        async def fake_job_func():
            called["count"] += 1
            return True

        fake_job = SimpleNamespace(
            id="daily_brief",
            name="Briefing giornaliero",
            next_run_time=datetime(2026, 4, 8, 8, 0, tzinfo=ROME),
            func=fake_job_func,
        )
        fake_scheduler = SimpleNamespace(
            get_job=lambda job_id: fake_job if job_id == "daily_brief" else None,
            get_jobs=lambda: [fake_job],
        )

        with (
            patch("interfaces.telegram.handlers.settings.telegram_chat_id", "123456789"),
            patch("core.scheduler.scheduler", new=fake_scheduler),
        ):
            await schedule_handler(update, context)

        self.assertEqual(called["count"], 1)
        first_reply = update.message.replies[0]["message"]
        self.assertIn("eseguito", first_reply.edits[0]["text"])


if __name__ == "__main__":
    unittest.main()
