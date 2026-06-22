"""Caduta di tensione AC — CEI 64-8 art.525."""
from __future__ import annotations
import json, math
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, Field

_DATA = json.loads((Path(__file__).parent / "data" / "portate_cei_unel_35024.json").read_text())


class CadutaVInput(BaseModel):
    I: float = Field(..., gt=0)
    L: float = Field(..., gt=0)
    sezione_mm2: float = Field(..., gt=0)
    cosfi: float = 0.9
    sistema: Literal["trifase", "monofase"] = "trifase"
    Vn: float = 400.0
    materiale: Literal["Cu", "Al"] = "Cu"
    temp_conduttore: float = 70.0
    validate_runtime: bool = Field(False, description="Modalità C runtime (ADR-009): cross-validation inline.")
    with_kb_references: bool = Field(False, description="Tappa 2: include riferimenti normativi KB in riferimenti_kb.")
    dynamic_kb: bool = Field(False, description="Tappa 2 Fase 2: con with_kb_references, recupera i verbatim live dalla KB invece dello snapshot statico. Default False.")
    validate_kb_values: bool = Field(False, description="Tappa 2 Fase 2: con with_kb_references, valida i valori normativi del tool contro i verbatim KB (campo kb_validation). Default False.")


class CadutaVOutput(BaseModel):
    delta_V_volt: float
    delta_V_percento: float
    R_unitario_ohm_per_km: float
    X_unitario_ohm_per_km: float
    verifica_CEI_525: bool
    margine_al_limite_4pc: float
    trace: dict
    cross_validation_eseguita: bool = False
    cross_validation_esito: str = "NON_ESEGUITA"
    cross_validation_delta_pct: dict = Field(default_factory=dict)
    cross_validation_note: list[str] = Field(default_factory=list)
    riferimenti_kb: list[dict] = Field(default_factory=list)
    kb_validation: list[dict] = Field(default_factory=list)


def caduta_tensione(inp: CadutaVInput) -> CadutaVOutput:
    rho20 = _DATA["resistivita_conduttori"][inp.materiale]
    rho = rho20 * (1 + 0.004 * (inp.temp_conduttore - 20))
    R_per_km = rho * 1000 / inp.sezione_mm2
    x_tbl = _DATA["reattanza_unitaria_cavi"]
    keys = sorted(float(k) for k in x_tbl.keys())
    X_per_km = 0.0
    if inp.sezione_mm2 >= keys[-1]: X_per_km = x_tbl[str(int(keys[-1]))]
    elif inp.sezione_mm2 >= keys[0]:
        for i in range(len(keys) - 1):
            if keys[i] <= inp.sezione_mm2 <= keys[i + 1]:
                X_per_km = x_tbl[str(int(keys[i]))] + (x_tbl[str(int(keys[i + 1]))] - x_tbl[str(int(keys[i]))]) * (inp.sezione_mm2 - keys[i]) / (keys[i + 1] - keys[i])
                break
    R_lin, X_lin = R_per_km * inp.L / 1000, X_per_km * inp.L / 1000
    sinfi = math.sqrt(max(0, 1 - inp.cosfi ** 2))
    if inp.sistema == "trifase":
        dV = math.sqrt(3) * inp.I * (R_lin * inp.cosfi + X_lin * sinfi)
        formula = "√3·I·L·(R·cosφ + X·sinφ)"
    else:
        dV = 2 * inp.I * (R_lin * inp.cosfi + X_lin * sinfi)
        formula = "2·I·L·(R·cosφ + X·sinφ)"
    dVpc = dV / inp.Vn * 100
    _out = CadutaVOutput(
        delta_V_volt=round(dV, 3), delta_V_percento=round(dVpc, 3),
        R_unitario_ohm_per_km=round(R_per_km, 4), X_unitario_ohm_per_km=round(X_per_km, 4),
        verifica_CEI_525=dVpc <= 4, margine_al_limite_4pc=round(4 - dVpc, 3),
        trace={"norma": "CEI 64-8 art.525", "formula": formula},
    )
    from ._cross_validation import finalize
    return finalize(inp, _out, "caduta_tensione", {})
