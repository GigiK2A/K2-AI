"""Loader default budget (inflazione, aliquote)."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

_DATA = Path(__file__).parent / "data" / "budget_defaults.json"


@lru_cache(maxsize=1)
def load_defaults() -> dict:
    with open(_DATA, encoding="utf-8") as f:
        return json.load(f)


def get_aliquota_default(snapshot: dict | None = None) -> float:
    s = snapshot or load_defaults()
    return float(s["aliquota_imposte_default_pct"])


def get_inflazione_default(snapshot: dict | None = None) -> float:
    s = snapshot or load_defaults()
    return float(s["inflazione_pct_2026"])


def get_snapshot_as_of() -> str:
    return load_defaults().get("snapshot_as_of", "unknown")
