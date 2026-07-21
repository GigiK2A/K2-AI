"""Report planner + pacchetto consulenziale operations (spec §6-§10, §14).

Il report non deve essere un template fisso KPI-finanza-cliente-processi-crescita:
la struttura dipende dal problema reale. Questo modulo:

1. `classify_problem(inputs)` — riconosce il tipo di caso dai dati/testo forniti
   (deterministico, nessuna chiamata LLM);
2. `build_pack(skill, inputs, deliverable)` — per un caso "gestione/riorganizzazione
   commesse" costruisce le sezioni consulenziali obbligatorie: AS-IS, criticità,
   TO-BE, stati standard, RACI, governance, SLA, requisiti funzionali, opzioni
   tecnologiche comparate, piano 30-60-90, dati da raccogliere.

Regole ferree (anti-allucinazione):
- l'AS-IS usa SOLO ciò che l'utente ha fornito (testo/numeri degli input);
- le criticità derivano dai KPI reali del deliverable, con evidenza e confidence A;
- stati/RACI/governance/SLA/opzioni sono PROPOSTE, marcate come tali (§10:
  "Soglia iniziale proposta, da validare dopo 30 giorni di misurazione");
- nessun costo/tempo inventato nelle opzioni tecnologiche; nessun nome di persona;
- ogni affermazione porta `confidence` A/B/C (§14) e le sue evidenze.

Le costanti (stati, attività RACI, ruoli, checklist) sono condivise col workbook
Excel (app/xlsx.py le importa) → PDF ed Excel coerenti per costruzione.
"""

from __future__ import annotations

import re
from typing import Any, Optional

from . import normalize as NORM

# ── Costanti condivise PDF/Excel (fonte unica) ────────────────────────────────
STATI_STANDARD = [
    ("Aperta", "Commessa registrata, in attesa di pianificazione",
     "Ordine/contratto ricevuto", "Piano e owner assegnati"),
    ("In pianificazione", "Scope, tempi e risorse in definizione",
     "Owner assegnato", "Piano approvato dalla direzione"),
    ("In corso", "Lavorazione attiva",
     "Piano approvato", "Attività tecniche completate"),
    ("In verifica", "Controllo tecnico/qualità della consegna",
     "Attività completate", "Verifica superata"),
    ("Bloccata", "Avanzamento fermo: motivazione e sblocco OBBLIGATORI",
     "Motivazione registrata nel Registro blocchi", "Blocco risolto → torna In corso"),
    ("In consegna", "Consegna/installazione presso il cliente",
     "Verifica superata", "Accettazione del cliente"),
    ("Chiusa", "Consegnata e accettata; pronta per fatturazione",
     "Accettazione cliente", "Fattura emessa"),
    ("Annullata", "Interrotta definitivamente (motivazione obbligatoria)",
     "Decisione della direzione", "—"),
]

RACI_RUOLI = ["Direzione", "Resp. operativo", "Project Manager",
              "Resp. tecnico", "Amministrazione", "Operatore assegnato"]

# Attività → assegnazioni proposte (R/A/C/I per ruolo, stesso ordine di RACI_RUOLI).
RACI_MATRICE = [
    ("Apertura commessa",      ["A", "R", "C", "", "I", ""]),
    ("Pianificazione",         ["I", "A", "R", "C", "", "I"]),
    ("Assegnazione task",      ["", "A", "R", "C", "", "I"]),
    ("Aggiornamento stato",    ["I", "A", "R", "", "", "C"]),
    ("Verifica tecnica",       ["", "I", "A", "R", "", "C"]),
    ("Gestione blocchi",       ["I", "A", "R", "C", "", "C"]),
    ("Comunicazione cliente",  ["A", "C", "R", "", "", ""]),
    ("Approvazione consegna",  ["A", "C", "R", "C", "", ""]),
    ("Chiusura",               ["I", "A", "R", "", "C", ""]),
    ("Fatturazione",           ["A", "I", "C", "", "R", ""]),
]
RACI_ATTIVITA = [r[0] for r in RACI_MATRICE]

CHECKLIST_FASI = [
    ("Apertura", ["Anagrafica commessa completa", "Contratto/ordine archiviato",
                  "Owner unico assegnato", "Priorità assegnata"]),
    ("Pianificazione", ["Scope e deliverable definiti", "Milestone con date",
                        "Risorse e carichi verificati", "Rischi principali annotati"]),
    ("Esecuzione", ["Stato aggiornato (cadenza definita)", "Blocchi registrati con motivazione",
                    "Data prossima azione sempre presente"]),
    ("Verifica", ["Checklist tecnica superata", "Non conformità registrate"]),
    ("Chiusura", ["Accettazione cliente archiviata", "Consuntivo ore/costi compilato",
                  "Fattura emessa", "Lesson learned annotate"]),
]

SOGLIA_LABEL = "Soglia iniziale proposta, da validare dopo 30 giorni di misurazione."

# ── Classificazione del problema ──────────────────────────────────────────────
_OPERATIONS_HINTS = (
    "commess", "cantier", "gestione progetti", "project manager", " pm ",
    "avanzamento", "riorganizz", "processi", "workflow", "blocc", "ritard",
    "gestionale", "attività aperte", "task", "consegn", "pianificazion",
)

_FINANCE_HINTS = (
    "liquidit", "cassa", "scoperto", "fido", "incass", "dso", "tesoreria",
    "interessi", "banca", "pagament", "credit", "fattur", "insolut", "anticipo",
    "cash flow", "flussi di cassa", "circolante",
)


def _free_text(inputs: dict) -> str:
    """Concatena i campi testuali liberi degli input (il 'racconto' dell'utente)."""
    parts: list[str] = []
    for k, v in (inputs or {}).items():
        v = NORM.unwrap_value(v)
        if isinstance(v, str) and len(v.strip()) >= 12 and k not in ("mese", "azienda",
                                                                     "ragione_sociale"):
            parts.append(v.strip())
    return " \n".join(parts)


def classify_problem(inputs: dict, skill: str = "") -> Optional[str]:
    """Tipo di problema dal testo/dati forniti. Riconosce 'operations_commesse' e
    'finanza_liquidita'; None = nessun pacchetto extra (il report resta com'è)."""
    text = _free_text(inputs).lower()
    ops_hits = sum(1 for h in _OPERATIONS_HINTS if h in text) if text else 0
    fin_hits = sum(1 for h in _FINANCE_HINTS if h in text) if text else 0
    # segnali strutturati contano quanto il testo: dati di tesoreria forniti = caso finance
    from .insight import Facts
    facts = Facts(inputs)
    if facts.has("incassi_mese", "uscite_mese") or facts.has("scoperto"):
        fin_hits += 2
    if fin_hits >= 2 and fin_hits >= ops_hits:
        return "finanza_liquidita"
    if ops_hits >= 2:
        return "operations_commesse"
    return None


# ── Estrazione AS-IS dai soli dati forniti ────────────────────────────────────
_TOOL_HINTS = ("gestionale", "excel", "whatsapp", "email", "erp", "crm",
               "fogli", "sheet", "carta", "telefono", "outlook", "teams")


def _as_is_from_inputs(inputs: dict) -> dict:
    """Fotografia del modello operativo attuale con SOLO ciò che l'utente ha detto."""
    text = _free_text(inputs)
    lowered = text.lower()
    strumenti = sorted({h.capitalize() for h in _TOOL_HINTS if h in lowered})
    numeri = {}
    for k in ("progetti_in_corso", "progetti_in_ritardo", "commesse_attive",
              "attivita_aperte", "project_manager", "pm_totali", "ore_lavorate",
              "ore_fatturabili", "clienti_attivi"):
        v = NORM.unwrap_value(inputs.get(k))
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            numeri[k] = v
    out: dict[str, Any] = {
        "titolo": "Processo AS-IS — come lavora oggi l'azienda",
        "confidence": "A" if (strumenti or numeri) else "C",
        "evidenze": [],
    }
    if strumenti:
        out["strumenti_in_uso"] = strumenti
        out["evidenze"].append("Strumenti citati direttamente nel racconto del cliente")
    if numeri:
        out["dati_dichiarati"] = {k.replace("_", " "): v for k, v in numeri.items()}
        out["evidenze"].append("Valori numerici forniti nel form/conversazione")
    if text:
        out["sintesi_dal_racconto"] = text[:900]
    if not (strumenti or numeri or text):
        out["nota"] = "Dati non disponibili: da raccogliere nel primo incontro operativo."
    return out


def _criticita_from_kpis(deliverable: dict) -> list[dict]:
    """Criticità ancorate ai KPI REALI del deliverable (confidence A, con evidenza)."""
    from .quality_gate import extract_kpis
    out = []
    for k in extract_kpis(deliverable):
        if k["semaforo"] in ("rosso", "giallo") and k["valore"] is not None:
            unita = k["unita"] or ""
            out.append({
                "criticita": f"{k['nome']}: {NORM.to_text(k['valore'])}{unita}"
                             + (f" (target {NORM.to_text(k['target'])}{unita})"
                                if k["target"] is not None else ""),
                "gravita": "alta" if k["semaforo"] == "rosso" else "media",
                "confidence": "A",
                "evidenze": [f"KPI '{k['nome']}' calcolato dai dati operativi forniti"
                             + (f" — sezione {k['sezione']}" if k["sezione"] else "")],
            })
    return out


def _dati_da_raccogliere(inputs: dict) -> list[str]:
    """Elenco onesto dei dati operativi NON forniti (mai riempiti con zeri)."""
    attesi = {
        "progetti_in_corso": "numero di commesse attive",
        "progetti_in_ritardo": "commesse in ritardo",
        "ore_fatturabili": "ore fatturabili del periodo",
        "ore_lavorate": "ore lavorate del periodo",
        "clienti_attivi": "clienti attivi",
        "crediti_clienti": "crediti verso clienti (per DSO)",
        "cash_flow_mese": "cash flow del mese",
    }
    out = []
    for k, label in attesi.items():
        v = NORM.unwrap_value((inputs or {}).get(k))
        if not isinstance(v, (int, float)) or isinstance(v, bool):
            out.append(label.capitalize())
    out.append("Storico mensile degli ultimi 6-12 mesi (per i trend reali)")
    out.append("Elenco commesse con stato/owner attuale (export dal gestionale)")
    return out


# ── Pacchetto operations ──────────────────────────────────────────────────────
def build_operations_pack(inputs: dict, deliverable: dict) -> dict:
    return {
        "_tipo": "operations_commesse",
        "processo_as_is": _as_is_from_inputs(inputs),
        "criticita_rilevate": _criticita_from_kpis(deliverable),
        "processo_to_be": {
            "titolo": "Processo TO-BE — modello operativo proposto",
            "confidence": "B",
            "evidenze": ["Modello standard di gestione commesse, adattato alle criticità rilevate"],
            "principi": [
                "Repository unico delle commesse: una sola fonte di verità, basta Excel personali",
                "Anagrafica commessa univoca (ID, cliente, owner, stato, priorità)",
                "Stati standard con criteri di ingresso/uscita (vedi Dizionario stati)",
                "Owner unico per commessa: una persona risponde dell'avanzamento",
                "Aggiornamento stato obbligatorio a cadenza fissa, con data prossima azione",
                "Ogni blocco registrato con motivazione e owner dello sblocco",
                "Dashboard direzionale su eccezioni (ritardi/blocchi), non su elenchi",
                "Alert automatici su soglie e riunione operativa basata sulle eccezioni",
            ],
        },
        "stati_commessa": [
            {"stato": s, "definizione": d, "ingresso": i, "uscita": u}
            for s, d, i, u in STATI_STANDARD
        ],
        "matrice_raci": {
            "nota": "Ruoli PROPOSTI (nessun nominativo): validare con l'organigramma reale. "
                    "Una sola A per attività.",
            "ruoli": [f"{r} (proposto)" for r in RACI_RUOLI],
            "attivita": [{"attivita": att, "assegnazioni": dict(zip(RACI_RUOLI, marks))}
                         for att, marks in RACI_MATRICE],
        },
        "governance": {
            "confidence": "B",
            "riunione_operativa": "Settimanale, max 30 minuti, SOLO sulle eccezioni "
                                  "(commesse bloccate/in ritardo), decisioni tracciate",
            "review_direzionale": "Mensile sulla dashboard KPI, con azioni e owner",
            "escalation": "Blocco non risolto entro la soglia → passa al Responsabile "
                          "operativo; oltre → Direzione",
        },
        "sla_interni": {
            "nota": SOGLIA_LABEL,
            "source": "assumption",
            "soglie": [
                {"attivita": "Aggiornamento stato commessa", "soglia_proposta": "ogni 7 giorni"},
                {"attivita": "Presa in carico di un blocco", "soglia_proposta": "48 ore"},
                {"attivita": "Risposta al cliente su avanzamento", "soglia_proposta": "1 giorno lavorativo"},
                {"attivita": "Chiusura amministrativa post-accettazione", "soglia_proposta": "10 giorni"},
            ],
        },
        "requisiti_funzionali": [
            "Anagrafica commessa con campi obbligatori (owner, stato, priorità, prossima azione)",
            "Stati configurabili con transizioni controllate",
            "Registro blocchi con motivazione obbligatoria",
            "Dashboard per direzione (eccezioni e KPI) e per PM (le proprie commesse)",
            "Notifiche su scadenze e soglie SLA",
            "Export dati (per contabilità e reporting)",
            "Permessi per ruolo",
            "API o integrazione col gestionale esistente",
        ],
        "opzioni_tecnologiche": {
            "nota": "Nessun prodotto è prescritto: i marchi sono ESEMPI. La scelta va fatta "
                    "solo dopo la verifica del punto raccomandazione.",
            "opzioni": [
                {"opzione": "A — Potenziare il gestionale interno",
                 "vantaggi": ["Nessuna migrazione dati", "Zero strumenti in più",
                              "Curva di adozione minima"],
                 "svantaggi": ["Dipende dalle capacità/API del gestionale",
                               "Sviluppi interni da manutenere"],
                 "complessita": "bassa-media", "rischio_migrazione": "nullo",
                 "scalabilita": "legata al gestionale"},
                {"opzione": "B — Integrare il gestionale con uno strumento di project management",
                 "vantaggi": ["Funzioni PM mature subito (esempi: Asana, ClickUp, Monday)",
                              "Il gestionale resta la fonte amministrativa"],
                 "svantaggi": ["Due sistemi da tenere allineati",
                               "Costo licenze aggiuntivo", "Integrazione da costruire"],
                 "complessita": "media", "rischio_migrazione": "basso",
                 "scalabilita": "buona"},
                {"opzione": "C — Sostituzione progressiva con piattaforma unica",
                 "vantaggi": ["Una sola fonte di verità nativa", "Processi ridisegnati da zero"],
                 "svantaggi": ["Migrazione dati e ri-formazione di tutti",
                               "Tempi e rischio più alti", "Dipendenza dal nuovo fornitore"],
                 "complessita": "alta", "rischio_migrazione": "alto",
                 "scalabilita": "alta"},
            ],
            "raccomandazione_condizionata":
                "Prima verificare le API e le capacità reali del gestionale interno "
                "(campi commessa, stati, estrazioni): se coprono i requisiti funzionali, "
                "partire dall'opzione A; altrimenti B. L'opzione C solo se A e B falliscono "
                "la verifica, e comunque dopo il pilota.",
        },
        "piano_30_60_90": [
            {"orizzonte": "0-30 giorni",
             "azioni": ["Adottare anagrafica e stati standard sulle commesse attive",
                        "Nominare gli owner e avviare il Registro blocchi",
                        "Verifica tecnica del gestionale (API/campi) per la scelta A/B"]},
            {"orizzonte": "31-60 giorni",
             "azioni": ["Pilota su un sottoinsieme di commesse (un PM, un reparto)",
                        "Prima dashboard direzionale sulle eccezioni",
                        "Misurare le soglie SLA proposte e correggerle sui dati reali"]},
            {"orizzonte": "61-90 giorni",
             "azioni": ["Estensione a tutte le commesse",
                        "Riunione operativa a eccezioni a regime",
                        "Review: KPI prima/dopo e decisione definitiva sullo strumento"]},
        ],
        "dati_da_raccogliere": _dati_da_raccogliere(inputs),
    }


# ── Pacchetto finanza/liquidità: i 4 motori di ragionamento ───────────────────
def _value_sections_finance(insights: list[dict], facts) -> dict:
    """Sezioni §13 dedotte dai DATI (mai testo generico): errori probabili,
    opportunità, decisioni entro 7 giorni, domande per il management."""
    by_id = {i["id"]: i for i in insights}
    errori, opportunita, decisioni, domande = [], [], [], []

    saldo = by_id.get("cash.saldo_mensile")
    costo = by_id.get("debt.costo_scoperto")
    capitale = by_id.get("wc.capitale_in_crediti")
    conc = by_id.get("risk.concentrazione")

    if saldo and saldo["valore"] < 0:
        errori.append("Trattare lo scoperto come 'normalità operativa': con un deficit "
                      "strutturale il fido non è un cuscinetto, è il sintomo.")
        decisioni.append("Decidere CHI è l'owner della cassa (una persona, non 'l'ufficio') "
                         "e avviare il forecast settimanale.")
        domande.append("Sappiamo oggi in quale settimana del prossimo trimestre la cassa "
                       "tocca il punto peggiore?")
    if capitale:
        errori.append("Considerare i crediti 'fatturato fatto': finché non incassati sono "
                      "capitale prestato ai clienti a costo pieno.")
        opportunita.append(f"~{capitale['valore']:,.0f} € recuperabili (in parte) "
                           .replace(",", ".") + "accorciando il ciclo di incasso: è la "
                           "'linea di credito' più economica disponibile.")
        domande.append("Chi sollecita i crediti, con quale cadenza, e dopo quanti giorni "
                       "di ritardo parte la prima azione?")
    if costo:
        errori.append(f"Accettare un costo del debito ~{costo['valore']:.0f}%/anno senza "
                      "confrontare alternative: lo scoperto è la forma più cara.")
        decisioni.append("Chiedere entro 7 giorni due quotazioni alternative (anticipo "
                         "fatture, consolidamento) da confrontare con lo scoperto.")
    if conc:
        opportunita.append("Rinegoziare i termini di pagamento coi clienti principali "
                           "al prossimo rinnovo: pochi contratti muovono gran parte "
                           "della cassa.")
        domande.append("Cosa succede alla cassa se il cliente principale sposta il "
                       "pagamento di 30 giorni? (la simulazione è nel report)")

    return {"errori_probabili": errori, "opportunita_non_sfruttate": opportunita,
            "decisioni_entro_7_giorni": decisioni, "domande_per_il_management": domande}


def build_finance_pack(inputs: dict, deliverable: dict) -> dict:
    """Pacchetto consulenziale finanza/liquidità: insight → catene causali →
    forecast/simulazioni → confronto opzioni → raccomandazioni coi 4 perché."""
    from . import decision, insight, reasoning, scenario

    insights, facts = insight.derive_finance_insights(inputs)
    chains = reasoning.build_finance_chains(insights, inputs)
    forecast = scenario.cash_forecast_13w(inputs)
    sims = scenario.what_if(inputs)
    options = decision.finance_options(inputs, insights)
    recs = decision.finance_recommendations(inputs, insights)
    value = _value_sections_finance(insights, facts)
    coverage = insight.coverage_report(facts)

    pack: dict[str, Any] = {
        "_tipo": "finanza_liquidita",
        "insight_derivati": insights,
        "analisi_sistemica": chains,
        "confronto_soluzioni": options,
        "raccomandazioni_operative": recs,
        "copertura_dati": coverage,
        **value,
        "dati_da_raccogliere": [
            "Scadenzario incassi/pagamenti (per il forecast reale settimana per settimana)",
            "Aging crediti per cliente (chi deve cosa, da quanto)",
            "Condizioni bancarie scritte (tassi, commissioni, covenant)",
        ],
    }
    if forecast:
        pack["forecast_13_settimane"] = forecast
    if sims:
        pack["simulazioni"] = sims
    return pack


def build_pack(skill: str, inputs: dict, deliverable: dict) -> Optional[dict]:
    """Entry point del planner: pacchetto consulenziale se il caso lo richiede."""
    problem = classify_problem(inputs, skill)
    if problem == "operations_commesse":
        return build_operations_pack(inputs, deliverable)
    if problem == "finanza_liquidita":
        return build_finance_pack(inputs, deliverable)
    return None
