from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TaskPriority(str, Enum):
    alta = "alta"
    media = "media"
    bassa = "bassa"


class TaskStatus(str, Enum):
    todo = "todo"
    doing = "doing"
    done = "done"
    cancelled = "cancelled"


class TaskBase(BaseModel):
    lead_id: Optional[UUID] = None
    title: str
    notes: Optional[str] = None
    priority: TaskPriority = TaskPriority.media
    status: TaskStatus = TaskStatus.todo
    due_at: Optional[datetime] = None
    position: int = 0


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    lead_id: Optional[UUID] = None
    title: Optional[str] = None
    notes: Optional[str] = None
    priority: Optional[TaskPriority] = None
    status: Optional[TaskStatus] = None
    due_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    position: Optional[int] = None


class TaskRead(TaskBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
