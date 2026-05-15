from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api._crud import (
    delete_row, get_row, insert_row, list_rows, model_to_payload, update_row,
)
from app.deps import require_auth
from app.models.revenue import RevenueEventCreate, RevenueEventRead, RevenueEventUpdate

router = APIRouter(prefix="/api/revenue", tags=["revenue"], dependencies=[Depends(require_auth)])

TABLE = "board_revenue_events"


@router.get("/", response_model=List[RevenueEventRead])
def list_revenue(limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0)):
    return list_rows(
        TABLE, RevenueEventRead, limit=limit, offset=offset,
        order_by="occurred_at", descending=True,
    )


@router.post("/", response_model=RevenueEventRead, status_code=201)
def create_revenue(body: RevenueEventCreate):
    return insert_row(TABLE, model_to_payload(body), RevenueEventRead)


@router.get("/{event_id}", response_model=RevenueEventRead)
def get_revenue(event_id: UUID):
    return get_row(TABLE, event_id, RevenueEventRead)


@router.patch("/{event_id}", response_model=RevenueEventRead)
def update_revenue(event_id: UUID, body: RevenueEventUpdate):
    return update_row(
        TABLE, event_id, model_to_payload(body, exclude_unset=True), RevenueEventRead,
    )


@router.delete("/{event_id}", status_code=204)
def delete_revenue(event_id: UUID):
    delete_row(TABLE, event_id)
