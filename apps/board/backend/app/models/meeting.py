from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MeetingBase(BaseModel):
    external_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    starts_at: datetime
    ends_at: datetime
    location: Optional[str] = None
    meet_link: Optional[str] = None
    attendees: List[Any] = Field(default_factory=list)
    contact_id: Optional[UUID] = None
    lead_id: Optional[UUID] = None


class MeetingCreate(MeetingBase):
    pass


class MeetingUpdate(BaseModel):
    external_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    location: Optional[str] = None
    meet_link: Optional[str] = None
    attendees: Optional[List[Any]] = None
    contact_id: Optional[UUID] = None
    lead_id: Optional[UUID] = None


class MeetingRead(MeetingBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime
    updated_at: datetime
