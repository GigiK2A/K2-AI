"""Dimensional analysis con pint — pilot L1.a (quick win B3).

Convenzione: gli input/output dei tool sono scalari con l'unita' codificata nel
SUFFISSO del nome (es. q_p_z_Nm2, N_pl_Rd_kN, eta_globale). pint si usa SOLO per
la verifica dimensionale all'output, non per i calcoli interni (overhead non
giustificato per scalari).

Pilot su 3 tool: wind_action, check_tubular_resistance, check_foundation.
Disattivabile con env K2A_DIMENSIONAL_CHECK=0 (default attivo).
"""

from __future__ import annotations

import math
import os

from pint import UnitRegistry

ureg = UnitRegistry()
Q_ = ureg.Quantity


def dimensional_check_enabled() -> bool:
    return os.getenv("K2A_DIMENSIONAL_CHECK", "1") != "0"


# Suffisso nome campo -> unita' pint attesa. None = adimensionale/non verificabile.
_SUFFIX_UNIT: dict[str, str] = {
    "ms": "meter/second",
    "Nm2": "newton/meter**2",
    "kPa": "kilopascal",
    "MPa": "megapascal",
    "kNm": "kilonewton*meter",
    "kN": "kilonewton",
    "m2": "meter**2",
    "m": "meter",
    "s": "second",
}

# Unita' attesa per ogni campo di output rilevante, per tool.
EXPECTED_UNITS: dict[str, dict[str, str]] = {
    "wind_action": {
        "v_b_ref_ms": "meter/second",
        "v_r_ms": "meter/second",
        "q_b_Nm2": "newton/meter**2",
        "q_p_z_Nm2": "newton/meter**2",
        "c_e_z": "dimensionless",
    },
    "check_tubular_resistance": {
        "N_pl_Rd_kN": "kilonewton",
        "V_pl_Rd_kN": "kilonewton",
        "M_el_Rd_kNm": "kilonewton*meter",
        "M_pl_Rd_kNm": "kilonewton*meter",
        "M_N_Rd_kNm": "kilonewton*meter",
        "eta_N": "dimensionless",
        "eta_V": "dimensionless",
        "eta_M_N": "dimensionless",
        "eta_globale": "dimensionless",
    },
    "check_foundation": {
        "A_eff_m2": "meter**2",
        "eccentricita_m": "meter",
        "q_Ed_kPa": "kilopascal",
        "q_Rd_kPa": "kilopascal",
        "H_Rd_scorrimento_kN": "kilonewton",
        "M_stab_kNm": "kilonewton*meter",
        "M_rib_d_kNm": "kilonewton*meter",
        "eta_capacita": "dimensionless",
        "eta_scorrimento": "dimensionless",
        "eta_ribaltamento": "dimensionless",
    },
    "seismic_spectrum": {
        "T_B_s": "second",
        "T_C_s": "second",
        "T_D_s": "second",
        "S_S": "dimensionless",
        "C_C": "dimensionless",
        "S_T": "dimensionless",
        "S": "dimensionless",
        "eta_smorzamento": "dimensionless",
    },
    "check_tubular_stability": {
        "N_cr_kN": "kilonewton",
        "N_b_Rd_kN": "kilonewton",
        "lambda_bar": "dimensionless",
        "chi": "dimensionless",
        "chi_shell": "dimensionless",
        "k_yy": "dimensionless",
        "eta_compressione": "dimensionless",
        "eta_interazione": "dimensionless",
    },
}


def _suffix_unit_for(field: str) -> str | None:
    """Inferisce l'unita' dal suffisso del nome campo (match piu' lungo)."""
    for suf in sorted(_SUFFIX_UNIT, key=len, reverse=True):
        if field.endswith("_" + suf):
            return _SUFFIX_UNIT[suf]
    return None


def verify_output_dimensions(values: dict, tool_name: str) -> list[str]:
    """Verifica coerenza dimensionale degli output di un tool.

    Per ogni campo atteso: valore finito + unita' attesa parsabile + (se il nome
    ha un suffisso unita') dimensionalita' del suffisso == dimensionalita' attesa.
    Ritorna la lista delle incoerenze (vuota se tutto ok).
    """
    expected = EXPECTED_UNITS.get(tool_name, {})
    issues: list[str] = []
    for field, exp_unit in expected.items():
        val = values.get(field)
        if val is None or isinstance(val, bool):
            continue
        if not isinstance(val, (int, float)):
            continue
        if not math.isfinite(val):
            issues.append(f"{field}: valore non finito ({val})")
            continue
        exp_dim = ureg(exp_unit).dimensionality
        suf_unit = _suffix_unit_for(field)
        if suf_unit is not None and ureg(suf_unit).dimensionality != exp_dim:
            issues.append(
                f"{field}: suffisso '{suf_unit}' incoerente con unita' attesa '{exp_unit}'"
            )
    return issues
