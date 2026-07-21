"""Reasoning Engine — catene causa-effetto (spec §1-§2).

Un consulente non elenca azioni: spiega PERCHÉ succede, quali cause, come sono
collegate, quali effetti producono, come risolverle. Questo motore costruisce
catene causali strutturate a 6 fasi:

    OSSERVAZIONE → CAUSE → CONSEGUENZE → PRIORITÀ → INTERVENTO → RISULTATO ATTESO

Le catene nascono a REGOLE dagli insight quantitativi (insight.py): ogni nodo
porta le sue evidenze (id degli insight / campi input) e la catena la sua
confidence. Niente LLM: se i dati per una catena non ci sono, la catena non
esiste — mai narrativa inventata.

Generico: `Chain`/`node` sono riusabili per qualunque dominio; qui le regole
finance/liquidità. Altri domini = nuove funzioni build_*_chains.
"""

from __future__ import annotations

from typing import Optional

FASI = ("osservazione", "cause", "conseguenze", "priorita", "intervento",
        "risultato_atteso")


def node(fase: str, testo: str, evidenze: list[str] | None = None) -> dict:
    assert fase in FASI, fase
    return {"fase": fase, "testo": testo, "evidenze": list(evidenze or [])}


def chain(id_: str, titolo: str, nodi: list[dict], priorita: str = "alta",
          confidence: str = "A") -> dict:
    return {"id": id_, "titolo": titolo, "catena": nodi, "priorita": priorita,
            "confidence": confidence}


def _by_id(insights: list[dict]) -> dict:
    return {i["id"]: i for i in insights}


def _fmt(v: Optional[float], unit: str = "") -> str:
    if v is None:
        return ""
    s = f"{v:,.0f}".replace(",", ".")
    return f"{s} {unit}".strip()


def build_finance_chains(insights: list[dict], inputs: dict) -> list[dict]:
    """Catene causali di tesoreria/liquidità dagli insight calcolati."""
    ins = _by_id(insights)
    chains: list[dict] = []

    saldo = ins.get("cash.saldo_mensile")
    costo = ins.get("debt.costo_scoperto")
    capitale = ins.get("wc.capitale_in_crediti")
    conc = ins.get("risk.concentrazione")
    peso = ins.get("debt.peso_interessi")

    # ── Catena 1: la spirale dello scoperto (il caso-tipo della spec §2) ──────
    if saldo and saldo["valore"] < 0 and (capitale or costo):
        cause_txt, cause_ev = [], []
        if capitale:
            cause_txt.append(f"incassi lenti che immobilizzano ~{_fmt(capitale['valore'], '€')} "
                             "nei crediti")
            cause_ev.append(capitale["id"])
        cause_txt.append(f"uscite mensili superiori agli incassi "
                         f"({_fmt(abs(saldo['valore']), '€/mese')} di deficit)")
        cause_ev.append(saldo["id"])
        cause_txt.append("assenza di un forecast: il fabbisogno si scopre quando è già cassa")

        conseg_txt = ["pressione continua sulla cassa e ricorso permanente allo scoperto"]
        conseg_ev = []
        if costo:
            conseg_txt.append(f"interessi che costano ~{costo['valore']:.0f}%/anno "
                              "sull'esposizione")
            conseg_ev.append(costo["id"])
        if peso:
            conseg_txt.append(f"~{peso['valore']:.1f}% del fatturato assorbito dagli oneri "
                              "finanziari → meno margine, meno capacità di investimento")
            conseg_ev.append(peso["id"])
        conseg_txt.append("dipendenza crescente dalla banca: ogni rinnovo del fido "
                          "diventa una trattativa al ribasso")

        chains.append(chain(
            "finance.spirale_scoperto", "La spirale dello scoperto",
            [node("osservazione",
                  f"La gestione corrente perde {_fmt(abs(saldo['valore']), '€/mese')} e "
                  "l'azienda vive stabilmente dentro il fido.",
                  [saldo["id"]]),
             node("cause", "; ".join(cause_txt), cause_ev),
             node("conseguenze", "; ".join(conseg_txt), conseg_ev),
             node("priorita",
                  "Massima: il costo del problema cresce ogni mese e riduce le opzioni "
                  "disponibili (chi ha cassa negozia, chi non ne ha subisce)."),
             node("intervento",
                  "Agire sulle CAUSE nell'ordine: accorciare il ciclo di incasso "
                  "(fatturazione immediata, solleciti strutturati, acconti), costruire il "
                  "forecast a 13 settimane per anticipare i buchi, e solo dopo negoziare "
                  "la forma di finanziamento giusta al costo giusto."),
             node("risultato_atteso",
                  "Riduzione strutturale del fabbisogno finanziato, oneri in calo e ritorno "
                  "del margine alla sua funzione: remunerare l'azienda, non la banca.")],
            priorita="alta"))

    # ── Catena 2: concentrazione clienti → fragilità di cassa ────────────────
    if conc and (saldo or capitale):
        ev = [conc["id"]] + ([saldo["id"]] if saldo else [])
        chains.append(chain(
            "finance.concentrazione", "Concentrazione clienti e fragilità di cassa",
            [node("osservazione",
                  f"Il {conc['valore']:.0f}% del fatturato dipende da pochissimi clienti.",
                  [conc["id"]]),
             node("cause",
                  "Portafoglio commerciale sbilanciato; potere negoziale dei grandi "
                  "clienti sui termini di pagamento."),
             node("conseguenze",
                  "Basta il ritardo di UN pagamento per spostare la cassa dell'intero "
                  "mese; i termini li detta il cliente, non l'azienda"
                  + (" — su una cassa già in deficit strutturale" if saldo and
                     saldo["valore"] < 0 else "") + ".",
                  ev),
             node("priorita",
                  "Alta: è un moltiplicatore del rischio di liquidità, non un rischio "
                  "a sé."),
             node("intervento",
                  "Nel breve: presidio dedicato dei crediti verso i top client (date "
                  "certe, sollecito al giorno 1). Nel medio: diversificazione commerciale "
                  "mirata e clausole di pagamento negoziate sui nuovi contratti."),
             node("risultato_atteso",
                  "Cassa meno esposta al comportamento di un singolo cliente; potere "
                  "negoziale riequilibrato.")],
            priorita="alta"))

    return chains


def validate_chain(c: dict) -> list[str]:
    """Controlli di struttura: ≥4 fasi, ordine rispettato, evidenze sull'osservazione."""
    problems = []
    fasi = [n.get("fase") for n in c.get("catena", [])]
    if len(fasi) < 4:
        problems.append("catena troppo corta (<4 fasi)")
    order = [f for f in FASI if f in fasi]
    if fasi != order:
        problems.append("fasi fuori ordine")
    oss = next((n for n in c.get("catena", []) if n.get("fase") == "osservazione"), None)
    if oss is not None and not oss.get("evidenze"):
        problems.append("osservazione senza evidenze")
    return problems
