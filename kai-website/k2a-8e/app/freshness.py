"""Freshness-gate a RUNTIME (Fix #6-gate, P0-10 / D-047).

Il freshness-gate esisteva solo come script CI (tests/test_freshness_gate.py): nessun
consumer a runtime → se lo snapshot regredisce a una legge pre-riforma e la CI non gira,
l'8e consegnerebbe testo superato come vigente. Qui la stessa logica diventa invocabile
dalla pipeline: blocca la generazione SE il boost usa un fatto normativo HARD-stale.

`evaluate` è puro (rules+entries → findings) per testabilità; `stale_findings` lo applica
allo snapshot reale, filtrato alle chiavi effettivamente usate dal boost.
"""
from __future__ import annotations

import json
import pathlib
from typing import Optional

from . import assets

_RULES_PATH = pathlib.Path(__file__).resolve().parent.parent / "grounding" / "freshness_rules.json"


def _rules() -> list:
    try:
        return json.loads(_RULES_PATH.read_text(encoding="utf-8")).get("rules", [])
    except Exception:
        return []


def evaluate(rules: list, entries: dict) -> list[dict]:
    """rules + entries snapshot → lista di finding (entry stale o senza evidenza riforma).
    Puro: nessun I/O. Stessa semantica del gate CI (stale_markers / evidence_any)."""
    findings: list[dict] = []
    for r in rules:
        key = r.get("key")
        sev = r.get("severity", "hard")
        e = entries.get(key)
        if e is None:
            findings.append({"key": key, "severity": sev, "law": r.get("law"),
                             "motivo": "entry assente nello snapshot"})
            continue
        testo = e.get("testo", "") or ""
        stale = [m for m in r.get("stale_markers", []) if m in testo]
        if stale:
            findings.append({"key": key, "severity": sev, "law": r.get("law"),
                             "motivo": f"marker di testo superato presenti: {stale}"})
        elif not any(m in testo for m in r.get("evidence_any", [])):
            findings.append({"key": key, "severity": sev, "law": r.get("law"),
                             "motivo": f"nessuna evidenza della riforma (manca uno di {r.get('evidence_any')})"})
    return findings


def stale_findings(used_keys: Optional[set] = None, hard_only: bool = True) -> list[dict]:
    """Finding stale sullo snapshot REALE, opzionalmente filtrati alle chiavi usate dal
    boost. hard_only=True → solo le regole `hard` (quelle che bloccano la consegna)."""
    f = evaluate(_rules(), assets.load_snapshot().get("entries", {}))
    if hard_only:
        f = [x for x in f if x.get("severity") == "hard"]
    if used_keys is not None:
        f = [x for x in f if x.get("key") in used_keys]
    return f
