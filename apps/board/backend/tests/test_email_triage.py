"""Tests for Sprint 9C — email triage stub flow."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict
from unittest.mock import MagicMock

import pytest

from app.agent.email_triage import (
    InboundEmail,
    StubProvider,
    execute_email_action,
    triage_inbox,
)
from tests.test_approval_executor import FakeSupabase


def _email(**overrides: Any) -> InboundEmail:
    base = {
        "id": "e1",
        "from_email": "mario@acme.it",
        "from_name": "Mario Rossi",
        "subject": "Richiesta preventivo",
        "body": "Buongiorno, vorrei un preventivo per un agente AI.",
        "received_at": datetime(2026, 5, 15, 10, 0, tzinfo=timezone.utc),
    }
    base.update(overrides)
    return InboundEmail(**base)


def test_execute_action_ignora_is_noop():
    sb = FakeSupabase()
    out = execute_email_action(sb, {"category": "ignora"}, _email())
    assert out["category"] == "ignora"
    assert "board_memos" not in sb.tables


def test_execute_action_memo_creates_memo():
    sb = FakeSupabase()
    out = execute_email_action(
        sb,
        {"category": "memo", "summary": "Cliente saluta"},
        _email(),
    )
    assert out["category"] == "memo"
    assert len(sb.tables["board_memos"].rows) == 1
    memo = sb.tables["board_memos"].rows[0]
    assert "Mario Rossi" in memo["body"]
    assert "email-triage" in memo["tags"]


def test_execute_action_lead_creates_approval():
    sb = FakeSupabase()
    out = execute_email_action(
        sb,
        {"category": "lead", "summary": "Vuole preventivo", "suggested_action": "rispondere"},
        _email(),
    )
    assert out["category"] == "lead"
    # propose_new_lead inserts into board_approvals (not directly into leads).
    assert len(sb.tables["board_approvals"].rows) == 1
    approval = sb.tables["board_approvals"].rows[0]
    assert "tool=propose_new_lead" in approval["body"]


def test_execute_action_task_creates_approval():
    sb = FakeSupabase()
    out = execute_email_action(
        sb,
        {"category": "task", "summary": "Chiamare", "suggested_action": "Chiama domani"},
        _email(),
    )
    assert out["category"] == "task"
    assert len(sb.tables["board_approvals"].rows) == 1
    assert "tool=propose_task" in sb.tables["board_approvals"].rows[0]["body"]


@pytest.mark.asyncio
async def test_triage_inbox_dispatches_to_classifier_and_marks_triaged():
    sb = FakeSupabase()
    # Seed an inbox row so the stub provider has something to return.
    sb.table("board_inbox_pending").insert(
        {
            "id": "inbox-1",
            "from_email": "mario@acme.it",
            "from_name": "Mario",
            "subject": "Preventivo",
            "body": "Vorrei info",
            "received_at": datetime.now(tz=timezone.utc).isoformat(),
        }
    ).execute()

    async def fake_classifier(_email: InboundEmail) -> Dict[str, Any]:
        return {"category": "memo", "summary": "ok", "suggested_action": "ok"}

    provider = StubProvider(sb=sb)
    result = await triage_inbox(provider, sb=sb, classifier=fake_classifier)

    assert result["processed"] == 1
    assert result["actions"][0]["category"] == "memo"
    # mark_triaged should have run.
    inbox = sb.tables["board_inbox_pending"]
    assert any(c[0] == "update" for c in inbox.calls)
