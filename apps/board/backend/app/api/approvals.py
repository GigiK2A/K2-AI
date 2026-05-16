from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.agent.approval_executor import (
    execute_approved_action,
    extract_edited_email_body,
    extract_edited_subject,
    parse_meta_marker,
)
from app.api._crud import (
    delete_row,
    get_row,
    insert_row,
    list_rows,
    model_to_payload,
    update_row,
)
from app.db.client import get_supabase
from app.deps import require_auth
from app.models.approval import (
    ApprovalCreate,
    ApprovalRead,
    ApprovalStatus,
    ApprovalUpdate,
)

router = APIRouter(prefix="/api/approvals", tags=["approvals"], dependencies=[Depends(require_auth)])
log = logging.getLogger(__name__)

TABLE = "board_approvals"

_EXECUTE_STATUSES = {ApprovalStatus.approved, ApprovalStatus.edited_and_sent}


@router.get("/", response_model=List[ApprovalRead])
def list_approvals(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    status: Optional[ApprovalStatus] = None,
):
    filters = {"status": status.value} if status else None
    return list_rows(TABLE, ApprovalRead, limit=limit, offset=offset, filters=filters)


@router.post("/", response_model=ApprovalRead, status_code=201)
def create_approval(body: ApprovalCreate):
    return insert_row(TABLE, model_to_payload(body), ApprovalRead)


@router.get("/{approval_id}", response_model=ApprovalRead)
def get_approval(approval_id: UUID):
    return get_row(TABLE, approval_id, ApprovalRead)


@router.patch("/{approval_id}", response_model=ApprovalRead)
async def update_approval(approval_id: UUID, body: ApprovalUpdate):
    """Patch an approval. If the new status is approved/edited_and_sent and
    the body contains a `[meta] tool=...` marker, execute the action and
    record the result in ``decision_note``."""
    payload = model_to_payload(body, exclude_unset=True)

    if body.status in _EXECUTE_STATUSES:
        # Load current row to recover original meta marker + body.
        existing = get_row(TABLE, approval_id, ApprovalRead)
        if existing.status not in _EXECUTE_STATUSES:
            # Use the NEW body if the user edited it, else fall back to stored.
            effective_body = payload.get("body") or existing.body
            tool_name, args = parse_meta_marker(effective_body)
            # Fall back to the stored body for the marker — user may have wiped it.
            if not tool_name:
                tool_name, args = parse_meta_marker(existing.body)

            if tool_name:
                edited_body: Optional[str] = None
                if body.status == ApprovalStatus.edited_and_sent and payload.get("body"):
                    if tool_name == "propose_email_draft":
                        edited_body = extract_edited_email_body(payload["body"])
                        # Subject may have changed too.
                        new_subject = extract_edited_subject(payload["body"])
                        if new_subject:
                            args["subject"] = new_subject
                    elif tool_name == "propose_proposta_commerciale":
                        edited_body = extract_edited_email_body(payload["body"])

                try:
                    sb = get_supabase()
                    note = await execute_approved_action(
                        tool_name,
                        args,
                        str(approval_id),
                        sb=sb,
                        edited_body=edited_body,
                    )
                except Exception as exc:  # noqa: BLE001
                    log.exception("approval.execute_failed", extra={"approval_id": str(approval_id)})
                    note = f"Esecuzione fallita: {exc}"

                # Merge with any caller-supplied decision_note (caller wins).
                if "decision_note" not in payload or not payload.get("decision_note"):
                    payload["decision_note"] = note
                else:
                    payload["decision_note"] = f"{payload['decision_note']} | {note}"

        if "decided_at" not in payload:
            payload["decided_at"] = datetime.now(tz=timezone.utc).isoformat()

    return update_row(TABLE, approval_id, payload, ApprovalRead)


@router.delete("/{approval_id}", status_code=204)
def delete_approval(approval_id: UUID):
    delete_row(TABLE, approval_id)
