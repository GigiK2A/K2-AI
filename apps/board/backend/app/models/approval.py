from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ApprovalKind(str, Enum):
    email = "email"
    proposta = "proposta"
    post = "post"
    reply = "reply"
    altro = "altro"


class ApprovalStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    edited_and_sent = "edited_and_sent"


class ApprovalBase(BaseModel):
    kind: ApprovalKind
    title: str
    body: str
    rationale: Optional[str] = None
    lead_id: Optional[UUID] = None
    contact_id: Optional[UUID] = None


class ApprovalCreate(ApprovalBase):
    status: ApprovalStatus = ApprovalStatus.pending


class ApprovalUpdate(BaseModel):
    kind: Optional[ApprovalKind] = None
    title: Optional[str] = None
    body: Optional[str] = None
    rationale: Optional[str] = None
    lead_id: Optional[UUID] = None
    contact_id: Optional[UUID] = None
    status: Optional[ApprovalStatus] = None
    decision_note: Optional[str] = None
    decided_at: Optional[datetime] = None


class ApprovalRead(ApprovalBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    status: ApprovalStatus
    decision_note: Optional[str] = None
    created_at: datetime
    decided_at: Optional[datetime] = None
