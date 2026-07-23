"""Grounding FORZATO sui numeri fattuali (17 lug — risposta a Luca: «essendoci mcp non
dovrebbe esserci questo errore»).

Il problema: gpt-oss locale, sulle domande di NUMERO specifico (scadenze, aliquote, soglie,
durate, termini), risponde a MEMORIA e inventa valori plausibili-ma-sbagliati ('comunicazione
assunzione entro 10 giorni' — è il giorno prima). Il web_search ESISTE ma è discrezionale: il
modello non lo chiama perché 'crede' di sapere. Il corpus normattiva verifica gli ARTICOLI,
non le scadenze.

Soluzione: quando la domanda dell'utente chiede un numero fattuale, il SERVER esegue una
ricerca web (OpenAI, la stessa già usata) PRIMA del turno e inietta i risultati nel prompt
come DATI VERIFICATI — il modello risponde ancorato alla fonte, non alla memoria. Trigger
deterministico (pattern-based), esecuzione best-effort e fail-open (se la ricerca non va, si
prosegue col linguaggio prudente del prompt). KBOT_FACT_GROUNDING=0 disattiva.
"""
from __future__ import annotations

import logging
import os
import re

from . import signals, web_search

log = logging.getLogger(__name__)

# Filosofia (Luca): la conoscenza va SEMPRE presa dalle fonti, non dalla memoria — in OGNI
# ambito, non solo il legale. Il grounding scatta quando la domanda chiede un FATTO
# SPECIFICO (un valore, un dato, un termine, un'entità con una risposta verificabile):
# numeri/quantità/date/scadenze/soglie/aliquote/prezzi/statistiche/quote di mercato, oppure
# 'cos'è / come funziona X', o dati su un'azienda/prodotto/settore. Domain-AGNOSTICO.
_FACTUAL = re.compile(
    r"\b("
    # quantità/numeri/tempi/importi
    r"quant[oiae]\b|"
    r"qual[e']?\s+è\s+(?:l['\s]|la\s+|il\s+|lo\s+)?(?:aliquota|soglia|limite|tetto|termine|scadenza|"
    r"durata|percentuale|imposta|tasso|prezzo|costo|importo|valore|quota|numero|massimale|minimo|massimo)|"
    r"che\s+(?:aliquota|soglia|percentuale|termine|tasso|prezzo|costo)\b|"
    r"entro\s+(?:quando|quant\w+)|"
    r"quando\s+(?:scade|devo|bisogna|va)\b|"
    # dati esterni / mercato / entità
    r"(?:qual[ei]|chi)\s+sono\s+(?:i|le|gli)\b|"
    r"prezzo\s+(?:di|del|della|medio)|costo\s+(?:di|del|della|medio)|"
    r"(?:dati|statistic\w+|numeri|trend|andamento)\s+(?:su|del|di|sul)|"
    r"quota\s+di\s+mercato|dimension\w+\s+del\s+mercato|"
    # definizione di una cosa specifica
    r"(?:cos'?\s?è|che\s+cos'?\s?è|cosa\s+significa|come\s+funziona)\s+(?:il|lo|la|l'|un|una|i|le|gli)\b"
    r")", re.I)

# Esclusioni: GIUDIZI soggettivi e strategici (lì serve il METODO delle skill, non un fatto
# esterno da cercare) e il conversazionale. Su questi NON si cerca (niente latenza inutile).
_JUDGMENT = re.compile(
    r"\b(dovrei|conviene|converrebbe|è\s+meglio|meglio\s+\w+\s+o|consigli\w*|"
    r"cosa\s+ne\s+pensi|secondo\s+te|che\s+ne\s+dici|come\s+(?:faccio|posso|miglioro|"
    r"gestisco|motivo|imposto|organizzo|riduco|aumento|struttur\w+)|"
    r"cosa\s+(?:faccio|mi\s+consigli|devo\s+fare)|ha\s+senso|vale\s+la\s+pena)\b", re.I)


# --- Estensione "webresearch effettivo" (lug 2026, richiesta Luca) ----------------------
# Il tool-use discrezionale sul modello locale non parte quasi mai → la ricerca scatta
# DETERMINISTICAMENTE anche su: (a) richieste esplicite («cerca», «verifica online»);
# (b) due diligence di un provider/fornitore nominato in contesto normativo/contrattuale
# (es. «ho scelto openai» in un audit GDPR → documentazione DPA/data residency ufficiale);
# (c) verifiche di conformità («è tutto in regola?»); (d) domande su norme/adempimenti.
_EXPLICIT = re.compile(
    r"\b(cerca\w*|ricerca\s+(?:sul\s+web|online)|verifica\s+(?:online|sul\s+web)|"
    r"controlla\s+(?:online|sul\s+web)|trova\w*\s+(?:informazioni|dati|fonti)|"
    r"fonti\s+aggiornate|notizie\s+(?:su|recenti))\b", re.I)
_PROVIDERS = re.compile(
    r"\b(open\s?ai|anthropic|google|microsoft|azure|aws|amazon|meta|stripe|paypal|"
    r"supabase|firebase|cloudflare|vercel|railway|render|replicate|hugging\s?face|"
    r"mistral|clerk|auth0|shopify|salesforce|hubspot|mailchimp|resend|zendesk|"
    r"chat\s?gpt|gpt-\w+|claude|gemini|copilot)\b", re.I)
_NORM_CONTEXT = re.compile(
    r"\b(gdpr|gpdr|privacy|dati\s+personali|dpia|dpa|ai\s+act|normativ\w+|decreto|"
    r"regolament\w+|direttiv\w+|ccnl|codice\s+civile|testo\s+unico|obblig\w+|"
    r"adempiment\w+|autorizzazion\w+|conform\w+|compliance|contratt\w+|clausol\w+|"
    r"licenz\w+|trasferiment\w+|consenso|informativ\w+|231|whistleblowing|"
    r"antiriciclaggio|sicurezza\s+sul\s+lavoro|haccp)\b", re.I)
_NORM_QUESTION = re.compile(
    r"\b(cosa\s+(?:dice|prevede|richiede)\s+(?:la|il|lo)\b|è\s+obbligatori\w+|"
    r"serve\s+(?:il|la|un|una)\s+(?:consenso|autorizzazione|licenza|dpia|dpa|informativa)|"
    r"in\s+regola|a\s+norma|conform\w+|quali\s+(?:obblighi|requisiti|adempimenti))", re.I)


def _enabled() -> bool:
    return os.getenv("KBOT_FACT_GROUNDING", "1") != "0" and web_search.enabled()


def needs_grounding(user_text: str) -> bool:
    t = (user_text or "").strip()
    if len(t) < 12:                       # saluti / 'ok' / 'grazie' → niente ricerca
        return False
    if _JUDGMENT.search(t):               # giudizio/strategia → metodo dalle skill, non fatto
        return False
    return bool(_FACTUAL.search(t))


def _query(user_text: str) -> str:
    # query neutra e domain-agnostica: la sola domanda dell'utente (+ ancoraggio Italia/
    # attualità che aiuta su dati e norme senza distorcere gli altri temi).
    return f"{user_text.strip()[:220]} (contesto: Italia, dato aggiornato)"


def research_query(user_text: str, context_text: str = "") -> str | None:
    """La query di ricerca per questo turno, o None se la ricerca non serve.
    Decisione DETERMINISTICA sull'ULTIMO messaggio (il contesto recente serve solo a
    qualificare il tema, mai a ri-triggerare da solo → niente ricerca a ogni turno)."""
    t = (user_text or "").strip()
    if len(t) < 12:
        return None
    ctx = f"{context_text or ''} {t}"
    # (a) richiesta esplicita di cercare → si cerca sempre
    if _EXPLICIT.search(t):
        return _query(t)
    # (b) provider nominato in contesto normativo/contrattuale → due diligence documentale
    m = _PROVIDERS.search(t)
    if m and _NORM_CONTEXT.search(ctx):
        provider = m.group(0).strip()
        return (f"{provider}: DPA, data residency, trasferimento dati extra-UE, uso dei "
                f"dati per training, termini API vs consumer — documentazione ufficiale "
                f"aggiornata (contesto GDPR Italia)")
    if _JUDGMENT.search(t):               # giudizio/strategia → niente ricerca
        return None
    # (c) verifica di conformità → requisiti e obblighi dalle fonti
    if signals.is_compliance_check(t):
        return f"{t[:200]} (requisiti e obblighi, normativa italiana, fonti ufficiali)"
    # (d) domanda su norme/adempimenti
    if _NORM_QUESTION.search(t) and _NORM_CONTEXT.search(ctx):
        return f"{t[:220]} (normativa italiana aggiornata, fonte ufficiale)"
    # (e) fatto specifico (trigger storico)
    if _FACTUAL.search(t):
        return _query(t)
    return None


def ground_block(user_text: str, context_text: str = "") -> str | None:
    """Blocco di grounding da iniettare nel prompt, o None se non serve / ricerca non
    disponibile. best-effort: qualunque errore → None (fail-open, prosegue col prompt)."""
    if not _enabled():
        return None
    q = research_query(user_text, context_text)
    if not q:
        return None
    try:
        res = web_search.run_openai_search(q)
    except Exception:
        log.warning("fact_grounding: ricerca fallita (fail-open)", exc_info=True)
        return None
    if not res or res.startswith("[ricerca web"):
        return None  # nessun risultato utile → il prompt prudente gestisce da solo
    return (
        "\nRISULTATI DI RICERCA WEB (aggiornati, NON pre-validati) — la domanda richiede "
        "fatti, norme o documentazione verificabili. Usa QUESTI risultati come base, NON la "
        "tua memoria, e cita un valore/termine/condizione solo se compare QUI (cita le "
        "fonti nel testo). ATTENZIONE: sono pagine web generiche, non una fonte ufficiale — "
        "su scadenze e termini di legge il web ripete spesso errori. Se i risultati non "
        "danno il dato preciso in modo CHIARO e COERENTE (o si contraddicono), NON asserire "
        "un numero: dillo e rimanda alla fonte ufficiale, senza indovinare.\n"
        "<<<RISULTATI RICERCA>>>\n" + res[:2500] + "\n<<<FINE RISULTATI>>>\n"
    )
