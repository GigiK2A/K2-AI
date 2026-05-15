"""Generic CRUD helpers built on top of supabase-py.

All routers use these — we serialize Pydantic models to JSON-safe dicts,
delegate to the Supabase REST client, and return parsed read-models.

Service-role key bypasses RLS by design.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Type, TypeVar
from uuid import UUID

from fastapi import HTTPException
from pydantic import BaseModel

from app.db.client import get_supabase

R = TypeVar("R", bound=BaseModel)


def _jsonable(value: Any) -> Any:
    """Coerce a Pydantic-dumped value to something the Supabase REST client accepts."""
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    # Round-trip via json default helpers; pydantic's mode='json' already handles most cases.
    return value


def model_to_payload(model: BaseModel, *, exclude_unset: bool = False) -> Dict[str, Any]:
    raw = model.model_dump(mode="json", exclude_unset=exclude_unset)
    return _jsonable(raw)


def list_rows(
    table: str,
    read_model: Type[R],
    *,
    limit: int = 100,
    offset: int = 0,
    order_by: str = "created_at",
    descending: bool = True,
    filters: Optional[Dict[str, Any]] = None,
) -> List[R]:
    sb = get_supabase()
    q = sb.table(table).select("*")
    if filters:
        for col, val in filters.items():
            q = q.eq(col, val)
    q = q.order(order_by, desc=descending).range(offset, offset + max(limit - 1, 0))
    res = q.execute()
    rows = res.data or []
    return [read_model.model_validate(r) for r in rows]


def get_row(table: str, row_id: UUID, read_model: Type[R]) -> R:
    sb = get_supabase()
    res = sb.table(table).select("*").eq("id", str(row_id)).limit(1).execute()
    rows = res.data or []
    if not rows:
        raise HTTPException(status_code=404, detail=f"{table[:-1]} not found")
    return read_model.model_validate(rows[0])


def insert_row(table: str, payload: Dict[str, Any], read_model: Type[R]) -> R:
    sb = get_supabase()
    res = sb.table(table).insert(payload).execute()
    rows = res.data or []
    if not rows:
        raise HTTPException(status_code=500, detail=f"insert into {table} returned no row")
    return read_model.model_validate(rows[0])


def update_row(
    table: str, row_id: UUID, payload: Dict[str, Any], read_model: Type[R]
) -> R:
    if not payload:
        # Nothing to update — just return current.
        return get_row(table, row_id, read_model)
    sb = get_supabase()
    res = sb.table(table).update(payload).eq("id", str(row_id)).execute()
    rows = res.data or []
    if not rows:
        raise HTTPException(status_code=404, detail=f"{table[:-1]} not found")
    return read_model.model_validate(rows[0])


def delete_row(table: str, row_id: UUID) -> None:
    sb = get_supabase()
    sb.table(table).delete().eq("id", str(row_id)).execute()
