"""Verifica selettività catena protezioni MT-BT — CEI 0-16:2022 §8.5 + CEI 64-8 §536.

Analizza una catena ORDINATA di livelli di protezione (dall'upstream più alto al
downstream più basso) e verifica per ogni coppia adiacente:
  - selettività cronometrica: Δt = t_upstream - t_downstream ≥ Δt_richiesto
    Δt_richiesto standard = 200 ms (CEI 0-16 default)
    Δt_richiesto con ZSI su entrambi i livelli = 50 ms (selettività logica)
  - selettività amperometrica (opzionale): Ir_upstream ≥ k_safety × Ir_downstream
    con k_safety = 1.6 (CEI 0-16 §8.5.2)
"""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field


class LivelloProtezione(BaseModel):
    nome: str
    tipo: Literal["DSO", "MT_protezione", "ACB_BT", "MCCB_BT", "MCB_BT"]
    In_A: float | None = Field(default=None, ge=0,
        description="Corrente nominale (None per DSO).")
    Ir_pickup_A: float | None = Field(default=None, ge=0,
        description="Pickup magnetico ridotto (LSIG/LSI). Se None, "
                    "selettività amperometrica non valutata per la coppia.")
    t_intervento_s: float = Field(..., ge=0,
        description="Tempo di intervento atteso alla Icc del livello downstream.")
    Icu_kA: float | None = Field(default=None, ge=0)
    ZSI_attivo: bool = False
    note: str | None = None


class VerificaSelettivitaCatenaInput(BaseModel):
    catena: list[LivelloProtezione] = Field(..., min_length=2,
        description="Lista ORDINATA dall'upstream (più alto) al downstream.")
    Icc_max_BT_kA: float = Field(..., gt=0,
        description="Icc prospettica al livello BT (per documentazione/trace).")
    delta_t_minimo_s: float = Field(0.2, gt=0,
        description="Margine cronometrico standard tra livelli (CEI 0-16 §8.5.2).")
    delta_t_ZSI_s: float = Field(0.05, gt=0,
        description="Margine ridotto con ZSI attivo su entrambi i livelli.")
    k_safety_amperometrica: float = Field(1.6, gt=1,
        description="Rapporto minimo Ir_up/Ir_down per selettività amperometrica.")


class CoppiaSelettivita(BaseModel):
    upstream: str
    downstream: str
    selettiva_cronometrica: bool
    delta_t_calcolato_s: float
    delta_t_richiesto_s: float
    selettiva_amperometrica: bool | None
    rapporto_Ir_up_down: float | None
    note: list[str]


class VerificaSelettivitaCatenaOutput(BaseModel):
    coppie_analizzate: list[CoppiaSelettivita]
    n_coppie_selettive: int
    n_coppie_non_selettive: int
    catena_completamente_selettiva: bool
    raccomandazioni: list[str]
    norma_riferimento_internazionale: str
    norma_riferimento_locale: dict
    trace: dict


def verifica_selettivita_catena(
    inp: VerificaSelettivitaCatenaInput,
) -> VerificaSelettivitaCatenaOutput:
    coppie: list[CoppiaSelettivita] = []
    raccomandazioni: list[str] = []

    for i in range(len(inp.catena) - 1):
        up = inp.catena[i]
        dn = inp.catena[i + 1]
        note: list[str] = []

        # A) Cronometrica
        zsi_logico = up.ZSI_attivo and dn.ZSI_attivo
        dt_richiesto = inp.delta_t_ZSI_s if zsi_logico else inp.delta_t_minimo_s
        dt_calc = up.t_intervento_s - dn.t_intervento_s
        cron_ok = dt_calc >= dt_richiesto
        if zsi_logico:
            note.append(
                f"ZSI attivo su entrambi: selettività logica garantita, "
                f"Δt richiesto ridotto a {dt_richiesto*1000:.0f} ms."
            )
        if not cron_ok:
            shortage = dt_richiesto - dt_calc
            raccomandazioni.append(
                f"[{up.nome} → {dn.nome}] aumentare t_intervento di {up.nome} "
                f"di almeno {shortage*1000:.0f} ms (attuale Δt={dt_calc*1000:.0f} ms, "
                f"richiesto {dt_richiesto*1000:.0f} ms)."
            )

        # B) Amperometrica
        amp_ok: bool | None = None
        rapporto: float | None = None
        if up.Ir_pickup_A is not None and dn.Ir_pickup_A is not None and dn.Ir_pickup_A > 0:
            rapporto = up.Ir_pickup_A / dn.Ir_pickup_A
            amp_ok = rapporto >= inp.k_safety_amperometrica
            if not amp_ok:
                raccomandazioni.append(
                    f"[{up.nome} → {dn.nome}] selettività amperometrica KO: "
                    f"Ir_up/Ir_down={rapporto:.2f} < {inp.k_safety_amperometrica} "
                    f"richiesto. Aumentare pickup magnetico {up.nome} o "
                    f"abbassare {dn.nome}."
                )
            else:
                note.append(
                    f"Ir_up/Ir_down={rapporto:.2f} >= {inp.k_safety_amperometrica} → "
                    f"selettività amperometrica OK."
                )
        else:
            note.append(
                "Ir_pickup non disponibile su uno o entrambi i livelli: "
                "selettività amperometrica non valutata."
            )

        coppie.append(CoppiaSelettivita(
            upstream=up.nome, downstream=dn.nome,
            selettiva_cronometrica=cron_ok,
            delta_t_calcolato_s=round(dt_calc, 4),
            delta_t_richiesto_s=round(dt_richiesto, 4),
            selettiva_amperometrica=amp_ok,
            rapporto_Ir_up_down=round(rapporto, 3) if rapporto is not None else None,
            note=note,
        ))

    # Conteggio: una coppia è "selettiva" se cron OK E (amp OK o non valutata)
    n_sel = sum(
        1 for c in coppie
        if c.selettiva_cronometrica and (c.selettiva_amperometrica is not False)
    )
    n_non = len(coppie) - n_sel
    completa = n_non == 0

    if completa:
        raccomandazioni.insert(0,
            f"Catena completamente selettiva: tutte le {len(coppie)} coppie "
            f"verificate conformi a CEI 0-16:2022 §8.5 + CEI 64-8 §536."
        )

    return VerificaSelettivitaCatenaOutput(
        coppie_analizzate=coppie,
        n_coppie_selettive=n_sel,
        n_coppie_non_selettive=n_non,
        catena_completamente_selettiva=completa,
        raccomandazioni=raccomandazioni,
        norma_riferimento_internazionale="IEC 60364-5-53 + IEC 60947-2 (coordinamento)",
        norma_riferimento_locale={
            "IT": "CEI 0-16:2022 §8.5 (utenti MT) + CEI 64-8:2021 §536 (coordinamento BT)",
            "DE": "VDE-AR-N 4110 / DIN VDE 0100-536",
            "FR": "UTE C 13-100 / NF C 15-100 §536",
            "ES": "RAT MT-AT / REBT ITC-BT-22",
            "UK": "ENA G99 (DNO) + BS 7671 §536",
        },
        trace={
            "metodo": "selettività cronometrica + amperometrica per coppie adiacenti",
            "n_livelli_catena": len(inp.catena),
            "Icc_BT_kA": inp.Icc_max_BT_kA,
            "delta_t_standard_ms": int(inp.delta_t_minimo_s * 1000),
            "delta_t_ZSI_ms": int(inp.delta_t_ZSI_s * 1000),
            "k_safety_amperometrica": inp.k_safety_amperometrica,
        },
    )
