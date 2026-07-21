"""Alternative strategiche per tipo di proposta — teeth deterministiche della review
'la proposta del cliente è un'ipotesi, non il problema'.

Quando il cliente propone una strategia (aprire una filiale, comprare un concorrente,
investire in IA, assumere, licenziare, lanciare un prodotto, delocalizzare, vendere), il
motore NON deve passare all'implementazione: deve prima VALIDARE l'ipotesi e valutare le
alternative. Questa mappa fornisce, in modo deterministico, il set di alternative concrete
che il consulente DEVE aver considerato prima di raccomandare — così l'evaluation non
dipende dall'estro del modello.

`alternatives_hint(text)` rileva il tipo di proposta dal testo e restituisce un blocco da
iniettare nel system prompt. Ritorna "" se nel testo non c'è una proposta riconosciuta.
"""
from __future__ import annotations

from . import signals

# (keywords che identificano il TIPO di proposta, etichetta, alternative concrete)
_ALTERNATIVES: list[tuple[tuple[str, ...], str, list[str]]] = [
    (("filiale", "succursale", "sede all'estero", "espansione", "espander", "internazionalizz",
      "mercato estero", "mercati esteri", "all'estero", "entrare nel mercato", "market entry",
      "germania", "francia", "spagna", "usa", "stati uniti", "estero"),
     "espansione / nuovo mercato",
     ["distributori o agenti locali", "partnership commerciale sul territorio",
      "export diretto senza struttura fissa", "e-commerce cross-border",
      "acquisizione di un operatore già presente", "crescere di più nel mercato attuale",
      "nessuna espansione ora (consolidare)"]),
    (("intelligenza artificiale", "ia ", " ia", "machine learning", "piattaforma ia",
      "piattaforma di intelligenza", "software proprietario", "sviluppare un software",
      "costruire una piattaforma", "modello ai", "un'ai", "una ai"),
     "investimento tecnologico / IA",
     ["soluzioni SaaS già pronte sul mercato", "partnership tecnologica",
      "automazioni mirate (no-code / RPA) sui processi che pesano",
      "outsourcing dello sviluppo", "un pilot piccolo prima del full-build",
      "nessun investimento (il problema si risolve a monte, nell'organizzazione o nei dati)"]),
    (("acquisizione", "acquistare un", "acquisire un", "comprare un", "rilevare",
      "concorrente", "azienda target", "fusione", "m&a"),
     "acquisizione (M&A)",
     ["crescita organica interna", "partnership o joint venture",
      "accordo commerciale/distributivo", "acqui-hire mirato solo delle competenze",
      "nessuna acquisizione (allocare il capitale su altro con miglior ritorno)"]),
    (("assumere", "assunzion", "nuove risorse", "nuovo personale", "reclutare", "recruit",
      "ampliare l'organico", "più personale"),
     "assunzioni",
     ["recuperare capacità dai processi esistenti (colli di bottiglia, riunioni)",
      "esternalizzare le attività non-core", "automatizzare le attività ripetitive",
      "formazione/riqualificazione interna", "assumere SOLO il ruolo davvero critico",
      "nessuna assunzione ora"]),
    (("nuovo prodotto", "lanciare un prodotto", "lancio del prodotto", "nuova linea",
      "nuovo servizio", "lanciare un servizio"),
     "nuovo prodotto / servizio",
     ["estendere o migliorare un prodotto già esistente", "un MVP / test di mercato prima del lancio",
      "partnership o white-label", "concentrarsi sul core attuale", "nessun lancio ora"]),
    (("licenzia", "far uscire", "mandare via", "allontanare il"),
     "uscita di una persona",
     ["piano di miglioramento (PIP) con obiettivi chiari", "ricollocazione su un altro ruolo",
      "ridurre il rischio-chiave (documentare, formare un backup)",
      "mediare il conflitto sottostante", "uscita concordata gestita",
      "mantenere la persona ma cambiare il modo di gestirla"]),
    (("delocalizz", "spostare la produzione", "trasferire la produzione", "offshoring",
      "produrre all'estero"),
     "delocalizzazione",
     ["efficientare il sito produttivo attuale", "automazione della produzione",
      "nearshoring parziale", "fornitori esterni selezionati", "nessuna delocalizzazione"]),
    (("vendere l'azienda", "vendere l azienda", "cedere l'azienda", "vendere l'attività",
      "cessione dell'azienda", "vendere la società", "vendere la mia azienda"),
     "cessione / vendita dell'azienda",
     ["aprire il capitale a un socio/investitore", "passaggio generazionale",
      "management buyout", "risanare e rilanciare prima di vendere", "non vendere ora"]),
]


def _detect(text: str) -> tuple[str, list[str]] | None:
    t = " " + (text or "").lower() + " "
    for keys, label, alts in _ALTERNATIVES:
        if any(k in t for k in keys):
            return label, alts
    return None


def alternatives_hint(text: str) -> str:
    """Blocco da iniettare nel system prompt quando il cliente propone una strategia.
    Elenca le alternative concrete che il consulente DEVE valutare prima di raccomandare.
    Ritorna "" se non c'è una proposta riconosciuta o se è una pura domanda tecnica."""
    if not text or not signals.proposes_strategy(text):
        return ""
    det = _detect(text)
    if not det:
        return ""
    label, alts = det
    voci = "; ".join(alts)
    return (
        f"\nVALUTAZIONE STRATEGICA (il cliente propone: {label}). La proposta è un'IPOTESI da "
        "validare, NON il problema da risolvere: NON passare all'implementazione. Prima (1) "
        "chiedi/deduci PERCHÉ ritiene sia la scelta giusta e quale problema vuole davvero "
        "risolvere; (2) verifica se il problema è reale; (3) VALUTA ESPLICITAMENTE almeno "
        f"alcune di queste alternative — {voci}; e l'opzione «non fare nulla»; (4) solo dopo "
        "prendi posizione (la farei / non la farei / rimanderei / c'è una scelta migliore), "
        "motivandola. Gli aspetti tecnici (fiscali, normativi, operativi) vengono DOPO, solo "
        "se la direzione scelta lo richiede.\n"
    )
