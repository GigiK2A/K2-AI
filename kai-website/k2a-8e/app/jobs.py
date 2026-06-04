"""Job store in-memory (Phase-1, non durabile). Phase-2: storage esterno."""
from __future__ import annotations

import threading
import time
import uuid
from typing import Any, Optional

_LOCK = threading.Lock()
_JOBS: dict[str, dict[str, Any]] = {}


def create(service_id: str, blueprint_id: str, confidence: float) -> str:
    job_id = "job_" + uuid.uuid4().hex[:12]
    with _LOCK:
        _JOBS[job_id] = {
            "job_id": job_id,
            "service_id": service_id,
            "blueprint_id": blueprint_id,
            "confidence": confidence,
            "status": "routed",
            "created_at": time.time(),
            "outputs": None,
            "validation": None,
            "citazioni": [],
            "refusal_reason": None,
            "error": None,
        }
    return job_id


def update(job_id: str, **fields: Any) -> None:
    with _LOCK:
        if job_id in _JOBS:
            _JOBS[job_id].update(fields)


def get(job_id: str) -> Optional[dict]:
    with _LOCK:
        j = _JOBS.get(job_id)
        return dict(j) if j else None
