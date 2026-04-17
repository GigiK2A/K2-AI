"""Shared datetime helpers for services.

Kept separate from controllers so services don't depend on the
`interfaces.dashboard.routes` helpers and remain independently testable.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

WEEKDAYS_IT = [
    "Lunedì",
    "Martedì",
    "Mercoledì",
    "Giovedì",
    "Venerdì",
    "Sabato",
    "Domenica",
]
MONTHS_IT = [
    "Gennaio",
    "Febbraio",
    "Marzo",
    "Aprile",
    "Maggio",
    "Giugno",
    "Luglio",
    "Agosto",
    "Settembre",
    "Ottobre",
    "Novembre",
    "Dicembre",
]
MONTHS_SHORT_IT = [
    "Gen",
    "Feb",
    "Mar",
    "Apr",
    "Mag",
    "Giu",
    "Lug",
    "Ago",
    "Set",
    "Ott",
    "Nov",
    "Dic",
]


def parse_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    if not value:
        return None
    text = str(value).replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def format_home_date(value: datetime) -> str:
    return f"{WEEKDAYS_IT[value.weekday()]}, {value.day} {MONTHS_IT[value.month - 1]} {value.year}"


def compact_datetime(value: Any) -> str:
    dt = parse_datetime(value)
    if not dt:
        return "—"
    return f"{dt.day:02d} {MONTHS_SHORT_IT[dt.month - 1]}, {dt.strftime('%H:%M')}"


def relative_time_it(value: Any, now: datetime) -> str:
    dt = parse_datetime(value)
    if not dt:
        return "ora"
    delta = max(now - dt, timedelta())
    minutes = int(delta.total_seconds() // 60)
    if minutes <= 0:
        return "adesso"
    if minutes < 60:
        return f"{minutes} min fa"
    hours = minutes // 60
    if hours < 24:
        return f"{hours} ora fa" if hours == 1 else f"{hours} ore fa"
    days = hours // 24
    return f"{days} giorno fa" if days == 1 else f"{days} giorni fa"
