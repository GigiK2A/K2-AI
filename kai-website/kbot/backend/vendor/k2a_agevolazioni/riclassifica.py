"""Riclassificazione del bilancio CEE (artt. 2424/2425 c.c.).

Da bilancio civilistico → Stato Patrimoniale riclassificato a criterio
finanziario + Conto Economico a valore aggiunto. Calcola i margini patrimoniali
(CCN, margine di tesoreria, margine di struttura) e produce un blocco
'bancabilita_input' pronto per il tool indici_bancabilita.

Le voci sono aggregate per macro-classe; dove la distinzione conta (crediti e
debiti entro/oltre 12 mesi, quota finanziaria dei debiti) gli input sono separati.
"""
from __future__ import annotations
from pydantic import BaseModel, Field, model_validator

_TOLL_QUADRATURA = 1.0  # euro


class BilancioCEEInput(BaseModel):
    # ---- STATO PATRIMONIALE - ATTIVO ----
    crediti_v_soci: float = Field(0.0, ge=0, description="A) Crediti verso soci per versamenti dovuti.")
    immobilizzazioni: float = Field(0.0, ge=0, description="B) Immobilizzazioni (immateriali+materiali+finanziarie).")
    rimanenze: float = Field(0.0, ge=0, description="C.I) Rimanenze di magazzino.")
    crediti_entro_12m: float = Field(0.0, ge=0, description="C.II) Crediti esigibili entro 12 mesi.")
    crediti_oltre_12m: float = Field(0.0, ge=0, description="C.II) Crediti esigibili oltre 12 mesi.")
    attivita_finanziarie_non_immob: float = Field(0.0, ge=0, description="C.III) Attività finanziarie non immobilizzate.")
    disponibilita_liquide: float = Field(0.0, ge=0, description="C.IV) Disponibilità liquide (cassa + banca).")
    ratei_risconti_attivi: float = Field(0.0, ge=0, description="D) Ratei e risconti attivi.")
    # ---- STATO PATRIMONIALE - PASSIVO ----
    patrimonio_netto: float = Field(..., description="A) Patrimonio netto (può essere negativo).")
    fondi_rischi_oneri: float = Field(0.0, ge=0, description="B) Fondi per rischi e oneri.")
    tfr: float = Field(0.0, ge=0, description="C) Trattamento di fine rapporto.")
    debiti_entro_12m: float = Field(0.0, ge=0, description="D) Debiti esigibili entro 12 mesi (totali).")
    debiti_oltre_12m: float = Field(0.0, ge=0, description="D) Debiti esigibili oltre 12 mesi (totali).")
    ratei_risconti_passivi: float = Field(0.0, ge=0, description="E) Ratei e risconti passivi.")
    # di cui finanziari (banche, obbligazioni, altri finanziatori): sottoinsieme dei debiti
    debiti_finanziari_entro_12m: float = Field(0.0, ge=0, description="Di cui finanziari entro 12m (banche/obblig./finanziatori).")
    debiti_finanziari_oltre_12m: float = Field(0.0, ge=0, description="Di cui finanziari oltre 12m.")
    # ---- CONTO ECONOMICO ----
    ricavi_vendite: float = Field(..., gt=0, description="A.1) Ricavi delle vendite e delle prestazioni.")
    altri_ricavi_e_proventi: float = Field(0.0, description="A.2-A.5) Altri componenti del valore della produzione.")
    costi_materie: float = Field(0.0, ge=0, description="B.6 + B.11) Materie prime/sussidiarie e var. rimanenze MP.")
    costi_servizi: float = Field(0.0, ge=0, description="B.7) Costi per servizi.")
    costi_godimento_beni_terzi: float = Field(0.0, ge=0, description="B.8) Godimento beni di terzi.")
    costo_personale: float = Field(0.0, ge=0, description="B.9) Costi per il personale.")
    ammortamenti_svalutazioni: float = Field(0.0, ge=0, description="B.10) Ammortamenti e svalutazioni.")
    accantonamenti: float = Field(0.0, ge=0, description="B.12 + B.13) Accantonamenti per rischi e altri.")
    oneri_diversi_gestione: float = Field(0.0, ge=0, description="B.14) Oneri diversi di gestione.")
    proventi_finanziari: float = Field(0.0, ge=0, description="C.15 + C.16) Proventi finanziari.")
    oneri_finanziari: float = Field(0.0, ge=0, description="C.17) Interessi e altri oneri finanziari.")
    rettifiche_finanziarie: float = Field(0.0, description="D) Rettifiche di valore di attività finanziarie (+/-).")
    imposte: float = Field(0.0, description="20) Imposte sul reddito d'esercizio.")

    @model_validator(mode="after")
    def _check_finanziari(self):
        if self.debiti_finanziari_entro_12m > self.debiti_entro_12m + _TOLL_QUADRATURA:
            raise ValueError("debiti_finanziari_entro_12m non possono superare i debiti_entro_12m.")
        if self.debiti_finanziari_oltre_12m > self.debiti_oltre_12m + _TOLL_QUADRATURA:
            raise ValueError("debiti_finanziari_oltre_12m non possono superare i debiti_oltre_12m.")
        return self


class RiclassificaOutput(BaseModel):
    # SP riclassificato finanziario
    attivo_immobilizzato: float
    attivo_corrente: float
    totale_attivo: float
    patrimonio_netto: float
    passivo_consolidato: float
    passivo_corrente: float
    totale_passivo: float
    quadratura_ok: bool
    sbilancio_eur: float
    debiti_finanziari: float
    pfn: float
    # CE a valore aggiunto
    valore_produzione: float
    valore_aggiunto: float
    ebitda: float
    ebit: float
    risultato_ante_imposte: float
    utile_netto: float
    # Margini patrimoniali
    capitale_circolante_netto: float
    margine_tesoreria: float
    margine_struttura: float
    # Pronto per indici_bancabilita
    bancabilita_input: dict
    avvertenze: list[str]
    riferimento_normativo: str
    trace: dict


def riclassifica_bilancio(inp: BilancioCEEInput) -> RiclassificaOutput:
    avvertenze: list[str] = []

    # ---- SP riclassificato a criterio finanziario ----
    attivo_immobilizzato = inp.immobilizzazioni + inp.crediti_oltre_12m
    attivo_corrente = (
        inp.crediti_v_soci + inp.rimanenze + inp.crediti_entro_12m
        + inp.attivita_finanziarie_non_immob + inp.disponibilita_liquide
        + inp.ratei_risconti_attivi
    )
    totale_attivo = attivo_immobilizzato + attivo_corrente

    passivo_consolidato = inp.debiti_oltre_12m + inp.tfr + inp.fondi_rischi_oneri
    passivo_corrente = inp.debiti_entro_12m + inp.ratei_risconti_passivi
    totale_passivo = inp.patrimonio_netto + passivo_consolidato + passivo_corrente

    sbilancio = totale_attivo - totale_passivo
    quadratura_ok = abs(sbilancio) <= _TOLL_QUADRATURA
    if not quadratura_ok:
        avvertenze.append(
            f"QUADRATURA: attivo ({totale_attivo:.2f}) ≠ passivo ({totale_passivo:.2f}), "
            f"sbilancio {sbilancio:.2f}€. Verificare le voci inserite."
        )

    debiti_finanziari = inp.debiti_finanziari_entro_12m + inp.debiti_finanziari_oltre_12m
    pfn = debiti_finanziari - inp.disponibilita_liquide

    # ---- CE a valore aggiunto ----
    valore_produzione = inp.ricavi_vendite + inp.altri_ricavi_e_proventi
    costi_esterni = (
        inp.costi_materie + inp.costi_servizi
        + inp.costi_godimento_beni_terzi + inp.oneri_diversi_gestione
    )
    valore_aggiunto = valore_produzione - costi_esterni
    ebitda = valore_aggiunto - inp.costo_personale
    ebit = ebitda - inp.ammortamenti_svalutazioni - inp.accantonamenti
    risultato_ante = ebit + inp.proventi_finanziari - inp.oneri_finanziari + inp.rettifiche_finanziarie
    utile_netto = risultato_ante - inp.imposte

    # ---- Margini patrimoniali ----
    ccn = attivo_corrente - passivo_corrente
    margine_tesoreria = (attivo_corrente - inp.rimanenze) - passivo_corrente
    margine_struttura = inp.patrimonio_netto - attivo_immobilizzato

    if ccn < 0:
        avvertenze.append("Capitale circolante netto NEGATIVO: il passivo corrente eccede "
                          "l'attivo corrente (potenziale tensione di liquidità).")
    if margine_struttura < 0:
        avvertenze.append("Margine di struttura negativo: le immobilizzazioni non sono "
                          "interamente coperte dal patrimonio netto.")
    if ebitda <= 0:
        avvertenze.append("EBITDA non positivo: la gestione caratteristica non genera margine.")

    bancabilita_input = {
        "totale_attivo": round(totale_attivo, 2),
        "attivo_corrente": round(attivo_corrente, 2),
        "rimanenze": round(inp.rimanenze, 2),
        "liquidita_immediata": round(inp.disponibilita_liquide, 2),
        "passivo_corrente": round(passivo_corrente, 2),
        "patrimonio_netto": round(inp.patrimonio_netto, 2),
        "debiti_finanziari": round(debiti_finanziari, 2),
        "ricavi": round(inp.ricavi_vendite, 2),
        "ebitda": round(ebitda, 2),
        "ebit": round(ebit, 2),
        "oneri_finanziari": round(inp.oneri_finanziari, 2),
        "utile_netto": round(utile_netto, 2),
    }

    return RiclassificaOutput(
        attivo_immobilizzato=round(attivo_immobilizzato, 2),
        attivo_corrente=round(attivo_corrente, 2),
        totale_attivo=round(totale_attivo, 2),
        patrimonio_netto=round(inp.patrimonio_netto, 2),
        passivo_consolidato=round(passivo_consolidato, 2),
        passivo_corrente=round(passivo_corrente, 2),
        totale_passivo=round(totale_passivo, 2),
        quadratura_ok=quadratura_ok,
        sbilancio_eur=round(sbilancio, 2),
        debiti_finanziari=round(debiti_finanziari, 2),
        pfn=round(pfn, 2),
        valore_produzione=round(valore_produzione, 2),
        valore_aggiunto=round(valore_aggiunto, 2),
        ebitda=round(ebitda, 2),
        ebit=round(ebit, 2),
        risultato_ante_imposte=round(risultato_ante, 2),
        utile_netto=round(utile_netto, 2),
        capitale_circolante_netto=round(ccn, 2),
        margine_tesoreria=round(margine_tesoreria, 2),
        margine_struttura=round(margine_struttura, 2),
        bancabilita_input=bancabilita_input,
        avvertenze=avvertenze,
        riferimento_normativo="Artt. 2424 (SP) e 2425 (CE) c.c.; riclassificazione SP a criterio "
                              "finanziario e CE a valore aggiunto (prassi di analisi di bilancio).",
        trace={
            "metodo_sp": "criterio finanziario (liquidità/esigibilità entro-oltre 12 mesi)",
            "metodo_ce": "valore aggiunto → EBITDA → EBIT → utile netto",
            "tolleranza_quadratura_eur": _TOLL_QUADRATURA,
            "costi_esterni_eur": round(costi_esterni, 2),
        },
    )
