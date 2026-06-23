"""Ricarica veicoli elettrici — CEI 64-8 sez.722 + IEC 61851-1."""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field


class WallboxEVInput(BaseModel):
    potenza_wallbox_kW: float = Field(..., gt=0, description="Potenza wallbox in kW (tipico: 3.7, 7.4, 11, 22)")
    sistema: Literal["monofase", "trifase"] = "monofase"
    L_linea_m: float = Field(..., gt=0)
    Vn: float = Field(230.0, description="V nominale (230 monofase, 400 trifase)")
    contatore_dedicato: bool = Field(True, description="Contatore dedicato per detrazione fiscale")
    accumulo_FV_presente: bool = Field(False)


class WallboxEVOutput(BaseModel):
    corrente_carico_A: float
    sezione_min_cavo_mm2: float
    interruttore_magnetotermico_A: int
    interruttore_differenziale_tipo: str
    SPD_richiesto: bool
    eccedenza_potenza_su_base: bool
    note_normative: list[str]
    delta_V_pc_su_sezione: float
    trace: dict


def progetta_wallbox(inp: WallboxEVInput) -> WallboxEVOutput:
    P = inp.potenza_wallbox_kW * 1000
    if inp.sistema == "monofase":
        I = P / (inp.Vn * 0.95)  # cosφ wallbox ≈ 1, margine 0.95
    else:
        import math
        I = P / (math.sqrt(3) * inp.Vn * 0.95)

    # Tabella semplificata: sezione min e magnetotermico CEI 64-8/722
    if I <= 16:
        S, In = 2.5, 16
    elif I <= 20:
        S, In = 4, 20
    elif I <= 25:
        S, In = 6, 25
    elif I <= 32:
        S, In = 6, 32
    elif I <= 40:
        S, In = 10, 40
    elif I <= 50:
        S, In = 16, 50
    else:
        S, In = 25, 63

    # Caduta tensione veloce check: ΔV ≤ 4% (CEI 525)
    rho = 0.0178 * (1 + 0.004 * 50)  # Cu 70°C semplificato
    R_loop = (2 if inp.sistema == "monofase" else 1) * rho * inp.L_linea_m / S * (2 if inp.sistema == "monofase" else 1.732)
    # Più rigoroso: monofase ΔV=2·I·R·L/S, trifase √3·I·R·L/S
    if inp.sistema == "monofase":
        dV = 2 * I * rho * inp.L_linea_m / S
    else:
        import math
        dV = math.sqrt(3) * I * rho * inp.L_linea_m / S
    dVpc = dV / inp.Vn * 100
    if dVpc > 4.0:
        # Aumenta sezione
        for s_new in [10, 16, 25, 35, 50, 70, 95]:
            if inp.sistema == "monofase":
                dV_new = 2 * I * rho * inp.L_linea_m / s_new
            else:
                dV_new = math.sqrt(3) * I * rho * inp.L_linea_m / s_new
            if dV_new / inp.Vn * 100 <= 4.0:
                S = s_new
                dVpc = dV_new / inp.Vn * 100
                break

    note = [
        "CEI 64-8/722: alimentazione veicoli elettrici",
        "IEC 61851-1: modo di carica 3 (wallbox dedicata)",
        "Vietato uso prese CEE 16A o domestiche per ricarica prolungata",
        "Cavo dedicato dal quadro, no derivazioni",
    ]
    # Differenziale: tipo B (per ricarica DC) OPPURE A + RDC-DD integrato nel wallbox
    rcd_type = "Tipo B (rileva DC) OPPURE Tipo A + RDC-DD integrato nel wallbox (CEI 64-8/722.531.3.101)"
    SPD = True  # SPD tipo 2 obbligatorio
    note.append(f"Differenziale: {rcd_type}")
    note.append("SPD tipo 2 obbligatorio (722.534)")
    if inp.contatore_dedicato:
        note.append("Contatore dedicato installato → detrazione fiscale 50% applicabile")
    if inp.accumulo_FV_presente:
        note.append("Integrazione con FV/accumulo: verificare CEI 0-21 (regolazione inverter)")
    if inp.potenza_wallbox_kW > 7.4 and inp.sistema == "monofase":
        note.append("WARNING: potenza >7.4kW in monofase comporta squilibrio rete — preferire trifase")

    return WallboxEVOutput(
        corrente_carico_A=round(I, 2),
        sezione_min_cavo_mm2=S,
        interruttore_magnetotermico_A=In,
        interruttore_differenziale_tipo=rcd_type,
        SPD_richiesto=SPD,
        eccedenza_potenza_su_base=inp.potenza_wallbox_kW > 3.0,  # potenza base contratto residenziale standard
        note_normative=note,
        delta_V_pc_su_sezione=round(dVpc, 3),
        trace={
            "norma": "CEI 64-8 sez. 722 + IEC 61851-1 + CEI 64-8 sez.443/534 (SPD)",
            "ipotesi": "cosφ wallbox≈1, margine 5%, ΔV limite 4%",
            "formula_I": "I = P / (V × 0.95)  [monofase] o P / (√3 × V × 0.95)  [trifase]",
        },
    )
