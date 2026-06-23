"""Tool DECISIONALI (non solo calcolo) — §5.2.3 master plan.

Supporto alle scelte progettuali (suggeriscono, non solo calcolano), deterministici e
grounded su norme CEI. 4 tool:
  - seleziona_protezione_partenza  — In/curva/Icu/differenziale da Ib+Icc+carico (CEI 64-8)
  - dimensiona_quadro_partenze     — forma/sbarra/moduli da lista partenze (CEI EN 61439)
  - progetta_cabina_topologia      — n.trafi/ridondanza/ATS da bilancio (CEI 0-16/99-2)
  - coordina_protezioni_automatico — tarature tempi per selettività catena (CEI 64-8 §536)

Sono suggerimenti ingegneristici (da validare dal progettista), NON sostituiscono la
verifica puntuale dei tool di calcolo.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# Correnti nominali standard IEC 60898 / 60947-2 (A).
_IN_STD = [6, 10, 13, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160, 200,
           250, 320, 400, 500, 630, 800, 1000, 1250, 1600, 2000, 2500, 3200, 4000]
# Poteri di interruzione commerciali Icu (kA).
_ICU_STD = [4.5, 6, 10, 15, 25, 36, 50, 65, 70, 85, 100]


def _next_ge(val: float, serie: list) -> float:
    for s in serie:
        if s >= val:
            return float(s)
    return float(serie[-1])


# =========================================================================== #
# 1) seleziona_protezione_partenza
# =========================================================================== #
class SelezionaProtezioneInput(BaseModel):
    Ib_A: float = Field(..., gt=0, description="Corrente di impiego del circuito")
    Iz_A: float = Field(..., gt=0, description="Portata della conduttura")
    Icc_punto_kA: float = Field(..., gt=0, description="Icc presunta nel punto di installazione")
    tipo_carico: Literal["generico", "motore", "illuminazione", "prese", "fv", "ev"] = "generico"
    ambiente: Literal["ordinario", "bagno_doccia", "cantiere", "medico", "agricolo"] = "ordinario"
    selettivita_a_valle: bool = Field(False, description="C'è selettività da garantire verso valle")


class SelezionaProtezioneOutput(BaseModel):
    In_A: float
    curva: Literal["B", "C", "D"]
    Icu_kA: float
    differenziale_tipo: Literal["nessuno", "AC", "A", "F", "B"]
    Idn_mA: int | None
    poli: Literal["1P", "1P+N", "3P", "3P+N", "4P"]
    motivazioni: list[str]
    norma_riferimento: str = "CEI 64-8 art.433/434, 415.1 (differenziali); IEC 60898/60947-2"
    avvertenze: list[str] = Field(default_factory=list)


def seleziona_protezione_partenza(inp: SelezionaProtezioneInput) -> SelezionaProtezioneOutput:
    mot: list[str] = []
    avv: list[str] = []
    # In: primo standard con Ib ≤ In ≤ Iz (CEI 64-8 433.1).
    candidati = [s for s in _IN_STD if inp.Ib_A <= s <= inp.Iz_A]
    In = float(candidati[0]) if candidati else _next_ge(inp.Ib_A, _IN_STD)
    if not candidati:
        avv.append(f"Nessun In standard tra Ib={inp.Ib_A} e Iz={inp.Iz_A}: verificare la sezione.")
    mot.append(f"In={In} A: primo standard ≥ Ib e ≤ Iz (CEI 64-8 433.1).")

    # Curva: D per motori (spunto), C generico, B per carichi resistivi/lunghi.
    if inp.tipo_carico == "motore":
        curva = "D"; mot.append("Curva D: spunto motore (5–10× In non deve far scattare).")
    elif inp.tipo_carico in ("illuminazione", "prese"):
        curva = "C"; mot.append("Curva C: uso generale civile/terziario.")
    else:
        curva = "C"
        mot.append("Curva C: default uso generale.")

    # Icu ≥ Icc presunta.
    Icu = _next_ge(inp.Icc_punto_kA, _ICU_STD)
    mot.append(f"Icu={Icu} kA ≥ Icc presunta {inp.Icc_punto_kA} kA (CEI 64-8 434).")

    # Differenziale per ambiente/carico.
    dif: str = "nessuno"; idn: int | None = None
    if inp.ambiente in ("bagno_doccia", "cantiere", "agricolo") or inp.tipo_carico in ("prese", "ev"):
        dif, idn = "A", 30
        mot.append("Differenziale tipo A 30 mA: protezione addizionale (CEI 64-8 415.1).")
    if inp.ambiente == "medico":
        dif, idn = "A", 30; avv.append("Locali medici: valutare IT-M e differenziali dedicati (sez.710).")
    if inp.tipo_carico == "fv" or inp.tipo_carico == "ev":
        dif = "B"; idn = 30
        mot.append("Differenziale tipo B: correnti di guasto continue (FV/EV, CEI 64-8 722/712).")

    # Poli.
    if inp.tipo_carico in ("illuminazione", "prese") and inp.ambiente != "cantiere":
        poli = "1P+N"
    else:
        poli = "4P" if dif != "nessuno" else "3P+N"

    return SelezionaProtezioneOutput(
        In_A=In, curva=curva, Icu_kA=Icu, differenziale_tipo=dif, Idn_mA=idn,
        poli=poli, motivazioni=mot, avvertenze=avv)


# =========================================================================== #
# 2) dimensiona_quadro_partenze
# =========================================================================== #
class Partenza(BaseModel):
    nome: str = "partenza"
    In_A: float = Field(..., gt=0)
    poli: int = Field(4, ge=1, le=4)


class DimensionaQuadroInput(BaseModel):
    partenze: list[Partenza] = Field(..., min_length=1)
    contemporaneita: float = Field(0.8, gt=0, le=1)
    forma_richiesta: Literal["auto", "1", "2b", "3b", "4b"] = "auto"
    ambiente: Literal["interno", "esterno"] = "interno"


class DimensionaQuadroOutput(BaseModel):
    In_sbarra_A: float
    forma_segregazione: str
    n_moduli_stimati: int
    n_file_stimate: int
    IP_minimo: str
    interruttore_generale_In_A: float
    motivazioni: list[str]
    norma_riferimento: str = "CEI EN 61439-1/2 (forme, sbarre); CEI 64-8"


def dimensiona_quadro_partenze(inp: DimensionaQuadroInput) -> DimensionaQuadroOutput:
    mot: list[str] = []
    somma = sum(p.In_A for p in inp.partenze)
    carico_contemp = somma * inp.contemporaneita
    In_gen = _next_ge(carico_contemp, _IN_STD)
    In_sbarra = _next_ge(In_gen * 1.0, _IN_STD)
    mot.append(f"Σ In partenze={somma:.0f} A · k_cont={inp.contemporaneita} → "
               f"carico {carico_contemp:.0f} A; generale In={In_gen} A; sbarra {In_sbarra} A.")

    # Forma: più partenze/potenza → forma più alta.
    if inp.forma_richiesta != "auto":
        forma = f"Forma {inp.forma_richiesta}"
    elif In_sbarra >= 630 or len(inp.partenze) >= 12:
        forma = "Forma 3b (sbarre segregate + unità separate)"
    elif len(inp.partenze) >= 6:
        forma = "Forma 2b (sbarre segregate)"
    else:
        forma = "Forma 1 (nessuna segregazione)"
    mot.append(f"{forma}: scelta da n.partenze={len(inp.partenze)} e In sbarra (CEI EN 61439).")

    # Moduli: ~ 2 moduli per polo + margine 30%.
    moduli = sum(p.poli * 2 for p in inp.partenze) + 4  # +generale
    moduli = int(moduli * 1.3)
    file = max(1, -(-moduli // 24))  # ceil su 24 moduli/fila DIN
    IP = "IP55" if inp.ambiente == "esterno" else "IP30/IP40"
    mot.append(f"{moduli} moduli DIN stimati (+30% margine) su {file} file; {IP}.")

    return DimensionaQuadroOutput(
        In_sbarra_A=In_sbarra, forma_segregazione=forma, n_moduli_stimati=moduli,
        n_file_stimate=file, IP_minimo=IP, interruttore_generale_In_A=In_gen, motivazioni=mot)


# =========================================================================== #
# 3) progetta_cabina_topologia
# =========================================================================== #
class ProgettaCabinaInput(BaseModel):
    P_carico_kW: float = Field(..., gt=0)
    cosphi: float = Field(0.9, gt=0, le=1)
    continuita: Literal["ordinaria", "alta", "critica"] = "ordinaria"
    ha_fotovoltaico: bool = False
    margine_futuro_pct: float = Field(20.0, ge=0, le=100)


class ProgettaCabinaOutput(BaseModel):
    S_richiesta_kVA: float
    n_trasformatori: int
    Sn_per_trafo_kVA: float
    ridondanza: Literal["N", "N+1", "2N"]
    gruppo_elettrogeno: bool
    ats: bool
    note_topologia: list[str]
    norma_riferimento: str = "CEI 0-16 / CEI 99-2 (cabine); CEI EN 60076 (trafi)"


def progetta_cabina_topologia(inp: ProgettaCabinaInput) -> ProgettaCabinaOutput:
    note: list[str] = []
    S = inp.P_carico_kW / inp.cosphi * (1 + inp.margine_futuro_pct / 100)
    note.append(f"S richiesta {S:.0f} kVA (P/cosφ + margine {inp.margine_futuro_pct:.0f}%).")

    serie = [160, 250, 400, 630, 800, 1000, 1250, 1600, 2000, 2500]
    if inp.continuita == "critica":
        ridond = "2N"; n = 2; sn = _next_ge(S, serie)
        note.append("Continuità critica → ridondanza 2N (2 trafi 100% ciascuno).")
    elif inp.continuita == "alta":
        ridond = "N+1"; n = 2; sn = _next_ge(S / 2 * 1.5, serie)
        note.append("Continuità alta → N+1 (2 trafi, ciascuno copre ~75% con margine).")
    else:
        ridond = "N"; sn = _next_ge(S, serie); n = 1
        if sn > 1600:
            n = 2; sn = _next_ge(S / 2, serie)
            note.append("S elevata → 2 trafi in parallelo per taglie commerciali gestibili.")
        else:
            note.append("Continuità ordinaria → trafo singolo.")

    ge = inp.continuita in ("alta", "critica")
    ats = ge
    if ge:
        note.append("Gruppo elettrogeno + ATS per i carichi essenziali (CEI 64-8 §551).")
    if inp.ha_fotovoltaico:
        note.append("FV presente: prevedere SPI/SPG e coordinamento (CEI 0-16/0-21).")

    return ProgettaCabinaOutput(
        S_richiesta_kVA=round(S, 1), n_trasformatori=n, Sn_per_trafo_kVA=sn,
        ridondanza=ridond, gruppo_elettrogeno=ge, ats=ats, note_topologia=note)


# =========================================================================== #
# 4) coordina_protezioni_automatico
# =========================================================================== #
class LivelloCatena(BaseModel):
    nome: str
    In_A: float = Field(..., gt=0)
    ruolo: Literal["DSO", "MT", "generale_BT", "distribuzione", "terminale"] = "distribuzione"


class CoordinaProtezioniInput(BaseModel):
    catena: list[LivelloCatena] = Field(..., min_length=2,
                                        description="Dal più a monte (DSO) al più a valle")
    delta_t_s: float = Field(0.3, gt=0, description="Gradino cronometrico tra livelli")
    usa_zsi: bool = Field(False, description="Selettività di zona ZSI (Δt ridotto)")


class CoordinaProtezioniOutput(BaseModel):
    tarature: list[dict]
    selettivita_amperometrica_ok: bool
    note: list[str]
    norma_riferimento: str = "CEI 64-8 §536 (selettività); CEI 0-16 §8.5 (catena MT-BT)"
    avvertenze: list[str] = Field(default_factory=list)


def coordina_protezioni_automatico(inp: CoordinaProtezioniInput) -> CoordinaProtezioniOutput:
    note: list[str] = []
    avv: list[str] = []
    dt = 0.05 if inp.usa_zsi else inp.delta_t_s
    if inp.usa_zsi:
        note.append("ZSI attiva: Δt ridotto a 50 ms tra livelli (selettività di zona).")
    else:
        note.append(f"Selettività cronometrica: Δt={dt} s tra livelli successivi.")

    n = len(inp.catena)
    tarature = []
    # Il livello più a valle ha t minimo; salendo verso il DSO il tempo cresce di Δt.
    for i, liv in enumerate(inp.catena):
        t = round(0.05 + dt * (n - 1 - i), 3)  # valle→monte crescente
        tarature.append({"livello": liv.nome, "ruolo": liv.ruolo, "In_A": liv.In_A,
                          "t_intervento_s": t})

    # Selettività amperometrica: In deve decrescere verso valle (monte > valle).
    ampe_ok = True
    for monte, valle in zip(inp.catena, inp.catena[1:]):
        if monte.In_A <= valle.In_A:
            ampe_ok = False
            avv.append(f"Selettività amperometrica a rischio: {monte.nome} In={monte.In_A} "
                       f"≤ {valle.nome} In={valle.In_A} (atteso monte > valle).")
    note.append("Selettività amperometrica: In decrescente da monte a valle "
                "(rapporto ≥1,6 raccomandato).")

    return CoordinaProtezioniOutput(
        tarature=tarature, selettivita_amperometrica_ok=ampe_ok, note=note, avvertenze=avv)
