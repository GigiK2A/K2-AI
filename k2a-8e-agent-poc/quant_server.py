"""quant — MCP in-process coi tool di valutazione DETERMINISTICI.

SWAP dal quant-lite al QUANT VERO (i 4 tool che Luca ha mergiato nel k2a_quant
pubblicato; qui via `quant_real/`, copia della patch — quando il pubblicato è
vendorizzato in repo si importa da lì):
  - capm_cost_of_equity          ke da snapshot reale (Hamada + CAPM + size)
  - ev_from_multiples            EV da multiplo di settore (snapshot Damodaran)
  - valida_assunzioni            il RECINTO del giudizio (OK/WARN/FAIL)
  - dcf_enterprise_value_guarded DCF col g-range hard-reject (wrappa compute_dcf vendored)
Helper deterministici mantenuti (non parte dei 4): wacc, patrimonial_value,
reconcile_ev, indici_bilancio.

I numeri escono SOLO da qui (funzioni Python pure / snapshot), mai dal modello.
Ogni risultato porta un call_id (audit) che l'agente DEVE citare nel deliverable
(provenienza esplicita, criterio Luca #2).

Snapshot reale: data/snapshot_real.json (vendored Damodaran + italy rf 2.95% /
erp 6.69% anti-doppio-conteggio, dettati da Luca). NON tocca il vendored live.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from claude_agent_sdk import create_sdk_mcp_server, tool

import audit

POC_DIR = Path(__file__).parent
sys.path.insert(0, str(POC_DIR))                                                      # quant_real
sys.path.insert(0, str(POC_DIR.parent / "kai-website" / "kbot" / "backend" / "vendor"))  # k2a_quant vendored

from quant_real import capm_cost_of_equity, ev_from_multiples, valida_assunzioni      # noqa: E402
from quant_real.dcf_guard import dcf_enterprise_value_guarded                         # noqa: E402
from k2a_quant.dcf import compute_dcf, DcfInput                                       # noqa: E402

_SNAPSHOT_PATH = POC_DIR / "data" / "snapshot_real.json"
SNAP = json.loads(_SNAPSHOT_PATH.read_text(encoding="utf-8"))


def _ok(name: str, inputs: dict, outputs: dict) -> dict:
    """Output + call_id univoco (audit). L'agente DEVE citare il call_id nella
    provenance del deliverable. La verifica di provenienza nel gate Stop usa i
    NUMERI registrati qui, quindi `outputs` deve contenere i valori citati."""
    full = f"mcp__quant__{name}"
    call_id = audit.TRACE.quant_result(full, inputs, outputs) if audit.TRACE else f"{full}#000"
    payload = {"call_id": call_id, **outputs}
    return {"content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False)}]}


# ============================ i 4 tool REALI ============================
@tool(
    "capm_cost_of_equity",
    "Costo dell'equity (ke) con relevering di Hamada + CAPM + size premium. Beta, "
    "rf, ERP e size vengono dallo SNAPSHOT dato il settore (non li passi tu). Deterministico.",
    {"settore": str, "pfn_eur": float, "patrimonio_netto_eur": float, "fatturato_eur": float},
)
async def t_capm(args: dict) -> dict:
    r = capm_cost_of_equity(
        str(args["settore"]).strip(), pfn_eur=float(args["pfn_eur"]),
        patrimonio_netto_eur=float(args["patrimonio_netto_eur"]),
        fatturato_eur=float(args["fatturato_eur"]), snapshot=SNAP)
    out = r.get("outputs") or {"errore": r.get("errore")}
    return _ok("capm_cost_of_equity", args, out)


@tool(
    "ev_from_multiples",
    "Enterprise value da multiplo di settore (snapshot Damodaran): EBITDA>0 → EV/EBITDA, "
    "altrimenti EV/Ricavi. Il multiplo viene dallo snapshot. Deterministico.",
    {"settore": str, "ebitda_eur": float, "ricavi_eur": float},
)
async def t_ev_mult(args: dict) -> dict:
    r = ev_from_multiples(str(args["settore"]).strip(), ebitda_eur=float(args["ebitda_eur"]),
                          ricavi_eur=float(args["ricavi_eur"]), snapshot=SNAP)
    out = r.get("outputs") or {"errore": r.get("errore")}
    return _ok("ev_from_multiples", args, out)


@tool(
    "valida_assunzioni",
    "IL RECINTO: valida le assunzioni forward (FCF previsti, g, costo debito) contro gli "
    "storici del cliente e i range di settore. Ritorna esito_globale OK/WARN/FAIL. "
    "DEVE essere chiamato PRIMA del DCF. Deterministico.",
    {"settore": str, "ricavi_storici_eur": list, "ebitda_storici_eur": list,
     "fcf_previsti_eur": list, "g_perpetuo_pct": float, "costo_debito_pct": float,
     "patrimonio_netto_eur": float},
)
async def t_valida(args: dict) -> dict:
    storici = {"ricavi_eur": [float(x) for x in args.get("ricavi_storici_eur") or []],
               "ebitda_eur": [float(x) for x in args.get("ebitda_storici_eur") or []]}
    assunzioni = {"fcf_previsti_eur": [float(x) for x in args.get("fcf_previsti_eur") or []],
                  "g_perpetuo_pct": float(args["g_perpetuo_pct"]),
                  "costo_debito_pct": float(args["costo_debito_pct"])}
    r = valida_assunzioni(storici, assunzioni, str(args["settore"]).strip(), SNAP,
                          patrimonio_netto_eur=float(args.get("patrimonio_netto_eur") or 0) or None)
    return _ok("valida_assunzioni", args, r.get("outputs") or {"errore": r.get("errore")})


@tool(
    "dcf_enterprise_value_guarded",
    "Enterprise value con DCF (Gordon) e g-range HARD-REJECT: se g è fuori dal range di "
    "settore il tool RIFIUTA (errore, non warning). Richiede che valida_assunzioni sia già "
    "stato chiamato (lo impone l'hook). Deterministico.",
    {"settore": str, "fcf_previsti_eur": list, "wacc_pct": float, "g_perpetuo_pct": float},
)
async def t_dcf(args: dict) -> dict:
    dcf_input = {"fcf": [float(x) for x in args["fcf_previsti_eur"]],
                 "wacc": round(float(args["wacc_pct"]) / 100, 6),
                 "g_perpetual": round(float(args["g_perpetuo_pct"]) / 100, 6),
                 "terminal_method": "gordon"}
    r = dcf_enterprise_value_guarded(dcf_input, str(args["settore"]).strip(), SNAP, compute_dcf, DcfInput)
    if r.get("errore"):
        return _ok("dcf_enterprise_value_guarded", args, {"errore": r["errore"]})
    o = r.get("outputs") or {}
    out = {"ev_dcf_eur": o.get("enterprise_value"), "pv_terminal_value_eur": o.get("pv_terminal"),
           "terminal_value_eur": o.get("terminal_value"), "warnings": r.get("warnings")}
    return _ok("dcf_enterprise_value_guarded", args, out)


# ============================ helper deterministici (non parte dei 4) ============================
@tool(
    "wacc",
    "WACC = peso_equity·ke + peso_debito·kd·(1−t). Usa il ke da capm_cost_of_equity. Deterministico.",
    {"equity_eur": float, "debito_finanziario_eur": float, "costo_equity_pct": float,
     "costo_debito_pct": float, "tax_rate_pct": float},
)
async def t_wacc(args: dict) -> dict:
    e, d = float(args["equity_eur"]), max(float(args["debito_finanziario_eur"]), 0.0)
    ke, kd, tax = float(args["costo_equity_pct"]) / 100, float(args["costo_debito_pct"]) / 100, float(args["tax_rate_pct"]) / 100
    v = e + d
    if v <= 0:
        return _ok("wacc", args, {"errore": "equity+debito deve essere > 0"})
    w = (e / v) * ke + (d / v) * kd * (1 - tax)
    return _ok("wacc", args, {"wacc_pct": round(w * 100, 2), "peso_equity_pct": round(e / v * 100, 1), "peso_debito_pct": round(d / v * 100, 1)})


@tool(
    "patrimonial_value",
    "Valore patrimoniale: PN contabile + rettifiche dichiarate (plus/minusvalori). Deterministico.",
    {"patrimonio_netto_eur": float, "rettifiche_eur": list},
)
async def t_patr(args: dict) -> dict:
    pn = float(args["patrimonio_netto_eur"])
    rett = [{"voce": str(r.get("voce", "?")), "importo_eur": float(r.get("importo_eur", 0))}
            for r in (args.get("rettifiche_eur") or []) if isinstance(r, dict)]
    tot = sum(r["importo_eur"] for r in rett)
    return _ok("patrimonial_value", args, {"valore_patrimoniale_eur": round(pn + tot, 2), "pn_contabile_eur": pn, "totale_rettifiche_eur": round(tot, 2), "rettifiche": rett})


@tool(
    "reconcile_ev",
    "Riconcilia i 3 metodi (multipli, DCF, patrimoniale) in un valore raccomandato: media "
    "ponderata con pesi espliciti che sommano a 1. Deterministico.",
    {"ev_multipli_eur": float, "ev_dcf_eur": float, "valore_patrimoniale_eur": float,
     "peso_multipli": float, "peso_dcf": float, "peso_patrimoniale": float},
)
async def t_recon(args: dict) -> dict:
    pesi = [float(args["peso_multipli"]), float(args["peso_dcf"]), float(args["peso_patrimoniale"])]
    if abs(sum(pesi) - 1.0) > 1e-6:
        return _ok("reconcile_ev", args, {"errore": f"i pesi devono sommare a 1 (somma={sum(pesi)})"})
    vals = [float(args["ev_multipli_eur"]), float(args["ev_dcf_eur"]), float(args["valore_patrimoniale_eur"])]
    ev = sum(v * p for v, p in zip(vals, pesi))
    return _ok("reconcile_ev", args, {"ev_raccomandato_eur": round(ev, 2), "pesi": {"multipli": pesi[0], "dcf": pesi[1], "patrimoniale": pesi[2]}})


@tool(
    "indici_bilancio",
    "Indici chiave (D/E, PFN/EBITDA, incidenza personale, margine EBITDA, ROE, alert CCII). Deterministico.",
    {"ricavi_eur": float, "ebitda_eur": float, "risultato_netto_eur": float,
     "patrimonio_netto_eur": float, "pfn_eur": float, "costo_personale_eur": float},
)
async def t_indici(args: dict) -> dict:
    ric, ebitda = float(args["ricavi_eur"]), float(args["ebitda_eur"])
    pn, pfn, pers = float(args["patrimonio_netto_eur"]), float(args["pfn_eur"]), float(args["costo_personale_eur"])
    rn = float(args["risultato_netto_eur"])
    de = round(pfn / pn, 2) if pn else None
    pfn_ebitda = round(pfn / ebitda, 2) if ebitda > 0 else None
    out = {
        "margine_ebitda_pct": round(ebitda / ric * 100, 1) if ric else None,
        "d_e": de,
        "pfn_ebitda": pfn_ebitda if pfn_ebitda is not None else "n.c. (EBITDA non positivo)",
        "incidenza_personale_pct": round(pers / ric * 100, 1) if ric else None,
        "roe_pct": round(rn / pn * 100, 1) if pn else None,
        "alert_ccii": bool((ebitda <= 0) or (pfn_ebitda is not None and pfn_ebitda > 6) or (de is not None and de > 4) or (rn < 0 and abs(rn) > pn / 3 if pn else False)),
    }
    return _ok("indici_bilancio", args, out)


QUANT_SERVER = create_sdk_mcp_server(
    name="quant",
    version="0.2.0",
    tools=[t_capm, t_ev_mult, t_valida, t_dcf, t_wacc, t_patr, t_recon, t_indici],
)

QUANT_TOOL_NAMES = [
    "mcp__quant__capm_cost_of_equity", "mcp__quant__ev_from_multiples",
    "mcp__quant__valida_assunzioni", "mcp__quant__dcf_enterprise_value_guarded",
    "mcp__quant__wacc", "mcp__quant__patrimonial_value", "mcp__quant__reconcile_ev",
    "mcp__quant__indici_bilancio",
]

# Nome del tool DCF e del tool recinto — usati dall'hook PreToolUse per imporre
# "valida_assunzioni PRIMA del DCF" (contratto assunzioni, brief Luca).
DCF_TOOL_NAME = "mcp__quant__dcf_enterprise_value_guarded"
VALIDA_TOOL_NAME = "mcp__quant__valida_assunzioni"
