"""Check di sostenibilità (CCII vigente) — strumento diagnostico informale.

ATTENZIONE QUADRO NORMATIVO: il sistema di allerta con indicatori/INDICI della crisi
(impianto CNDCEC ai sensi dell'originario art. 13 D.Lgs. 14/2019) è stato ELIMINATO
dal D.Lgs. 83/2022 (in vigore 15/7/2022), poi correttivo D.Lgs. 136/2024. NON esiste
più un "superamento congiunto dei 5 indici" che faccia scattare un indizio legale.
Il monitoraggio vigente poggia su: ADEGUATI ASSETTI (art. 2086 c.c. / art. 3 CCII),
SEGNALAZIONI dei creditori pubblici qualificati (art. 25-novies CCII), COMPOSIZIONE
NEGOZIATA (artt. 12 ss.). L'art. 13 oggi = "lista di controllo" piani di risanamento.

Questo tool calcola gli stessi indici (DSCR, PN, oneri/ricavi, liquidità, ...) come
STRUMENTO DIAGNOSTICO INFORMALE di sostenibilità — NON come trigger legale.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, Field

_DATA = json.loads((Path(__file__).parent / "data" / "crisi_cndcec.json").read_text())
_SETTORI = list(_DATA["soglie_per_settore"].keys())


class CrisiCNDCECInput(BaseModel):
    # Prerequisiti
    patrimonio_netto: float = Field(..., description="Patrimonio netto (può essere negativo).")
    dscr_6_mesi: float | None = Field(
        default=None, gt=0,
        description="DSCR a 6 mesi se disponibile e affidabile. Se fornito, prevale "
                    "sui 5 indici settoriali.")
    # Dati per i 5 indici settoriali
    ricavi: float = Field(..., gt=0, description="Ricavi delle vendite.")
    oneri_finanziari: float = Field(0.0, ge=0, description="Oneri finanziari.")
    debiti_totali: float = Field(..., gt=0, description="Totale debiti.")
    cash_flow: float = Field(..., description="Flusso di cassa (cash flow) dell'esercizio.")
    totale_attivo: float = Field(..., gt=0, description="Totale attivo.")
    attivita_breve: float = Field(..., ge=0, description="Attività a breve termine.")
    passivita_breve: float = Field(..., gt=0, description="Passività a breve termine.")
    debiti_previdenziali_tributari: float = Field(
        0.0, ge=0, description="Debiti verso enti previdenziali e tributari.")
    settore: str = Field(
        "generico",
        description=f"Settore per le soglie. Disponibili: {_SETTORI}. "
                    f"Default 'generico' (PLACEHOLDER da validare).")


class IndiceCrisiOut(BaseModel):
    id: str
    label: str
    valore: float
    soglia: float
    direzione: str
    superato: bool   # True = oltre soglia in senso peggiorativo (segnale negativo)


class CrisiCNDCECOutput(BaseModel):
    esito: str        # "fondato_indizio_crisi" | "nessun_indizio_dai_5_indici" | "monitorare"
    crisi_segnalata: bool
    motivazione: list[str]
    pn_negativo: bool
    dscr_usato: bool
    dscr_valore: float | None
    indici_settoriali: list[IndiceCrisiOut]
    n_indici_superati: int
    indici_superati_tutti: bool
    settore: str
    avvertenze: list[str]
    riferimento_normativo: str
    trace: dict


def scoring_crisi_cndcec(inp: CrisiCNDCECInput) -> CrisiCNDCECOutput:
    avvertenze: list[str] = [_DATA["_disclaimer"]]
    motivazione: list[str] = []

    if inp.settore not in _DATA["soglie_per_settore"]:
        avvertenze.append(
            f"Settore '{inp.settore}' non presente: uso soglie 'generico'. "
            f"Settori disponibili: {_SETTORI}."
        )
        settore = "generico"
    else:
        settore = inp.settore
    soglie = _DATA["soglie_per_settore"][settore]
    if soglie.get("_da_validare") or _DATA.get("_da_validare"):
        avvertenze.append(
            "Soglie settoriali marcate _DA_VALIDARE: caricare la tabella ufficiale "
            "CNDCEC a 11 settori prima dell'uso in pratica. Risultato indicativo."
        )

    pn_negativo = inp.patrimonio_netto < 0
    if pn_negativo:
        motivazione.append("Patrimonio netto NEGATIVO: fondato indizio di crisi a "
                           "prescindere dagli indici (capitale eroso).")

    # Calcolo dei 5 indici
    valori = {
        "oneri_fin_ricavi": inp.oneri_finanziari / inp.ricavi,
        "pn_debiti": inp.patrimonio_netto / inp.debiti_totali,
        "cashflow_attivo": inp.cash_flow / inp.totale_attivo,
        "liquidita": inp.attivita_breve / inp.passivita_breve,
        "indebit_prev_trib": inp.debiti_previdenziali_tributari / inp.totale_attivo,
    }
    indici: list[IndiceCrisiOut] = []
    n_superati = 0
    for d in _DATA["indici_settoriali"]["definizioni"]:
        iid = d["id"]
        v = valori[iid]
        soglia = float(soglie[iid])
        direzione = d["direzione"]
        superato = (v > soglia) if direzione == "sopra" else (v < soglia)
        if superato:
            n_superati += 1
        indici.append(IndiceCrisiOut(
            id=iid, label=d["label"], valore=round(v, 4),
            soglia=soglia, direzione=direzione, superato=superato))

    tutti_superati = n_superati == len(indici)

    # Indicatore principale DSCR
    dscr_usato = inp.dscr_6_mesi is not None
    if dscr_usato:
        if inp.dscr_6_mesi < 1.0:
            motivazione.append(f"DSCR a 6 mesi = {inp.dscr_6_mesi:.2f} < 1: i flussi "
                               "prospettici non coprono il servizio del debito.")
        else:
            motivazione.append(f"DSCR a 6 mesi = {inp.dscr_6_mesi:.2f} ≥ 1: copertura "
                               "prospettica del debito adeguata.")

    # Determinazione esito
    crisi = False
    if pn_negativo:
        crisi = True
        esito = "fondato_indizio_crisi"
    elif dscr_usato and inp.dscr_6_mesi < 1.0:
        crisi = True
        esito = "fondato_indizio_crisi"
        motivazione.append("DSCR < 1 (indicatore principale): prevale sui 5 indici settoriali.")
    elif dscr_usato and inp.dscr_6_mesi >= 1.0:
        crisi = False
        esito = "nessun_indizio_dscr_adeguato"
        motivazione.append("DSCR ≥ 1 affidabile: indicatore principale soddisfatto, "
                           "5 indici settoriali non determinanti.")
    else:
        # niente DSCR → si guardano i 5 indici (superamento congiunto)
        if tutti_superati:
            crisi = True
            esito = "fondato_indizio_crisi"
            motivazione.append(f"Tutti i {len(indici)} indici settoriali superati "
                               "congiuntamente: indizio di crisi.")
        else:
            crisi = False
            esito = "monitorare" if n_superati > 0 else "nessun_indizio_dai_5_indici"
            motivazione.append(f"{n_superati}/{len(indici)} indici superati: superamento "
                               "NON congiunto, nessun indizio automatico dai 5 indici "
                               "(monitorare se >0).")

    return CrisiCNDCECOutput(
        esito=esito,
        crisi_segnalata=crisi,
        motivazione=motivazione,
        pn_negativo=pn_negativo,
        dscr_usato=dscr_usato,
        dscr_valore=inp.dscr_6_mesi,
        indici_settoriali=indici,
        n_indici_superati=n_superati,
        indici_superati_tutti=tutti_superati,
        settore=settore,
        avvertenze=avvertenze,
        riferimento_normativo=_DATA["_fonte"],
        trace={
            "fonte_dati": _DATA["_fonte"],
            "data_validita_dati": _DATA["_data_validita"],
            "logica": "Check di sostenibilità (CCII vigente): screening informale su PN, DSCR e indici di liquidità/redditività. NON è il trigger legale dell'art.13 (abrogato dal D.Lgs. 83/2022): nessun superamento di indici fa scattare un indizio di crisi ai fini di legge.",
            "settore_usato": settore,
        },
    )
