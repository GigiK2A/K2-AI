"""Parallelo di 2 trasformatori MT/BT — condizioni, corrente di circolazione, ripartizione carico.

Norme: CEI EN 60076-8 (guida applicativa trasformatori), IEC 60076-1.
Casi d'uso: cabine con 2 trafi in parallelo su sbarra BT comune (es. 2×1000 kVA).

Formule (per-unit su base comune S_base = Sn_a + Sn_b):
  In_i  = Sn_i·1000 / (√3·Vn_BT)                         [A]
  z_i   = (vcc_i/100)·(S_base/Sn_i)                       [pu, impedenza su base comune]
  Δe    = (dev_a − dev_b)/100                             [pu, scostamento rapporto trasformazione]
  i_c   = Δe / (z_a + z_b)                                [pu] → corrente di circolazione
  S_i   = S_carico·(1/z_i)/(1/z_a + 1/z_b)                [kVA] → ripartizione carico
  loading_i% = S_i / Sn_i · 100
  I_trafo_i ≈ I_load_i ± Ic  (circolazione si somma al trafo a EMF maggiore)
"""
from __future__ import annotations
import math
from typing import Literal
from pydantic import BaseModel, Field


class TrafoParallelo(BaseModel):
    Sn_kVA: float = Field(..., gt=0, description="Potenza nominale [kVA]")
    vcc_pct: float = Field(..., gt=0, le=100, description="Tensione di cortocircuito vcc [%]")
    gruppo: str = Field("Dyn11", description="Gruppo vettoriale (es. Dyn11) — deve coincidere tra i due trafi")
    dev_rapporto_pct: float = Field(0.0, description="Scostamento % del rapporto di trasformazione rispetto al nominale (es. ±0.5)")


class ParalleloTrafiInput(BaseModel):
    Vn_BT_V: float = Field(400.0, gt=0, description="Tensione nominale BT concatenata [V]")
    trafo_a: TrafoParallelo
    trafo_b: TrafoParallelo
    S_carico_kVA: float | None = Field(None, ge=0, description="Carico totale sulla sbarra [kVA] (opz., per ripartizione)")
    tol_rapporto_pct: float = Field(0.5, gt=0, description="Tolleranza ammessa sul disallineamento rapporto [%] (IEC 60076: 0.5)")
    tol_vcc_scarto_pct: float = Field(10.0, gt=0, description="Scarto vcc max ammesso [%] tra i due trafi")
    rapporto_Sn_max: float = Field(3.0, gt=1, description="Rapporto Sn massimo raccomandato (≤ 3:1)")


class CondizioneParallelo(BaseModel):
    nome: str
    esito: bool
    dettaglio: str


class ParalleloTrafiOutput(BaseModel):
    In_a_A: float
    In_b_A: float
    Ic_circolazione_A: float
    Ic_pct_In_a: float
    Ic_pct_In_b: float
    ripartizione: dict | None
    condizioni_parallelo: list[CondizioneParallelo]
    parallelo_ammesso: bool
    verifica_sovraccarico: dict | None
    trace: dict


def _in_nominale_A(Sn_kVA: float, Vn_BT_V: float) -> float:
    return Sn_kVA * 1000.0 / (math.sqrt(3) * Vn_BT_V)


def parallelo_trafi_circolazione(inp: ParalleloTrafiInput) -> ParalleloTrafiOutput:
    a, b = inp.trafo_a, inp.trafo_b
    Vn = inp.Vn_BT_V

    In_a = _in_nominale_A(a.Sn_kVA, Vn)
    In_b = _in_nominale_A(b.Sn_kVA, Vn)

    # Base comune per il per-unit
    S_base = a.Sn_kVA + b.Sn_kVA
    I_base = _in_nominale_A(S_base, Vn)
    z_a = (a.vcc_pct / 100.0) * (S_base / a.Sn_kVA)
    z_b = (b.vcc_pct / 100.0) * (S_base / b.Sn_kVA)

    # Corrente di circolazione da disallineamento rapporto
    delta_e = (a.dev_rapporto_pct - b.dev_rapporto_pct) / 100.0
    i_c_pu = abs(delta_e) / (z_a + z_b)
    Ic_A = i_c_pu * I_base

    # Ripartizione del carico (proporzionale a 1/z, cioè a Sn/vcc)
    ripartizione = None
    verifica_sovraccarico = None
    if inp.S_carico_kVA is not None and inp.S_carico_kVA > 0:
        inv_sum = (1.0 / z_a) + (1.0 / z_b)
        S_a = inp.S_carico_kVA * (1.0 / z_a) / inv_sum
        S_b = inp.S_carico_kVA * (1.0 / z_b) / inv_sum
        loading_a = S_a / a.Sn_kVA * 100.0
        loading_b = S_b / b.Sn_kVA * 100.0
        ripartizione = {
            "S_a_kVA": round(S_a, 2), "S_b_kVA": round(S_b, 2),
            "loading_a_pct": round(loading_a, 1), "loading_b_pct": round(loading_b, 1),
            "trafo_piu_caricato": "a" if loading_a >= loading_b else "b",
            "nota": "Carico ripartito proporzionalmente a Sn/vcc; il trafo con vcc minore si carica di più.",
        }
        # Corrente effettiva per trafo: quota di carico ± circolazione (somma conservativa)
        I_load_a = _in_nominale_A(S_a, Vn)
        I_load_b = _in_nominale_A(S_b, Vn)
        I_tot_a = I_load_a + Ic_A
        I_tot_b = I_load_b + Ic_A  # conservativo: applica Ic ad entrambi
        verifica_sovraccarico = {
            "I_trafo_a_A": round(I_tot_a, 1), "In_a_A": round(In_a, 1),
            "I_trafo_b_A": round(I_tot_b, 1), "In_b_A": round(In_b, 1),
            "sovraccarico_a": I_tot_a > In_a,
            "sovraccarico_b": I_tot_b > In_b,
            "nota": "I_trafo = quota carico (∝1/z) + Ic (somma conservativa). Verifica I_trafo ≤ In.",
        }

    # Condizioni di parallelo (CEI EN 60076-8)
    cond: list[CondizioneParallelo] = []
    # 1) gruppo vettoriale
    same_grp = a.gruppo.strip().lower() == b.gruppo.strip().lower()
    cond.append(CondizioneParallelo(
        nome="gruppo_vettoriale",
        esito=same_grp,
        dettaglio=f"{a.gruppo} vs {b.gruppo} — devono coincidere (obbligatorio)" if not same_grp
                  else f"{a.gruppo} = {b.gruppo} OK"))
    # 2) disallineamento rapporto
    drap = abs(a.dev_rapporto_pct - b.dev_rapporto_pct)
    cond.append(CondizioneParallelo(
        nome="rapporto_trasformazione",
        esito=drap <= inp.tol_rapporto_pct,
        dettaglio=f"Δrapporto={drap:.2f}% vs tol {inp.tol_rapporto_pct}% → Ic={Ic_A:.1f} A "
                  f"({Ic_A/In_a*100:.2f}% In_a)"))
    # 3) scarto vcc
    vcc_mean = (a.vcc_pct + b.vcc_pct) / 2.0
    scarto_vcc = abs(a.vcc_pct - b.vcc_pct) / vcc_mean * 100.0
    cond.append(CondizioneParallelo(
        nome="scarto_vcc",
        esito=scarto_vcc <= inp.tol_vcc_scarto_pct,
        dettaglio=f"vcc {a.vcc_pct}% / {b.vcc_pct}% → scarto {scarto_vcc:.1f}% vs tol {inp.tol_vcc_scarto_pct}%"))
    # 4) rapporto potenze
    rap_Sn = max(a.Sn_kVA, b.Sn_kVA) / min(a.Sn_kVA, b.Sn_kVA)
    cond.append(CondizioneParallelo(
        nome="rapporto_potenze",
        esito=rap_Sn <= inp.rapporto_Sn_max,
        dettaglio=f"Sn {a.Sn_kVA}/{b.Sn_kVA} kVA → rapporto {rap_Sn:.2f}:1 vs max {inp.rapporto_Sn_max}:1"))

    parallelo_ammesso = all(c.esito for c in cond)

    return ParalleloTrafiOutput(
        In_a_A=round(In_a, 1),
        In_b_A=round(In_b, 1),
        Ic_circolazione_A=round(Ic_A, 2),
        Ic_pct_In_a=round(Ic_A / In_a * 100.0, 3),
        Ic_pct_In_b=round(Ic_A / In_b * 100.0, 3),
        ripartizione=ripartizione,
        condizioni_parallelo=cond,
        parallelo_ammesso=parallelo_ammesso,
        verifica_sovraccarico=verifica_sovraccarico,
        trace={
            "norma": "CEI EN 60076-8 + IEC 60076-1 (trasformatori in parallelo)",
            "base_comune_kVA": S_base,
            "z_a_pu": round(z_a, 5), "z_b_pu": round(z_b, 5),
            "formula_Ic": "Ic = Δe / (z_a + z_b) [pu], Δe = (dev_a − dev_b)/100",
            "formula_ripartizione": "S_i = S_carico·(1/z_i)/Σ(1/z); loading_i = S_i/Sn_i",
            "ipotesi": "2 trafi, stessa sbarra BT; Ic sommata conservativamente al carico per verifica In.",
        },
    )
