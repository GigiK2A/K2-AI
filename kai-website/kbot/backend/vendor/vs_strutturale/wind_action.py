"""Azione del vento — NTC 2018 §3.3 + Circolare 21/1/2019 §C3.3.

Pipeline:
  1. v_b,0 da zona vento (Tab. 3.3.I) → corretto per altitudine sito → v_b
  2. v_b corretto per periodo di ritorno → v_r
  3. q_b = ½ · ρ · v_r²        (NTC eq. 3.3.4)
  4. categoria esposizione da (zona, classe rugosità, distanza costa) — Tab. 3.3.II
  5. c_e(z) coefficiente di esposizione — NTC eq. 3.3.5
  6. q_p(z) = q_b · c_e(z) · c_d · c_p   (qui restituiamo q_b · c_e(z); c_d e c_p applicati dal chiamante)

Densità aria assunta ρ = 1.25 kg/m³ (NTC §3.3.6).
"""

from __future__ import annotations
from ._hashing import compute_inputs_hash
from ._sanity import apply_sanity_rules_to_output, sanity_check_enabled
from ._units import dimensional_check_enabled, verify_output_dimensions

import math

from .data.ntc_zone_vento import (
    NTC_CAT_ESPOSIZIONE,
    NTC_PARAMETRI_CAT_ESPOSIZIONE,
    NTC_ZONE_VENTO,
)
from .schemas import TraceStep, WindActionInput, WindActionOutput

RHO_ARIA = 1.25  # kg/m³ — NTC 2018 §3.3.6


def _fascia_distanza_costa(d_km: float | None) -> str:
    if d_km is None:
        return ">30km"
    if d_km <= 2:
        return "0-2km"
    if d_km <= 10:
        return "2-10km"
    if d_km <= 30:
        return "10-30km"
    return ">30km"


def _coefficiente_altitudine(zona: int, a_s: float) -> float:
    """c_a — NTC eq. 3.3.2.

    c_a = 1                     se a_s ≤ a_0
    c_a = 1 + k_s · (a_s/a_0 − 1)  se a_s > a_0
    """
    z = NTC_ZONE_VENTO[zona]
    if a_s <= z["a_0_m"]:
        return 1.0
    return 1.0 + z["k_s"] * (a_s / z["a_0_m"] - 1.0)


def _coefficiente_ritorno(T_R: int) -> float:
    """c_r — NTC eq. 3.3.3.

    Per T_R = 50 → c_r = 1.0
    Per T_R ≠ 50 → c_r = 0.75 · √(1 − 0.2 · ln(−ln(1 − 1/T_R)))
    """
    if T_R == 50:
        return 1.0
    arg = 1.0 - 1.0 / T_R
    return 0.75 * math.sqrt(1.0 - 0.2 * math.log(-math.log(arg)))


def _coefficiente_esposizione(z: float, cat: str, c_t: float) -> float:
    """c_e(z) — NTC eq. 3.3.5.

    c_e(z) = k_r² · c_t · ln(z/z_0) · [7 + c_t · ln(z/z_0)]    se z ≥ z_min
    c_e(z) = c_e(z_min)                                         se z < z_min
    """
    p = NTC_PARAMETRI_CAT_ESPOSIZIONE[cat]
    z_eff = max(z, p["z_min_m"])
    k_r, z_0 = p["k_r"], p["z_0_m"]
    ln_z = math.log(z_eff / z_0)
    return k_r * k_r * c_t * ln_z * (7.0 + c_t * ln_z)


def compute_wind_action(inp: WindActionInput) -> WindActionOutput:
    """Calcolo deterministico azione vento NTC 2018 §3.3."""
    h = compute_inputs_hash(inp)
    out = WindActionOutput(tool="wind_action", inputs_hash=h)

    # Out-of-scope guard v1
    if inp.zona_vento in (1, 4) and inp.zona_vento != 2 and inp.zona_vento != 3:
        # Manteniamo aperte zone 5-9 ma marchiamo warning
        if inp.zona_vento in (1, 4):
            out.out_of_scope = True
            out.out_of_scope_reason = (
                f"Zona vento {inp.zona_vento} fuori perimetro v1 (zone 2-3). "
                f"Calcolo eseguibile ma validation set non copre questa zona."
            )
    if inp.altezza_struttura_m > 34:
        out.warnings.append(
            f"Altezza {inp.altezza_struttura_m}m oltre perimetro validato v1 (max 34m)."
        )

    z_data = NTC_ZONE_VENTO[inp.zona_vento]

    # Step 1 — v_b,0
    v_b0 = z_data["v_b0_ms"]
    out.trace.append(TraceStep(
        label="v_b,0",
        formula="v_b,0 = lookup(zona)",
        substitution=f"v_b,0 = NTC_Tab_3.3.I[zona={inp.zona_vento}] = {v_b0} m/s",
        value=v_b0, unit="m/s",
        norm_ref="NTC 2018 §3.3.2 — Tab. 3.3.I",
    ))

    # Step 2 — c_a coefficiente altitudine
    c_a = _coefficiente_altitudine(inp.zona_vento, inp.altitudine_sito_m)
    out.trace.append(TraceStep(
        label="c_a",
        formula="c_a = 1 se a_s ≤ a_0 ; altrimenti c_a = 1 + k_s·(a_s/a_0 − 1)",
        substitution=(
            f"a_s={inp.altitudine_sito_m}m, a_0={z_data['a_0_m']}m, k_s={z_data['k_s']} "
            f"→ c_a = {c_a:.4f}"
        ),
        value=c_a, unit="-",
        norm_ref="NTC 2018 §3.3.2 — eq. 3.3.2",
    ))

    # Step 3 — v_b
    v_b = v_b0 * c_a
    out.trace.append(TraceStep(
        label="v_b",
        formula="v_b = v_b,0 · c_a",
        substitution=f"v_b = {v_b0} · {c_a:.4f} = {v_b:.3f} m/s",
        value=v_b, unit="m/s",
        norm_ref="NTC 2018 §3.3.2 — eq. 3.3.1",
    ))

    # Step 4 — c_r periodo di ritorno
    c_r = _coefficiente_ritorno(inp.periodo_ritorno_anni)
    out.trace.append(TraceStep(
        label="c_r",
        formula="c_r = 1 se T_R=50 ; altrimenti c_r = 0.75·√(1 − 0.2·ln(−ln(1 − 1/T_R)))",
        substitution=f"T_R={inp.periodo_ritorno_anni} anni → c_r = {c_r:.4f}",
        value=c_r, unit="-",
        norm_ref="NTC 2018 §3.3.2 — eq. 3.3.3",
    ))

    # Step 5 — v_r
    v_r = v_b * c_r
    out.trace.append(TraceStep(
        label="v_r",
        formula="v_r = v_b · c_r",
        substitution=f"v_r = {v_b:.3f} · {c_r:.4f} = {v_r:.3f} m/s",
        value=v_r, unit="m/s",
        norm_ref="NTC 2018 §3.3.2",
    ))
    out.v_b_ref_ms = v_b
    out.v_r_ms = v_r

    # Step 6 — q_b pressione cinetica di riferimento
    q_b = 0.5 * RHO_ARIA * v_r * v_r
    out.trace.append(TraceStep(
        label="q_b",
        formula="q_b = ½ · ρ · v_r²",
        substitution=f"q_b = 0.5 · {RHO_ARIA} · {v_r:.3f}² = {q_b:.2f} N/m²",
        value=q_b, unit="N/m²",
        norm_ref="NTC 2018 §3.3.4 — eq. 3.3.4",
    ))
    out.q_b_Nm2 = q_b

    # Step 7 — categoria esposizione
    fascia = _fascia_distanza_costa(inp.distanza_costa_km)
    key = (inp.zona_vento, inp.classe_rugosita, fascia)
    cat = NTC_CAT_ESPOSIZIONE.get(key)
    if cat is None:
        out.warnings.append(
            f"Combinazione (zona={inp.zona_vento}, rug={inp.classe_rugosita}, "
            f"fascia={fascia}) non in tabella ridotta v1. Defaulting II."
        )
        cat = "II"
    out.categoria_esposizione = cat
    out.trace.append(TraceStep(
        label="cat_esposizione",
        formula="cat = lookup(zona, classe_rugosita, fascia_costa)",
        substitution=(
            f"zona={inp.zona_vento}, classe_rug={inp.classe_rugosita}, "
            f"distanza_costa={inp.distanza_costa_km}km → fascia={fascia} → cat={cat}"
        ),
        value=0, unit="-",
        norm_ref="NTC 2018 §3.3.7 — Tab. 3.3.II",
    ))

    # Step 8 — c_e(z)
    c_e = _coefficiente_esposizione(inp.quota_z_m, cat, inp.coefficiente_topografico)
    p = NTC_PARAMETRI_CAT_ESPOSIZIONE[cat]
    z_eff = max(inp.quota_z_m, p["z_min_m"])
    out.trace.append(TraceStep(
        label="c_e(z)",
        formula="c_e(z) = k_r² · c_t · ln(z/z_0) · [7 + c_t · ln(z/z_0)]    (z ≥ z_min)",
        substitution=(
            f"z={inp.quota_z_m}m, z_min={p['z_min_m']}m → z_eff={z_eff}m ; "
            f"k_r={p['k_r']}, z_0={p['z_0_m']}m, c_t={inp.coefficiente_topografico} "
            f"→ c_e(z) = {c_e:.4f}"
        ),
        value=c_e, unit="-",
        norm_ref="NTC 2018 §3.3.7 — eq. 3.3.5",
    ))
    out.c_e_z = c_e

    # Step 9 — q_p(z) (senza c_d e c_p; applicati dal chiamante a valle)
    q_p = q_b * c_e
    out.trace.append(TraceStep(
        label="q_p(z)",
        formula="q_p(z) = q_b · c_e(z)    [c_d e c_p applicati a valle]",
        substitution=f"q_p({inp.quota_z_m}) = {q_b:.2f} · {c_e:.4f} = {q_p:.2f} N/m²",
        value=q_p, unit="N/m²",
        norm_ref="NTC 2018 §3.3.6",
    ))
    out.q_p_z_Nm2 = q_p
    out.primary_value = q_p
    out.primary_unit = "N/m²"

    if dimensional_check_enabled():
        for _w in verify_output_dimensions(out.model_dump(), out.tool):
            out.warnings.append(f"[dim] {_w}")
    if sanity_check_enabled():
        out.warnings.extend(apply_sanity_rules_to_output(out.tool, out.model_dump()))
    return out
