"""Listino e abbonamenti — UNICA fonte di verità sui prezzi.

Espone il listino dal catalogo (catalogo_documenti.json) così che l'agente/skill
NON debba (e NON possa) inventare i prezzi. Due tool:
  - lista_abbonamenti: piani Free/Pro/Business + pacchetti crediti + consulenza.
  - scheda_listino: dato un prodotto, restituisce strato, prezzo, costo in crediti
    e il prezzo effettivo per ciascun piano di abbonamento (sconto Boost incluso).
"""
from __future__ import annotations
import json
import calendar
from datetime import date
from pathlib import Path
from pydantic import BaseModel, Field

_CATALOGO = json.loads((Path(__file__).parent / "data" / "catalogo_documenti.json").read_text())
_TIPI = _CATALOGO["tipi"]
_ABB = _CATALOGO["abbonamenti"]
_CREDITI = _CATALOGO["crediti"]
_PERCORSI = _CATALOGO.get("percorsi", {})


# ----------------------------------------------------------- abbonamenti ----

class ListaAbbonamentiInput(BaseModel):
    pass


class ListaAbbonamentiOutput(BaseModel):
    nota: str
    piani: list[dict]
    pacchetti_crediti: list[dict]
    valore_credito_eur: float
    consulenza_umana: dict
    trace: dict


def lista_abbonamenti(inp: ListaAbbonamentiInput | None = None) -> ListaAbbonamentiOutput:
    piani = [{"id": k, **v} for k, v in _ABB["piani"].items()]
    return ListaAbbonamentiOutput(
        nota=_ABB["_nota"],
        piani=piani,
        pacchetti_crediti=_CREDITI["pacchetti"],
        valore_credito_eur=float(_CREDITI["valore_credito_eur"]),
        consulenza_umana=_CATALOGO["consulenza_umana"],
        trace={"fonte": "catalogo_documenti.json", "n_piani": len(piani)},
    )


# -------------------------------------------------------------- listino ----

class SchedaListinoInput(BaseModel):
    prodotto: str = Field(..., description=f"Id prodotto dal catalogo. Disponibili: {list(_TIPI.keys())}.")


class SchedaListinoOutput(BaseModel):
    prodotto: str
    label: str
    prodotto_commerciale: str | None = None  # FIX-3 task #8: esposto per evitare ambiguità label/tier
    argomenti: list[str] = []  # task 8c: temi/argomenti coperti dal servizio (faccia A). Opzionale.
    ambito: str
    strato: str
    modello_prezzo: str
    prezzo_listino_eur: float | None
    costo_crediti: int | None
    success_fee_pct: float | None
    prezzo_per_piano: dict
    note_acquisto: str
    da_validare: bool
    avvertenze: list[str]
    trace: dict


def scheda_listino(inp: SchedaListinoInput) -> SchedaListinoOutput:
    if inp.prodotto not in _TIPI:
        return SchedaListinoOutput(
            prodotto=inp.prodotto, label="", ambito="", strato="", modello_prezzo="",
            prezzo_listino_eur=None, costo_crediti=None, success_fee_pct=None, prezzo_per_piano={},
            note_acquisto="", da_validare=False,
            avvertenze=[f"Prodotto '{inp.prodotto}' non presente a catalogo. Disponibili: {list(_TIPI.keys())}."],
            trace={"fonte": "catalogo_documenti.json"})

    t = _TIPI[inp.prodotto]
    strato = t.get("strato", "")
    prezzo = t.get("prezzo_documento_eur")
    costo_cr = t.get("costo_crediti")
    success_fee = t.get("success_fee_pct")
    avvertenze: list[str] = []
    prezzo_per_piano: dict = {}

    if strato == "retainer":
        note = (f"Servizio in abbonamento (Retainer): canone {prezzo:.0f}€/mese"
                + (f" + {success_fee:.0f}% success fee sul risultato (es. Δ RevPAR)." if success_fee else ".")
                + " Richiede misurazione continua; gradino sopra al Boost one-shot.")
    elif strato in ("servizio", "tappa"):
        # FIX-1 task #8: lo strato 'tappa' (componente di percorso Boost) eredita
        # lo stesso modello commerciale dei Servizio: pagato a progetto, mai a crediti,
        # con sconto piano L3 per gli abbonati (Pro -10%, Business -20%).
        if strato == "servizio":
            note = ("Boost (strato Servizio): prezzo a progetto, NON acquistabile a crediti. "
                    "Gli abbonati ottengono lo sconto del loro piano.")
        else:
            note = ("Tappa di percorso Boost: prezzo a progetto, NON acquistabile a crediti. "
                    "Gli abbonati ottengono lo sconto del loro piano (L3). "
                    "La somma delle tappe è inferiore al Boost destinazione (sconto-percorso).")
        for pid, p in _ABB["piani"].items():
            sconto = p.get("sconto_boost_pct", 0)
            prezzo_per_piano[pid] = round(prezzo * (1 - sconto / 100), 2) if prezzo is not None else None
    elif strato == "consumo":
        # Check express: pagato a crediti; serve almeno Pro per eseguire
        note = (f"Check express (strato Consumo): costa {costo_cr} crediti. "
                "Eseguibile solo con piano Pro o Business (l'account Free non esegue servizi).")
        for pid, p in _ABB["piani"].items():
            if not p.get("servizi_eseguibili"):
                prezzo_per_piano[pid] = "non disponibile (serve Pro)"
            else:
                prezzo_per_piano[pid] = f"{costo_cr} crediti"
    else:
        note = "Strato non standard."

    if t.get("_da_validare") or _CATALOGO.get("_da_validare"):
        avvertenze.append("Prezzo marcato _da_validare: confermare con il listino ufficiale K2-AI.")

    return SchedaListinoOutput(
        prodotto=inp.prodotto, label=t.get("label", ""),
        prodotto_commerciale=t.get("prodotto_commerciale"),
        argomenti=t.get("argomenti", []),
        ambito=t.get("ambito", ""),
        strato=strato, modello_prezzo=t.get("modello_prezzo", ""),
        prezzo_listino_eur=float(prezzo) if prezzo is not None else None,
        costo_crediti=int(costo_cr) if costo_cr is not None else None,
        success_fee_pct=float(success_fee) if success_fee is not None else None,
        prezzo_per_piano=prezzo_per_piano, note_acquisto=note,
        da_validare=bool(t.get("_da_validare") or _CATALOGO.get("_da_validare")),
        avvertenze=avvertenze,
        trace={"fonte": "catalogo_documenti.json", "tier": t.get("tier", "")},
    )


# ------------------------------------------------- L2-Inattività crediti ----
# MASTERPLAN-K2AI v2.4 §3.6 / D-013: i crediti NON scadono per scadenza fissa,
# decadono solo dopo `inattivita_max_mesi` mesi di inattività totale (oggi: 12).
# Funzione PURA (§12.19): nessun datetime.now interno, nessuno stato persistente.

def _add_months(d: date, months: int) -> date:
    """Aggiunge N mesi a una data gestendo l'overflow di fine mese
    (es. 31 gennaio + 1 mese = 28/29 febbraio)."""
    month = d.month + months
    year = d.year + (month - 1) // 12
    month = ((month - 1) % 12) + 1
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(d.day, last_day))


class StatusCreditiInput(BaseModel):
    """Input per crediti_attivi: verifica L2-Inattività dei crediti."""
    data_ultimo_movimento: date = Field(
        ...,
        description="Data dell'ultima attività del cliente (acquisto, utilizzo, abbonamento attivo). "
                    "Riferimento per il calcolo della decadenza.")
    oggi: date = Field(
        ...,
        description="Data corrente per il calcolo. Input esplicito per garantire determinismo "
                    "(no datetime.now interno, §12.19).")


class StatusCreditiOutput(BaseModel):
    """Esito del check L2-Inattività sui crediti."""
    attivi: bool = Field(..., description="True se i crediti sono ancora validi, False se decaduti per inattività.")
    data_decadenza: date = Field(..., description="Data in cui i crediti decadono se l'inattività continua.")
    giorni_alla_decadenza: int = Field(..., description="Giorni residui prima della decadenza. Negativo se già decaduti.")
    inattivita_max_mesi: int = Field(..., description="Parametro letto dal catalogo (oggi: 12). Esposto per tracciabilità.")
    motivazione: str = Field(..., description="Testo descrittivo per asseverazione documentale.")


# --------------------------------------------------------- percorsi Boost ----
# Task #8 — Modello 1 "Boost-a-percorsi": un percorso è la sequenza ordinata
# di tappe (Check d'ingresso + tappe intermedie + tappa finale) che porta a un
# Boost destinazione. La somma delle tappe < destinazione (sconto-percorso).
# Funzioni pure (§12.19): leggono solo il catalogo statico, nessuno stato.


class ListaPercorsiInput(BaseModel):
    pass


class ListaPercorsiOutput(BaseModel):
    nota: str
    percorsi: list[dict]
    trace: dict


def lista_percorsi(inp: ListaPercorsiInput | None = None) -> ListaPercorsiOutput:
    """Elenco compatto dei percorsi Boost: id, destinazione, sconto, n. tappe."""
    out: list[dict] = []
    for pid, perc in _PERCORSI.items():
        dest_id = perc["destinazione_id"]
        dest = _TIPI.get(dest_id, {})
        out.append({
            "id": pid,
            "destinazione_id": dest_id,
            "destinazione_label": dest.get("label", ""),
            "destinazione_eur": perc["destinazione_eur"],
            "sconto_percorso_pct": perc["sconto_percorso_pct"],
            "somma_tappe_attesa_eur": perc["somma_tappe_attesa_eur"],
            "n_tappe": len(perc["tappe"]),
        })
    return ListaPercorsiOutput(
        nota=("Percorso Boost: sequenza di tappe (Check d'ingresso + intermedie + finale) "
              "che porta a un Boost destinazione. Somma tappe < destinazione (sconto-percorso). "
              "Tappe scontate L3 per gli abbonati (Pro -10%, Business -20%)."),
        percorsi=out,
        trace={"fonte": "catalogo_documenti.json", "n_percorsi": len(out)},
    )


class SchedaPercorsoInput(BaseModel):
    percorso_id: str = Field(..., description=f"Id percorso. Disponibili: {list(_PERCORSI.keys())}.")


class SchedaPercorsoOutput(BaseModel):
    percorso_id: str
    destinazione_id: str | None
    destinazione_label: str
    destinazione_eur: float | None
    sconto_percorso_pct: float | None
    somma_tappe_attesa_eur: float | None
    destinazione_prezzo_per_piano: dict
    tappe: list[dict]
    avvertenze: list[str]
    trace: dict


def scheda_percorso(inp: SchedaPercorsoInput) -> SchedaPercorsoOutput:
    """Dato un percorso, ritorna composizione completa con prezzi per piano risolti.

    Ogni tappa è risolta sul catalogo `tipi` e arricchita con label, prezzo_listino_eur
    e prezzo_per_piano (sconto L3 abbonati). I percorsi sono read-only sul catalogo.
    """
    if inp.percorso_id not in _PERCORSI:
        return SchedaPercorsoOutput(
            percorso_id=inp.percorso_id, destinazione_id=None, destinazione_label="",
            destinazione_eur=None, sconto_percorso_pct=None, somma_tappe_attesa_eur=None,
            destinazione_prezzo_per_piano={}, tappe=[],
            avvertenze=[f"Percorso '{inp.percorso_id}' non presente. Disponibili: {list(_PERCORSI.keys())}."],
            trace={"fonte": "catalogo_documenti.json"},
        )
    perc = _PERCORSI[inp.percorso_id]
    dest_id = perc["destinazione_id"]
    dest_node = _TIPI.get(dest_id, {})

    def _prezzo_per_piano(prezzo: float | None) -> dict:
        if prezzo is None:
            return {}
        out: dict[str, float] = {}
        for pid, p in _ABB["piani"].items():
            sconto = p.get("sconto_boost_pct", 0)
            out[pid] = round(prezzo * (1 - sconto / 100), 2)
        return out

    tappe_out: list[dict] = []
    avvertenze: list[str] = []
    for t in perc["tappe"]:
        tid = t["id_tipo"]
        node = _TIPI.get(tid)
        if not node:
            avvertenze.append(f"Tappa ordine {t['ordine']}: id_tipo '{tid}' non trovato nel catalogo.")
            tappe_out.append({"ordine": t["ordine"], "id_tipo": tid, "label": "",
                              "strato": "", "prezzo_listino_eur": None, "prezzo_per_piano": {}})
            continue
        prezzo = node.get("prezzo_documento_eur")
        tappe_out.append({
            "ordine": t["ordine"],
            "id_tipo": tid,
            "label": node.get("label", ""),
            "strato": node.get("strato", ""),
            "prezzo_listino_eur": float(prezzo) if prezzo is not None else None,
            "prezzo_per_piano": _prezzo_per_piano(prezzo),
        })

    dest_prezzo = dest_node.get("prezzo_documento_eur")
    return SchedaPercorsoOutput(
        percorso_id=inp.percorso_id,
        destinazione_id=dest_id,
        destinazione_label=dest_node.get("label", ""),
        destinazione_eur=float(perc["destinazione_eur"]),
        sconto_percorso_pct=float(perc["sconto_percorso_pct"]),
        somma_tappe_attesa_eur=float(perc["somma_tappe_attesa_eur"]),
        destinazione_prezzo_per_piano=_prezzo_per_piano(dest_prezzo),
        tappe=tappe_out,
        avvertenze=avvertenze,
        trace={"fonte": "catalogo_documenti.json", "n_tappe": len(tappe_out)},
    )


def crediti_attivi(inp: StatusCreditiInput) -> StatusCreditiOutput:
    """Verifica se i crediti sono ancora attivi secondo la leva L2-Inattività.

    Regola (MASTERPLAN v2.4 §3.6, D-013): i crediti decadono dopo
    `inattivita_max_mesi` mesi di inattività totale. Parametro letto dal
    catalogo: data['crediti']['inattivita_max_mesi'] (oggi: 12).
    Funzione pura (§12.19): no datetime.now interno, no stato persistente.
    """
    mesi = _CREDITI["inattivita_max_mesi"]
    data_decadenza = _add_months(inp.data_ultimo_movimento, mesi)
    giorni_alla_decadenza = (data_decadenza - inp.oggi).days
    attivi = inp.oggi < data_decadenza
    if attivi:
        motivazione = (
            f"Crediti attivi. Ultima attività il {inp.data_ultimo_movimento.isoformat()}. "
            f"Decadranno il {data_decadenza.isoformat()} se l'inattività continua "
            f"({giorni_alla_decadenza} giorni residui). Parametro L2: {mesi} mesi.")
    else:
        motivazione = (
            f"Crediti decaduti per inattività. Ultima attività il {inp.data_ultimo_movimento.isoformat()}. "
            f"Decadenza il {data_decadenza.isoformat()} ({abs(giorni_alla_decadenza)} giorni fa). "
            f"Parametro L2: {mesi} mesi.")
    return StatusCreditiOutput(
        attivi=attivi,
        data_decadenza=data_decadenza,
        giorni_alla_decadenza=giorni_alla_decadenza,
        inattivita_max_mesi=mesi,
        motivazione=motivazione,
    )
