"""Tests for Sprint 9D — approval execution.

We fake the Supabase service-role client; the executor only needs the
`.table(name).insert(...).update(...).select(...).eq(...).execute()`
fluent surface. Each test drives one branch of the dispatcher.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List
from unittest.mock import MagicMock

import pytest

from app.agent.approval_executor import (
    execute_approved_action,
    extract_edited_email_body,
    parse_meta_marker,
)


class FakeQuery:
    def __init__(self, table: "FakeTable", op: str, payload: Any = None) -> None:
        self.table = table
        self.op = op
        self.payload = payload
        self.filters: List[tuple] = []
        self._return_rows: List[Dict[str, Any]] = []

    # Filter chain methods.
    def eq(self, col: str, val: Any) -> "FakeQuery":
        self.filters.append(("eq", col, val))
        return self

    def ilike(self, col: str, val: Any) -> "FakeQuery":
        self.filters.append(("ilike", col, val))
        return self

    def is_(self, col: str, val: Any) -> "FakeQuery":
        self.filters.append(("is", col, val))
        return self

    def gte(self, col: str, val: Any) -> "FakeQuery":
        self.filters.append(("gte", col, val))
        return self

    def lte(self, col: str, val: Any) -> "FakeQuery":
        self.filters.append(("lte", col, val))
        return self

    def or_(self, *args: Any) -> "FakeQuery":
        return self

    def order(self, *args: Any, **kwargs: Any) -> "FakeQuery":
        return self

    def limit(self, *args: Any) -> "FakeQuery":
        return self

    def range(self, *args: Any) -> "FakeQuery":
        return self

    def execute(self) -> Any:
        self.table.calls.append((self.op, dict(self.payload) if isinstance(self.payload, dict) else self.payload, list(self.filters)))
        if self.op == "insert":
            row = dict(self.payload) if isinstance(self.payload, dict) else {}
            row.setdefault("id", f"{self.table.name}-id-{len(self.table.calls)}")
            self.table.rows.append(row)
            return MagicMock(data=[row])
        if self.op == "select":
            return MagicMock(data=list(self.table.rows))
        if self.op == "update":
            for r in self.table.rows:
                r.update(self.payload or {})
            return MagicMock(data=list(self.table.rows))
        return MagicMock(data=[])


class FakeTable:
    def __init__(self, name: str) -> None:
        self.name = name
        self.calls: List[tuple] = []
        self.rows: List[Dict[str, Any]] = []

    def select(self, *_args: Any, **_kwargs: Any) -> FakeQuery:
        return FakeQuery(self, "select")

    def insert(self, payload: Dict[str, Any]) -> FakeQuery:
        return FakeQuery(self, "insert", payload)

    def update(self, payload: Dict[str, Any]) -> FakeQuery:
        return FakeQuery(self, "update", payload)

    def delete(self) -> FakeQuery:
        return FakeQuery(self, "delete")


class FakeSupabase:
    def __init__(self) -> None:
        self.tables: Dict[str, FakeTable] = {}

    def table(self, name: str) -> FakeTable:
        if name not in self.tables:
            self.tables[name] = FakeTable(name)
        return self.tables[name]


# ── Marker parsing ──────────────────────────────────────────────────────────

def test_parse_meta_marker_extracts_tool_and_payload():
    body = (
        "PROPOSTA AGENTE — Nuovo lead\n"
        "Titolo: Acme\n"
        "[meta] tool=propose_new_lead\n"
        "[meta] payload={\"title\": \"Acme\", \"source\": \"outbound\"}"
    )
    tool, args = parse_meta_marker(body)
    assert tool == "propose_new_lead"
    assert args == {"title": "Acme", "source": "outbound"}


def test_parse_meta_marker_missing_returns_none():
    tool, args = parse_meta_marker("nessun marker qui")
    assert tool is None
    assert args == {}


def test_parse_meta_marker_malformed_payload_yields_empty():
    body = "[meta] tool=propose_task\n[meta] payload={not json}"
    tool, args = parse_meta_marker(body)
    assert tool == "propose_task"
    assert args == {}


def test_extract_edited_email_body():
    body = (
        "PROPOSTA AGENTE — Draft email\n"
        "To contact: abc\n"
        "Subject: Ciao\n\n"
        "---\nCorpo nuovo\nseconda riga\n---\n\n"
        "Rationale: ..."
    )
    assert extract_edited_email_body(body) == "Corpo nuovo\nseconda riga"


# ── Dispatch ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_execute_new_lead_creates_lead_and_contact():
    sb = FakeSupabase()
    args = {
        "title": "Acme inquiry",
        "source": "outbound",
        "contact_company": "Acme Spa",
        "value_eur": 5000,
        "rationale": "Hot lead",
    }
    note = await execute_approved_action("propose_new_lead", args, "approval-1", sb=sb)
    assert "Lead creato" in note
    # Contact created (no pre-existing) AND lead created.
    assert len(sb.tables["board_contacts"].rows) == 1
    assert sb.tables["board_contacts"].rows[0]["company"] == "Acme Spa"
    assert len(sb.tables["board_leads"].rows) == 1
    lead = sb.tables["board_leads"].rows[0]
    assert lead["title"] == "Acme inquiry"
    assert lead["value_eur"] == 5000
    assert lead["contact_id"] == sb.tables["board_contacts"].rows[0]["id"]


@pytest.mark.asyncio
async def test_execute_task_creates_task():
    sb = FakeSupabase()
    args = {
        "title": "Richiamare Mario",
        "priority": "alta",
        "due_at": "2026-05-20T10:00:00Z",
    }
    note = await execute_approved_action("propose_task", args, "approval-2", sb=sb)
    assert "Task creato" in note
    assert len(sb.tables["board_tasks"].rows) == 1
    task = sb.tables["board_tasks"].rows[0]
    assert task["title"] == "Richiamare Mario"
    assert task["priority"] == "alta"


@pytest.mark.asyncio
async def test_execute_lead_update_applies_fields():
    sb = FakeSupabase()
    # Seed a lead so update has something to mutate.
    sb.table("board_leads").insert({"id": "lead-1", "title": "old"}).execute()
    args = {
        "lead_id": "lead-1",
        "fields_json": {"status": "proposta", "value_eur": 7000},
        "rationale": "Avanzamento",
    }
    note = await execute_approved_action("propose_lead_update", args, "approval-3", sb=sb)
    assert "lead-1" in note
    lead = sb.tables["board_leads"].rows[0]
    assert lead["status"] == "proposta"
    assert lead["value_eur"] == 7000


@pytest.mark.asyncio
async def test_execute_email_without_resend_saves_memo():
    sb = FakeSupabase()
    # Seed a contact with an email so we go past the "no recipient" branch.
    sb.table("board_contacts").insert(
        {"id": "contact-1", "email": "luca@example.com", "person_name": "Luca"}
    ).execute()
    args = {
        "to_contact_id": "contact-1",
        "subject": "Saluti",
        "body_markdown": "Ciao Luca, ...",
    }
    note = await execute_approved_action(
        "propose_email_draft", args, "approval-4", sb=sb
    )
    # Without RESEND_API_KEY set, we expect the memo fallback.
    assert "memo" in note.lower() or "resend" in note.lower()
    memos = sb.tables.get("board_memos")
    assert memos is not None
    assert len(memos.rows) == 1


@pytest.mark.asyncio
async def test_execute_email_uses_edited_body():
    sb = FakeSupabase()
    sb.table("board_contacts").insert(
        {"id": "contact-2", "email": "x@y.it"}
    ).execute()
    args = {
        "to_contact_id": "contact-2",
        "subject": "Originale",
        "body_markdown": "ORIGINALE",
    }
    await execute_approved_action(
        "propose_email_draft",
        args,
        "approval-5",
        sb=sb,
        edited_body="VERSIONE EDITATA",
    )
    memo = sb.tables["board_memos"].rows[0]
    assert "VERSIONE EDITATA" in memo["body"]
    assert "ORIGINALE" not in memo["body"]


@pytest.mark.asyncio
async def test_execute_unknown_tool_returns_message():
    sb = FakeSupabase()
    note = await execute_approved_action("propose_unknown", {}, "x", sb=sb)
    assert "non riconosciuto" in note.lower()
