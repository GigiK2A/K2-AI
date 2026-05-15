from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api._crud import (
    delete_row, get_row, insert_row, list_rows, model_to_payload, update_row,
)
from app.deps import require_auth
from app.models.meeting import MeetingCreate, MeetingRead, MeetingUpdate

router = APIRouter(prefix="/api/meetings", tags=["meetings"], dependencies=[Depends(require_auth)])

TABLE = "board_meetings"


@router.get("/", response_model=List[MeetingRead])
def list_meetings(limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0)):
    return list_rows(
        TABLE, MeetingRead, limit=limit, offset=offset,
        order_by="starts_at", descending=False,
    )


@router.post("/", response_model=MeetingRead, status_code=201)
def create_meeting(body: MeetingCreate):
    return insert_row(TABLE, model_to_payload(body), MeetingRead)


@router.get("/{meeting_id}", response_model=MeetingRead)
def get_meeting(meeting_id: UUID):
    return get_row(TABLE, meeting_id, MeetingRead)


@router.patch("/{meeting_id}", response_model=MeetingRead)
def update_meeting(meeting_id: UUID, body: MeetingUpdate):
    return update_row(TABLE, meeting_id, model_to_payload(body, exclude_unset=True), MeetingRead)


@router.delete("/{meeting_id}", status_code=204)
def delete_meeting(meeting_id: UUID):
    delete_row(TABLE, meeting_id)
