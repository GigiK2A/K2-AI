"""boost_agent — generazione A2 dei Boost "che ragionano".

Architettura decisa con Luca: un AGENTE esegue la skill di dominio e, per OGNI
numero, chiama i tool MCP di Luca (`k2a-quant`, eseguito nel backend via
`mcp_quant`). Implementato come tool-use loop sul **raw Anthropic SDK** (NON
l'Agent SDK) → niente CLI `claude` nel container: serve solo `anthropic` (gia dep)
+ crediti per il modello.

Gate di grounding IN-LOOP (codice, non modello):
- CONTRATTO ASSUNZIONI: `dcf_enterprise_value_guarded` negato finche non e' stato
  chiamato `valida_assunzioni` con esito OK/WARN (FAIL → l'agente rivede le FCF).
- PROVENIENZA: ogni risultato porta un call_id (envelope di Luca); il deliverable
  deve citarlo. Verifica fail-closed: numeri EV senza provenienza → non si consegna.
- I NUMERI escono solo dai tool, mai dal modello.

NB: la generazione vera consuma crediti Anthropic. Tutto cio' che non e' la call al
modello (catalogo tool, gate, helper, provenienza) e' testabile senza crediti.
"""
from __future__ import annotations

import json
import time
from typing import Any, Optional

from . import mcp_quant
from .. import settings

DCF_TOOL = "dcf_enterprise_value_guarded"
VALIDA_TOOL = "valida_assunzioni"

OPERATING_RULES = """
## Regole operative (vincolanti)
Stai eseguendo la skill come AGENTE, server-side, senza utente.
1. OGNI numero di valutazione (ke, WACC, DCF, multipli, EV) DEVE uscire dai tool —
   MAI calcolato da te. Sequenza valutazione: capm_cost_of_equity → calc_wacc →
   valida_assunzioni (OBBLIGATORIO prima del DCF) → dcf_enterprise_value_guarded →
   ev_from_multiples → (patrimonial_value) → reconcile_ev.
2. CONTRATTO ASSUNZIONI: le FCF forward sono assunzioni TUE. Prima del DCF chiama
   valida_assunzioni. Esito OK → procedi; WARN → procedi MA motiva nel deliverable;
   FAIL → rivedi le FCF e ri-valida. Il DCF e' negato se non l'hai fatto.
3. Ogni risultato dei tool ha un campo "call_id": DEVI citarlo nella provenance.
4. Output FINALE = SOLO un blocco JSON con le chiavi del deliverable + un oggetto
   "enterprise_value" con ev_multipli_eur, ev_dcf_eur, valore_patrimoniale_eur,
   ev_raccomandato_eur (numeri PRESI dai tool) e "provenance" che mappa ogni campo
   al call_id del tool che l'ha prodotto. Niente numeri inventati.
"""

# ----- helper deterministici locali (NON nel MCP di Luca) -----
_LOCAL_TOOLS = [
    {"name": "patrimonial_value", "description": "Valore patrimoniale: PN contabile + rettifiche dichiarate.",
     "input_schema": {"type": "object", "properties": {
         "patrimonio_netto_eur": {"type": "number"}, "rettifiche_eur": {"type": "array", "items": {"type": "object"}}},
         "required": ["patrimonio_netto_eur"]}},
    {"name": "reconcile_ev", "description": "EV raccomandato: media ponderata dei 3 metodi (pesi sommano a 1).",
     "input_schema": {"type": "object", "properties": {
         "ev_multipli_eur": {"type": "number"}, "ev_dcf_eur": {"type": "number"}, "valore_patrimoniale_eur": {"type": "number"},
         "peso_multipli": {"type": "number"}, "peso_dcf": {"type": "number"}, "peso_patrimoniale": {"type": "number"}},
         "required": ["ev_multipli_eur", "ev_dcf_eur", "valore_patrimoniale_eur", "peso_multipli", "peso_dcf", "peso_patrimoniale"]}},
]


def _exec_local(name: str, args: dict) -> dict:
    if name == "patrimonial_value":
        pn = float(args.get("patrimonio_netto_eur", 0))
        rett = [{"voce": str(r.get("voce", "?")), "importo_eur": float(r.get("importo_eur", 0))}
                for r in (args.get("rettifiche_eur") or []) if isinstance(r, dict)]
        tot = sum(r["importo_eur"] for r in rett)
        return {"outputs": {"valore_patrimoniale_eur": round(pn + tot, 2), "pn_contabile_eur": pn,
                            "totale_rettifiche_eur": round(tot, 2)}}
    if name == "reconcile_ev":
        pesi = [float(args["peso_multipli"]), float(args["peso_dcf"]), float(args["peso_patrimoniale"])]
        if abs(sum(pesi) - 1.0) > 1e-6:
            return {"errore": f"i pesi devono sommare a 1 (somma={sum(pesi)})"}
        vals = [float(args["ev_multipli_eur"]), float(args["ev_dcf_eur"]), float(args["valore_patrimoniale_eur"])]
        return {"outputs": {"ev_raccomandato_eur": round(sum(v * p for v, p in zip(vals, pesi)), 2)}}
    return {"errore": f"tool locale sconosciuto: {name}"}


class Trace:
    """Registro delle chiamate tool: provenienza per call_id + stato del recinto."""
    def __init__(self) -> None:
        self.calls: list[dict] = []
        self._n = 0

    def record(self, name: str, args: dict, out: dict) -> str:
        # usa il call_id dell'envelope di Luca se c'e', altrimenti ne genera uno locale
        self._n += 1
        cid = out.get("call_id") or f"local__{name}#{self._n:03d}"
        self.calls.append({"call_id": cid, "tool": name, "outputs": out.get("outputs") or out})
        return cid

    def last_valida_esito(self) -> Optional[str]:
        for c in reversed(self.calls):
            if c["tool"] == VALIDA_TOOL:
                return (c["outputs"] or {}).get("esito_globale")
        return None

    def numbers_for(self, call_id: str) -> set[float]:
        acc: set[float] = set()
        for c in self.calls:
            if c["call_id"] == call_id:
                _walk(c["outputs"], acc)
        return acc


def _walk(v: Any, acc: set[float]) -> None:
    if isinstance(v, bool):
        return
    if isinstance(v, (int, float)):
        acc.add(round(float(v), 2))
    elif isinstance(v, dict):
        for x in v.values():
            _walk(x, acc)
    elif isinstance(v, list):
        for x in v:
            _walk(x, acc)


def exec_tool(name: str, args: dict, trace: Trace, quant_names: set[str]) -> dict:
    """Esegue un tool con i gate. CONTRATTO ASSUNZIONI: DCF negato senza valida OK/WARN.
    Pura logica deterministica → testabile senza crediti."""
    if name == DCF_TOOL:
        esito = trace.last_valida_esito()
        if esito is None:
            return {"errore": "DCF negato: chiama prima valida_assunzioni sulle FCF previste (contratto assunzioni)"}
        if esito == "FAIL":
            return {"errore": "DCF negato: valida_assunzioni=FAIL. Rivedi le FCF/g e ri-valida (serve OK o WARN)"}
    if name in quant_names:
        out = mcp_quant.call(name, args)
    else:
        out = _exec_local(name, args)
    trace.record(name, args, out)
    return out


def check_deliverable(doc: dict, trace: Trace, sezioni: list[str]) -> list[str]:
    """Fail-closed: sezioni presenti + provenienza verificata dei numeri EV."""
    problemi: list[str] = []
    for s in sezioni:
        if doc.get(s) in (None, "", [], {}):
            problemi.append(f"sezione mancante/vuota: '{s}'")
    ev = doc.get("enterprise_value") or {}
    prov = ev.get("provenance") or {}
    for campo in ("ev_multipli_eur", "ev_dcf_eur", "valore_patrimoniale_eur", "ev_raccomandato_eur"):
        v = ev.get(campo)
        if not isinstance(v, (int, float)) or isinstance(v, bool):
            problemi.append(f"enterprise_value.{campo} assente o non numerico")
            continue
        ref = prov.get(campo)
        if not ref:
            problemi.append(f"enterprise_value.{campo}: manca la provenance (call_id)")
        elif round(float(v), 2) not in trace.numbers_for(ref):
            problemi.append(f"enterprise_value.{campo}={v} non corrisponde all'output della chiamata citata '{ref}'")
    return problemi


def build_tools() -> tuple[list[dict], set[str]]:
    """Catalogo tool per l'agente: i tool MCP di Luca + gli helper locali.
    Ritorna (tools_anthropic, nomi_quant). Deterministico, no crediti."""
    quant = mcp_quant.tool_defs() if mcp_quant.available() else []
    quant_names = {t["name"] for t in quant}
    return quant + _LOCAL_TOOLS, quant_names


def run_boost_agent(skill_text: str, inputs: dict, servizio_id: str, *,
                    sezioni: list[str], model: Optional[str] = None, max_steps: int = 24) -> dict:
    """Esegue l'agente A2. CONSUMA CREDITI (call al modello). Ritorna deliverable +
    audit + metriche. fail-closed se la checklist/provenienza non passa."""
    from anthropic import Anthropic  # import locale: dep gia presente
    client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    mdl = model or getattr(settings, "ANTHROPIC_PDF_MODEL", None) or "claude-sonnet-4-6"
    tools, quant_names = build_tools()
    if not quant_names:
        return {"delivered": False, "error": "MCP quant non disponibile nel backend"}
    system = skill_text + "\n\n" + OPERATING_RULES
    messages: list[dict] = [{"role": "user",
        "content": f"Genera il deliverable AdvisorBoost per il servizio {servizio_id}. Dati cliente:\n{json.dumps(inputs, ensure_ascii=False)}"}]
    trace = Trace()
    t0 = time.time()
    n_tool_calls = 0
    final_text = ""
    for _ in range(max_steps):
        resp = client.messages.create(model=mdl, system=system, tools=tools,
                                       messages=messages, max_tokens=8192)
        messages.append({"role": "assistant", "content": [b.model_dump() for b in resp.content]})
        tool_uses = [b for b in resp.content if getattr(b, "type", None) == "tool_use"]
        if not tool_uses:
            final_text = "".join(getattr(b, "text", "") for b in resp.content if getattr(b, "type", None) == "text")
            break
        results = []
        for tu in tool_uses:
            n_tool_calls += 1
            out = exec_tool(tu.name, dict(tu.input), trace, quant_names)
            results.append({"type": "tool_result", "tool_use_id": tu.id,
                            "content": json.dumps(out, ensure_ascii=False)})
        messages.append({"role": "user", "content": results})

    doc = _extract_json(final_text)
    problemi = check_deliverable(doc, trace, sezioni) if doc else ["deliverable non e' JSON valido"]
    delivered = not problemi
    return {
        "delivered": delivered, "problemi": problemi,
        "deliverable": doc if delivered else None,
        "deliverable_rejected": None if delivered else doc,
        "provenance_calls": trace.calls,
        "metrics": {"servizio_id": servizio_id, "model": mdl, "tool_calls": n_tool_calls,
                    "duration_s": round(time.time() - t0, 1)},
    }


def _extract_json(text: str) -> Optional[dict]:
    if not text:
        return None
    s = text.find("{")
    e = text.rfind("}")
    if s < 0 or e <= s:
        return None
    try:
        return json.loads(text[s:e + 1])
    except json.JSONDecodeError:
        return None
