from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MemoBase(BaseModel):
    subject: str
    body: str
    tags: List[str] = Field(default_factory=list)
    contact_id: Optional[UUID] = None
    lead_id: Optional[UUID] = None


class MemoCreate(MemoBase):
    pass


class MemoUpdate(BaseModel):
    subject: Optional[str] = None
    body: Optional[str] = None
    tags: Optional[List[str]] = None
    contact_id: Optional[UUID] = None
    lead_id: Optional[UUID] = None


class MemoRead(MemoBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime
    updated_at: datetime
