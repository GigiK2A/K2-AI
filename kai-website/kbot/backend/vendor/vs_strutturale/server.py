"""MCP server entrypoint — espone tutti i tool di calcolo via protocollo MCP.

Tool READY (validati su fixture reali, asseverabili):
  - wind_action            (NTC §3.3)
  - seismic_spectrum       (NTC §3.2)
  - combine_loads          (NTC §2.5.3)

Tool STUB (schema visibile, calcolo bloccato fino a validation set):
  - solver_cantilever      (F3)
  - check_tubular_resistance, check_tubular_stability, check_sls_deflection (F4)
  - check_flange, check_fatigue, check_foundation (F5)
  - get_antenna, get_profile (DB)
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .antenna_lookup import GetAntennaInput as AntennaInput, lookup_antenna
from .combine_loads import CombineLoadsInput, compute_combine_loads
from .check_fatigue import CheckFatigueInput, check_fatigue
from .check_flange import CheckFlangeInput, check_flange
from .check_foundation import CheckFoundationInput, check_foundation
from .check_resistance import CheckResistanceInput, check_tubular_resistance
from .check_sls import CheckSlsInput, check_sls_deflection
from .check_local_buckling import CheckLocalBucklingInput, check_tubular_local_buckling
from .check_stability import CheckStabilityInput, check_tubular_stability
from .check_vortex import CheckVortexInput, check_vortex_shedding
from .check_anchor import CheckAnchorInput, check_anchor_en1992_4
from .check_capacity_pile import CheckCapacityPileInput, check_capacity_pile
from .check_brinch_hansen import CheckBrinchHansenInput, check_brinch_hansen
from .check_pile_group import CheckPileGroupInput, check_pile_group
from .check_micropali import CheckMicropaliInput, check_micropali
from .check_settlement import CheckSettlementInput, check_settlement
from .check_anchor_wall import CheckAnchorWallInput, check_anchor_wall
from .check_bolt_group import CheckBoltGroupInput, check_bolt_group
from .formula_lookup import LookupFormulaInput, lookup_formula
from .tools_final import (
    ClassifyStaticSchemeInput, DistributeAnchorInput,
    GetRtTemplateInput, LookupFatigueDetailInput,
    classify_static_scheme, distribute_anchor_reactions,
    get_rt_template, lookup_fatigue_detail,
)
from .check_wind_fatigue import CheckWindFatigueInput, check_wind_fatigue
from .fem_beam import FEMBucklingInput, FEMSolverInput, buckling_analysis, solve_fem_beam
from .solve_frame_3d import Frame3DInput, solve_frame_3d
from .wind_dynamic import WindDynamicFactorInput, compute_wind_dynamic_factor
from .tools_extra import (
    CheckAntennaRotationInput, CheckPunchingShearInput,
    check_antenna_rotation, check_punching_shear,
)
from .tools_misc import (
    CheckOverturningInput, CheckSectionClassInput, CheckSlidingInput,
    GetCombinationFactorsInput, IceLoadInput,
    check_overturning, check_section_class, check_sliding,
    get_combination_factors, ice_load,
)
from .committenza import GetCommittenzaSpecInput, get_committenza_spec
from .ntc_lookup import LookupNtcInput, lookup_ntc
from .profile_lookup import GetProfileInput, lookup_profile
from .schemas import WindActionInput
from .modal_analysis import ModalAnalysisInput, modal_analysis
from .check_modal_complete import CheckModalCompleteInput, check_modal_complete
from .check_pushover import CheckPushoverInput, check_pushover
from .check_serviceability_combined import (
    CheckServiceabilityCombinedInput, check_serviceability_combined,
)
from .check_aerodynamic_damping import (
    CheckAerodynamicDampingInput, check_aerodynamic_damping,
)
from .check_rc_flexure import CheckRcFlexureInput, check_rc_flexure
from .check_rc_shear import CheckRcShearInput, check_rc_shear
from .check_rc_cracking import CheckRcCrackingInput, check_rc_cracking
from .check_rc_bond import CheckRcBondInput, check_rc_bond
from .check_rc_confinement import CheckRcConfinementInput, check_rc_confinement
from .check_capacity_combined_rc import (
    CheckCapacityCombinedRcInput, check_capacity_combined_rc,
)
from .seismic_spectrum import SeismicSpectrumInput, compute_seismic_spectrum
from .solver_cantilever import SolverInput, solve_cantilever
from .wind_action import compute_wind_action

server: Server = Server("vs-strutturale")


_TOOLS = [
    # READY ----------------------------------------------------------------
    ("wind_action",
     "Azione del vento NTC 2018 §3.3 — q_p(z) tracciabile. Perimetro v1: zone 2-3, h≤34m.",
     WindActionInput,
     lambda a: json.dumps(compute_wind_action(WindActionInput(**a)).model_dump(), indent=2)),
    ("seismic_spectrum",
     "Spettro elastico e di progetto NTC 2018 §3.2 — S_e(T), S_d(T) con tracce.",
     SeismicSpectrumInput,
     lambda a: json.dumps(compute_seismic_spectrum(SeismicSpectrumInput(**a)).model_dump(), indent=2)),
    ("combine_loads",
     "Combinazioni di carico NTC 2018 §2.5.3 — SLU/SLE.",
     CombineLoadsInput,
     lambda a: json.dumps(compute_combine_loads(CombineLoadsInput(**a)).model_dump(), indent=2)),
    # STUBS ----------------------------------------------------------------
    ("solver_cantilever",
     "Solver sollecitazioni N, V, M per palo a mensola con carichi distribuiti + "
     "concentrati + peso proprio. Da validare contro FEM su 5 casi noti.",
     SolverInput,
     lambda a: json.dumps(solve_cantilever(SolverInput(**a)).model_dump(), indent=2)),
    ("check_tubular_resistance",
     "Verifica resistenza sezione tubolare cava NTC §4.2.4 / EN1993-1-1 §6.2. "
     "Calcola N_pl,Rd, M_pl,Rd, V_pl,Rd, interazione N+M (eq.6.31), η globale.",
     CheckResistanceInput,
     lambda a: json.dumps(check_tubular_resistance(CheckResistanceInput(**a)).model_dump(), indent=2)),
    ("check_tubular_stability",
     "Verifica stabilità asta CHS compressa+inflessa EN 1993-1-1 §6.3. "
     "Calcola N_cr, λ̄, χ, N_b,Rd e interazione N+M (eq. 6.61).",
     CheckStabilityInput,
     lambda a: json.dumps(check_tubular_stability(CheckStabilityInput(**a)).model_dump(), indent=2)),
    ("check_tubular_local_buckling",
     "Area efficace A_eff per CHS classe 4 (instabilità locale) — ρ=√(90ε²/(d/t)) EC3 "
     "semplificato; method='K2A' per convenzione legacy 2A/π. EN 1993-1-1 §6.2.2.5.",
     CheckLocalBucklingInput,
     lambda a: json.dumps(check_tubular_local_buckling(CheckLocalBucklingInput(**a)).model_dump(), indent=2)),
    ("check_sls_deflection",
     "Verifica SLE freccia in testa per palo a mensola a sezioni variabili "
     "(integrazione M/EI). Default limite H/100.",
     CheckSlsInput,
     lambda a: json.dumps(check_sls_deflection(CheckSlsInput(**a)).model_dump(), indent=2)),
    ("check_flange",
     "Verifica flangia circolare bullonata EN 1993-1-8 — bulloni (trazione, taglio, "
     "combinata) e flessione locale flangia (modello mensola cautelativo).",
     CheckFlangeInput,
     lambda a: json.dumps(check_flange(CheckFlangeInput(**a)).model_dump(), indent=2)),
    ("lookup_formula",
     "Catalogo 50+ formule strutturali (NTC 2018 + EC + CNR-DT 207). Filtra "
     "per categoria/simbolo/keyword. Sostituisce vs-catalogo-formule.",
     LookupFormulaInput,
     lambda a: json.dumps(lookup_formula(LookupFormulaInput(**a)).model_dump(), indent=2)),
    ("distribute_anchor_reactions",
     "Distribuzione T+V su layout 2D ancoraggi (piastra rigida). Per RT con "
     "tirafondi/baggioli — T_max e ancoraggio critico identificati.",
     DistributeAnchorInput,
     lambda a: json.dumps(distribute_anchor_reactions(DistributeAnchorInput(**a)).model_dump(), indent=2)),
    ("lookup_fatigue_detail",
     "Lookup Δσ_C dettagli costruttivi pali TLC (EN 1993-1-9 + Cellnex).",
     LookupFatigueDetailInput,
     lambda a: json.dumps(lookup_fatigue_detail(LookupFatigueDetailInput(**a)).model_dump(), indent=2)),
    ("classify_static_scheme",
     "Classifica schema statico (5 tipologie RT-A..RT-E) da vincoli rilevati.",
     ClassifyStaticSchemeInput,
     lambda a: json.dumps(classify_static_scheme(ClassifyStaticSchemeInput(**a)).model_dump(), indent=2)),
    ("get_rt_template",
     "Recupera template completo paline RT (vincoli, h, ancoraggio, verifiche critiche).",
     GetRtTemplateInput,
     lambda a: json.dumps(get_rt_template(GetRtTemplateInput(**a)).model_dump(), indent=2)),
    ("check_bolt_group",
     "Verifica gruppo bulloni — distribuzione M·r/Σr² + trazione + taglio + "
     "rifollamento + punzonamento + interazione (EN 1993-1-8 Tab. 3.4).",
     CheckBoltGroupInput,
     lambda a: json.dumps(check_bolt_group(CheckBoltGroupInput(**a)).model_dump(), indent=2)),
    ("check_anchor_en1992_4",
     "Verifica ancoraggi nel cls EN 1992-4: acciaio, cono cls, pull-out, "
     "pry-out, cono di bordo, interazione esponenziale §7.4.",
     CheckAnchorInput,
     lambda a: json.dumps(check_anchor_en1992_4(CheckAnchorInput(**a)).model_dump(), indent=2)),
    ("check_anchor_wall",
     "Verifica ancoraggi su MURATURA (ETAG 029 + EN 1996). Per attacchi a parete "
     "di paline RT su muratura piena/forata/cls cellulare/tufo/pietra. Modello "
     "semplificato cono muratura + acciaio + pull-out ETA. OBBLIGATORIA per "
     "verifica ancoraggio palo-muro in checklist RT v3 voce 13.",
     CheckAnchorWallInput,
     lambda a: json.dumps(check_anchor_wall(CheckAnchorWallInput(**a)).model_dump(), indent=2)),
    ("check_punching_shear",
     "Verifica punzonamento plinto / soletta su pilastro — EC2 §6.4 con "
     "v_Rd,c = C·k·(100·ρ·f_ck)^(1/3).",
     CheckPunchingShearInput,
     lambda a: json.dumps(check_punching_shear(CheckPunchingShearInput(**a)).model_dump(), indent=2)),
    ("check_antenna_rotation",
     "Verifica SLE rotazione antenna vs HPBW (datasheet). Criterio "
     "iliad/Cellnex: rotazione ≤ HPBW/2 − margine.",
     CheckAntennaRotationInput,
     lambda a: json.dumps(check_antenna_rotation(CheckAntennaRotationInput(**a)).model_dump(), indent=2)),
    ("solve_fem_beam",
     "Mini-FEM Euler-Bernoulli 2D — palo con vincoli intermedi (stralli/puntoni) "
     "e P-Δ iterativo. Per casi dove solver_cantilever è insufficiente.",
     FEMSolverInput,
     lambda a: json.dumps(solve_fem_beam(FEMSolverInput(**a)).model_dump(), indent=2)),
    ("solve_frame_3d",
     "Solver telaio spaziale 3D (direct stiffness, 6 dof/nodo): aste con N/taglio/"
     "torsione/flessione biassiale, vincoli per-gdl (incastro/cerniera), svincoli "
     "d'estremità (cerniere), carichi nodali e distribuiti. Restituisce reazioni ai "
     "vincoli, spostamenti e azioni d'estremità N/V/M/T. Per porta-antenne completi "
     "(palo+puntoni+telaio+baggioli) e reazioni reali ai baggioli.",
     Frame3DInput,
     lambda a: json.dumps(solve_frame_3d(Frame3DInput(**a)).model_dump(), indent=2)),
    ("buckling_analysis_fem",
     "Buckling FEM: λ_cr da autoproblema K·φ=λ·K_g·φ. Restituisce L_cr,eq "
     "esatta per palo rastremato (sostituisce L_cr=β·H assunto).",
     FEMBucklingInput,
     lambda a: json.dumps(buckling_analysis(FEMBucklingInput(**a)).model_dump(), indent=2)),
    ("wind_dynamic_factor",
     "CsCd EN 1991-1-4 Annex B Procedure 1 — fattore dinamico vento per pali "
     "snelli (sostituisce c_d=1.0 statico). Calcola I_v, B², R², k_p, CsCd.",
     WindDynamicFactorInput,
     lambda a: json.dumps(compute_wind_dynamic_factor(WindDynamicFactorInput(**a)).model_dump(), indent=2)),
    ("modal_analysis",
     "Analisi modale semplificata (Rayleigh) — frequenza fondamentale n_1, T_1, "
     "smorzamento, masse partecipanti per pali a mensola conici/cilindrici. "
     "Input per wind_dynamic_factor (c_sc_d). EN 1998-1 §4.3.3.2 + NTC §7.3.3.",
     ModalAnalysisInput,
     lambda a: json.dumps(modal_analysis(ModalAnalysisInput(**a)).model_dump(), indent=2)),
    ("check_modal_complete",
     "Analisi modale multimodale completa (eigensolver FE Euler-Bernoulli): modi superiori "
     "fino a massa partecipante cumulata ≥ target (default 90%). frequenze, periodi, "
     "partecipazioni per modo. EN 1998-1 §4.3.3.3 + NTC §7.3.3.1.",
     CheckModalCompleteInput,
     lambda a: json.dumps(check_modal_complete(CheckModalCompleteInput(**a)).model_dump(), indent=2)),
    ("check_pushover",
     "Analisi statica non lineare (pushover) metodo N2 Fajfar EN 1998-1 §4.3.3.4: curva di "
     "capacità MDOF→SDOF, bilineare equi-energia, target displacement, duttilità richiesta, "
     "verifica capacità ≥ domanda.",
     CheckPushoverInput,
     lambda a: json.dumps(check_pushover(CheckPushoverInput(**a)).model_dump(), indent=2)),
    ("check_serviceability_combined",
     "Verdetto SLE combinato: aggrega più check di esercizio (deflessione, rotazione, "
     "frequenza comfort, cedimenti) in un esito unico OK/NV con dettaglio e check governante. "
     "NTC 2018 §3.3 + §7.3.6.",
     CheckServiceabilityCombinedInput,
     lambda a: json.dumps(check_serviceability_combined(CheckServiceabilityCombinedInput(**a)).model_dump(), indent=2)),
    ("check_aerodynamic_damping",
     "Smorzamento aerodinamico δ_a EN 1991-1-4 §F.5: δ_a = c_f·ρ·b·v_m/(2·n_1·m_e), "
     "δ_tot = δ_s + δ_a + δ_d (da usare come smorzamento_totale_log in wind_dynamic_factor).",
     CheckAerodynamicDampingInput,
     lambda a: json.dumps(check_aerodynamic_damping(CheckAerodynamicDampingInput(**a)).model_dump(), indent=2)),
    ("check_rc_flexure",
     "Verifica sezione c.a. a flessione composta N+M SLU (EC2 §6.1 + NTC §4.1.2.1): stress "
     "block rettangolare, bisection asse neutro → M_Rd, x/d, η, governing (acciaio/cls).",
     CheckRcFlexureInput,
     lambda a: json.dumps(check_rc_flexure(CheckRcFlexureInput(**a)).model_dump(), indent=2)),
    ("check_rc_shear",
     "Verifica taglio SLU sezione c.a. EC2 §6.2 + NTC §4.1.2.3.5: V_Rd,c (senza staffe) / "
     "V_Rd,s + V_Rd,max (traliccio cotθ) → V_Rd, η, serve_armatura.",
     CheckRcShearInput,
     lambda a: json.dumps(check_rc_shear(CheckRcShearInput(**a)).model_dump(), indent=2)),
    ("check_rc_cracking",
     "Verifica fessurazione SLE c.a. EC2 §7.3.4 + NTC §4.1.2.2.4: w_k = s_r,max·(ε_sm−ε_cm) "
     "vs w_max per classe di esposizione.",
     CheckRcCrackingInput,
     lambda a: json.dumps(check_rc_cracking(CheckRcCrackingInput(**a)).model_dump(), indent=2)),
    ("check_rc_bond",
     "Aderenza e lunghezza di ancoraggio barre c.a. EC2 §8.4 + NTC §4.1.6.1.4: "
     "f_bd = 2.25·η_1·η_2·f_ctd, l_bd = α·(Φ/4)(σ_sd/f_bd) ≥ l_b,min. Anchor K2A foglio 30.",
     CheckRcBondInput,
     lambda a: json.dumps(check_rc_bond(CheckRcBondInput(**a)).model_dump(), indent=2)),
    ("check_rc_confinement",
     "Confinamento sismico c.a. EC8 §5.4.3.2.2 + NTC §7.4.6.2.2: ω_wd vs ω_wd,req/ω_wd,min "
     "(eq.7.4.29) + verifica spaziatura staffe per classe duttilità CD-A/CD-B.",
     CheckRcConfinementInput,
     lambda a: json.dumps(check_rc_confinement(CheckRcConfinementInput(**a)).model_dump(), indent=2)),
    ("check_capacity_combined_rc",
     "Verdetto combinato sezione c.a.: aggrega η di flessione/taglio/fessurazione/confinamento "
     "in esito unico OK/NV + governante (+ interazione quadratica SLU opzionale). NTC §4.1.2.",
     CheckCapacityCombinedRcInput,
     lambda a: json.dumps(check_capacity_combined_rc(CheckCapacityCombinedRcInput(**a)).model_dump(), indent=2)),
    ("ice_load",
     "Carico ghiaccio manicotto CNR-DT 207 §3.6 + iliad LG (10mm prescritto). "
     "Calcola D' = D+2s, peso/m, area frontale aumentata.",
     IceLoadInput,
     lambda a: json.dumps(ice_load(IceLoadInput(**a)).model_dump(), indent=2)),
    ("check_sliding",
     "Verifica scorrimento alla base — NTC §6.4.2.1 (A1+M2+R3) stand-alone.",
     CheckSlidingInput,
     lambda a: json.dumps(check_sliding(CheckSlidingInput(**a)).model_dump(), indent=2)),
    ("check_overturning_equ",
     "Verifica ribaltamento — NTC §2.6.1 EQU (γ_G,fav=0.9, γ_G,sfav=1.1).",
     CheckOverturningInput,
     lambda a: json.dumps(check_overturning(CheckOverturningInput(**a)).model_dump(), indent=2)),
    ("check_section_class",
     "Classificazione sezione tubolare EN 1993-1-1 §5.5 — restituisce classe "
     "1/2/3/4 + d/t + limiti.",
     CheckSectionClassInput,
     lambda a: json.dumps(check_section_class(CheckSectionClassInput(**a)).model_dump(), indent=2)),
    ("get_combination_factors",
     "Lookup ψ_0/ψ_1/ψ_2 + γ_G/γ_Q NTC Tab. 2.5.I + Tab. 2.6.I.",
     GetCombinationFactorsInput,
     lambda a: json.dumps(get_combination_factors(GetCombinationFactorsInput(**a)).model_dump(), indent=2)),
    ("check_vortex_shedding",
     "Verifica vortex shedding CNR-DT 207 §3.3 + EN 1993-3-1. Calcola v_cr per "
     "ciascun modo, Sc, segnala risonanza possibile e amplitude attesa.",
     CheckVortexInput,
     lambda a: json.dumps(check_vortex_shedding(CheckVortexInput(**a)).model_dump(), indent=2)),
    ("check_fatigue",
     "Verifica a fatica EN 1993-1-9 — regola di Miner su spettro di carico, "
     "curva S-N trilineare (m=3, m=5, cutoff).",
     CheckFatigueInput,
     lambda a: json.dumps(check_fatigue(CheckFatigueInput(**a)).model_dump(), indent=2)),
    ("check_wind_fatigue",
     "Fatica indotta da vento turbolento EN 1993-3-1 Annex B (rapid method). "
     "σ_E,2 = λ·σ_max → D = (σ_E,2/Δσ_C,d)^3. Per pali TLC vita 50 anni.",
     CheckWindFatigueInput,
     lambda a: json.dumps(check_wind_fatigue(CheckWindFatigueInput(**a)).model_dump(), indent=2)),
    ("check_foundation",
     "Verifica fondazione superficiale a plinto NTC §6.4.2 — capacità portante "
     "(Vesic), scorrimento, ribaltamento (EQU). Micropali in v1.1.",
     CheckFoundationInput,
     lambda a: json.dumps(check_foundation(CheckFoundationInput(**a)).model_dump(), indent=2)),
    ("check_capacity_pile",
     "Capacità portante assiale palo singolo EN 1997-1 §7 (metodo statico): "
     "R_b,k (punta) + R_s,k (laterale α/β-method) → R_c,k, R_c,d. Terreni argilla/sabbia "
     "stratificati con falda. Pali infissi/trivellati/CFA.",
     CheckCapacityPileInput,
     lambda a: json.dumps(check_capacity_pile(CheckCapacityPileInput(**a)).model_dump(), indent=2)),
    ("check_brinch_hansen",
     "Capacità portante generale fondazione superficiale Brinch-Hansen/Vesić (18 fattori "
     "completi: forma/profondità/inclinazione/pendenza terreno/inclinazione base). EN 1997-1 "
     "Annex D + NTC §6.4.2.1. Necessario per carichi inclinati (chiude Issue #002).",
     CheckBrinchHansenInput,
     lambda a: json.dumps(check_brinch_hansen(CheckBrinchHansenInput(**a)).model_dump(), indent=2)),
    ("check_pile_group",
     "Efficienza gruppo di pali (Converse-Labarre + Feld) → η, R_group = η·n·R_single. "
     "Reticolo m×n, interasse/diametro. EN 1997 §7.6.2.2.",
     CheckPileGroupInput,
     lambda a: json.dumps(check_pile_group(CheckPileGroupInput(**a)).model_dump(), indent=2)),
    ("check_micropali",
     "Verifica micropalo singolo e gruppo FHWA NHI-05-039 + UNI EN 14199: bond grout-terreno "
     "(α per tipo iniezione A/B/C/D) + resistenza armatura → R_single, R_group. "
     "Compressione/trazione.",
     CheckMicropaliInput,
     lambda a: json.dumps(check_micropali(CheckMicropaliInput(**a)).model_dump(), indent=2)),
    ("check_settlement",
     "Cedimenti palo singolo e gruppo, metodo elastico EN 1997-1 §7.4.2: accorciamento "
     "elastico + cedimento base (Boussinesq) → s_single, s_group (Poulos R_s), verifica SLE.",
     CheckSettlementInput,
     lambda a: json.dumps(check_settlement(CheckSettlementInput(**a)).model_dump(), indent=2)),
    ("get_committenza_spec",
     "Parametri prescrittivi LG committenza TLC (iliad / INWIT / Cellnex): "
     "limiti freccia, FC, γ_M, coefficienti vento, classi qualità. Da usare come "
     "default-override su tutte le verifiche.",
     GetCommittenzaSpecInput,
     lambda a: json.dumps(get_committenza_spec(GetCommittenzaSpecInput(**a)).model_dump(), indent=2)),
    ("lookup_ntc",
     "Ricerca testo NTC 2018 D.M. 17/01/2018. Restituisce paragrafi rilevanti per "
     "una query FTS5. Es. query='\"3.3.2\"' o paragrafo='3.3' per estrarre §3.3.x. "
     "Sorgente: 468 chunk indicizzati dal PDF ufficiale.",
     LookupNtcInput,
     lambda a: json.dumps(lookup_ntc(LookupNtcInput(**a)).model_dump(), indent=2)),
    ("get_antenna",
     "Recupero dati antenna TLC dal DB seed (Kathrein/CommScope/Huawei/ZTE/parabole/RRU). "
     "Restituisce A_ref, C_d, peso, bande. DB espandibile.",
     AntennaInput,
     lambda a: json.dumps(lookup_antenna(AntennaInput(**a)).model_dump(), indent=2)),
    ("get_profile",
     "Caratteristiche profilo strutturale: tubolare commerciale (CHS) / tubolare libero / "
     "poligonale TLC. Restituisce A, I, W_el, W_pl, i, peso, classe sezione.",
     GetProfileInput,
     lambda a: json.dumps(lookup_profile(GetProfileInput(**a)).model_dump(), indent=2)),
]


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(name=name, description=desc, inputSchema=schema.model_json_schema())
        for (name, desc, schema, _) in _TOOLS
    ]


_DISPATCH: dict[str, Any] = {name: fn for (name, _d, _s, fn) in _TOOLS}


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    if name not in _DISPATCH:
        raise ValueError(f"Tool sconosciuto: {name}")
    return [TextContent(type="text", text=_DISPATCH[name](arguments))]


def main() -> None:
    async def _run() -> None:
        async with stdio_server() as (r, w):
            await server.run(r, w, server.create_initialization_options())

    asyncio.run(_run())


if __name__ == "__main__":
    main()
