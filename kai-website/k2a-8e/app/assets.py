"""Adapter asset reali (handoff Luca v2.27) — blueprint, snapshot, manifest, catalog.

L'engine consuma direttamente gli artefatti consegnati:
- blueprints/<skill>/{blueprint,output-schema,form}.json  + manifest.json
- grounding/grounding-snapshot.json  (entries verbatim per tipo)
- k2a_validation/  (meta-schema L1)

Quando Luca aggiorna gli asset (es. snapshot v2.28 con benchmark), si sostituiscono
i file → zero modifiche codice.
"""
from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Optional

from .settings import (
    BLUEPRINTS_DIR, BOOST_PLACEHOLDERS_PATH, CATALOG_PATH, MANIFEST_PATH, SNAPSHOT_PATH,
)

log = logging.getLogger("8e.assets")


def _read(path: Path) -> Optional[dict]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        log.warning("read fallita %s: %s", path, exc)
        return None


@lru_cache(maxsize=1)
def manifest() -> dict:
    return (_read(MANIFEST_PATH) or {}).get("services", {})


def service_to_skill(service_id: str) -> Optional[str]:
    return manifest().get(service_id, {}).get("skill")


def blueprint_id(service_id: str) -> Optional[str]:
    return manifest().get(service_id, {}).get("blueprint_id")


@lru_cache(maxsize=32)
def load_blueprint(skill: str) -> Optional[dict]:
    return _read(BLUEPRINTS_DIR / skill / "blueprint.json")


@lru_cache(maxsize=32)
def load_output_schema(skill: str) -> Optional[dict]:
    return _read(BLUEPRINTS_DIR / skill / "output-schema.json")


@lru_cache(maxsize=32)
def load_form(skill: str) -> Optional[dict]:
    return _read(BLUEPRINTS_DIR / skill / "form.json")


@lru_cache(maxsize=1)
def load_snapshot() -> dict:
    return _read(SNAPSHOT_PATH) or {"entries": {}}


def snapshot_version() -> str:
    return str(load_snapshot().get("snapshot_version", "unknown"))


@lru_cache(maxsize=1)
def _boost_placeholders() -> dict:
    return _read(BOOST_PLACEHOLDERS_PATH) or {}


def placeholders_for(skill: str) -> list[str]:
    """Chiavi snapshot che il boost consuma. INTERIM (manca build_snapshot.py di Luca)."""
    return list(_boost_placeholders().get(skill, []))


def meta_schema() -> dict:
    """Meta-schema L1 dalla libreria reale di Luca."""
    from k2a_validation import default_meta_schema
    return default_meta_schema()
