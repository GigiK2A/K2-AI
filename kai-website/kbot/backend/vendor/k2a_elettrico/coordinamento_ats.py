"""Coordinamento ATS multi-sorgente (rete pubblica + GE diesel + FV).

Verifica il coordinamento temporale tra ATS (Automatic Transfer Switch) e
protezioni di interfaccia SPI/SPG per sistemi multi-sorgente in BT/MT.

Tier 1 (questo modulo) — tre sequenze:
  A) mancanza rete pubblica  -> commutazione ATS verso GE
  B) cortocircuito rete      -> SPI/SPG disconnette FV prima dello switch
  C) riconnessione rete      -> sequenza ordinata rete->ATS->GE off->FV on

Tier 2 (NON coperto): gestione BESS dinamica, black-start GE, microgrid
avanzato, power quality (armoniche, sag/swell).

Norme:
  - CEI 0-21:2024 (connessione FV BT, SPI/SPG, riconnessione)
  - CEI 0-16:2024 (connessione MT, P > 200 kW) — solo riferimento
  - CEI 64-8 sez. 551 (alimentazioni alternative / di sicurezza)
  - IEC 60364-5-56 (alimentazioni di sicurezza, riferimento internazionale)

Pattern architetturale: default conservativi (worst-case plausibile, ADR-004)
con override esplicito dell'utente. I default rappresentano il caso peggiore
realistico per non sovrastimare la prontezza del sistema.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# ====================================================================
# COSTANTI NORMATIVE (worst-case plausibile / soglie CEI)
# ====================================================================

# CEI 64-8 §551: tempo massimo per alimentazione carichi di sicurezza/essenziali.
# La norma distingue varie classi (0, <0.5s, <5s, <15s, >15s); per "servizi
# essenziali" con commutazione automatica si adotta 15s come soglia di classe.
# Il brief target indica 30s come limite superiore di accettabilità operativa.
T_MAX_ALIMENTAZIONE_PRIVILEGIATI_S = 30.0

# CEI 0-21 §8.6 (e §8.5): ritardo minimo di riconnessione dopo ripristino rete.
T_RICONNESSIONE_MIN_S = 180.0

# CEI 0-21: la riconnessione del FV avviene dopo un intervallo di rete stabile.
# Valore di osservazione tipico prima del rientro del generatore (s).
T_FV_RICONNESSIONE_DOPO_RETE_STABILE_S = 30.0

# CEI 0-21 §8.5: tempi massimi di intervento SPI ammessi (soglie di norma).
SPI_T_MAX_SOVRATENSIONE_MS = 100.0   # 59.S1/59.S2 (sovratensione) — rapido
SPI_T_MAX_SOTTOTENSIONE_MS = 200.0   # 27.S1 (sottotensione)
SPI_T_MAX_FREQUENZA_MS = 100.0       # 81>.S1 / 81<.S1 (fuori frequenza)

# Margine di potenza GE su carichi privilegiati (spunti motori, ADR-004).
MARGINE_GE = 1.25

# Tempo di rilevazione mancanza rete da parte dell'ATS [ms] (worst-case tipico).
T_RILEVAZIONE_MANCANZA_MS = 50.0

# Tempo tipico di intervento della protezione del DSO su cortocircuito rete [ms]
# (worst-case plausibile per la sequenza B; valore conservativo).
T_INTERVENTO_PROTEZIONE_DSO_MS = 500.0


# ====================================================================
# MODELLI INPUT
# ====================================================================

class ImpiantoFVInput(BaseModel):
    presente: bool = Field(False, description="Impianto FV presente")
    P_nominale_kW: float = Field(0.0, ge=0, description="Potenza FV nominale [kW]")
    tipologia_SPI: Literal["SPI_BT", "SPG_MT", "non_richiesto"] = Field(
        "SPI_BT", description="Protezione interfaccia: SPI (BT), SPG (MT) o non richiesta")

    t_intervento_sovratensione_ms: float = Field(
        100.0, ge=0, description="Tempo intervento SPI per sovratensione (CEI 0-21 §8.5)")
    t_intervento_sottotensione_ms: float = Field(
        200.0, ge=0, description="Tempo intervento SPI per sottotensione (CEI 0-21 §8.5)")
    t_intervento_frequenza_ms: float = Field(
        100.0, ge=0, description="Tempo intervento SPI per fuori frequenza (CEI 0-21 §8.5)")


class GruppoElettrogenoInput(BaseModel):
    presente: bool = Field(False, description="GE diesel presente")
    P_nominale_kVA: float = Field(0.0, ge=0, description="Potenza apparente GE [kVA]")

    t_avviamento_s: float = Field(
        10.0, ge=0, le=60, description="Tempo avvio GE dal segnale ATS (tipico 5-15 s)")
    t_stabilizzazione_s: float = Field(
        5.0, ge=0, description="Tempo stabilizzazione tensione/frequenza GE")
    autonomia_minima_h: float = Field(
        8.0, ge=0, description="Autonomia minima richiesta (norma + serbatoio)")
    cosphi: float = Field(
        0.8, gt=0, le=1.0, description="Fattore di potenza per conversione kVA->kW")


class ATSInput(BaseModel):
    tipologia: Literal["meccanico", "statico_SCR", "ibrido"] = Field(
        "meccanico", description="Tecnologia di commutazione")
    t_commutazione_ms: float = Field(
        150.0, ge=0,
        description="Tempo commutazione ATS rete->GE. Meccanico 100-300ms, "
                    "Statico SCR 4-20ms, Ibrido 20-100ms")
    t_ritardo_riconnessione_s: float = Field(
        180.0, ge=0,
        description="Ritardo riconnessione rete dopo ripristino. CEI 0-21 §8.6: minimo 180s")


class CoordinamentoATSInput(BaseModel):
    """Input completo per la verifica di coordinamento ATS multi-sorgente."""
    impianto_fv: ImpiantoFVInput = Field(default_factory=ImpiantoFVInput)
    gruppo_elettrogeno: GruppoElettrogenoInput = Field(default_factory=GruppoElettrogenoInput)
    ats: ATSInput = Field(default_factory=ATSInput)

    P_utenza_kW: float = Field(..., gt=0, description="Potenza totale utenza [kW]")
    Un_BT_V: float = Field(400.0, description="Tensione nominale BT [V]")
    Un_MT_kV: float | None = Field(None, description="Tensione MT [kV] se presente")

    P_privilegiati_kW: float = Field(
        0.0, ge=0, description="Potenza carichi privilegiati (alimentati da GE) [kW]")

    norma_connessione: Literal["CEI_0_21", "CEI_0_16"] = Field(
        "CEI_0_21", description="Norma di connessione applicabile (BT vs MT)")


# ====================================================================
# MODELLI OUTPUT
# ====================================================================

class VerificaSequenza(BaseModel):
    nome_sequenza: str
    descrizione: str
    durata_totale_ms: float
    fasi: list[dict]
    esito: Literal["OK", "AVVERTENZA", "NON_CONFORME"]
    note: list[str] = Field(default_factory=list)


class CoordinamentoATSOutput(BaseModel):
    verifica_mancanza_rete: VerificaSequenza
    verifica_cortocircuito_rete: VerificaSequenza
    verifica_riconnessione: VerificaSequenza

    dimensionamento_GE: dict
    dimensionamento_autonomia: dict

    esito_globale: Literal["CONFORME", "CONFORME_CON_PRESCRIZIONI", "NON_CONFORME"]
    prescrizioni: list[str] = Field(default_factory=list)

    norma_riferimento_internazionale: str = Field(
        "IEC 60364-5-56 (alimentazioni di sicurezza)")
    norma_riferimento_locale: str = Field(
        "CEI 0-21:2024, CEI 64-8 sez. 551, CEI 0-16 se MT")
    note_calcolo: list[str] = Field(default_factory=list)

    diagramma_sequenza: str = Field(description="Diagramma testuale del coordinamento")


# ====================================================================
# HELPER
# ====================================================================

def _peggiore(*esiti: str) -> str:
    """Combina esiti restituendo il peggiore (NON_CONFORME > AVVERTENZA > OK)."""
    ordine = {"OK": 0, "AVVERTENZA": 1, "NON_CONFORME": 2}
    return max(esiti, key=lambda e: ordine[e])


def _fase(tempo_ms: float, evento: str, sorgente: str) -> dict:
    return {"tempo_ms": round(tempo_ms, 1), "evento": evento, "sorgente_attiva": sorgente}


# ====================================================================
# SEQUENZE
# ====================================================================

def sequenza_mancanza_rete(inp: CoordinamentoATSInput) -> VerificaSequenza:
    """SEQUENZA A — mancanza rete pubblica: switch ATS verso GE."""
    fv, ge, ats = inp.impianto_fv, inp.gruppo_elettrogeno, inp.ats
    fasi: list[dict] = []
    note: list[str] = []
    esito = "OK"

    fasi.append(_fase(0.0, "Rete pubblica scomparsa", "nessuna"))
    t_ril = T_RILEVAZIONE_MANCANZA_MS
    fasi.append(_fase(t_ril, "ATS rileva mancanza rete", "nessuna"))

    # SPI disconnette FV (se presente e richiesto)
    if fv.presente and fv.tipologia_SPI != "non_richiesto":
        t_spi = fv.t_intervento_sottotensione_ms
        fasi.append(_fase(t_spi, "SPI disconnette FV (sottotensione, CEI 0-21)", "nessuna"))
        if t_spi > SPI_T_MAX_SOTTOTENSIONE_MS:
            esito = _peggiore(esito, "NON_CONFORME")
            note.append(
                f"SPI sottotensione {t_spi:g}ms > max norma {SPI_T_MAX_SOTTOTENSIONE_MS:g}ms "
                "(CEI 0-21 §8.5)")
    elif fv.presente and fv.tipologia_SPI == "non_richiesto":
        esito = _peggiore(esito, "NON_CONFORME")
        note.append("FV presente ma SPI 'non_richiesto': pericolo isola con GE. Richiesto SPI/SPG.")

    if not ge.presente:
        # nessun GE: i carichi privilegiati non sono alimentabili in mancanza rete
        durata = t_ril
        esito = _peggiore(esito, "AVVERTENZA")
        note.append("Nessun GE: in mancanza rete i carichi privilegiati NON sono alimentati.")
        return VerificaSequenza(
            nome_sequenza="A - Mancanza rete pubblica",
            descrizione="Mancanza rete senza sorgente di backup",
            durata_totale_ms=round(durata, 1), fasi=fasi, esito=esito, note=note)

    # GE: avviamento + stabilizzazione + commutazione
    t_ge_pronto = t_ril + ge.t_avviamento_s * 1000.0
    fasi.append(_fase(t_ge_pronto, "GE avviato", "GE (avvio)"))
    t_ge_stabile = t_ge_pronto + ge.t_stabilizzazione_s * 1000.0
    fasi.append(_fase(t_ge_stabile, "GE stabile (V/f)", "GE"))
    t_switch = t_ge_stabile + ats.t_commutazione_ms
    fasi.append(_fase(t_switch, "ATS commuta carichi privilegiati su GE", "GE"))
    fasi.append(_fase(t_switch, "Carichi privilegiati alimentati", "GE"))

    durata = t_switch
    if durata > T_MAX_ALIMENTAZIONE_PRIVILEGIATI_S * 1000.0:
        esito = _peggiore(esito, "AVVERTENZA")
        note.append(
            f"Tempo totale {durata/1000:.1f}s > {T_MAX_ALIMENTAZIONE_PRIVILEGIATI_S:g}s "
            "(CEI 64-8 §551 servizi essenziali): verificare classe di continuità richiesta.")

    return VerificaSequenza(
        nome_sequenza="A - Mancanza rete pubblica",
        descrizione="Commutazione automatica rete->GE con disconnessione FV",
        durata_totale_ms=round(durata, 1), fasi=fasi, esito=esito, note=note)


def sequenza_cortocircuito_rete(inp: CoordinamentoATSInput) -> VerificaSequenza:
    """SEQUENZA B — cortocircuito rete: SPI deve disconnettere FV prima dello switch."""
    fv, ge, ats = inp.impianto_fv, inp.gruppo_elettrogeno, inp.ats
    fasi: list[dict] = []
    note: list[str] = []
    esito = "OK"

    fasi.append(_fase(0.0, "Cortocircuito su rete pubblica", "rete (guasto)"))
    t_dso = T_INTERVENTO_PROTEZIONE_DSO_MS
    fasi.append(_fase(t_dso, "Protezione DSO interrompe la rete", "nessuna"))

    # istante della commutazione ATS verso GE (riferimento per il vincolo SPI)
    t_switch = None
    if ge.presente:
        t_switch = T_RILEVAZIONE_MANCANZA_MS + (ge.t_avviamento_s + ge.t_stabilizzazione_s) * 1000.0 + ats.t_commutazione_ms

    if fv.presente and fv.tipologia_SPI != "non_richiesto":
        # SPI interviene sul minimo dei suoi tempi (la condizione più rapida che scatta)
        t_spi = min(fv.t_intervento_sottotensione_ms, fv.t_intervento_sovratensione_ms,
                    fv.t_intervento_frequenza_ms)
        fasi.append(_fase(t_spi, "SPI/SPG disconnette FV", "nessuna"))
        # vincoli di norma sui tempi SPI
        if fv.t_intervento_sottotensione_ms > SPI_T_MAX_SOTTOTENSIONE_MS:
            esito = _peggiore(esito, "NON_CONFORME")
            note.append(f"SPI sottotensione {fv.t_intervento_sottotensione_ms:g}ms > {SPI_T_MAX_SOTTOTENSIONE_MS:g}ms (CEI 0-21 §8.5)")
        if fv.t_intervento_sovratensione_ms > SPI_T_MAX_SOVRATENSIONE_MS:
            esito = _peggiore(esito, "NON_CONFORME")
            note.append(f"SPI sovratensione {fv.t_intervento_sovratensione_ms:g}ms > {SPI_T_MAX_SOVRATENSIONE_MS:g}ms (CEI 0-21 §8.5)")
        if fv.t_intervento_frequenza_ms > SPI_T_MAX_FREQUENZA_MS:
            esito = _peggiore(esito, "NON_CONFORME")
            note.append(f"SPI frequenza {fv.t_intervento_frequenza_ms:g}ms > {SPI_T_MAX_FREQUENZA_MS:g}ms (CEI 0-21 §8.5)")
        # vincolo di sicurezza: SPI PRIMA dello switch GE (no isola FV+GE)
        if t_switch is not None and t_spi >= t_switch:
            esito = _peggiore(esito, "NON_CONFORME")
            note.append(
                f"SPI interviene a {t_spi:g}ms ma ATS commuta a {t_switch:g}ms: rischio FV "
                "in isola con GE. SPI deve intervenire PRIMA dello switch.")
        else:
            note.append("SPI interviene prima della commutazione ATS: nessuna isola FV+GE.")
    elif fv.presente:
        esito = _peggiore(esito, "NON_CONFORME")
        note.append("FV presente senza SPI/SPG: in cortocircuito rete il FV resterebbe in isola. NON CONFORME.")
    else:
        note.append("Nessun FV: nessun vincolo SPI in questa sequenza.")

    if ge.presente and t_switch is not None:
        fasi.append(_fase(t_switch, "ATS commuta su GE (come mancanza rete)", "GE"))
        durata = t_switch
    else:
        durata = max(t_dso, fasi[-1]["tempo_ms"])

    return VerificaSequenza(
        nome_sequenza="B - Cortocircuito rete pubblica",
        descrizione="Disconnessione FV via SPI prima della commutazione su GE",
        durata_totale_ms=round(durata, 1), fasi=fasi, esito=esito, note=note)


def sequenza_riconnessione(inp: CoordinamentoATSInput) -> VerificaSequenza:
    """SEQUENZA C — riconnessione rete: ordine rete->ATS->GE off->FV on."""
    fv, ge, ats = inp.impianto_fv, inp.gruppo_elettrogeno, inp.ats
    fasi: list[dict] = []
    note: list[str] = []
    esito = "OK"

    fasi.append(_fase(0.0, "Rete pubblica ripristinata", "GE"))
    t_ritardo = ats.t_ritardo_riconnessione_s * 1000.0
    fasi.append(_fase(t_ritardo, "Timer riconnessione ATS scaduto", "GE"))

    if ats.t_ritardo_riconnessione_s < T_RICONNESSIONE_MIN_S:
        esito = _peggiore(esito, "NON_CONFORME")
        note.append(
            f"Ritardo riconnessione {ats.t_ritardo_riconnessione_s:g}s < minimo "
            f"{T_RICONNESSIONE_MIN_S:g}s (CEI 0-21 §8.6).")

    t_switch_back = t_ritardo + ats.t_commutazione_ms
    fasi.append(_fase(t_switch_back, "ATS commuta carichi su rete", "rete"))

    if ge.presente:
        fasi.append(_fase(t_switch_back, "GE in shutdown (raffreddamento)", "rete"))

    if fv.presente and fv.tipologia_SPI != "non_richiesto":
        t_fv = t_switch_back + T_FV_RICONNESSIONE_DOPO_RETE_STABILE_S * 1000.0
        fasi.append(_fase(t_fv, "FV si riconnette (rete stabile, CEI 0-21)", "rete + FV"))
        durata = t_fv
    else:
        durata = t_switch_back

    note.append("Sequenza ordinata: rete -> ATS switch -> GE off -> FV on.")
    return VerificaSequenza(
        nome_sequenza="C - Riconnessione rete dopo guasto",
        descrizione="Rientro ordinato su rete con ritardo CEI 0-21 e riconnessione FV",
        durata_totale_ms=round(durata, 1), fasi=fasi, esito=esito, note=note)


# ====================================================================
# DIMENSIONAMENTO
# ====================================================================

def _dimensiona_GE(inp: CoordinamentoATSInput) -> dict:
    ge = inp.gruppo_elettrogeno
    P_richiesta = inp.P_privilegiati_kW * MARGINE_GE
    P_disponibile = ge.P_nominale_kVA * ge.cosphi if ge.presente else 0.0
    ok = (not ge.presente and inp.P_privilegiati_kW == 0.0) or (P_disponibile >= P_richiesta)
    return {
        "P_privilegiati_kW": inp.P_privilegiati_kW,
        "margine": MARGINE_GE,
        "P_richiesta_kW": round(P_richiesta, 2),
        "P_GE_disponibile_kW": round(P_disponibile, 2),
        "GE_presente": ge.presente,
        "esito": "OK" if ok else "NON_CONFORME",
    }


def _dimensiona_autonomia(inp: CoordinamentoATSInput) -> dict:
    ge = inp.gruppo_elettrogeno
    if not ge.presente:
        return {"GE_presente": False, "autonomia_h": 0.0, "esito": "N/A"}
    ok = ge.autonomia_minima_h >= 8.0
    return {
        "GE_presente": True,
        "autonomia_h": ge.autonomia_minima_h,
        "soglia_servizi_essenziali_h": 8.0,
        "esito": "OK" if ok else "AVVERTENZA",
    }


# ====================================================================
# DIAGRAMMA TESTUALE
# ====================================================================

_SIMB = {"OK": "✓", "AVVERTENZA": "!", "NON_CONFORME": "✗"}
_SORG_TAG = {
    "nessuna": "[---]", "rete": "[RETE]", "rete (guasto)": "[RETE]",
    "GE": "[GE] ", "GE (avvio)": "[GE] ", "rete + FV": "[RETE]", "rete + FV ": "[RETE]",
}


def _tag_evento(evento: str) -> str:
    e = evento.lower()
    if "spi" in e or "spg" in e:
        return "[SPI]"
    if "ats" in e or "timer" in e or "commuta" in e:
        return "[ATS]"
    if "ge" in e:
        return "[GE] "
    if "fv" in e:
        return "[FV] "
    if "rete" in e:
        return "[RETE]"
    if "carichi" in e:
        return "[UTE]"
    return "[...]"


def genera_diagramma(seq: VerificaSequenza) -> str:
    barra = "━" * 35
    righe = [seq.nome_sequenza.upper(), barra, ""]
    for f in seq.fasi:
        t = f["tempo_ms"]
        t_str = f"t={t:g}ms" if t < 1000 else f"t={t/1000:g}s"
        righe.append(f"{t_str:<12}{_tag_evento(f['evento'])} {f['evento']}")
    righe.append("")
    dur = seq.durata_totale_ms
    dur_str = f"{dur:g}ms" if dur < 1000 else f"{dur/1000:.1f}s"
    righe.append(f"Durata totale: {dur_str}")
    righe.append(f"Conformità: {seq.esito} {_SIMB[seq.esito]}")
    return "\n".join(righe)


# ====================================================================
# FUNZIONE PRINCIPALE
# ====================================================================

def coordinamento_ats_fv_generatore(inp: CoordinamentoATSInput) -> CoordinamentoATSOutput:
    """Verifica il coordinamento ATS multi-sorgente (3 sequenze + dimensionamento)."""
    note: list[str] = []

    seq_a = sequenza_mancanza_rete(inp)
    seq_b = sequenza_cortocircuito_rete(inp)
    seq_c = sequenza_riconnessione(inp)

    dim_ge = _dimensiona_GE(inp)
    dim_aut = _dimensiona_autonomia(inp)

    # esito globale = peggiore tra sequenze + dimensionamento
    esiti = [seq_a.esito, seq_b.esito, seq_c.esito]
    if dim_ge["esito"] == "NON_CONFORME":
        esiti.append("NON_CONFORME")
    if dim_aut["esito"] == "AVVERTENZA":
        esiti.append("AVVERTENZA")
    peggiore = _peggiore(*esiti)
    esito_globale = {
        "OK": "CONFORME", "AVVERTENZA": "CONFORME_CON_PRESCRIZIONI",
        "NON_CONFORME": "NON_CONFORME",
    }[peggiore]

    prescrizioni: list[str] = []
    for seq in (seq_a, seq_b, seq_c):
        for n in seq.note:
            if seq.esito != "OK":
                prescrizioni.append(f"[{seq.nome_sequenza}] {n}")
    if dim_ge["esito"] == "NON_CONFORME":
        prescrizioni.append(
            f"GE sottodimensionato: disponibile {dim_ge['P_GE_disponibile_kW']} kW < "
            f"richiesto {dim_ge['P_richiesta_kW']} kW (margine {MARGINE_GE}).")
    if dim_aut["esito"] == "AVVERTENZA":
        prescrizioni.append(
            f"Autonomia GE {dim_aut['autonomia_h']}h < {dim_aut['soglia_servizi_essenziali_h']}h "
            "raccomandate per servizi essenziali.")

    # note di calcolo / tracciabilità
    note.append(f"Default conservativi (ADR-004): rilevazione mancanza {T_RILEVAZIONE_MANCANZA_MS:g}ms, "
                f"margine GE {MARGINE_GE}, riconnessione min {T_RICONNESSIONE_MIN_S:g}s.")
    if inp.norma_connessione == "CEI_0_16":
        note.append("Norma MT (CEI 0-16): SPG e soglie MT non interamente coperte da questo Tier 1; "
                    "verificare requisiti specifici CEI 0-16 §8 per P>200kW.")
    if inp.Un_MT_kV is not None and inp.norma_connessione == "CEI_0_21":
        note.append("Un_MT valorizzato ma norma_connessione=CEI_0_21: verificare se l'impianto è MT "
                    "(allora applicare CEI 0-16).")

    diagramma = "\n\n".join(genera_diagramma(s) for s in (seq_a, seq_b, seq_c))

    return CoordinamentoATSOutput(
        verifica_mancanza_rete=seq_a,
        verifica_cortocircuito_rete=seq_b,
        verifica_riconnessione=seq_c,
        dimensionamento_GE=dim_ge,
        dimensionamento_autonomia=dim_aut,
        esito_globale=esito_globale,
        prescrizioni=prescrizioni,
        note_calcolo=note,
        diagramma_sequenza=diagramma,
    )
