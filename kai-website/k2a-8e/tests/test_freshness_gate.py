"""Freshness-gate sullo snapshot (D-047 esteso al testo normativo).

Per ogni regola in `grounding/freshness_rules.json`, verifica che il verbatim
dell'entry nello snapshot porti EVIDENZA di aver incorporato la riforma nota
(almeno una stringa in `evidence_any`) e NON contenga marker di testo superato
(`stale_markers`). Regole `hard` → fail CI; `soft` → warning.

Rende automatico ciò che oggi è QA manuale: se un rebuild dello snapshot
regredisce a testo pre-riforma, la CI se ne accorge. Estende la regola "numero da
fonte verificata alla data" dal numero-cliente al testo di legge.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import assets  # noqa: E402

RULES_PATH = Path(__file__).resolve().parent.parent / "grounding" / "freshness_rules.json"


def main() -> int:
    rules = json.loads(RULES_PATH.read_text(encoding="utf-8")).get("rules", [])
    entries = assets.load_snapshot().get("entries", {})
    hard_fail, soft_warn, ok = [], [], 0

    for r in rules:
        key = r["key"]
        sev = r.get("severity", "hard")
        e = entries.get(key)
        if e is None:
            (hard_fail if sev == "hard" else soft_warn).append((key, "entry assente nello snapshot"))
            continue
        testo = e.get("testo", "") or ""
        ev_ok = any(m in testo for m in r.get("evidence_any", []))
        stale = [m for m in r.get("stale_markers", []) if m in testo]
        if stale:
            (hard_fail if sev == "hard" else soft_warn).append(
                (key, f"MARKER STALE presenti: {stale} — testo superato vs {r['law']}"))
        elif not ev_ok:
            (hard_fail if sev == "hard" else soft_warn).append(
                (key, f"nessuna evidenza di {r['law']} (manca uno di {r.get('evidence_any')})"))
        else:
            ok += 1
            print(f"  {key:18} OK  ({r['law']})")

    print(f"\nFRESHNESS-GATE: {ok}/{len(rules)} entry fresche")
    for key, msg in soft_warn:
        print(f"  ⚠ SOFT {key}: {msg}")
    if hard_fail:
        print("\n🔴 HARD FAIL (snapshot stale rispetto a legge nota):")
        for key, msg in hard_fail:
            print(f"  - {key}: {msg}")
    print("\n" + ("FRESHNESS-GATE PASS" if not hard_fail else "FRESHNESS-GATE FAIL"))
    return 1 if hard_fail else 0


if __name__ == "__main__":
    sys.exit(main())
