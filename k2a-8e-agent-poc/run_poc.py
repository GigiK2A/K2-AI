"""PoC AdvisorBoost — agente a guinzaglio corto (Claude Agent SDK).

Dimostra: l'agente ESEGUE la skill `flusso-advisorboost-pmi` (decide lui la
sequenza/metodi in base ai dati), i numeri escono SOLO dai tool quant
deterministici, gli hook bloccano (allowlist tier + anti-omissione), tutto
finisce in un audit trace riproducibile. Misura token/costo/latenza.

Run:  set -a; . ../kai-website/kbot/backend/.env.local; set +a
      .venv/bin/python run_poc.py
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    HookMatcher,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    query,
)

import audit
import hooks
from quant_server import QUANT_SERVER, QUANT_TOOL_NAMES

POC_DIR = Path(__file__).parent
SKILL_PATH = POC_DIR.parent / "kai-website" / "lib" / "skills" / "flusso-advisorboost-pmi" / "SKILL.md"
INPUT_PATH = POC_DIR / "data" / "juventus_input.json"
MODEL = "claude-sonnet-4-6"  # parità col motore 8e (pipeline usa Sonnet): confronto onesto

OPERATING_RULES = """
## Regole operative del PoC (vincolanti)

Stai eseguendo la skill qui sopra come AGENTE, in ambiente server-side senza utente.
1. I dati cliente sono in data/juventus_input.json (leggili con Read).
2. OGNI numero di valutazione (indici, WACC, DCF, multipli, valore patrimoniale,
   EV raccomandato) DEVE uscire dai tool mcp__quant__* — MAI calcolato da te.
   Scegli TU quali metodi pesare di più in base ai dati (motiva la scelta).
3. Il deliverable è il SOLO output JSON (punto 4 della skill): scrivilo con Write
   in out/deliverable.json con ESATTAMENTE queste chiavi top-level:
   executive_summary (str), analisi_bilancio (obj), analisi_settore (obj),
   posizionamento_vrio (obj), opzioni_strategiche (obj), piano_36_mesi (obj),
   enterprise_value (obj con: ev_multipli_eur, ev_dcf_eur, valore_patrimoniale_eur,
   ev_raccomandato_eur — numeri PRESI dagli output dei tool — più 'motivazione_pesi'),
   azioni_prioritarie (lista 5-8), cruscotto_kpi (obj), disclaimer (str — include
   la frase 'supporto decisionale' come da skill).
4. Se i dati attivano le soglie di allerta CCII (usa mcp__quant__indici_bilancio),
   dichiaralo esplicitamente nell'executive_summary, come impone la skill.
5. Niente DOCX/XLSX/HTML in questo PoC: solo il JSON. Sii completo ma essenziale.
"""


async def main() -> int:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERRORE: ANTHROPIC_API_KEY mancante (source .env.local)", file=sys.stderr)
        return 2

    skill_text = SKILL_PATH.read_text(encoding="utf-8")
    audit.TRACE = audit.AuditTrace(SKILL_PATH, INPUT_PATH, MODEL)
    hooks.OUT_DIR.mkdir(exist_ok=True)
    (hooks.DELIVERABLE).unlink(missing_ok=True)

    options = ClaudeAgentOptions(
        model=MODEL,
        system_prompt=skill_text + "\n\n" + OPERATING_RULES,
        cwd=POC_DIR,
        setting_sources=None,  # isolamento: niente CLAUDE.md/skill esterne
        mcp_servers={"quant": QUANT_SERVER},
        allowed_tools=QUANT_TOOL_NAMES + ["Read", "Write", "Edit", "TodoWrite"],
        disallowed_tools=["Bash", "WebSearch", "WebFetch", "Task", "Glob", "Grep", "NotebookEdit"],
        permission_mode="bypassPermissions",  # headless; il guinzaglio vero sono gli hook (solo-stringono)
        max_turns=60,
        hooks={
            "PreToolUse": [HookMatcher(hooks=[hooks.pre_tool_use_gate])],
            "Stop": [HookMatcher(hooks=[hooks.stop_gate])],
        },
    )

    prompt = (
        "Genera il deliverable AdvisorBoost per il cliente descritto in "
        "data/juventus_input.json seguendo la skill e le regole operative."
    )

    n_tool_calls = 0
    result: ResultMessage | None = None
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, ToolUseBlock):
                    n_tool_calls += 1
                    print(f"  → tool: {block.name}")
                elif isinstance(block, TextBlock) and block.text.strip():
                    print(f"  [agente] {block.text.strip()[:140]}")
        elif isinstance(message, ResultMessage):
            result = message

    ok_deliverable = not hooks._check_deliverable()
    meta = {
        "deliverable_ok": ok_deliverable,
        "gate_blocks_stop": sum(1 for g in audit.TRACE.data["gate_events"] if g["hook"] == "Stop" and g["action"] == "block"),
        "gate_denies_pretool": sum(1 for g in audit.TRACE.data["gate_events"] if g["hook"] == "PreToolUse" and g["action"] == "deny"),
        "tool_calls": n_tool_calls,
        "num_turns": getattr(result, "num_turns", None),
        "duration_s": round(getattr(result, "duration_ms", 0) / 1000, 1) if result else None,
        "total_cost_usd": getattr(result, "total_cost_usd", None),
        "usage": getattr(result, "usage", None),
        "is_error": getattr(result, "is_error", None),
    }
    audit_path = audit.TRACE.finish(meta)
    (POC_DIR / "out" / "metrics.json").write_text(json.dumps(meta, indent=2, default=str), encoding="utf-8")

    print("\n========== ESITO PoC ==========")
    print(json.dumps(meta, indent=2, default=str))
    print(f"audit trace: {audit_path}")
    print(f"deliverable: {hooks.DELIVERABLE} ({'OK' if ok_deliverable else 'INCOMPLETO'})")
    return 0 if ok_deliverable else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
