"""MCP server entrypoint — k2a-quant.

Tools v0.2:
  Corporate finance & valuation
    - calc_wacc, calc_dcf, sensitivity_dcf
    - lookup_multiples, lookup_country, list_sectors
    - generate_dcf_excel
  Derivati & fixed income
    - black_scholes
    - bond_pricing
  Portfolio & risk
    - markowitz_optimize
    - calc_var
  Statistica
    - ols_regression
"""
from __future__ import annotations

import asyncio
import json
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .wacc import WaccInput, compute_wacc
from .dcf import DcfInput, SensitivityInput, compute_dcf, sensitivity_dcf
from .lookups import (
    LookupMultiplesInput, LookupCountryInput, ListSectorsInput,
    lookup_multiples, lookup_country, list_sectors,
)
from .excel_dcf import ExcelDcfInput, generate_dcf_excel
from .black_scholes import BlackScholesInput, compute_black_scholes
from .bond import BondInput, compute_bond
from .portfolio import MarkowitzInput, compute_markowitz
from .var_es import VarInput, compute_var
from .regression import OLSInput, compute_ols
from .factor import FactorInput, compute_factor
from .lbo import LBOInput, compute_lbo
from .binomial import BinomialInput, compute_binomial
from .yield_curve import BootstrapInput, SwapInput, bootstrap_curve, price_swap
from .time_series import ARIMAInput, GARCHInput, fit_arima, fit_garch11
from .npv_irr import NpvIrrInput, compute_npv_irr
from .hypothesis import (
    TTestInput, ChiSquareInput, AnovaInput,
    t_test, chi_square, anova_oneway,
)
from .logit import LogitInput, fit_logit
from .monte_carlo import MonteCarloInput, simulate
from .game_theory import NashInput, AuctionInput, solve_nash, optimal_bid

# --- AdvisorBoost-ready: tool da snapshot (patch quant) ---
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
from .capm import capm_cost_of_equity
from .ev_multiples import ev_from_multiples
from .valida_assunzioni import valida_assunzioni
from .dcf_guard import dcf_enterprise_value_guarded

# Snapshot caricato dal file dati (puro, nessuna rete a runtime).
_SNAP = json.loads((Path(__file__).parent / "data" / "industry_multiples.json").read_text())


class CapmInput(BaseModel):
    settore: str = Field(..., description="Chiave settore (vedi list_sectors / ateco_to_sector).")
    pfn_eur: float = Field(..., description="Posizione finanziaria netta (debito netto), EUR.")
    patrimonio_netto_eur: float = Field(..., description="Patrimonio netto, EUR (!= 0).")
    fatturato_eur: float = Field(..., description="Ricavi, EUR (per size premium).")
    paese: str = Field("italy", description="Paese per rf_10y/erp/tax_rate dallo snapshot.")
    tax_rate_pct: Optional[float] = Field(None, description="Override aliquota fiscale in %.")


class EvMultiplesInput(BaseModel):
    settore: str = Field(..., description="Chiave settore.")
    ebitda_eur: float = Field(..., description="EBITDA EUR. >0 → EV/EBITDA; <=0 → EV/Ricavi.")
    ricavi_eur: float = Field(..., description="Ricavi EUR (usati se EBITDA<=0).")


class ValidaAssunzioniInput(BaseModel):
    storici: dict = Field(..., description="Storici cliente: {ricavi_eur:[...], ebitda_eur:[...]}.")
    assunzioni: dict = Field(..., description="Assunzioni forward: fcf_previsti_eur, g_perpetuo_pct, costo_debito_pct, rettifiche_totale_eur.")
    settore: str = Field(..., description="Chiave settore (per g_range/banda).")
    patrimonio_netto_eur: Optional[float] = Field(None, description="PN per check rettifiche.")


class DcfGuardInput(BaseModel):
    dcf_input: dict = Field(..., description="Dict conforme a DcfInput (fcf, wacc, g_perpetual, terminal_method...).")
    settore: str = Field(..., description="Chiave settore (per g_range hard-reject).")


server: Server = Server("k2a-quant")


def _wrap(fn, model):
    return lambda a: json.dumps(
        fn(model(**a)).model_dump() if hasattr(fn(model(**a)), "model_dump") else fn(model(**a)),
        indent=2,
    )


_TOOLS = [
    # --- Corporate finance & valuation ---
    ("calc_wacc",
     "WACC con beta levered (Hamada) e Ke (CAPM).",
     WaccInput, lambda a: json.dumps(compute_wacc(WaccInput(**a)).model_dump(), indent=2)),
    ("calc_dcf",
     "DCF con terminal value Gordon o exit_multiple. Restituisce EV, Equity, PV breakdown.",
     DcfInput, lambda a: json.dumps(compute_dcf(DcfInput(**a)).model_dump(), indent=2)),
    ("sensitivity_dcf",
     "Sensitivity grid WACC × g su Equity Value.",
     SensitivityInput, lambda a: json.dumps(sensitivity_dcf(SensitivityInput(**a)), indent=2)),
    ("lookup_multiples",
     "Multipli settoriali (EV/EBITDA, EV/Sales, P/E, β unlevered).",
     LookupMultiplesInput, lambda a: json.dumps(lookup_multiples(LookupMultiplesInput(**a)), indent=2)),
    ("lookup_country",
     "Dati paese: risk-free 10Y, ERP, tax rate.",
     LookupCountryInput, lambda a: json.dumps(lookup_country(LookupCountryInput(**a)), indent=2)),
    ("list_sectors",
     "Elenca settori disponibili in lookup_multiples.",
     ListSectorsInput, lambda a: json.dumps(list_sectors(ListSectorsInput(**a)), indent=2)),
    ("generate_dcf_excel",
     "Genera modello DCF Excel vivo con formule.",
     ExcelDcfInput, lambda a: json.dumps(generate_dcf_excel(ExcelDcfInput(**a)), indent=2)),

    # --- AdvisorBoost: assunzioni dallo snapshot + envelope CalcResult + recinto ---
    ("capm_cost_of_equity",
     "Costo equity (CAPM + Hamada) con beta/rf/erp/size DALLO SNAPSHOT dato il settore. Ritorna envelope CalcResult.",
     CapmInput, lambda a: json.dumps(
         capm_cost_of_equity(**{**CapmInput(**a).model_dump(), "snapshot": _SNAP}), indent=2, ensure_ascii=False)),
    ("ev_from_multiples",
     "Enterprise Value dai multipli di settore: EBITDA>0 → EV/EBITDA, EBITDA<=0 → EV/Ricavi. Envelope CalcResult.",
     EvMultiplesInput, lambda a: json.dumps(
         ev_from_multiples(**{**EvMultiplesInput(**a).model_dump(), "snapshot": _SNAP}), indent=2, ensure_ascii=False)),
    ("valida_assunzioni",
     "Recinto deterministico OK/WARN/FAIL su assunzioni forward (CAGR FCF vs storico, traiettoria margini, g-in-range, costo debito, rettifiche).",
     ValidaAssunzioniInput, lambda a: json.dumps(
         valida_assunzioni(**{**ValidaAssunzioniInput(**a).model_dump(), "snapshot": _SNAP}), indent=2, ensure_ascii=False)),
    ("dcf_enterprise_value_guarded",
     "DCF con hard-reject se g fuori dal g_range di settore. Wrappa compute_dcf invariato. Envelope CalcResult.",
     DcfGuardInput, lambda a: json.dumps(
         dcf_enterprise_value_guarded(dcf_input=a["dcf_input"], settore=a["settore"], snapshot=_SNAP,
                                      compute_dcf=compute_dcf, DcfInput=DcfInput), indent=2, ensure_ascii=False)),

    # --- Derivati & fixed income ---
    ("black_scholes",
     "Pricing opzioni europee (call/put) + greeks (Δ, Γ, Vega, Θ, ρ) con dividend yield.",
     BlackScholesInput,
     lambda a: json.dumps(compute_black_scholes(BlackScholesInput(**a)).model_dump(), indent=2)),
    ("bond_pricing",
     "Bond pricing: YTM ↔ prezzo, Macaulay/Modified duration, convexity, DV01.",
     BondInput, lambda a: json.dumps(compute_bond(BondInput(**a)).model_dump(), indent=2)),

    # --- Portfolio & risk ---
    ("markowitz_optimize",
     "Ottimizzazione mean-variance: min-variance, tangency, frontiera efficiente.",
     MarkowitzInput, lambda a: json.dumps(compute_markowitz(MarkowitzInput(**a)).model_dump(), indent=2)),
    ("calc_var",
     "VaR ed Expected Shortfall: metodo parametric / historical / monte_carlo.",
     VarInput, lambda a: json.dumps(compute_var(VarInput(**a)).model_dump(), indent=2)),

    # --- Statistica ---
    ("ols_regression",
     "OLS regression con R², adj R², t-stat, p-value, IC 95%, F-test, VIF.",
     OLSInput, lambda a: json.dumps(compute_ols(OLSInput(**a)).model_dump(), indent=2)),
    ("factor_regression",
     "Fama-French 3 o 5 factor regression — alpha (Jensen), factor loadings, t-stat.",
     FactorInput, lambda a: json.dumps(compute_factor(FactorInput(**a)).model_dump(), indent=2)),

    # --- Private equity / M&A ---
    ("lbo_model",
     "LBO model: IRR sponsor, MOIC, debt paydown schedule con cash sweep.",
     LBOInput, lambda a: json.dumps(compute_lbo(LBOInput(**a)).model_dump(), indent=2)),

    # --- Derivati: opzioni americane ---
    ("binomial_tree",
     "Cox-Ross-Rubinstein binomial tree — opzioni europee/americane. Restituisce premium early-exercise.",
     BinomialInput, lambda a: json.dumps(compute_binomial(BinomialInput(**a)).model_dump(), indent=2)),

    # --- Fixed income avanzato ---
    ("bootstrap_yield_curve",
     "Bootstrap zero curve da par yields → spot rates, DF, forward 1Y.",
     BootstrapInput, lambda a: json.dumps(bootstrap_curve(BootstrapInput(**a)).model_dump(), indent=2)),
    ("swap_pricing",
     "Pricing IRS plain vanilla: NPV, par swap rate, PV gambe fissa/floating.",
     SwapInput, lambda a: json.dumps(price_swap(SwapInput(**a)).model_dump(), indent=2)),

    # --- Time series ---
    ("arima_forecast",
     "ARIMA(p,d,q) fit MLE Gaussiano + forecast con SE.",
     ARIMAInput, lambda a: json.dumps(fit_arima(ARIMAInput(**a)).model_dump(), indent=2)),
    ("garch_volatility",
     "GARCH(1,1) Gaussian — ω, α, β, persistence, long-run var, forecast volatility.",
     GARCHInput, lambda a: json.dumps(fit_garch11(GARCHInput(**a)).model_dump(), indent=2)),

    # --- Capital budgeting standalone ---
    ("calc_npv_irr",
     "NPV, IRR, MIRR, Payback, Discounted Payback, Profitability Index su serie di cash flows.",
     NpvIrrInput, lambda a: json.dumps(compute_npv_irr(NpvIrrInput(**a)).model_dump(), indent=2)),

    # --- Hypothesis testing ---
    ("t_test",
     "t-test: one_sample, two_sample (equal var), welch (unequal var), paired. Restituisce p-value, IC, Cohen's d.",
     TTestInput, lambda a: json.dumps(t_test(TTestInput(**a)).model_dump(), indent=2)),
    ("chi_square_test",
     "χ² test di indipendenza su tabella di contingenza con Cramer's V.",
     ChiSquareInput, lambda a: json.dumps(chi_square(ChiSquareInput(**a)).model_dump(), indent=2)),
    ("anova_oneway",
     "ANOVA one-way con eta-squared (effect size).",
     AnovaInput, lambda a: json.dumps(anova_oneway(AnovaInput(**a)).model_dump(), indent=2)),

    # --- Modelli scelta binaria ---
    ("logit_regression",
     "Logistic regression IRLS — coefficienti, odds ratio, z-stat, pseudo-R² McFadden, AIC.",
     LogitInput, lambda a: json.dumps(fit_logit(LogitInput(**a)).model_dump(), indent=2)),

    # --- Monte Carlo generico ---
    ("monte_carlo_simulate",
     "Simulazione Monte Carlo generica con variabili a distribuzione (normal/lognormal/uniform/triangular/beta/discrete) ed espressione.",
     MonteCarloInput, lambda a: json.dumps(simulate(MonteCarloInput(**a)).model_dump(), indent=2)),

    # --- Game theory & aste ---
    ("nash_equilibrium",
     "Equilibri di Nash in giochi 2 giocatori in forma normale: NE pure, miste (2x2 closed-form), strategie dominanti.",
     NashInput, lambda a: json.dumps(solve_nash(NashInput(**a)).model_dump(), indent=2)),
    ("auction_optimal_bid",
     "Bid ottimale ad asta: first_price, second_price/english, dutch — uniforme + risk-neutral.",
     AuctionInput, lambda a: json.dumps(optimal_bid(AuctionInput(**a)).model_dump(), indent=2)),
]


@server.list_tools()
async def _list() -> list[Tool]:
    return [
        Tool(name=name, description=desc, inputSchema=schema.model_json_schema())
        for name, desc, schema, _ in _TOOLS
    ]


@server.call_tool()
async def _call(name: str, args: dict[str, Any]) -> list[TextContent]:
    for n, _, _, fn in _TOOLS:
        if n == name:
            try:
                return [TextContent(type="text", text=fn(args))]
            except Exception as e:
                return [TextContent(type="text", text=json.dumps({"error": str(e), "tool": name}))]
    return [TextContent(type="text", text=json.dumps({"error": f"Tool '{name}' non trovato."}))]


async def _run() -> None:
    async with stdio_server() as (r, w):
        await server.run(r, w, server.create_initialization_options())


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
