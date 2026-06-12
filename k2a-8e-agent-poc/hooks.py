"""Hook deterministici — il guinzaglio dell'agente. Codice, non LLM: "sempre", non "quasi sempre".

- PreToolUse  = gate entitlement/allowlist: il tier decide quali tool sono ammessi;
                Write/Edit solo dentro out/. Tutto il resto: deny.
- Stop        = gate anti-omissione: non si consegna senza tutte le sezioni
                obbligatorie, EV completo e — requisito chiave — ogni numero
                dell'EV TRACCIATO a un output dei tool quant (mai dal modello).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import audit
from quant_server import QUANT_TOOL_NAMES

POC_DIR = Path(__file__).parent
OUT_DIR = POC_DIR / "out"
DELIVERABLE = OUT_DIR / "deliverable.json"

# Entitlement simulato (in produzione: derivato dal token firmato del backend).
TIER_ALLOWLIST: dict[str, set[str]] = {
    "standard": set(QUANT_TOOL_NAMES) | {"Read", "Write", "Edit", "TodoWrite"},
    # esempio tier ridotto: light non può usare il DCF (solo multipli+patrimoniale)
    "light": (set(QUANT_TOOL_NAMES) - {"mcp__quant__dcf_enterprise_value"}) | {"Read", "Write", "Edit", "TodoWrite"},
}
TIER = "standard"

SEZIONI_OBBLIGATORIE = [
    "executive_summary", "analisi_bilancio", "analisi_settore", "posizionamento_vrio",
    "opzioni_strategiche", "piano_36_mesi", "enterprise_value", "azioni_prioritarie",
    "cruscotto_kpi", "disclaimer",
]
EV_CAMPI = ["ev_multipli_eur", "ev_dcf_eur", "valore_patrimoniale_eur", "ev_raccomandato_eur"]

_stop_blocks = 0
MAX_STOP_BLOCKS = 3  # anti-loop: dopo 3 rifiuti consegna comunque, run marcato FAILED


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
            deny_reason = f"scrittura ammessa solo in out/ (richiesto: {fp})"

    if deny_reason:
        if audit.TRACE:
            audit.TRACE.gate("PreToolUse", "deny", deny_reason)
        return {"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": deny_reason,
        }}
    return {}


def _check_deliverable() -> list[str]:
    """Checklist anti-omissione. Ritorna i problemi (vuota = consegnabile)."""
    problemi: list[str] = []
    if not DELIVERABLE.exists():
        return [f"manca il file {DELIVERABLE.name} in out/"]
    try:
        doc = json.loads(DELIVERABLE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"deliverable.json non è JSON valido: {e}"]

    for s in SEZIONI_OBBLIGATORIE:
        v = doc.get(s)
        if v in (None, "", [], {}):
            problemi.append(f"sezione obbligatoria mancante o vuota: '{s}'")

    ev = doc.get("enterprise_value") or {}
    traced = audit.TRACE.traced_numbers() if audit.TRACE else set()
    for campo in EV_CAMPI:
        v = ev.get(campo)
        if not isinstance(v, (int, float)) or isinstance(v, bool):
            problemi.append(f"enterprise_value.{campo} assente o non numerico")
        elif round(float(v), 2) not in traced:
            problemi.append(
                f"enterprise_value.{campo}={v} NON tracciato a un output dei tool quant "
                f"(i numeri devono uscire dai tool, non dal modello)"
            )

    discl = str(doc.get("disclaimer", ""))
    if "supporto decisionale" not in discl:
        problemi.append("disclaimer obbligatorio assente (deve contenere 'supporto decisionale')")
    return problemi


async def stop_gate(input_data: dict[str, Any], tool_use_id: str | None, context: Any) -> dict[str, Any]:
    global _stop_blocks
    problemi = _check_deliverable()
    if not problemi:
        if audit.TRACE:
            audit.TRACE.gate("Stop", "allow", "checklist completa, numeri tracciati")
        return {}
    if _stop_blocks >= MAX_STOP_BLOCKS:
        if audit.TRACE:
            audit.TRACE.gate("Stop", "allow_failed", f"{len(problemi)} problemi dopo {MAX_STOP_BLOCKS} blocchi: {problemi}")
        return {}
    _stop_blocks += 1
    reason = (
        f"CONSEGNA RIFIUTATA dal gate anti-omissione (tentativo {_stop_blocks}/{MAX_STOP_BLOCKS}). "
        f"Correggi e riscrivi out/deliverable.json. Problemi: " + "; ".join(problemi)
    )
    if audit.TRACE:
        audit.TRACE.gate("Stop", "block", reason)
    return {"decision": "block", "reason": reason}
