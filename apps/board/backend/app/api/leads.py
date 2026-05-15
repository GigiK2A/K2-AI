from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api._crud import (
    delete_row, get_row, insert_row, list_rows, model_to_payload, update_row,
)
from app.deps import require_auth
from app.models.lead import LeadCreate, LeadRead, LeadStatus, LeadUpdate

router = APIRouter(prefix="/api/leads", tags=["leads"], dependencies=[Depends(require_auth)])

TABLE = "leads"


@router.get("/", response_model=List[LeadRead])
def list_leads(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    status: Optional[LeadStatus] = None,
):
    filters = {"status": status.value} if status else None
    return list_rows(TABLE, LeadRead, limit=limit, offset=offset, filters=filters)


@router.post("/", response_model=LeadRead, status_code=201)
def create_lead(body: LeadCreate):
    return insert_row(TABLE, model_to_payload(body), LeadRead)


@router.get("/{lead_id}", response_model=LeadRead)
def get_lead(lead_id: UUID):
    return get_row(TABLE, lead_id, LeadRead)


@router.patch("/{lead_id}", response_model=LeadRead)
def update_lead(lead_id: UUID, body: LeadUpdate):
    return update_row(TABLE, lead_id, model_to_payload(body, exclude_unset=True), LeadRead)


@router.delete("/{lead_id}", status_code=204)
def delete_lead(lead_id: UUID):
    delete_row(TABLE, lead_id)
