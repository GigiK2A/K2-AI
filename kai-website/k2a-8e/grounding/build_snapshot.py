"""build_snapshot — genera grounding/legalboost.snapshot.json dai placeholder.

REGOLA D'ORO (PROMPT_8e_Phase1): il testo di legge viene SOLO da normattiva
`get_articolo`, mai scritto a mano. Questo script è il punto in cui, SUL MAC DI
LUCA (dove gira l'MCP normattiva), si materializza lo snapshot reale.

Sul lato Luigi l'MCP normattiva NON è raggiungibile → lo script gira in modalità
COVERAGE-ONLY: legge i placeholder dichiarati nell'output-schema, verifica quali
sono risolti nello snapshot corrente, e FAIL-CLOSED se manca anche un solo
placeholder (esattamente come il gate del prompt Phase-1). Non inventa testi.

Uso:
    python grounding/build_snapshot.py            # coverage-report (fail-closed)
    K2A_NORMATTIVA_CMD=... python ...             # (su Mac Luca) risoluzione reale

Resolver normattiva: pluggabile. Se esiste un client (env K2A_NORMATTIVA_URL o un
modulo `normattiva_client`), lo si usa; altrimenti coverage-only.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "fixtures" / "flusso-legalboost-pmi.output-schema.json"
SNAPSHOT = ROOT / "grounding" / "legalboost.snapshot.json"


def declared_placeholders() -> list[dict]:
    data = json.loads(SCHEMA.read_text(encoding="utf-8"))
    return data.get("deterministici", [])


def current_snapshot() -> dict:
    try:
        return json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    except Exception:
        return {}


def resolve_normattiva(ph: dict) -> dict | None:
    """Hook risoluzione reale. Su Luigi ritorna None (MCP non raggiungibile).

    Su Mac Luca: implementare qui la chiamata `normattiva get_articolo` con le
    `coordinate` del placeholder e ritornare
    {testo, fonte, coordinate, vigenza, status} con `source: override_locale`.
    """
    import os
    if not os.environ.get("K2A_NORMATTIVA_URL") and not os.environ.get("K2A_NORMATTIVA_CMD"):
        return None
    # Placeholder per integrazione reale (da implementare sul Mac di Luca).
    raise NotImplementedError(
        "Integrazione normattiva da implementare sul Mac di Luca: "
        "chiamare get_articolo con le coordinate e restituire il verbatim."
    )


def main() -> int:
    placeholders = declared_placeholders()
    snap = current_snapshot()
    is_fixture = snap.get("_meta", {}).get("source") == "fixture"

    print("=== 8e build_snapshot · coverage-report (LegalBoost) ===")
    missing = []
    rows = []
    for ph in placeholders:
        chiave = ph.get("chiave")
        resolved = resolve_normattiva(ph)
        if resolved:
            snap[chiave] = resolved
            present, status = True, resolved.get("status", "")
        else:
            present = chiave in snap
            status = snap.get(chiave, {}).get("status", "MISSING")
        if not present:
            missing.append(chiave)
        flag = "⚠ FIXTURE/da confermare" if (is_fixture or "confermare" in str(status).lower()
                                              or "FIXTURE" in str(status)) else "ok"
        rows.append((chiave, "sì" if present else "NO", status, flag))

    w = max(len(r[0]) for r in rows) if rows else 10
    print(f"{'placeholder'.ljust(w)} | presente | status")
    for k, pres, st, flag in rows:
        print(f"{k.ljust(w)} | {pres.center(8)} | {st}  [{flag}]")

    if missing:
        print(f"\nFAIL-CLOSED: {len(missing)} placeholder NON risolti: {missing}")
        return 1

    if is_fixture:
        print("\nNOTA: snapshot corrente è FIXTURE (testi non normativi).")
        print("Per produzione: eseguire su Mac di Luca con normattiva → testi reali.")
        # Coverage formale OK (tutti i placeholder presenti) ma fixture → exit 0
        # con warning, così lo skeleton gira; il gate pre-vendita resta aperto.
        return 0

    SNAPSHOT.write_text(json.dumps(snap, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nOK: snapshot scritto in {SNAPSHOT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
