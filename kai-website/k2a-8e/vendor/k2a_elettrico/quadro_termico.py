"""Verifica termica quadri BT — IEC 60890 / CEI EN 61439-1 §10.10.4.2.

Metodo per CALCOLO della temperatura media all'interno dell'enclosure
per quadri BT fino a 1600 A nominali (oltre = prima approssimazione
con avvertenza, norma richiede verifica di tipo da costruttore).

Algoritmo (IEC 60890 ed.1987 + ammendamenti):
  Ae = Σ (A_faccia × b_faccia)     [superficie effettiva di scambio]
  k  = tabella IEC 60890 §4.3, interpolazione lineare su Ae
  d  = fattore distribuzione (semplificazione: 1.0/1.05/1.1 per 1/2/≥3 sezioni)
  x  = 0.804 (chiuso senza aperture, IP≥4X)
       0.715 (ventilazione forzata o aperture naturali, IP3X o inferiore)
  c  = 1.05 (IP≥4X chiuso) | 1.3 (IP3X aperture naturali) | 1.0 (vent. forzata)

  ΔT_meta_altezza = d × k(Ae) × P^x / Ae^x
  ΔT_sommita      = ΔT_meta × c
  T_interna_max   = T_amb + ΔT_sommita

Limiti CEI EN 61439-1 tab.6:
  sbarre nude: 65 K; morsetti dispositivi: 70 K; maniglie isolate: 25 K.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, Field

_PERDITE_DB = json.loads(
    (Path(__file__).parent / "data" / "perdite_apparecchi.json").read_text()
)


# -------- Input models --------

class DispositivoQuadro(BaseModel):
    sigla: str
    tipo: Literal["ACB", "MCCB", "MCB", "TA", "contattore", "sezionatore", "altro"]
    In_A: float = Field(..., gt=0)
    P_dissipata_W: float | None = Field(default=None, ge=0,
        description="Se None, lookup database via 'famiglia' o stima empirica per tipo.")
    famiglia: str | None = Field(default=None,
        description="Chiave database (es. 'ABB_Tmax_XT.MCCB_T3_250A').")
    quantita: int = Field(1, ge=1)


class SezioneQuadro(BaseModel):
    nome: str
    altezza_m: float = Field(..., gt=0)
    larghezza_m: float = Field(..., gt=0)
    profondita_m: float = Field(..., gt=0)
    dispositivi: list[DispositivoQuadro] = Field(default_factory=list)
    P_sbarre_W: float = Field(0.0, ge=0,
        description="Perdite Joule sbarre interne sezione (se calcolate a parte).")


class VerificaQuadroTermicoInput(BaseModel):
    sigla_quadro: str
    tipo_installazione: Literal[
        "interna_libera",
        "addossata_parete",
        "in_nicchia",
        "addossata_separata",
    ] = "interna_libera"
    IP: str = Field("31", description="Grado IP enclosure (es. '31', '41', '54', '65').")
    ventilazione: Literal["naturale", "forzata"] = "naturale"
    Tamb_C: float = Field(35.0, description="Ambiente di riferimento (CEI EN 61439-1).")
    sezioni: list[SezioneQuadro] = Field(..., min_length=1)
    limiti_DT: dict = Field(default_factory=lambda: {
        "sbarre_K": 65.0,
        "morsetti_K": 70.0,
        "maniglie_isolate_K": 25.0,
    })


# -------- Output models --------

class VerificaQuadroTermicoOutput(BaseModel):
    P_dissipata_totale_W: float
    P_dissipata_per_sezione_W: dict
    Ae_superficie_effettiva_m2: float
    k_enclosure: float
    d_distribuzione: float
    c_top_su_meta: float
    x_esponente_norma: float
    DT_meta_altezza_K: float
    DT_sommita_K: float
    temperatura_interna_max_C: float
    verifica_DT_sbarre: bool
    verifica_DT_morsetti: bool
    margini: dict
    conclusione_conforme: bool
    avvertenze: list[str]
    note_applicabilita: str
    norma_riferimento_internazionale: str
    norma_riferimento_locale: dict
    trace: dict


# -------- Helpers --------

# Tabella k IEC 60890 §4.3 — interpolazione lineare su Ae [m²]
_K_TABLE: list[tuple[float, float]] = [
    (1.25, 0.524), (1.5, 0.50), (2.0, 0.45), (3.0, 0.38),
    (4.0, 0.34),  (5.0, 0.32), (6.0, 0.30), (8.0, 0.28),
    (10.0, 0.27), (12.0, 0.26),
]


def _k_da_Ae(Ae: float) -> float:
    """Interpolazione lineare tabella IEC 60890 §4.3. Plateau ai bordi."""
    if Ae <= _K_TABLE[0][0]:
        return _K_TABLE[0][1]
    if Ae >= _K_TABLE[-1][0]:
        return _K_TABLE[-1][1]
    for i in range(len(_K_TABLE) - 1):
        ae0, k0 = _K_TABLE[i]
        ae1, k1 = _K_TABLE[i + 1]
        if ae0 <= Ae <= ae1:
            return k0 + (k1 - k0) * (Ae - ae0) / (ae1 - ae0)
    return _K_TABLE[-1][1]


def _x_esponente(ventilazione: str, IP: str) -> tuple[float, str]:
    """Esponente potenza specifica IEC 60890 (ritorna anche motivazione per trace).

    Regola IEC 60890 §4.4 (curva A vs curva B):
      x = 0.804  → enclosure CHIUSO senza aperture significative (IP≥4X).
                   La convezione interna è limitata, lo scambio termico è
                   prevalentemente conduttivo+irraggiamento sulle pareti.
      x = 0.715  → enclosure con APERTURE NATURALI (IP≤3X) o VENTILAZIONE FORZATA.
                   Lo scambio termico è dominato dal flusso d'aria attraverso
                   le aperture: la dipendenza da P è più debole (esponente minore).

    L'IP3X (3X = protetto contro corpi solidi ≥2.5mm, ma con aperture <2.5mm
    di norma presenti per ventilazione) viene considerato "con aperture
    naturali" → x=0.715 (curva B).
    """
    if ventilazione == "forzata":
        return 0.715, "ventilazione forzata → curva B IEC 60890 §4.4"
    try:
        primo_grado = int(IP.strip()[0]) if IP and IP.strip()[0].isdigit() else 4
    except (IndexError, ValueError):
        primo_grado = 4
    if primo_grado <= 3:
        return 0.715, (
            f"IP{IP} (primo grado={primo_grado}≤3) → aperture naturali, "
            f"curva B IEC 60890 §4.4 → x=0.715"
        )
    return 0.804, (
        f"IP{IP} (primo grado={primo_grado}≥4) → enclosure chiuso, "
        f"curva A IEC 60890 §4.4 → x=0.804"
    )


def _c_top_su_meta(ventilazione: str, IP: str) -> float:
    """Rapporto DT_sommità / DT_metà_altezza (stratificazione verticale)."""
    if ventilazione == "forzata":
        return 1.0   # miscelamento forzato → no stratificazione
    try:
        primo_grado = int(IP.strip()[0]) if IP and IP.strip()[0].isdigit() else 4
    except (IndexError, ValueError):
        primo_grado = 4
    if primo_grado <= 3:
        return 1.3   # aperture naturali → stratificazione marcata
    return 1.05      # chiuso → stratificazione contenuta


# Fattori b di esposizione facce (IEC 60890 §4.2 / Tab.1)
# NOTA FONTE: IEC 60890 ed.1987 + A1:1995, valori di norma:
#   - tetto orizzontale scoperto: b=1.4
#   - tutte pareti verticali libere (fronte, retro, laterali): b=0.9
#   - pareti addossate (no convezione esterna): b=0.5
#   - fondo: b=0 (norma esclude scambio dal fondo per ventilazione naturale)
# Il brief draft assegnava b=0.7 al fronte; ho uniformato a b=0.9 (valore di norma)
# perché 0.7 non è documentato nella tabella ufficiale.
_FATTORI_B = {
    "interna_libera": {
        "tetto": 1.4, "fronte": 0.9, "retro": 0.9,
        "laterale_sx": 0.9, "laterale_dx": 0.9, "fondo": 0.0,
    },
    "addossata_parete": {
        "tetto": 1.4, "fronte": 0.9, "retro": 0.5,
        "laterale_sx": 0.9, "laterale_dx": 0.9, "fondo": 0.0,
    },
    "in_nicchia": {
        "tetto": 1.4, "fronte": 0.9, "retro": 0.5,
        "laterale_sx": 0.5, "laterale_dx": 0.5, "fondo": 0.0,
    },
    "addossata_separata": {
        "tetto": 1.4, "fronte": 0.9, "retro": 0.5,
        "laterale_sx": 0.9, "laterale_dx": 0.5, "fondo": 0.0,
    },
}


def _calcola_Ae(sezioni: list[SezioneQuadro], tipo_installazione: str) -> float:
    """Ae totale = somma facce esposte × fattori b.

    Ipotesi: sezioni affiancate orizzontalmente, stessa altezza/profondità.
    Tetto e fondo: somma su L_totale. Fronte/retro: somma su L_totale × H.
    Laterali estremi: solo sx prima sezione + dx ultima sezione.
    """
    b = _FATTORI_B[tipo_installazione]
    if not sezioni:
        return 0.0
    H = sezioni[0].altezza_m
    L_tot = sum(s.larghezza_m for s in sezioni)
    P = sezioni[0].profondita_m
    Ae = 0.0
    Ae += (L_tot * P) * b["tetto"]
    Ae += (L_tot * P) * b["fondo"]
    Ae += (L_tot * H) * b["fronte"]
    Ae += (L_tot * H) * b["retro"]
    Ae += (P * H) * b["laterale_sx"]
    Ae += (P * H) * b["laterale_dx"]
    return Ae


def _stima_P_diss_empirica(tipo: str, In_A: float) -> tuple[float, str]:
    """Fallback se famiglia non in DB. Ritorna (W, nota)."""
    if tipo == "ACB":
        return 2 * In_A ** 2 * 1e-6 + 50, "stima empirica ACB"
    if tipo == "MCCB":
        return 1.5 * In_A ** 2 * 1e-6 + 25, "stima empirica MCCB"
    if tipo == "MCB":
        return 3 * In_A ** 2 * 1e-6 + 5, "stima empirica MCB"
    if tipo == "TA":
        return 2.0, "stima TA misura"
    if tipo == "contattore":
        return 5 + 0.1 * In_A, "stima contattore"
    return 5.0, f"stima generica tipo={tipo}"


def _lookup_perdite_database(famiglia: str) -> float | None:
    try:
        costruttore, modello = famiglia.split(".", 1)
        return float(_PERDITE_DB[costruttore][modello]["P_diss_W"])
    except (KeyError, ValueError):
        return None


def _fattore_d(n_sezioni: int) -> float:
    if n_sezioni <= 1: return 1.0
    if n_sezioni == 2: return 1.05
    return 1.10


# -------- Funzione principale --------

def verifica_quadro_61439_iec60890(
    inp: VerificaQuadroTermicoInput,
) -> VerificaQuadroTermicoOutput:
    avvertenze: list[str] = []

    # 1) Somma P_dissipata per sezione + totale
    P_per_sez: dict[str, float] = {}
    P_tot = 0.0
    In_max = 0.0
    for sez in inp.sezioni:
        P_sez = sez.P_sbarre_W
        for d in sez.dispositivi:
            if d.P_dissipata_W is not None:
                P = d.P_dissipata_W
            elif d.famiglia:
                lookup = _lookup_perdite_database(d.famiglia)
                if lookup is not None:
                    P = lookup
                else:
                    P, nota = _stima_P_diss_empirica(d.tipo, d.In_A)
                    avvertenze.append(
                        f"[{d.sigla}] famiglia '{d.famiglia}' non in DB: {nota}"
                    )
            else:
                P, nota = _stima_P_diss_empirica(d.tipo, d.In_A)
                avvertenze.append(f"[{d.sigla}] perdita stimata ({nota}), verificare datasheet.")
            P_sez += P * d.quantita
            In_max = max(In_max, d.In_A)
        P_per_sez[sez.nome] = round(P_sez, 2)
        P_tot += P_sez

    # 2) Superficie effettiva Ae
    Ae = _calcola_Ae(inp.sezioni, inp.tipo_installazione)

    # 3) Fattori
    k = _k_da_Ae(Ae)
    d_fac = _fattore_d(len(inp.sezioni))
    c = _c_top_su_meta(inp.ventilazione, inp.IP)
    x, x_motivazione = _x_esponente(inp.ventilazione, inp.IP)

    # 4) ΔT IEC 60890 §4.4: DT_meta = d × k × P^x / Ae^x
    if P_tot <= 0 or Ae <= 0:
        raise ValueError(f"P_totale={P_tot} W e Ae={Ae} m² devono essere positivi")
    DT_meta = d_fac * k * (P_tot ** x) / (Ae ** x)
    DT_top = DT_meta * c
    T_int_max = inp.Tamb_C + DT_top

    # 5) Verifica limiti CEI EN 61439-1 tab.6
    lim = inp.limiti_DT
    ok_sbarre = DT_top <= lim["sbarre_K"]
    ok_morsetti = DT_meta <= lim["morsetti_K"]
    margini = {
        "sbarre_K": round(lim["sbarre_K"] - DT_top, 2),
        "morsetti_K": round(lim["morsetti_K"] - DT_meta, 2),
        "maniglie_K": round(lim["maniglie_isolate_K"] - DT_top, 2),
    }
    conclusione = ok_sbarre and ok_morsetti

    # 6) Avvertenze applicabilità
    if In_max > 1600:
        note_appl = (
            "IEC 60890 metodo verifica per calcolo applicabile a quadri ≤1600A. "
            "Per assembly > 1600A serve verifica di tipo (prove sperimentali "
            "o calcolo dettagliato dal costruttore). Questo calcolo costituisce "
            "verifica di prima approssimazione."
        )
        avvertenze.append("In_max dispositivi > 1600A: applicabilità IEC 60890 limitata.")
    else:
        note_appl = "Applicabile IEC 60890 per assembly ≤1600A."

    if P_tot > 3000:
        avvertenze.append(
            "Potenza dissipata > 3 kW: considerare ventilazione forzata o "
            "prove sperimentali di tipo."
        )
    if inp.Tamb_C > 35:
        avvertenze.append(
            f"Tamb={inp.Tamb_C}°C > 35°C riferimento norma: applicare derating "
            "alle correnti nominali dei dispositivi."
        )

    return VerificaQuadroTermicoOutput(
        P_dissipata_totale_W=round(P_tot, 2),
        P_dissipata_per_sezione_W=P_per_sez,
        Ae_superficie_effettiva_m2=round(Ae, 3),
        k_enclosure=round(k, 4),
        d_distribuzione=d_fac,
        c_top_su_meta=c,
        x_esponente_norma=x,
        DT_meta_altezza_K=round(DT_meta, 2),
        DT_sommita_K=round(DT_top, 2),
        temperatura_interna_max_C=round(T_int_max, 2),
        verifica_DT_sbarre=ok_sbarre,
        verifica_DT_morsetti=ok_morsetti,
        margini=margini,
        conclusione_conforme=conclusione,
        avvertenze=avvertenze,
        note_applicabilita=note_appl,
        norma_riferimento_internazionale="IEC 60890:1987 + A1:1995 / IEC 61439-1:2020 §10.10.4.2",
        norma_riferimento_locale={
            "IT": "CEI EN 61439-1:2021 + Guida CEI 17-43",
            "DE": "DIN EN 61439-1:2020",
            "FR": "NF EN 61439-1:2020",
            "ES": "UNE-EN 61439-1:2021",
            "UK": "BS EN 61439-1:2020",
        },
        trace={
            "metodo": "IEC 60890 verifica per calcolo",
            "formula_DT_meta": f"d × k × P^x / Ae^x = {d_fac} × {k:.4f} × {P_tot:.1f}^{x} / {Ae:.2f}^{x}",
            "formula_DT_top": f"DT_meta × c = {DT_meta:.2f} × {c}",
            "scelta_x_motivazione": x_motivazione,
            "n_sezioni": len(inp.sezioni),
            "n_dispositivi": sum(len(s.dispositivi) for s in inp.sezioni),
        },
    )
