"""Adapter asset di dominio — confine tra ENGINE (Luigi) e ASSET (Luca).

L'8e (engine) è asset-agnostico: carica blueprint, output-schema, form e
grounding-snapshot da:
  1. K2A_SKILLS_DIR (gli asset reali di Luca), se l'env è settato e il file esiste;
  2. altrimenti dalle FIXTURE locali (LegalBoost placeholder) per girare end-to-end.

Quando Luca consegna `k2a-skills` + lo snapshot reale, si setta K2A_SKILLS_DIR e
K2A_8E_SNAPSHOT → zero modifiche al codice engine. È il punto di drop-in.

`source()` dichiara da dove arriva ogni asset, così l'output sa se è REALE o FIXTURE.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from .settings import FIXTURES_DIR, SKILLS_DIR, SNAPSHOT_PATH

log = logging.getLogger("8e.assets")


def _read_json(path: Path) -> Optional[dict]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _skills_path(*parts: str) -> Optional[Path]:
    if not SKILLS_DIR:
        return None
    p = Path(SKILLS_DIR).joinpath(*parts)
    return p if p.exists() else None


# ---- Blueprint -----------------------------------------------------------

def load_blueprint(blueprint_id: str) -> tuple[Optional[dict], str]:
    """blueprint_id es. 'flusso-legalboost-pmi.boost'. Ritorna (data, source)."""
    fname = f"{blueprint_id}.blueprint.json"
    real = _skills_path("blueprints", fname)
    if real:
        data = _read_json(real)
        if data:
            return data, "real:k2a-skills"
    fx = FIXTURES_DIR / fname
    return _read_json(fx), "fixture"


def load_output_schema(service_id: str) -> tuple[Optional[dict], str]:
    real = _skills_path(service_id, "schemas", "output-schema.json")
    if real:
        data = _read_json(real)
        if data:
            return data, "real:k2a-skills"
    fx = FIXTURES_DIR / f"{service_id}.output-schema.json"
    return _read_json(fx), "fixture"


def load_form(service_id: str) -> tuple[Optional[dict], str]:
    real = _skills_path(service_id, "schemas", "form.json")
    if real:
        data = _read_json(real)
        if data:
            return data, "real:k2a-skills"
    fx = FIXTURES_DIR / f"{service_id}.form.json"
    return _read_json(fx), "fixture"


# ---- Grounding snapshot --------------------------------------------------

def load_snapshot() -> tuple[dict, str]:
    """Snapshot deterministico {chiave: {testo, fonte, vigenza, status}}.

    REALE = generato da grounding/build_snapshot.py via normattiva (Luca).
    FIXTURE = placeholder NON normativo (i testi NON sono legge reale).
    """
    data = _read_json(SNAPSHOT_PATH)
    if not data:
        return {}, "missing"
    meta = data.get("_meta", {})
    src = "real:normattiva" if meta.get("source") == "normattiva" else "fixture"
    return data, src


def snapshot_version() -> str:
    data, _ = load_snapshot()
    return str(data.get("_meta", {}).get("version", "unknown"))
