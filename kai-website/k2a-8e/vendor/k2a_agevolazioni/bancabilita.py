"""Indici di bancabilità — screening del merito creditizio di un'impresa.

Calcola gli indici di bilancio che le banche usano in sede di affidamento
(sostenibilità del debito, solidità patrimoniale, liquidità, redditività),
li confronta con soglie di prassi bancaria, e produce un punteggio sintetico
e una classe di bancabilità (A/B/C/D).

Doppia finalità:
  - 'finanziamento_bancario': autovalutazione dell'impresa che chiede credito;
  - 'dilazione_pagamento_cliente': valutazione del merito di un cliente a cui
    concedere un pagamento dilazionato (fido commerciale).

NB: soglie ORIENTATIVE di prassi, non un rating ufficiale. Segnala inoltre gli
indizi di crisi ex art. 3 D.Lgs. 14/2019 (DSCR<1, patrimonio netto negativo).
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, Field, model_validator

_DATA = json.loads((Path(__file__).parent / "data" / "indici_bancabilita.json").read_text())


class BancabilitaInput(BaseModel):
    # Stato patrimoniale riclassificato (criterio finanziario)
    totale_attivo: float = Field(..., gt=0, description="Totale attivo (capitale investito).")
    attivo_corrente: float = Field(..., ge=0, description="Attivo corrente (realizzabile entro 12 mesi).")
    rimanenze: float = Field(0.0, ge=0, description="Rimanenze di magazzino.")
    liquidita_immediata: float = Field(0.0, ge=0, description="Disponibilità liquide (cassa + banca).")
    passivo_corrente: float = Field(..., gt=0, description="Passivo corrente (debiti entro 12 mesi).")
    patrimonio_netto: float = Field(..., description="Patrimonio netto (può essere negativo).")
    debiti_finanziari: float = Field(..., ge=0, description="Debiti finanziari totali (breve + m/l termine).")
    # Conto economico
    ricavi: float = Field(..., gt=0, description="Ricavi delle vendite e prestazioni.")
    ebitda: float = Field(..., description="EBITDA (margine operativo lordo).")
    ebit: float = Field(..., description="EBIT (risultato operativo).")
    oneri_finanziari: float = Field(0.0, ge=0, description="Oneri finanziari (interessi passivi).")
    utile_netto: float = Field(..., description="Utile (perdita) netto d'esercizio.")
    # Servizio del debito (per DSCR) — opzionale
    servizio_debito_annuo: float | None = Field(
        default=None, gt=0,
        description="Servizio del debito annuo (quota capitale + interessi su finanziamenti). "
                    "Se assente, il DSCR non viene calcolato.")
    flusso_cassa_operativo: float | None = Field(
        default=None,
        description="Flusso di cassa operativo per il DSCR. Se assente, si usa l'EBITDA come proxy.")
    finalita: Literal["finanziamento_bancario", "dilazione_pagamento_cliente"] = Field(
        "finanziamento_bancario",
        description="Contesto d'uso: autovalutazione per credito bancario o "
                    "valutazione di un cliente per dilazione di pagamento.")

    @model_validator(mode="after")
    def _check_attivo(self):
        if self.attivo_corrente > self.totale_attivo:
            raise ValueError("attivo_corrente non può superare il totale_attivo.")
        if self.rimanenze > self.attivo_corrente:
            raise ValueError("rimanenze non possono superare l'attivo_corrente.")
        return self


class IndicatoreOut(BaseModel):
    indicatore: str
    label: str
    categoria: str
    valore: float | None
    valutazione: str          # ottimo | buono | attenzione | critico | n.d.
    score: int | None         # 3..0
    peso: int
    soglie: dict
    formula: str


class BancabilitaOutput(BaseModel):
    finalita: str
    punteggio_0_100: float
    classe: str
    giudizio: str
    colore: str
    pfn_eur: float
    indicatori: list[IndicatoreOut]
    indicatori_critici: list[str]
    segnali_crisi_codice_14_2019: list[str]
    raccomandazioni: list[str]
    avvertenze: list[str]
    riferimento_normativo: str
    trace: dict


_BANDA_LABEL = {3: "ottimo", 2: "buono", 1: "attenzione", 0: "critico"}


def _score_indicatore(direzione: str, valore: float, soglie: dict) -> int:
    o, b, a = soglie["ottimo"], soglie["buono"], soglie["attenzione"]
    if direzione == "alto_meglio":
        if valore >= o: return 3
        if valore >= b: return 2
        if valore >= a: return 1
        return 0
    else:  # basso_meglio
        if valore <= o: return 3
        if valore <= b: return 2
        if valore <= a: return 1
        return 0


def _safe_div(num: float, den: float) -> float | None:
    return None if den == 0 else num / den


def indici_bancabilita(inp: BancabilitaInput) -> BancabilitaOutput:
    avvertenze: list[str] = [_DATA["_disclaimer"]]

    pfn = inp.debiti_finanziari - inp.liquidita_immediata

    # Calcolo grezzo dei valori
    valori: dict[str, float | None] = {
        "pfn_ebitda": _safe_div(pfn, inp.ebitda) if inp.ebitda > 0 else None,
        "dscr": None,
        "interest_coverage": _safe_div(inp.ebitda, inp.oneri_finanziari) if inp.oneri_finanziari > 0 else None,
        "indipendenza_finanziaria": _safe_div(inp.patrimonio_netto, inp.totale_attivo),
        "leverage": _safe_div(inp.debiti_finanziari, inp.patrimonio_netto) if inp.patrimonio_netto > 0 else None,
        "current_ratio": _safe_div(inp.attivo_corrente, inp.passivo_corrente),
        "quick_ratio": _safe_div(inp.attivo_corrente - inp.rimanenze, inp.passivo_corrente),
        "ebitda_margin": _safe_div(inp.ebitda, inp.ricavi),
        "ros": _safe_div(inp.ebit, inp.ricavi),
        "roe": _safe_div(inp.utile_netto, inp.patrimonio_netto) if inp.patrimonio_netto > 0 else None,
    }

    # DSCR
    if inp.servizio_debito_annuo:
        numeratore = inp.flusso_cassa_operativo if inp.flusso_cassa_operativo is not None else inp.ebitda
        valori["dscr"] = numeratore / inp.servizio_debito_annuo
        if inp.flusso_cassa_operativo is None:
            avvertenze.append("DSCR calcolato usando l'EBITDA come proxy del flusso di cassa operativo.")
    else:
        avvertenze.append("DSCR non calcolato: 'servizio_debito_annuo' non fornito. Indicatore escluso dal punteggio.")

    # Note su EBITDA negativo: PFN/EBITDA non è numericamente significativo, ma NON va escluso
    # dal punteggio (escluderlo alleggerirebbe il rating proprio nel caso peggiore). Lo forziamo
    # a score 0 col suo peso nel denominatore — coerente con interest_coverage che entra a 0.
    forza_score_zero: set[str] = set()
    if inp.ebitda <= 0:
        valori["pfn_ebitda"] = None
        forza_score_zero.add("pfn_ebitda")
        avvertenze.append("EBITDA ≤ 0: PFN/EBITDA non significativo, valutato 'critico' (score 0) col suo peso nel punteggio (segnale fortemente negativo).")

    # Costruzione indicatori + scoring pesato sui soli disponibili
    indicatori: list[IndicatoreOut] = []
    critici: list[str] = []
    somma_pesata = 0.0
    peso_totale = 0
    for key, cfg in _DATA["indicatori"].items():
        v = valori.get(key)
        if v is None:
            if key in forza_score_zero:
                # valore non numerico ma segnale critico noto → score 0 CON peso (non escluso)
                somma_pesata += 0 * cfg["peso"]
                peso_totale += cfg["peso"]
                critici.append(cfg["label"])
                indicatori.append(IndicatoreOut(
                    indicatore=key, label=cfg["label"], categoria=cfg["categoria"],
                    valore=None, valutazione=_BANDA_LABEL[0], score=0, peso=cfg["peso"],
                    soglie=cfg["soglie"], formula=cfg["formula"]))
                continue
            indicatori.append(IndicatoreOut(
                indicatore=key, label=cfg["label"], categoria=cfg["categoria"],
                valore=None, valutazione="n.d.", score=None, peso=cfg["peso"],
                soglie=cfg["soglie"], formula=cfg["formula"]))
            continue
        s = _score_indicatore(cfg["direzione"], v, cfg["soglie"])
        somma_pesata += s * cfg["peso"]
        peso_totale += cfg["peso"]
        if s == 0:
            critici.append(cfg["label"])
        indicatori.append(IndicatoreOut(
            indicatore=key, label=cfg["label"], categoria=cfg["categoria"],
            valore=round(v, 4), valutazione=_BANDA_LABEL[s], score=s, peso=cfg["peso"],
            soglie=cfg["soglie"], formula=cfg["formula"]))

    # Punteggio normalizzato 0-100 (score max = 3 per indicatore)
    punteggio = round(somma_pesata / (peso_totale * 3) * 100.0, 1) if peso_totale > 0 else 0.0

    # Classe di rating
    banda = next(b for b in _DATA["rating_bande"] if punteggio >= b["min_score"])

    # Segnali di crisi ex art. 3 D.Lgs. 14/2019
    segnali: list[str] = []
    if inp.patrimonio_netto < 0:
        segnali.append("Patrimonio netto NEGATIVO: capitale eroso, indizio di crisi "
                       "(art. 3 D.Lgs. 14/2019 — obbligo di adeguati assetti).")
    if valori.get("dscr") is not None and valori["dscr"] < 1.0:
        segnali.append(f"DSCR = {valori['dscr']:.2f} < 1: flussi insufficienti a coprire il "
                       "servizio del debito (indizio di crisi prospettica).")
    if inp.ebitda <= 0:
        segnali.append("EBITDA non positivo: gestione operativa non in grado di generare margine.")

    # Raccomandazioni per finalità
    raccomandazioni: list[str] = []
    if inp.finalita == "finanziamento_bancario":
        if banda["classe"] in ("A", "B"):
            raccomandazioni.append("Profilo coerente con un'istruttoria di affidamento; "
                                   "preparare business plan e DSCR prospettico a supporto.")
        else:
            raccomandazioni.append("Prima di richiedere credito: rafforzare il patrimonio netto "
                                   "e/o ridurre la PFN per miglioare leva e DSCR.")
        if valori.get("pfn_ebitda") is not None and valori["pfn_ebitda"] and valori["pfn_ebitda"] > 4:
            raccomandazioni.append("Leva PFN/EBITDA > 4: molte banche pongono qui un cut-off; "
                                   "valutare rimodulazione del debito.")
    else:  # dilazione_pagamento_cliente
        if banda["classe"] == "A":
            raccomandazioni.append("Cliente con buon merito: dilazione concedibile; suggerito comunque "
                                   "monitoraggio periodico e definizione di un plafond di fido.")
        elif banda["classe"] == "B":
            raccomandazioni.append("Dilazione concedibile con cautela: limitare l'esposizione e/o "
                                   "richiedere garanzie (fideiussione, assicurazione del credito).")
        else:
            raccomandazioni.append("Merito debole: sconsigliata dilazione ampia; preferire pagamento "
                                   "anticipato/contestuale o garanzie reali.")

    avvertenze.append("Screening indicativo, NON un rating ufficiale né garanzia di affidamento: "
                      "ogni banca applica modelli di rating interno e cut-off settoriali propri.")

    return BancabilitaOutput(
        finalita=inp.finalita,
        punteggio_0_100=punteggio,
        classe=banda["classe"],
        giudizio=banda["giudizio"],
        colore=banda["colore"],
        pfn_eur=round(pfn, 2),
        indicatori=indicatori,
        indicatori_critici=critici,
        segnali_crisi_codice_14_2019=segnali,
        raccomandazioni=raccomandazioni,
        avvertenze=avvertenze,
        riferimento_normativo=_DATA["_fonte"],
        trace={
            "fonte_dati": _DATA["_fonte"],
            "data_validita_dati": _DATA["_data_validita"],
            "peso_totale_indicatori_usati": peso_totale,
            "metodo_punteggio": "media pesata degli score (0-3) sui soli indicatori disponibili, normalizzata 0-100",
            "indicatori_esclusi": [k for k, v in valori.items() if v is None],
        },
    )
