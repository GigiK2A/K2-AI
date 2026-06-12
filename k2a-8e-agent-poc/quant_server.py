"""quant-lite — MCP in-process con i tool di valutazione DETERMINISTICI.

Surrogato minimo di k2a-mcp-quant (di Luca, non presente in repo) per validare
l'architettura del PoC: l'agente RAGIONA la sequenza, ma ogni numero esce da qui
(funzioni Python pure), mai dal modello. Quando arriva il quant vero è uno swap.

NB snapshot multipli: PLACEHOLDER dichiarato (vedi data/multiples_snapshot.json)
— in produzione va il dataset Damodaran di Luca con manutenzione ricorrente.
"""
from __future__ import annotations

import json
from pathlib import Path

from claude_agent_sdk import create_sdk_mcp_server, tool

import audit

_SNAPSHOT_PATH = Path(__file__).parent / "data" / "multiples_snapshot.json"


def _ok(name: str, inputs: dict, outputs: dict) -> dict:
    """Ritorna l'output + un call_id univoco. L'agente DEVE citare il call_id
    nella sezione provenance del deliverable (criterio Luca #2: provenienza
    esplicita, non match per valore)."""
    full = f"mcp__quant__{name}"
    call_id = audit.TRACE.quant_result(full, inputs, outputs) if audit.TRACE else f"{full}#000"
    payload = {"call_id": call_id, **outputs}
    return {"content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False)}]}


@tool(
    "wacc",
    "Calcola il WACC (costo medio ponderato del capitale). Deterministico.",
    {"equity_eur": float, "debito_finanziario_eur": float, "costo_equity_pct": float,
     "costo_debito_pct": float, "tax_rate_pct": float},
)
async def wacc(args: dict) -> dict:
    e, d = float(args["equity_eur"]), float(args["debito_finanziario_eur"])
    ke, kd, tax = float(args["costo_equity_pct"]) / 100, float(args["costo_debito_pct"]) / 100, float(args["tax_rate_pct"]) / 100
    v = e + d
    if v <= 0:
        return _ok("wacc", args, {"errore": "equity+debito deve essere > 0"})
    w = (e / v) * ke + (d / v) * kd * (1 - tax)
    return _ok("wacc", args, {"wacc_pct": round(w * 100, 2), "peso_equity_pct": round(e / v * 100, 1), "peso_debito_pct": round(d / v * 100, 1)})


@tool(
    "dcf_enterprise_value",
    "Enterprise value con DCF: attualizza i FCF previsti + terminal value (Gordon). Deterministico.",
    {"fcf_previsti_eur": list, "wacc_pct": float, "g_perpetuo_pct": float},
)
async def dcf_enterprise_value(args: dict) -> dict:
    fcf = [float(x) for x in args["fcf_previsti_eur"]]
    w, g = float(args["wacc_pct"]) / 100, float(args["g_perpetuo_pct"]) / 100
    if w <= g:
        return _ok("dcf_enterprise_value", args, {"errore": "WACC deve essere > g perpetuo"})
    pv_fcf = sum(f / (1 + w) ** (i + 1) for i, f in enumerate(fcf))
    tv = fcf[-1] * (1 + g) / (w - g)
    pv_tv = tv / (1 + w) ** len(fcf)
    ev = pv_fcf + pv_tv
    return _ok("dcf_enterprise_value", args, {
        "ev_dcf_eur": round(ev, 2), "pv_fcf_eur": round(pv_fcf, 2),
        "terminal_value_eur": round(tv, 2), "pv_terminal_value_eur": round(pv_tv, 2),
        "peso_tv_su_ev_pct": round(pv_tv / ev * 100, 1) if ev else None,
    })


@tool(
    "ev_from_multiples",
    "Enterprise value da multipli EV/EBITDA o EV/Ricavi di settore (snapshot). Se EBITDA <= 0 usa il multiplo ricavi. Deterministico.",
    {"settore": str, "ebitda_eur": float, "ricavi_eur": float},
)
async def ev_from_multiples(args: dict) -> dict:
    snap = json.loads(_SNAPSHOT_PATH.read_text(encoding="utf-8"))
    settore = str(args["settore"]).lower().strip()
    row = snap["settori"].get(settore) or snap["settori"]["default"]
    ebitda, ricavi = float(args["ebitda_eur"]), float(args["ricavi_eur"])
    if ebitda > 0:
        ev, metodo = ebitda * row["ev_ebitda"], f"EV/EBITDA {row['ev_ebitda']}x"
    else:
        ev, metodo = ricavi * row["ev_ricavi"], f"EV/Ricavi {row['ev_ricavi']}x (EBITDA non positivo)"
    return _ok("ev_from_multiples", args, {
        "ev_multipli_eur": round(ev, 2), "metodo": metodo, "settore_usato": settore if settore in snap["settori"] else "default",
        "snapshot": {"fonte": snap["fonte"], "as_of": snap["as_of"], "placeholder": snap["placeholder"]},
    })


@tool(
    "patrimonial_value",
    "Valore patrimoniale: patrimonio netto contabile + rettifiche dichiarate (plusvalori/minusvalori). Deterministico.",
    {"patrimonio_netto_eur": float, "rettifiche_eur": list},
)
async def patrimonial_value(args: dict) -> dict:
    pn = float(args["patrimonio_netto_eur"])
    rett = [
        {"voce": str(r.get("voce", "?")), "importo_eur": float(r.get("importo_eur", 0))}
        for r in (args.get("rettifiche_eur") or [])
        if isinstance(r, dict)
    ]
    tot = sum(r["importo_eur"] for r in rett)
    return _ok("patrimonial_value", args, {"valore_patrimoniale_eur": round(pn + tot, 2), "pn_contabile_eur": pn, "totale_rettifiche_eur": round(tot, 2), "rettifiche": rett})


@tool(
    "reconcile_ev",
    "Riconcilia i 3 metodi in un valore raccomandato (media ponderata con pesi espliciti che sommano a 1). Deterministico.",
    {"ev_multipli_eur": float, "ev_dcf_eur": float, "valore_patrimoniale_eur": float,
     "peso_multipli": float, "peso_dcf": float, "peso_patrimoniale": float},
)
async def reconcile_ev(args: dict) -> dict:
    pesi = [float(args["peso_multipli"]), float(args["peso_dcf"]), float(args["peso_patrimoniale"])]
    if abs(sum(pesi) - 1.0) > 1e-6:
        return _ok("reconcile_ev", args, {"errore": f"i pesi devono sommare a 1 (somma={sum(pesi)})"})
    vals = [float(args["ev_multipli_eur"]), float(args["ev_dcf_eur"]), float(args["valore_patrimoniale_eur"])]
    ev = sum(v * p for v, p in zip(vals, pesi))
    return _ok("reconcile_ev", args, {"ev_raccomandato_eur": round(ev, 2), "pesi": {"multipli": pesi[0], "dcf": pesi[1], "patrimoniale": pesi[2]}})


@tool(
    "indici_bilancio",
    "Indici chiave da dati di bilancio (D/E, PFN/EBITDA, incidenza personale, margine EBITDA, alert CCII). Deterministico.",
    {"ricavi_eur": float, "ebitda_eur": float, "risultato_netto_eur": float,
     "patrimonio_netto_eur": float, "pfn_eur": float, "costo_personale_eur": float},
)
async def indici_bilancio(args: dict) -> dict:
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
    version="0.1.0",
    tools=[wacc, dcf_enterprise_value, ev_from_multiples, patrimonial_value, reconcile_ev, indici_bilancio],
)

QUANT_TOOL_NAMES = [
    "mcp__quant__wacc", "mcp__quant__dcf_enterprise_value", "mcp__quant__ev_from_multiples",
    "mcp__quant__patrimonial_value", "mcp__quant__reconcile_ev", "mcp__quant__indici_bilancio",
]
