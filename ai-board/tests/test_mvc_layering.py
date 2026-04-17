"""Parity tests for the MVC refactor.

Guards that:
- legacy shim imports still resolve the same callables,
- controllers expose the same HTTP surface as the old routers,
- service-level helpers produce the expected KPI shape.

Tests stub repositories to avoid touching Supabase/Notion.
"""

from __future__ import annotations

import unittest
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import patch

from services.agents_service import AgentsService
from services.home_service import HomeService


class FakeApprovals:
    def __init__(
        self,
        pending: list[dict[str, Any]] | None = None,
        recent: list[dict[str, Any]] | None = None,
        approved: list[dict[str, Any]] | None = None,
    ) -> None:
        self._pending = pending or []
        self._recent = recent or []
        self._approved = approved or []

    def list_pending(self) -> list[dict[str, Any]]:
        return list(self._pending)

    def list_recent(self, limit: int = 20) -> list[dict[str, Any]]:
        return list(self._recent[:limit])

    def list_approved(self) -> list[dict[str, Any]]:
        return list(self._approved)

    def list_pending_for_agents(self, related_names):
        names = set(related_names)
        return [row for row in self._pending if row.get("agent") in names]

    def list_for_task_ids(self, task_ids):
        ids = set(task_ids)
        return [
            row
            for row in self._recent
            if row.get("task_id") in ids
        ]

    def list_for_agents(self, related_names):
        names = set(related_names)
        return [row for row in self._recent if row.get("agent") in names]

    def recent_draft_for_agents(self, related_names, since_iso):
        return []


class FakeLogs:
    def __init__(
        self,
        recent: list[dict[str, Any]] | None = None,
        today: list[dict[str, Any]] | None = None,
        yesterday: list[dict[str, Any]] | None = None,
    ) -> None:
        self._recent = recent or []
        self._today = today or []
        self._yesterday = yesterday or []

    def list_recent(self, limit: int = 500) -> list[dict[str, Any]]:
        return list(self._recent[:limit])

    def list_since(self, since_iso: str) -> list[dict[str, Any]]:
        return list(self._today)

    def list_between(self, start_iso: str, end_iso: str) -> list[dict[str, Any]]:
        return list(self._yesterday)

    def list_summary(self, limit: int = 200) -> list[dict[str, Any]]:
        return list(self._recent[:limit])

    def list_for_agents(self, related_names, limit=200):
        names = set(related_names)
        return [row for row in self._recent if row.get("agent") in names]


class FakePipeline:
    def __init__(self, leads: list[dict[str, Any]] | None = None) -> None:
        self._leads = leads or []

    def list_leads(self) -> list[dict[str, Any]]:
        return list(self._leads)


class FakeTasks:
    def list_tasks(self) -> list[dict[str, Any]]:
        return []


class HomeServiceTests(unittest.TestCase):
    def test_load_home_data_shape_matches_contract(self) -> None:
        now = datetime.now(UTC)
        approvals = FakeApprovals(
            pending=[
                {"id": "a1", "agent": "content_engine", "created_at": now.isoformat()},
            ],
            recent=[
                {
                    "id": "a1",
                    "task_id": "t1",
                    "agent": "content_engine",
                    "status": "draft",
                    "content_preview": "preview",
                    "created_at": now.isoformat(),
                }
            ],
            approved=[
                {
                    "id": "a2",
                    "status": "approved",
                    "reviewed_at": (now - timedelta(days=1)).isoformat(),
                    "created_at": (now - timedelta(days=1)).isoformat(),
                }
            ],
        )
        logs = FakeLogs(
            recent=[
                {
                    "id": "l1",
                    "task_id": "t2",
                    "agent": "content_engine",
                    "action": "generate",
                    "status": "done",
                    "output_summary": "done",
                    "created_at": now.isoformat(),
                }
            ],
            today=[{"agent": "content_engine", "created_at": now.isoformat()}],
            yesterday=[],
        )
        pipeline = FakePipeline(leads=[{"status": "identified"}])

        with patch(
            "services.home_service.notion_board.notion_enabled",
            return_value=False,
        ):
            service = HomeService(
                approvals=approvals,
                agent_logs=logs,
                pipeline=pipeline,
                tasks=FakeTasks(),
            )
            data = service.load_home_data()

        expected_keys = {
            "today_label",
            "pending_approvals",
            "pending_created_today",
            "active_agents_today",
            "active_agents_delta",
            "pipeline_leads",
            "pipeline_created_week",
            "tasks_done_week",
            "tasks_done_change_pct",
            "activity_feed",
            "pipeline_summary",
            "pipeline_rows",
        }
        self.assertEqual(expected_keys, set(data.keys()))
        self.assertEqual(data["pending_approvals"], 1)
        self.assertEqual(data["pipeline_leads"], 1)
        # pipeline_rows always emits every configured stage
        self.assertEqual(len(data["pipeline_rows"]), 6)
        # activity feed surfaces approval entry
        self.assertGreaterEqual(len(data["activity_feed"]), 1)


class AgentsServiceTests(unittest.TestCase):
    def test_build_task_from_form_skips_csrf_and_files(self) -> None:
        class FakeForm:
            def multi_items(self):
                return [
                    ("csrf_token", "xyz"),
                    ("topic", "AI"),
                    ("flag", "on"),
                ]

        task = AgentsService.build_task_from_form(FakeForm())
        self.assertIn("Topic: AI", task)
        self.assertIn("Flag: Sì", task)
        self.assertNotIn("csrf", task)

    def test_agent_summary_counts_statuses(self) -> None:
        rows = [
            {"display_status": "approved"},
            {"display_status": "draft"},
            {"display_status": "error"},
        ]
        summary = AgentsService.agent_summary(rows)
        self.assertEqual(summary["value"], 3)
        self.assertIn("approvati", summary["footer"])

    def test_system_prompt_sections_defaults_when_empty(self) -> None:
        sections = AgentsService.system_prompt_sections(
            {"goal": "", "instructions": []}  # type: ignore[arg-type]
        )
        self.assertEqual(len(sections), 1)
        self.assertEqual(sections[0]["title"], "Prompt base")


class LegacyShimTests(unittest.TestCase):
    def test_home_shim_reexports_router_and_helper(self) -> None:
        from interfaces.dashboard.routes import home as home_shim

        self.assertTrue(hasattr(home_shim, "router"))
        self.assertTrue(callable(home_shim._load_home_data))

    def test_agents_shim_reexports_helpers(self) -> None:
        from interfaces.dashboard.routes import agents as agents_shim

        for name in (
            "_agent_meta",
            "_agent_chat_panel_payload",
            "_build_chat_history_context",
            "_collect_chat_attachments",
            "_load_agents_data",
            "_load_agent_chat_turns",
            "_load_agent_history_page",
            "_resolve_agent_slug",
            "RUN_REGISTRY",
            "router",
        ):
            self.assertTrue(
                hasattr(agents_shim, name),
                f"shim missing legacy symbol {name}",
            )


class RouterSurfaceTests(unittest.TestCase):
    def test_home_router_paths(self) -> None:
        from controllers import home_router

        paths = sorted({r.path for r in home_router.routes})
        self.assertEqual(
            paths, ["/", "/partials/activity", "/partials/kpi"]
        )

    def test_agents_router_paths(self) -> None:
        from controllers import agents_router

        paths = sorted({r.path for r in agents_router.routes})
        self.assertEqual(
            paths,
            [
                "/agents",
                "/agents/content_engine/generate",
                "/agents/{agent_name}",
                "/agents/{agent_name}/chat",
                "/agents/{agent_name}/history",
                "/agents/{agent_name}/run",
                "/agents/{agent_name}/status",
            ],
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
