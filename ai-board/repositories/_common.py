"""Shared helpers for repositories."""

from __future__ import annotations

from typing import Any, Callable, TypeVar

from loguru import logger

T = TypeVar("T")


def safely(default: T, operation: Callable[[], T], message: str) -> T:
    """Run `operation`, log + return `default` on failure.

    Mirrors the helper historically used inside the route modules so the
    repository layer can preserve defensive defaults without leaking
    FastAPI-specific concerns.
    """
    try:
        return operation()
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.warning(f"{message}: {exc}")
        return default
