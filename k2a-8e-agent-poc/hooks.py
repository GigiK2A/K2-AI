"""Hook deterministici — il guinzaglio dell'agente. Codice, non LLM.

- PreToolUse = gate entitlement/allowlist: il tier decide quali tool sono ammessi;
               Write/Edit solo dentro la out dir del run. Tutto il resto: deny.
- Stop       = gate anti-omissione + PROVENIENZA (criterio Luca #2): non si
               consegna senza tutte le sezioni obbligatorie, EV completo, e —
               requisito chiave — ogni numero EV deve CITARE la chiamata quant
               che l'ha prodotto (provenance), e quella chiamata deve davvero
               aver prodotto quel valore. Niente più match per valore (un numero
               inventato che coincide per caso NON passa più).

FAIL-CLOSED (criterio Luca #3): esaurito MAX_STOP_BLOCKS il run è marcato FAILED.
run_poc mette in quarantena il file e NON lo presenta come deliverable.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import audit
from quant_server import QUANT_TOOL_NAMES

POC_DIR = Path(__file__).parent

# Path della out dir del run corrente — settati da run_poc prima di ogni run.
OUT_DIR: Path = POC_DIR / "out"
DELIVERABLE: Path = OUT_DIR / "deliverable.json"

# Entitlement simulato (in produzione: derivato dal token firmato del backend).
TIER_ALLOWLIST: dict[str, set[str]] = {
    "standard": set(QUANT_TOOL_NAMES) | {"Read", "Write", "Edit", "TodoWrite"},
    "light": (set(QUANT_TOOL_NAMES) - {"mcp__quant__dcf_enterprise_value"}) | {"Read", "Write", "Edit", "TodoWrite"},
}
TIER = "standard"

SEZIONI_OBBLIGATORIE = [
    "executive_summary", "analisi_bilancio", "analisi_settore", "posizionamento_vrio",
    "opzioni_strategiche", "piano_36_mesi", "enterprise_value", "azioni_prioritarie",
    "cruscotto_kpi", "disclaimer",
]
EV_CAMPI = ["ev_multipli_eur", "ev_dcf_eur", "valore_patrimoniale_eur", "ev_raccomandato_eur"]

MAX_STOP_BLOCKS = 3
_stop_blocks = 0
RUN_FAILED = False


def configure(out_dir: Path, tier: str = "standard") -> None:
    """Reset dello stato per un nuovo run (chiamato da run_poc / run_batch)."""
    global OUT_DIR, DELIVERABLE, TIER, _stop_blocks, RUN_FAILED
    OUT_DIR = out_dir
    DELIVERABLE = out_dir / "deliverable.json"
    TIER = tier
    _stop_blocks = 0
    RUN_FAILED = False


async def pre_tool_use_gate(input_data: dict[str, Any], tool_use_id: str | None, context: Any) -> dict[str, Any]:
    name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input") or {}
    if audit.TRACE:
        audit.TRACE.tool_call(name, {k: v for k, v in tool_input.items() if k in ("file_path", "settore", "command")} or {})

    allowed = TIER_ALLOWLIST[TIER]
    deny_reason = None
    if name not in allowed:
        deny_reason = f"tool '{name}' non incluso nel tier '{TIER}'"
    elif name in ("Write", "Edit"):
        fp = Path(str(tool_input.get("file_path", ""))).resolve()
        if not str(fp).startswith(str(OUT_DIR.resolve())):
            deny_reason = f"scrittura ammessa solo nella out dir del run (richiesto: {fp})"

    if deny_reason:
        if audit.TRACE:
            audit.TRACE.gate("PreToolUse", "deny", deny_reason)
        return {"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": deny_reason,
        }}
    return {}


def check_deliverable() -> list[str]:
    """Checklist anti-omissione + provenienza. Vuota = consegnabile."""
    problemi: list[str] = []
    if not DELIVERABLE.exists():
        return [f"manca il file {DELIVERABLE.name} nella out dir"]
    try:
        doc = json.loads(DELIVERABLE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"deliverable.json non è JSON valido: {e}"]

    for s in SEZIONI_OBBLIGATORIE:
        if doc.get(s) in (None, "", [], {}):
            problemi.append(f"sezione obbligatoria mancante o vuota: '{s}'")

    ev = doc.get("enterprise_value") or {}
    prov = ev.get("provenance") or {}
    for campo in EV_CAMPI:
        v = ev.get(campo)
        if not isinstance(v, (int, float)) or isinstance(v, bool):
            problemi.append(f"enterprise_value.{campo} assente o non numerico")
            continue
        ref = prov.get(campo)
        if not ref:
            problemi.append(f"enterprise_value.{campo}: manca la provenance (deve citare 'mcp__quant__<tool>#<id>')")
            continue
        prodotti = audit.TRACE.call_numbers(ref) if audit.TRACE else set()
        if not prodotti:
            problemi.append(f"enterprise_value.{campo}: provenance '{ref}' non corrisponde ad alcuna chiamata quant registrata")
        elif round(float(v), 2) not in prodotti:
            problemi.append(
                f"enterprise_value.{campo}={v} NON è un output della chiamata citata '{ref}' "
                f"(provenienza non verificata — il numero non viene da quel tool)"
            )

    if "supporto decisionale" not in str(doc.get("disclaimer", "")):
        problemi.append("disclaimer obbligatorio assente (deve contenere 'supporto decisionale')")
    return problemi


async def stop_gate(input_data: dict[str, Any], tool_use_id: str | None, context: Any) -> dict[str, Any]:
    global _stop_blocks, RUN_FAILED
    problemi = check_deliverable()
    if not problemi:
        if audit.TRACE:
            audit.TRACE.gate("Stop", "allow", "checklist completa, provenienza verificata")
        return {}
    if _stop_blocks >= MAX_STOP_BLOCKS:
        RUN_FAILED = True  # fail-closed: run_poc metterà in quarantena, niente consegna
        if audit.TRACE:
            audit.TRACE.gate("Stop", "give_up_FAILED", f"{len(problemi)} problemi dopo {MAX_STOP_BLOCKS} blocchi: {problemi}")
        return {}
    _stop_blocks += 1
    reason = (
        f"CONSEGNA RIFIUTATA dal gate anti-omissione (tentativo {_stop_blocks}/{MAX_STOP_BLOCKS}). "
        f"Correggi e riscrivi deliverable.json. Per ogni numero EV inserisci enterprise_value.provenance "
        f"con il call_id del tool che l'ha prodotto. Problemi: " + "; ".join(problemi)
    )
    if audit.TRACE:
        audit.TRACE.gate("Stop", "block", reason)
    return {"decision": "block", "reason": reason}
