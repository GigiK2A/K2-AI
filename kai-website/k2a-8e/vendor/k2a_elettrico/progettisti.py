"""Orchestratori decisionali (§5.3.1) — "agenti" che combinano più tool per produrre
output progettuali integrati (bozze), non un singolo calcolo.

Deterministici (nessun LLM): compongono i tool di calcolo (dimensiona_trafo,
calcola_icc_cabina) e i tool decisionali (§5.2.3) in un risultato unico coerente.
Sono BOZZE da validare dal progettista, non PE definitivi.

  - progettista_cabina     — bilancio → topologia + trafo + Icc + protezione generale
  - progettista_quadro     — lista partenze → protezioni selezionate + dati quadro
  - coordinatore_protezioni — catena → tarature + (opz.) selettività catena
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from .cabina_mt import (DimensionaTrafoInput, IccCabinaMTInput,
                        calcola_icc_cabina, dimensiona_trafo)
from .decisionali import (CoordinaProtezioniInput, DimensionaQuadroInput, LivelloCatena,
                         Partenza, ProgettaCabinaInput, SelezionaProtezioneInput,
                         coordina_protezioni_automatico, dimensiona_quadro_partenze,
                         progetta_cabina_topologia, seleziona_protezione_partenza)


# =========================================================================== #
# 1) progettista_cabina
# =========================================================================== #
class ProgettistaCabinaInput(BaseModel):
    P_carico_kW: float = Field(..., gt=0)
    cosphi: float = Field(0.9, gt=0, le=1)
    tensione_MT_kV: float = Field(15.0, gt=1)
    continuita: Literal["ordinaria", "alta", "critica"] = "ordinaria"
    ha_fotovoltaico: bool = False
    margine_futuro_pct: float = Field(20.0, ge=0, le=100)
    Pcc_rete_MT_MVA: float = Field(500.0, gt=0)


class ProgettistaCabinaOutput(BaseModel):
    topologia: dict
    trafo: dict
    icc_cabina: dict
    protezione_generale_suggerita: dict
    sintesi: list[str]
    norma_riferimento: str = "CEI 0-16 / CEI 99-2 / CEI EN 60076 / CEI 64-8"
    avvertenze: list[str] = Field(default_factory=list)


def progettista_cabina(inp: ProgettistaCabinaInput) -> ProgettistaCabinaOutput:
    # 1) topologia (decisionale)
    topo = progetta_cabina_topologia(ProgettaCabinaInput(
        P_carico_kW=inp.P_carico_kW, cosphi=inp.cosphi, continuita=inp.continuita,
        ha_fotovoltaico=inp.ha_fotovoltaico, margine_futuro_pct=inp.margine_futuro_pct)).model_dump()
    # 2) trafo (calcolo) sulla taglia per-trafo suggerita
    trafo = dimensiona_trafo(DimensionaTrafoInput(
        Pn_carico_kW=inp.P_carico_kW / max(1, topo["n_trasformatori"]), cosfi=inp.cosphi,
        margine_futuro_pc=inp.margine_futuro_pct)).model_dump()
    Sn = topo["Sn_per_trafo_kVA"]
    # 3) Icc cabina (calcolo) sulla taglia commerciale
    icc = calcola_icc_cabina(IccCabinaMTInput(
        Sn_trafo_kVA=Sn, Vn_MT=inp.tensione_MT_kV, Vn_BT=0.4,
        Pcc_rete_MT_MVA=inp.Pcc_rete_MT_MVA)).model_dump()
    # 4) protezione generale BT suggerita (decisionale) — In dal lato BT del trafo
    In_bt = Sn * 1000.0 / (3 ** 0.5 * 400.0)
    Icc_bt = icc.get("Ik3_BT_kA") or icc.get("Icc_BT_kA") or 20.0
    prot = seleziona_protezione_partenza(SelezionaProtezioneInput(
        Ib_A=In_bt, Iz_A=In_bt * 1.25, Icc_punto_kA=float(Icc_bt))).model_dump()

    sintesi = [
        f"Topologia: {topo['n_trasformatori']}×{Sn} kVA, ridondanza {topo['ridondanza']}"
        f"{' + GE/ATS' if topo['gruppo_elettrogeno'] else ''}.",
        f"Trafo: S richiesta {topo['S_richiesta_kVA']} kVA → commerciale {Sn} kVA.",
        f"Icc BT stimata {Icc_bt} kA; generale BT In≈{prot['In_A']} A, Icu {prot['Icu_kA']} kA.",
    ]
    avv = ["Bozza progettuale da validare: verificare cavi/selettività/terra con i tool dedicati."]
    return ProgettistaCabinaOutput(
        topologia=topo, trafo=trafo, icc_cabina=icc,
        protezione_generale_suggerita=prot, sintesi=sintesi, avvertenze=avv)


# =========================================================================== #
# 2) progettista_quadro
# =========================================================================== #
class PartenzaBrief(BaseModel):
    nome: str = "partenza"
    Ib_A: float = Field(..., gt=0)
    Iz_A: float = Field(..., gt=0)
    Icc_punto_kA: float = Field(10.0, gt=0)
    tipo_carico: Literal["generico", "motore", "illuminazione", "prese", "fv", "ev"] = "generico"


class ProgettistaQuadroInput(BaseModel):
    partenze: list[PartenzaBrief] = Field(..., min_length=1)
    contemporaneita: float = Field(0.8, gt=0, le=1)
    ambiente: Literal["interno", "esterno"] = "interno"


class ProgettistaQuadroOutput(BaseModel):
    tabella_partenze: list[dict]
    quadro: dict
    sintesi: list[str]
    norma_riferimento: str = "CEI 64-8 + CEI EN 61439-1/2"
    avvertenze: list[str] = Field(default_factory=list)


def progettista_quadro(inp: ProgettistaQuadroInput) -> ProgettistaQuadroOutput:
    tabella: list[dict] = []
    partenze_quadro: list[Partenza] = []
    for p in inp.partenze:
        sel = seleziona_protezione_partenza(SelezionaProtezioneInput(
            Ib_A=p.Ib_A, Iz_A=p.Iz_A, Icc_punto_kA=p.Icc_punto_kA, tipo_carico=p.tipo_carico))
        poli_n = {"1P": 1, "1P+N": 2, "3P": 3, "3P+N": 4, "4P": 4}.get(sel.poli, 4)
        tabella.append({"nome": p.nome, "Ib_A": p.Ib_A, "In_A": sel.In_A, "curva": sel.curva,
                        "Icu_kA": sel.Icu_kA, "diff": sel.differenziale_tipo,
                        "Idn_mA": sel.Idn_mA, "poli": sel.poli})
        partenze_quadro.append(Partenza(nome=p.nome, In_A=sel.In_A, poli=poli_n))

    quadro = dimensiona_quadro_partenze(DimensionaQuadroInput(
        partenze=partenze_quadro, contemporaneita=inp.contemporaneita,
        ambiente=inp.ambiente)).model_dump()

    sintesi = [
        f"{len(tabella)} partenze dimensionate; generale In {quadro['interruttore_generale_In_A']} A, "
        f"sbarra {quadro['In_sbarra_A']} A.",
        f"{quadro['forma_segregazione']}; {quadro['n_moduli_stimati']} moduli su "
        f"{quadro['n_file_stimate']} file; {quadro['IP_minimo']}.",
    ]
    avv = ["Bozza quadro da validare: verificare I²t e selettività con i tool dedicati."]
    return ProgettistaQuadroOutput(
        tabella_partenze=tabella, quadro=quadro, sintesi=sintesi, avvertenze=avv)


# =========================================================================== #
# 3) coordinatore_protezioni
# =========================================================================== #
class CoordinatoreProtezioniInput(BaseModel):
    catena: list[LivelloCatena] = Field(..., min_length=2)
    delta_t_s: float = Field(0.3, gt=0)
    usa_zsi: bool = False


class CoordinatoreProtezioniOutput(BaseModel):
    piano_tarature: list[dict]
    selettivita_amperometrica_ok: bool
    sintesi: list[str]
    norma_riferimento: str = "CEI 64-8 §536 / CEI 0-16 §8.5"
    avvertenze: list[str] = Field(default_factory=list)


def coordinatore_protezioni(inp: CoordinatoreProtezioniInput) -> CoordinatoreProtezioniOutput:
    out = coordina_protezioni_automatico(CoordinaProtezioniInput(
        catena=inp.catena, delta_t_s=inp.delta_t_s, usa_zsi=inp.usa_zsi))
    sintesi = [
        f"Catena di {len(inp.catena)} livelli; "
        f"selettività amperometrica {'OK' if out.selettivita_amperometrica_ok else 'A RISCHIO'}.",
        f"Tempi: {' → '.join(f'{t['livello']} {t['t_intervento_s']}s' for t in out.tarature)}.",
    ]
    return CoordinatoreProtezioniOutput(
        piano_tarature=out.tarature, selettivita_amperometrica_ok=out.selettivita_amperometrica_ok,
        sintesi=sintesi, avvertenze=out.avvertenze)
