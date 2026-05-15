from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api._crud import (
    delete_row, get_row, insert_row, list_rows, model_to_payload, update_row,
)
from app.deps import require_auth
from app.models.approval import (
    ApprovalCreate, ApprovalRead, ApprovalStatus, ApprovalUpdate,
)

router = APIRouter(prefix="/api/approvals", tags=["approvals"], dependencies=[Depends(require_auth)])

TABLE = "board_approvals"


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
def update_approval(approval_id: UUID, body: ApprovalUpdate):
    return update_row(TABLE, approval_id, model_to_payload(body, exclude_unset=True), ApprovalRead)


@router.delete("/{approval_id}", status_code=204)
def delete_approval(approval_id: UUID):
    delete_row(TABLE, approval_id)
