"""Modalità QUESITO di LegalBoost — parere su un caso/incidente SPECIFICO.

Problema (bug prod, data-breach: il cliente porta un incidente puntuale ma il
report esce come audit-compliance PMI generico a 9 aree, l'80% fuori tema, senza
rispondere alle domande poste): LegalBoost aveva UN solo scheletro fisso (le 9
macro-aree in blueprint.json). Un *quesito puntuale* non aveva un percorso suo.

Fix: quando l'input porta un `quesito` sostanziale (l'incidente/la domanda del
cliente, raccolto in chat e messo nel form), lo scheletro diventa CASE-FIRST —
Fatti → Questioni → Analisi normativa → Rischio → Raccomandazione — con una prima
voce che RISPONDE diretto (scenari A/B/C). Niente `quesito` → comportamento
IDENTICO a prima (audit generale), zero regressione.

Modulo SENZA dipendenze pesanti (nessun import di llm/anthropic) per evitare cicli:
`pipeline` e `llm` importano da qui, non viceversa.
"""
from __future__ import annotations

import copy

LEGAL_SKILL = "flusso-legalboost-pmi"

# Soglia oltre cui un `quesito` è "sostanziale" (un caso vero, non un token vagante
# tipo 'gdpr' che sfugge all'autofill). Sotto → si resta in audit generale.
QUESITO_MIN_LEN = 40


def is_quesito(inputs: dict) -> bool:
    """True se l'input porta un caso/incidente specifico da trattare come quesito."""
    if not isinstance(inputs, dict):
        return False
    q = inputs.get("quesito")
    return isinstance(q, str) and len(q.strip()) >= QUESITO_MIN_LEN


# Scheletro CASE-FIRST. Mantiene ESATTAMENTE la shape delle voci del blueprint
# (ord/id/titolo/pagine/argomenti_obbligatori) → passa L1 (meta-schema) e L2 (linter).
# NB: la PRIMA voce riusa l'id `sintesi_mappa_rischi` e l'ULTIMA `piano_azione_handoff`:
# il render (render_pdf) li aggancia (sezione 01 + heatmap; tabella piano) — riusarli
# tiene il render invariato. Somma pagine.min = 17 ∈ [16,24] (R02). Prima voce = 2 (R05).
QUESITO_VOCI: list[dict] = [
    {"ord": 0, "id": "sintesi_mappa_rischi", "titolo": "Risposta al tuo quesito",
     "pagine": {"min": 2, "max": 2},
     "argomenti_obbligatori": [
         "risposta diretta e sintetica alle domande poste dal cliente (ogni domanda: sì/no motivato)",
         "scenari A/B/C con la condotta consigliata e le condizioni che attivano ciascuno",
         "livello di rischio complessivo del caso in una frase",
         "disclaimer di non-sostituzione della consulenza legale (D-034)"],
     "funzione_psico": "picco d'apertura: il cliente ha SUBITO la risposta alle sue domande"},
    {"ord": 1, "id": "fatti_raccolti", "titolo": "Fatti raccolti e ipotesi",
     "pagine": {"min": 2, "max": 2},
     "argomenti_obbligatori": [
         "elenco puntuale dei FATTI effettivamente dichiarati dal cliente",
         "distinzione esplicita tra FATTO accertato e IPOTESI da verificare",
         "dati rilevanti NON forniti, segnalati come 'da acquisire' (mai dati inventati)"],
     "funzione_psico": "trasparenza: il cliente vede su COSA si basa il parere"},
    {"ord": 2, "id": "questioni_giuridiche", "titolo": "Questioni giuridiche",
     "pagine": {"min": 2, "max": 2},
     "argomenti_obbligatori": [
         "le domande giuridiche che il caso concreto solleva",
         "qualificazione giuridica della fattispecie",
         "norme e istituti potenzialmente applicabili (indicati per nome)"]},
    {"ord": 3, "id": "analisi_normativa", "titolo": "Analisi normativa",
     "pagine": {"min": 3, "max": 4},
     "argomenti_obbligatori": [
         "analisi degli articoli/norme pertinenti richiamati dai FATTI",
         "presupposti, soglie e termini di applicazione al caso",
         "orientamenti, linee guida o prassi rilevanti",
         "riferimenti normativi ancorati (via MCP; norme UE via EUR-Lex)"]},
    {"ord": 4, "id": "valutazione_rischio", "titolo": "Valutazione del rischio",
     "pagine": {"min": 2, "max": 3},
     "argomenti_obbligatori": [
         "probabilità e gravità del rischio nel caso concreto (banda qualitativa)",
         "fattori attenuanti e aggravanti tratti dai FATTI",
         "esposizione sanzionatoria/economica indicativa, etichettata come stima"]},
    {"ord": 5, "id": "raccomandazione_operativa", "titolo": "Raccomandazione operativa",
     "pagine": {"min": 2, "max": 3},
     "argomenti_obbligatori": [
         "cosa fare ORA, in ordine di priorità, coerente con gli scenari A/B/C",
         "tempistiche e termini di legge applicabili al caso",
         "documentazione da produrre e conservare"]},
    {"ord": 6, "id": "adempimenti_documentali", "titolo": "Adempimenti e documentazione",
     "pagine": {"min": 2, "max": 2},
     "argomenti_obbligatori": [
         "tracciabilità e registrazione dell'evento/della decisione",
         "accountability: come provare la diligenza adottata",
         "procedura o modello interno da adottare per il futuro"]},
    {"ord": 7, "id": "piano_azione_handoff", "titolo": "Piano d'azione e quando serve l'avvocato",
     "pagine": {"min": 2, "max": 2},
     "argomenti_obbligatori": [
         "to-do prioritizzata con tempistiche",
         "quando e perché coinvolgere l'avvocato/DPO (handoff sui punti a rischio)",
         "modalità di ingaggio del professionista partner",
         "disclaimer di chiusura (D-034)"],
     "funzione_psico": "chiusura forte (peak-end) + CTA/handoff onesto",
     "stato": "voce-CTA del funnel"},
]

# Voci a cui ha senso agganciare i riferimenti normativi verificati (schema `norme_citate`).
NORME_VOCI_QUESITO = ("analisi_normativa", "questioni_giuridiche")


def maybe_quesito(skill: str, blueprint: dict | None, inputs: dict) -> dict | None:
    """Se lo skill è LegalBoost e c'è un quesito sostanziale → ritorna una COPIA del
    blueprint con lo scheletro case-first. Altrimenti ritorna il blueprint invariato.

    Deepcopy OBBLIGATORIO: `assets.load_blueprint` è lru_cached → mutare il dict
    condiviso inquinerebbe le richieste successive (audit userebbe le voci quesito)."""
    if skill != LEGAL_SKILL or not blueprint or not is_quesito(inputs):
        return blueprint
    bp = copy.deepcopy(blueprint)
    bp["voci"] = copy.deepcopy(QUESITO_VOCI)
    bp["descrizione"] = (
        "Primo parere legale su un QUESITO/INCIDENTE specifico portato dal cliente. "
        "Struttura case-first: fatti → questioni → analisi normativa → rischio → "
        "raccomandazione. Orientamento, NON consulenza legale (D-034)."
    )
    return bp


def caso_block(inputs: dict) -> str:
    """Blocco da mettere IN TESTA al prompt di generazione: il caso è il centro del
    documento. Vuoto se non siamo in modalità quesito."""
    if not is_quesito(inputs):
        return ""
    q = (inputs.get("quesito") or "").strip()
    return (
        "CASO / QUESITO DEL CLIENTE — è il CENTRO del documento: OGNI sezione deve servire "
        "a rispondere a QUESTO, non a un audit generico.\n"
        f"«{q}»\n\n"
        "ISTRUZIONI DI CASO:\n"
        "- Rispondi in modo DIRETTO alle domande del cliente (sì/no motivati), poi argomenta.\n"
        "- Analizza SOLO le aree di diritto pertinenti al caso. Un'area non pertinente va "
        "dichiarata 'non pertinente a questo quesito', NON riempita con contenuto generico.\n"
        "- Distingui sempre FATTO (dichiarato dal cliente) da IPOTESI (tua assunzione da "
        "verificare): non trasformare un'assunzione in un fatto.\n\n"
    )


# System prompt per la generazione delle voci in modalità QUESITO. Stesso contratto di
# output di _SYSTEM (JSON {voce_id: testo}), ma centrato sul caso e con la disciplina
# fatto-vs-ipotesi che spegne le allucinazioni di dati aziendali (e-commerce/DPA/registro/
# DPO mai dichiarati → il report li dava per veri).
SYSTEM = (
    "Sei un avvocato d'impresa che redige un PRIMO PARERE LEGALE su un quesito/incidente "
    "specifico portato da una PMI italiana (LegalBoost).\n"
    "OBIETTIVO: rispondere alle domande concrete del cliente sul SUO caso — non produrre un "
    "audit di compliance generico.\n"
    "REGOLE ASSOLUTE:\n"
    "- Il CASO/QUESITO del cliente è il centro: ogni voce serve a rispondere a quello.\n"
    "- NON inventare numeri, articoli di legge o citazioni. I FATTI normativi ti sono forniti "
    "già risolti e VERBATIM; ogni riferimento che citi deve essere tra quelli nei FATTI o una "
    "norma UE arcinota (GDPR/AI Act) indicata per nome.\n"
    "- FATTO vs IPOTESI (vincolante): usa come FATTI SOLO ciò che è nel CASO o nei DATI CLIENTE. "
    "NON asserire caratteristiche dell'azienda non fornite (presenza/assenza di e-commerce, "
    "profilazione, DPA, registro dei trattamenti, DPO, modello 231, marchio, informative): se "
    "un dato non è fornito, o lo OMETTI o lo marchi '(ipotesi da confermare)'. Mai spacciare "
    "un'assunzione per un fatto accertato.\n"
    "- NON trascinare aree non pertinenti (contrattualistica, 231, IP, lavoro, fiscale…) se il "
    "caso non le tocca: se un'area non c'entra, dillo in una riga e passa oltre.\n"
    "- Rispondi alle domande del cliente in modo diretto e motivato, con scenari A/B/C dove la "
    "condotta dipende da condizioni (es. soglie di rischio, termini).\n"
    "- Tono autorevole e chiaro per un titolare d'impresa; è orientamento, NON consulenza "
    "legale (D-034).\n"
    "- LUNGHEZZA: ~180-260 parole per voce, su più paragrafi. Prosa densa, niente riempitivo.\n"
    "- Restituisci SOLO un oggetto JSON {\"<voce_id>\": \"<testo>\", ...}, una chiave per voce richiesta."
)

# Frammento da APPENDERE al system di generate_structured_meta in modalità quesito:
# lo score e la mappa rischi devono riflettere il CASO, non un audit di 8 aree.
META_HINT = (
    "\nCONTESTO QUESITO: si tratta di un parere su un caso specifico. Lo `score` esprime la "
    "gravità/rischio del caso (0=rischio massimo, 100=nessun rischio); la `mappa_rischi` "
    "elenca SOLO le aree effettivamente toccate dal caso, non un audit completo."
)


def piano_azione(voci_meta: dict | None, voci: list[dict], inputs: dict | None = None) -> list[dict]:
    """Deriva `piano_azione` dalle azioni realmente prodotte per le voci (meta strutturato),
    in ordine di rilevanza (ordine voci). Sostituisce l'azione HARD-CODED che LegalBoost
    metteva sempre ('Adeguare le condizioni generali artt. 1341-1342') anche su casi che
    non c'entravano nulla coi contratti (es. un data breach). Vale per ENTRAMBE le modalità.

    handoff_avvocato = True se la voce da cui viene l'azione ha un rischio `serve_avvocato`.
    """
    items: list[dict] = []
    seen: set[str] = set()
    vm = voci_meta or {}
    for v in voci or []:
        if len(items) >= 8:
            break
        vid = v.get("id")
        meta = vm.get(vid) or {}
        serve = any(bool(r.get("serve_avvocato")) for r in meta.get("rischi", [])
                    if isinstance(r, dict))
        for a in meta.get("azioni", []) or []:
            azione = str(a).strip()
            key = azione.lower()
            if not azione or key in seen:
                continue
            seen.add(key)
            items.append({"priorita": len(items) + 1, "azione": azione[:300],
                          "handoff_avvocato": serve})
            if len(items) >= 8:
                break
    if not items:
        # Offline/demo o meta assente: fallback NEUTRO (mai l'azione contrattuale a caso).
        items = [{"priorita": 1,
                  "azione": "Approfondire con un professionista le priorità emerse dall'analisi.",
                  "handoff_avvocato": True}]
    return items
