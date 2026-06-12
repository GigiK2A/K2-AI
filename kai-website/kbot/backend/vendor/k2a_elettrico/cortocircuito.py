"""Corto circuito AC — IEC 60909 / CEI 11-25 (metodo impedenze)."""
from __future__ import annotations
import json, math
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, Field

_DATA = json.loads((Path(__file__).parent / "data" / "portate_cei_unel_35024.json").read_text())


class CortoCircuitoInput(BaseModel):
    potenza_trafo_kVA: float = Field(..., gt=0)
    Ucc_percento: float = 6.0
    Vn_BT: float = 400.0
    L_linea_m: float = Field(..., ge=0)
    sezione_mm2: float = Field(..., gt=0)
    materiale: Literal["Cu", "Al"] = "Cu"
    Pcc_rete_MVA: float | None = None


class CortoCircuitoOutput(BaseModel):
    Icc_trifase_origine_kA: float
    Icc_trifase_punto_kA: float
    Icc_monofase_F_PE_kA: float
    Z_trafo_ohm: float
    Z_totale_punto_ohm: float
    trace: dict


def corto_circuito(inp: CortoCircuitoInput) -> CortoCircuitoOutput:
    Vn = inp.Vn_BT
    Zt = inp.Ucc_percento / 100 * Vn ** 2 / (inp.potenza_trafo_kVA * 1000)
    Xt, Rt = Zt * 0.995, Zt * 0.1
    Zrete = Vn ** 2 / (inp.Pcc_rete_MVA * 1e6) if inp.Pcc_rete_MVA else 0.0
    rho = _DATA["resistivita_conduttori"][inp.materiale] * (1 + 0.004 * (80 - 20))
    R_lin = rho * inp.L_linea_m / inp.sezione_mm2
    x_tbl = _DATA["reattanza_unitaria_cavi"]
    keys = sorted(float(k) for k in x_tbl.keys())
    X_per_km = 0.0
    if inp.sezione_mm2 >= keys[-1]: X_per_km = x_tbl[str(int(keys[-1]))]
    elif inp.sezione_mm2 >= keys[0]:
        for i in range(len(keys) - 1):
            if keys[i] <= inp.sezione_mm2 <= keys[i + 1]:
                X_per_km = x_tbl[str(int(keys[i]))] + (x_tbl[str(int(keys[i + 1]))] - x_tbl[str(int(keys[i]))]) * (inp.sezione_mm2 - keys[i]) / (keys[i + 1] - keys[i])
                break
    X_lin = X_per_km * inp.L_linea_m / 1000
    Z_orig = math.sqrt(Rt ** 2 + (Xt + Zrete) ** 2)
    Icc3o = Vn / (math.sqrt(3) * Z_orig)
    Z_pt = math.sqrt((Rt + R_lin) ** 2 + (Xt + Zrete + X_lin) ** 2)
    Icc3p = Vn / (math.sqrt(3) * Z_pt)
    Z_loop = math.sqrt((2 * (Rt + R_lin)) ** 2 + (2 * (Xt + Zrete + X_lin)) ** 2)
    Icc1 = (Vn / math.sqrt(3)) / Z_loop
    return CortoCircuitoOutput(
        Icc_trifase_origine_kA=round(Icc3o / 1000, 3),
        Icc_trifase_punto_kA=round(Icc3p / 1000, 3),
        Icc_monofase_F_PE_kA=round(Icc1 / 1000, 3),
        Z_trafo_ohm=round(Zt, 5), Z_totale_punto_ohm=round(Z_pt, 5),
        trace={"norma": "IEC 60909 / CEI 11-25", "formula": "Zt = Ucc% × Vn²/(100·Sn); Icc = Vn/(√3·Z_tot)"},
    )
