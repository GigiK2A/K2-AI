from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api._crud import (
    delete_row, get_row, insert_row, list_rows, model_to_payload, update_row,
)
from app.deps import require_auth
from app.models.contact import ContactCreate, ContactRead, ContactUpdate

router = APIRouter(prefix="/api/contacts", tags=["contacts"], dependencies=[Depends(require_auth)])

TABLE = "board_contacts"


@router.get("/", response_model=List[ContactRead])
def list_contacts(limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0)):
    return list_rows(TABLE, ContactRead, limit=limit, offset=offset)


@router.post("/", response_model=ContactRead, status_code=201)
def create_contact(body: ContactCreate):
    return insert_row(TABLE, model_to_payload(body), ContactRead)


@router.get("/{contact_id}", response_model=ContactRead)
def get_contact(contact_id: UUID):
    return get_row(TABLE, contact_id, ContactRead)


@router.patch("/{contact_id}", response_model=ContactRead)
def update_contact(contact_id: UUID, body: ContactUpdate):
    return update_row(TABLE, contact_id, model_to_payload(body, exclude_unset=True), ContactRead)


@router.delete("/{contact_id}", status_code=204)
def delete_contact(contact_id: UUID):
    delete_row(TABLE, contact_id)
