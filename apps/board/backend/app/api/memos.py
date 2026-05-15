from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api._crud import (
    delete_row, get_row, insert_row, list_rows, model_to_payload, update_row,
)
from app.deps import require_auth
from app.models.memo import MemoCreate, MemoRead, MemoUpdate

router = APIRouter(prefix="/api/memos", tags=["memos"], dependencies=[Depends(require_auth)])

TABLE = "memos"


@router.get("/", response_model=List[MemoRead])
def list_memos(limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0)):
    return list_rows(TABLE, MemoRead, limit=limit, offset=offset)


@router.post("/", response_model=MemoRead, status_code=201)
def create_memo(body: MemoCreate):
    return insert_row(TABLE, model_to_payload(body), MemoRead)


@router.get("/{memo_id}", response_model=MemoRead)
def get_memo(memo_id: UUID):
    return get_row(TABLE, memo_id, MemoRead)


@router.patch("/{memo_id}", response_model=MemoRead)
def update_memo(memo_id: UUID, body: MemoUpdate):
    return update_row(TABLE, memo_id, model_to_payload(body, exclude_unset=True), MemoRead)


@router.delete("/{memo_id}", status_code=204)
def delete_memo(memo_id: UUID):
    delete_row(TABLE, memo_id)
