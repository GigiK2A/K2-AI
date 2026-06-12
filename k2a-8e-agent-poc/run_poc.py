"""PoC AdvisorBoost — agente a guinzaglio corto (Claude Agent SDK).

L'agente ESEGUE la skill `flusso-advisorboost-pmi`, i numeri escono SOLO dai tool
quant deterministici, gli hook bloccano (allowlist tier + anti-omissione +
PROVENIENZA), tutto in un audit trace riproducibile. FAIL-CLOSED: un run FAILED
non diventa mai un deliverable consegnato.

Uso:
  set -a; . ../kai-website/kbot/backend/.env.local; set +a
  .venv/bin/python run_poc.py [input.json] [out_dir]
Default: data/juventus_input.json → out/
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
MODEL = "claude-sonnet-4-6"  # parità col motore 8e (pipeline usa Sonnet): confronto onesto

OPERATING_RULES = """
## Regole operative del PoC (vincolanti)

Stai eseguendo la skill qui sopra come AGENTE, server-side senza utente.
1. I dati cliente sono nel file indicato qui sotto (leggilo con Read).
2. OGNI numero di valutazione (indici, WACC, DCF, multipli, valore patrimoniale,
   EV raccomandato) DEVE uscire dai tool mcp__quant__* — MAI calcolato da te.
   Scegli TU quali metodi pesare di più in base ai dati (motiva la scelta).
3. Ogni risultato dei tool quant include un campo "call_id". DEVI citarlo.
4. Il deliverable è il SOLO output JSON: scrivilo con Write in <OUTFILE> con
   ESATTAMENTE queste chiavi top-level:
   executive_summary (str), analisi_bilancio (obj), analisi_settore (obj),
   posizionamento_vrio (obj), opzioni_strategiche (obj), piano_36_mesi (obj),
   enterprise_value (obj), azioni_prioritarie (lista 5-8), cruscotto_kpi (obj),
   disclaimer (str — include la frase 'supporto decisionale').
   enterprise_value DEVE avere: ev_multipli_eur, ev_dcf_eur,
   valore_patrimoniale_eur, ev_raccomandato_eur (numeri PRESI dagli output dei
   tool), 'motivazione_pesi' (str), e 'provenance' (obj) che mappa OGNI campo
   numerico al call_id del tool che l'ha prodotto, es:
   "provenance": {"ev_multipli_eur":"mcp__quant__ev_from_multiples#005", ...}.
   Il valore nel campo DEVE coincidere con l'output di QUELLA chiamata, altrimenti
   il gate rifiuta la consegna.
5. Se i dati attivano le soglie di allerta CCII (mcp__quant__indici_bilancio),
   dichiaralo esplicitamente nell'executive_summary.
6. Niente DOCX/XLSX/HTML in questo PoC: solo il JSON. Completo ma essenziale.
"""


async def run(input_path: Path, out_dir: Path, tier: str = "standard") -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    deliverable = out_dir / "deliverable.json"
    deliverable.unlink(missing_ok=True)
    (out_dir / "deliverable.REJECTED.json").unlink(missing_ok=True)
    (out_dir / "ALERT.txt").unlink(missing_ok=True)

    audit.TRACE = audit.AuditTrace(SKILL_PATH, input_path, MODEL)
    hooks.configure(out_dir, tier=tier)

    skill_text = SKILL_PATH.read_text(encoding="utf-8")
    rules = OPERATING_RULES.replace("<OUTFILE>", str(deliverable))

    options = ClaudeAgentOptions(
        model=MODEL,
        system_prompt=skill_text + "\n\n" + rules,
        cwd=POC_DIR,
        setting_sources=None,
        mcp_servers={"quant": QUANT_SERVER},
        allowed_tools=QUANT_TOOL_NAMES + ["Read", "Write", "Edit", "TodoWrite"],
        disallowed_tools=["Bash", "WebSearch", "WebFetch", "Task", "Glob", "Grep", "NotebookEdit"],
        permission_mode="bypassPermissions",
        max_turns=60,
        hooks={
            "PreToolUse": [HookMatcher(hooks=[hooks.pre_tool_use_gate])],
            "Stop": [HookMatcher(hooks=[hooks.stop_gate])],
        },
    )

    prompt = (
        f"Genera il deliverable AdvisorBoost per il cliente descritto in "
        f"{input_path} seguendo la skill e le regole operative. Scrivi l'output in {deliverable}."
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
                    print(f"  [agente] {block.text.strip()[:120]}")
        elif isinstance(message, ResultMessage):
            result = message

    problemi = hooks.check_deliverable()
    failed = bool(problemi) or hooks.RUN_FAILED
    delivered = not failed

    # FAIL-CLOSED: un run FAILED non diventa MAI un deliverable consegnato.
    if failed and deliverable.exists():
        deliverable.rename(out_dir / "deliverable.REJECTED.json")
        (out_dir / "ALERT.txt").write_text(
            "RUN FAILED — NON consegnare. Problemi:\n- " + "\n- ".join(problemi or ["max blocchi gate raggiunti"]),
            encoding="utf-8",
        )

    meta = {
        "case": input_path.stem,
        "delivered": delivered,
        "run_failed": failed,
        "problemi": problemi,
        "gate_blocks_stop": sum(1 for g in audit.TRACE.data["gate_events"] if g["hook"] == "Stop" and g["action"] == "block"),
        "gate_denies_pretool": sum(1 for g in audit.TRACE.data["gate_events"] if g["hook"] == "PreToolUse" and g["action"] == "deny"),
        "provenance_verified": delivered,  # con i nuovi gate, delivered ⇒ provenienza verificata
        "tool_calls": n_tool_calls,
        "num_turns": getattr(result, "num_turns", None),
        "duration_s": round(getattr(result, "duration_ms", 0) / 1000, 1) if result else None,
        "total_cost_usd": getattr(result, "total_cost_usd", None),
        "output_tokens": (getattr(result, "usage", {}) or {}).get("output_tokens"),
        "is_error": getattr(result, "is_error", None),
    }
    audit.TRACE.finish(meta, out_dir)
    (out_dir / "metrics.json").write_text(json.dumps(meta, indent=2, default=str), encoding="utf-8")
    return meta


async def main() -> int:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERRORE: ANTHROPIC_API_KEY mancante (source .env.local)", file=sys.stderr)
        return 2
    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else POC_DIR / "data" / "juventus_input.json"
    out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else POC_DIR / "out"
    meta = await run(input_path, out_dir)
    print("\n========== ESITO PoC ==========")
    print(json.dumps(meta, indent=2, default=str))
    status = "CONSEGNATO" if meta["delivered"] else "FAILED → quarantena (deliverable.REJECTED.json + ALERT.txt)"
    print(f"esito: {status}")
    return 0 if meta["delivered"] else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
