from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class LeadStatus(str, Enum):
    nuovo = "nuovo"
    contatto = "contatto"
    proposta = "proposta"
    chiuso_vinto = "chiuso_vinto"
    chiuso_perso = "chiuso_perso"


class LeadSource(str, Enum):
    k_bot = "k_bot"
    contact_form = "contact_form"
    newsletter = "newsletter"
    referral = "referral"
    outbound = "outbound"
    other = "other"


class LeadBase(BaseModel):
    contact_id: Optional[UUID] = None
    title: str
    description: Optional[str] = None
    status: LeadStatus = LeadStatus.nuovo
    source: LeadSource = LeadSource.other
    value_eur: Optional[Decimal] = None
    probability: int = Field(default=50, ge=0, le=100)
    next_action_at: Optional[datetime] = None
    next_action_note: Optional[str] = None
    kbot_session_id: Optional[UUID] = None


class LeadCreate(LeadBase):
    pass


class LeadUpdate(BaseModel):
    contact_id: Optional[UUID] = None
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[LeadStatus] = None
    source: Optional[LeadSource] = None
    value_eur: Optional[Decimal] = None
    probability: Optional[int] = Field(default=None, ge=0, le=100)
    next_action_at: Optional[datetime] = None
    next_action_note: Optional[str] = None
    kbot_session_id: Optional[UUID] = None
    closed_at: Optional[datetime] = None


class LeadRead(LeadBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None
