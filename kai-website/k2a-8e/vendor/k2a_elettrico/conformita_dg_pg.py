"""Verifica di conformità DG/PG/PI a CEI 0-16 (MT-B).

Confronta le tarature IMPOSTATE (soglie/tempi del relè) + la REGOLAZIONE del
distributore (input runtime per-impianto) contro i valori di riferimento del
FACT-FILE GROUNDATO CEI 0-16 (MT-B0, `cei_0_16_facts.py`).

Invariante (DN-MT-5): i riferimenti vengono SOLO dal fact-file groundato (o,
dove il DSO li sovrascrive, dalla regolazione DSO fornita in input); NESSUN
valore normativo è cablato qui. Parametro mancante = gap dichiarato, non
inventato. Non è una taratura/ottimizzazione: solo verifica di conformità.

Trace ricco `CalcResult/TraceStep/inputs_hash` backward-compatible (norma+formula
come MT-A).
"""
from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field

from .cei_0_16_facts import carica_facts
from .trace import TraceStep, build_trace


class ImpostazioneFunzione(BaseModel):
    funzione: str  # es. "27.S1", "59.S2", "81>.S1", "67N.S1", "59V0"
    valore: str | None = None  # taratura impostata, es. "0,85 Un", "50,2 Hz", "250 A"
    tempo: str | None = None


class RegolazioneDSO(BaseModel):
    funzione: str
    valore: str | None = None  # override per-impianto del riferimento (es. Ig, soglie richieste)
    tempo: str | None = None


class ConformitaDgPgInput(BaseModel):
    impostazioni: list[ImpostazioneFunzione]
    regolazione_dso: list[RegolazioneDSO] = Field(default_factory=list)
    tolleranza_pc: float = Field(3.0, description="tolleranza ammessa (CEI 0-16 Tab.12 nota: ±3%)")


class EsitoFunzione(BaseModel):
    funzione: str
    stato: str  # "conforme" | "non_conforme" | "gap"
    conforme: bool | None
    impostato: str | None
    riferimento: str | None
    origine_riferimento: str  # "fact-file CEI 0-16" | "regolazione DSO" | "-"
    fonte: str
    vigenza: str | None
    messaggio: str


class ConformitaDgPgOutput(BaseModel):
    esiti: list[EsitoFunzione]
    conforme: bool
    completo: bool  # True se nessun gap (tutto verificabile)
    n_conformi: int
    n_non_conformi: int
    n_gap: int
    trace: dict[str, Any]


_NUM = re.compile(r"^\s*([0-9]+(?:[.,][0-9]+)?)\s*(.*)$")


def _parse(v: str | None) -> tuple[float, str] | None:
    """Estrae (numero, unità) da una stringa come '0,85 Un', '50,2 Hz', '500 ms'."""
    if not v:
        return None
    m = _NUM.match(v)
    if not m:
        return None
    num = float(m.group(1).replace(",", "."))
    unit = re.sub(r"\s+", "", m.group(2))
    if unit.lower() == "ms":
        return (num / 1000.0, "s")
    if unit.lower() == "s":
        return (num, "s")
    return (num, unit)


def _fonte_str(p: dict[str, Any]) -> str:
    f = p.get("fonte", {})
    s = f"CEI 0-16 §{f.get('paragrafo', '?')}"
    if f.get("tabella"):
        s += f" ({f['tabella']})"
    return s


def _indice() -> tuple[dict[str, list[dict]], dict[str, dict]]:
    facts = carica_facts()
    per_funzione: dict[str, list[dict]] = {}
    for p in facts["parametri"]:
        per_funzione.setdefault(p["funzione"], []).append(p)
    gap = {g["funzione"]: g for g in facts["gap"]}
    return per_funzione, gap


def conformita_dg_pg(inp: ConformitaDgPgInput) -> ConformitaDgPgOutput:
    per_funzione, gap_funzioni = _indice()
    dso = {d.funzione: d for d in inp.regolazione_dso}
    esiti: list[EsitoFunzione] = []
    steps: list[TraceStep] = []

    for i, imp in enumerate(inp.impostazioni, 1):
        f = imp.funzione
        fp = per_funzione.get(f)

        # --- risoluzione del riferimento (SOLO da fact-file groundato o DSO) ---
        ddso = dso.get(f)
        if ddso and ddso.valore:
            rif_val = ddso.valore
            origine = "regolazione DSO"
            base = _fonte_str(fp[0]) if fp and len(fp) == 1 else "CEI 0-16 (default sovrascritto da DSO)"
            fonte = f"regolazione DSO — {base}"
            vigenza = fp[0]["vigenza"] if fp and len(fp) == 1 else None
        elif f in gap_funzioni:
            esiti.append(EsitoFunzione(
                funzione=f, stato="gap", conforme=None, impostato=imp.valore, riferimento=None,
                origine_riferimento="fact-file CEI 0-16 (gap dichiarato)", fonte=_fonte_str(gap_funzioni[f]),
                vigenza=None, messaggio=f"parametro dichiarato GAP nel fact-file: {gap_funzioni[f]['motivo'][:90]}"))
            continue
        elif not fp:
            esiti.append(EsitoFunzione(
                funzione=f, stato="gap", conforme=None, impostato=imp.valore, riferimento=None,
                origine_riferimento="-", fonte="-", vigenza=None,
                messaggio="riferimento assente dal fact-file e nessuna regolazione DSO: parametro mancante (gap, non inventato)"))
            continue
        elif len(fp) > 1:
            esiti.append(EsitoFunzione(
                funzione=f, stato="gap", conforme=None, impostato=imp.valore, riferimento=None,
                origine_riferimento="fact-file CEI 0-16", fonte=_fonte_str(fp[0]), vigenza=fp[0]["vigenza"],
                messaggio=f"funzione ambigua ({len(fp)} soglie nel fact-file per '{f}'): specificare la soglia"))
            continue
        else:
            p = fp[0]
            rif_val = p["valore"]
            origine = "fact-file CEI 0-16"
            fonte = _fonte_str(p)
            vigenza = p["vigenza"]

        # --- confronto impostato vs riferimento ---
        if imp.valore is None:
            esiti.append(EsitoFunzione(
                funzione=f, stato="gap", conforme=None, impostato=None, riferimento=rif_val,
                origine_riferimento=origine, fonte=fonte, vigenza=vigenza, messaggio="valore impostato mancante"))
            continue

        ref = _parse(rif_val)
        setv = _parse(imp.valore)
        if ref is None:
            esiti.append(EsitoFunzione(
                funzione=f, stato="gap", conforme=None, impostato=imp.valore, riferimento=rif_val,
                origine_riferimento=origine, fonte=fonte, vigenza=vigenza,
                messaggio="riferimento non numerico (es. '140% Ig' / 'da concordare'): richiede valore DSO -> gap"))
            continue
        if setv is None or setv[1] != ref[1]:
            esiti.append(EsitoFunzione(
                funzione=f, stato="non_conforme", conforme=False, impostato=imp.valore, riferimento=rif_val,
                origine_riferimento=origine, fonte=fonte, vigenza=vigenza,
                messaggio=f"unità non confrontabili: impostato '{imp.valore}' vs riferimento '{rif_val}'"))
            continue

        tol = inp.tolleranza_pc / 100.0 * abs(ref[0])
        ok = abs(setv[0] - ref[0]) <= tol + 1e-9
        esiti.append(EsitoFunzione(
            funzione=f, stato="conforme" if ok else "non_conforme", conforme=ok,
            impostato=imp.valore, riferimento=rif_val, origine_riferimento=origine, fonte=fonte, vigenza=vigenza,
            messaggio=(f"OK: {imp.valore} entro ±{inp.tolleranza_pc}% del riferimento {rif_val} ({origine})" if ok
                       else f"KO: {imp.valore} fuori ±{inp.tolleranza_pc}% del riferimento {rif_val} ({origine})")))
        steps.append(TraceStep(
            step=i, descrizione=f"Conformità {f} ({origine})",
            formula="|impostato - riferimento| <= tolleranza·riferimento",
            valori={"impostato": setv[0], "riferimento": ref[0], "unita": ref[1], "tol_pc": inp.tolleranza_pc},
            risultato=1.0 if ok else 0.0, unita="bool"))

    n_conf = sum(1 for e in esiti if e.stato == "conforme")
    n_non = sum(1 for e in esiti if e.stato == "non_conforme")
    n_gap = sum(1 for e in esiti if e.stato == "gap")

    norma = "CEI 0-16:2025-04 §8.5.12.3 (PG) / §8.8.7.2 Tab.12 (PI) — verifica di conformità DG/PG/PI"
    formula = "conforme <=> |impostato - riferimento| <= tolleranza·riferimento (±3% ammesso da CEI 0-16, nota Tab.12)"
    trace = build_trace(
        norma=norma, formula=formula, steps=steps, inputs=inp.model_dump(),
        gap=[f"{e.funzione}: {e.messaggio}" for e in esiti if e.stato == "gap"])

    return ConformitaDgPgOutput(
        esiti=esiti, conforme=(n_non == 0), completo=(n_gap == 0),
        n_conformi=n_conf, n_non_conformi=n_non, n_gap=n_gap, trace=trace)
