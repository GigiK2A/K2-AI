"""Dimensionamento cavi BT — CEI-UNEL 35024/1 + CEI 64-8 art.433.1."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, Field

_DATA = json.loads((Path(__file__).parent / "data" / "portate_cei_unel_35024.json").read_text())


class DimensionaCavoInput(BaseModel):
    Ib: float = Field(..., gt=0, description="Corrente d'impiego A")
    posa: Literal["B1", "B2", "C", "E", "F", "D1"] = "C"
    isolante: Literal["PVC", "EPR_XLPE"] = "PVC"
    materiale: Literal["Cu"] = "Cu"
    temp_ambiente: float = 30.0
    n_circuiti_raggruppati: int = Field(1, ge=1)
    In_protezione: float | None = None
    validate_runtime: bool = Field(False, description="Modalità C runtime (ADR-009): cross-validation inline.")
    with_kb_references: bool = Field(False, description="Tappa 2: include riferimenti normativi KB in riferimenti_kb.")
    dynamic_kb: bool = Field(False, description="Tappa 2 Fase 2: con with_kb_references, recupera i verbatim live dalla KB invece dello snapshot statico. Default False.")
    validate_kb_values: bool = Field(False, description="Tappa 2 Fase 2: con with_kb_references, valida i valori normativi del tool contro i verbatim KB (campo kb_validation). Default False.")


class DimensionaCavoOutput(BaseModel):
    sezione_minima_mm2: float
    Iz_corretta: float
    fattore_temperatura_k1: float
    fattore_raggruppamento_k2: float
    coordinamento_433_1: bool | None
    coordinamento_msg: str
    trace: dict
    cross_validation_eseguita: bool = False
    cross_validation_esito: str = "NON_ESEGUITA"
    cross_validation_delta_pct: dict = Field(default_factory=dict)
    cross_validation_note: list[str] = Field(default_factory=list)
    riferimenti_kb: list[dict] = Field(default_factory=list)
    kb_validation: list[dict] = Field(default_factory=list)


def _fattore_temp(t: float, isol: str) -> float:
    key = "fattori_correttivi_temperatura_aria_PVC" if isol == "PVC" else "fattori_correttivi_temperatura_aria_EPR"
    tbl = _DATA[key]
    ts = sorted(int(k) for k in tbl.keys())
    if t <= ts[0]: return float(tbl[str(ts[0])])
    if t >= ts[-1]: return float(tbl[str(ts[-1])])
    for i in range(len(ts) - 1):
        if ts[i] <= t <= ts[i + 1]:
            return tbl[str(ts[i])] + (tbl[str(ts[i + 1])] - tbl[str(ts[i])]) * (t - ts[i]) / (ts[i + 1] - ts[i])
    return 1.0


def _fattore_raggr(n: int) -> float:
    tbl = _DATA["fattori_correttivi_raggruppamento"]
    ks = sorted(int(k) for k in tbl.keys())
    if n <= ks[0]: return float(tbl[str(ks[0])])
    if n >= ks[-1]: return float(tbl[str(ks[-1])])
    for k in ks:
        if k >= n: return float(tbl[str(k)])
    return 1.0


def dimensiona_cavo(inp: DimensionaCavoInput) -> DimensionaCavoOutput:
    tbl = _DATA[f"rame_{inp.isolante}"]
    k1 = _fattore_temp(inp.temp_ambiente, inp.isolante)
    k2 = _fattore_raggr(inp.n_circuiti_raggruppati)
    sez_ok, Iz_corr = None, 0.0
    for sez_str, riga in tbl.items():
        Iz_eff = riga[inp.posa] * k1 * k2
        if Iz_eff >= inp.Ib:
            sez_ok, Iz_corr = float(sez_str), Iz_eff
            break
    if sez_ok is None:
        raise ValueError(f"Nessuna sezione soddisfa Ib={inp.Ib}A")

    coord, msg = None, "In_protezione non fornita."
    if inp.In_protezione:
        coord = inp.Ib <= inp.In_protezione <= Iz_corr
        if coord:
            msg = f"OK 433.1: Ib={inp.Ib} ≤ In={inp.In_protezione} ≤ Iz={Iz_corr:.1f}A"
        elif inp.In_protezione < inp.Ib:
            msg = f"KO: In={inp.In_protezione} < Ib={inp.Ib}A"
        else:
            msg = f"KO: In={inp.In_protezione} > Iz={Iz_corr:.1f}A"

    _out = DimensionaCavoOutput(
        sezione_minima_mm2=sez_ok, Iz_corretta=round(Iz_corr, 2),
        fattore_temperatura_k1=round(k1, 3), fattore_raggruppamento_k2=round(k2, 3),
        coordinamento_433_1=coord, coordinamento_msg=msg,
        trace={"norma": "CEI-UNEL 35024/1 + CEI 64-8 art.433.1",
               "formula_Iz": "Iz_eff = Iz_30°C × k1(T) × k2(n)"},
    )
    from ._cross_validation import finalize
    return finalize(inp, _out, "dimensiona_cavo", {"In_protezione_fornita": inp.In_protezione is not None})


# ---- Helper pubblico: Iz per sezione installata --------------------------

PosaType = Literal["B1", "B2", "C", "D1", "E", "F"]


def iz_per_sezione(
    sezione_mm2: float,
    materiale: Literal["Cu", "Al"] = "Cu",
    isolante: Literal["PVC", "EPR", "XLPE", "EPR_XLPE"] = "PVC",
    posa: PosaType = "C",
    k1_temperatura: float = 1.0,
    k2_raggruppamento: float = 1.0,
) -> float:
    """Ritorna Iz [A] della sezione installata, considerando posa e derating.

    Lookup tabella CEI-UNEL 35024-1 ed. 2021. Iz_30°C tabellare × k1 × k2.

    Esempi:
        >>> iz_per_sezione(16, "Cu", "EPR_XLPE", "D1")
        95.0
        >>> iz_per_sezione(2.5, "Cu", "PVC", "B1")
        21.0
        >>> iz_per_sezione(10, "Cu", "PVC", "C", k1_temperatura=0.87)  # T=40°C
        49.59

    Solleva ValueError se sezione non in tabella.
    Solleva NotImplementedError se materiale=Al (non popolato in v0.3).
    """
    if materiale == "Al":
        raise NotImplementedError("Tabella Al non popolata in v0.3 (solo Cu).")
    isolante_key = "EPR_XLPE" if isolante in ("EPR", "XLPE", "EPR_XLPE") else "PVC"
    table_key = f"rame_{isolante_key}"
    if table_key not in _DATA:
        raise ValueError(f"Combinazione non supportata: {materiale}/{isolante}")
    tbl = _DATA[table_key]
    # Chiavi JSON: "1.5", "2.5", "4", "6", "10", "16", ...
    sez_key = str(int(sezione_mm2)) if sezione_mm2 == int(sezione_mm2) else str(sezione_mm2)
    if sez_key not in tbl:
        raise ValueError(
            f"Sezione {sezione_mm2}mm² non in tabella. "
            f"Disponibili: {sorted(tbl.keys(), key=float)}"
        )
    if posa not in tbl[sez_key]:
        raise ValueError(f"Posa '{posa}' non disponibile per sezione {sezione_mm2}mm².")
    Iz_30 = tbl[sez_key][posa]
    return round(Iz_30 * k1_temperatura * k2_raggruppamento, 2)
