from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RevenueEventBase(BaseModel):
    external_id: str
    customer_email: Optional[str] = None
    customer_id: Optional[str] = None
    amount_cents: int
    currency: str = "eur"
    description: Optional[str] = None
    status: str
    occurred_at: datetime
    lead_id: Optional[UUID] = None
    raw: Optional[Any] = None


class RevenueEventCreate(RevenueEventBase):
    pass


class RevenueEventUpdate(BaseModel):
    customer_email: Optional[str] = None
    customer_id: Optional[str] = None
    amount_cents: Optional[int] = None
    currency: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    occurred_at: Optional[datetime] = None
    lead_id: Optional[UUID] = None
    raw: Optional[Any] = None


class RevenueEventRead(RevenueEventBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime
