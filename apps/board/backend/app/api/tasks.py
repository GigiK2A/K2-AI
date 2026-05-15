from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api._crud import (
    delete_row, get_row, insert_row, list_rows, model_to_payload, update_row,
)
from app.deps import require_auth
from app.models.task import TaskCreate, TaskRead, TaskStatus, TaskUpdate

router = APIRouter(prefix="/api/tasks", tags=["tasks"], dependencies=[Depends(require_auth)])

TABLE = "tasks"


@router.get("/", response_model=List[TaskRead])
def list_tasks(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    status: Optional[TaskStatus] = None,
):
    filters = {"status": status.value} if status else None
    return list_rows(
        TABLE, TaskRead, limit=limit, offset=offset, filters=filters,
        order_by="position", descending=False,
    )


@router.post("/", response_model=TaskRead, status_code=201)
def create_task(body: TaskCreate):
    return insert_row(TABLE, model_to_payload(body), TaskRead)


@router.get("/{task_id}", response_model=TaskRead)
def get_task(task_id: UUID):
    return get_row(TABLE, task_id, TaskRead)


@router.patch("/{task_id}", response_model=TaskRead)
def update_task(task_id: UUID, body: TaskUpdate):
    return update_row(TABLE, task_id, model_to_payload(body, exclude_unset=True), TaskRead)


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: UUID):
    delete_row(TABLE, task_id)
