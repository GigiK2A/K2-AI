from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ContactBase(BaseModel):
    company: Optional[str] = None
    person_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    notes: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class ContactCreate(ContactBase):
    pass


class ContactUpdate(BaseModel):
    company: Optional[str] = None
    person_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None


class ContactRead(ContactBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime
    updated_at: datetime
