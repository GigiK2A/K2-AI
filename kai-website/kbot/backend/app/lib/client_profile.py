"""Stima del PROFILO dell'interlocutore + calibrazione del registro (review "adattamento
al profilo del cliente").

Il bug: a un imprenditore ~70enne non tecnico che dice «non sopporto più il mio socio,
voglio uscire», K2 rispondeva con la checklist da commercialista (EBITDA, DCF, multipli,
valore patrimoniale…). Un consulente vero ADATTA linguaggio, numero di domande e
profondità tecnica alla persona: più l'interlocutore è poco tecnico, meno tecnica la
conversazione iniziale.

Qui: stima DETERMINISTICA (dai messaggi UTENTE) di due dimensioni — quanto è tecnico
l'interlocutore e quanto è forte la componente personale/emotiva — e un blocco da iniettare
nel system prompt che calibra il comportamento. Nessuna chiamata LLM. Fail-open.
"""
from __future__ import annotations

import re

# Gergo tecnico di QUALSIASI dominio: se l'UTENTE lo usa spontaneamente, è a suo agio col
# tecnico (vale trasversalmente — finanza, legale, fiscale, HR, marketing, IT/operations —
# non solo M&A). La stima della tecnicità non deve dipendere dal settore del caso.
_TECH_TERMS = re.compile(
    r"\b("
    # finanza / valutazione
    r"ebitda|ebit\b|dcf|wacc|enterprise\s+value|\bev/ebitda\b|multipl\w+|patrimonio\s+netto|"
    r"cash\s*flow|flusso\s+di\s+cassa|marginalit\w+|\broi\b|\bpfn\b|posizione\s+finanziaria|"
    r"capex|working\s+capital|capitale\s+circolante|leva\s+finanziaria|leverage|goodwill|"
    r"avviamento|due\s+diligence|valore\s+patrimoniale|bilancio\s+riclassificat\w+|"
    r"free\s+cash\s+flow|net\s+debt|indebitamento\s+netto|break[\s-]?even|"
    # legale
    r"prescrizion\w+|decadenz\w+|litisconsorzi\w+|inadempiment\w+|clausol\w+\s+risolutiv\w+|"
    r"foro\s+competente|onere\s+della\s+prova|responsabilit\w+\s+(?:contrattuale|extracontrattuale)|"
    r"diffid\w+\s+ad\s+adempiere|risoluzione\s+(?:del\s+)?contratto|recesso\s+ad\s+nutum|"
    # fiscale
    r"ravvediment\w+|plafond|reverse\s+charge|split\s+payment|\bires\b|\birap\b|"
    r"deducibilit\w+|ammortament\w+\s+fiscal\w+|regime\s+forfettari\w+|transfer\s+pricing|"
    # HR / organizzazione
    r"turnover|retention|\bkpi\b|onboarding|performance\s+review|comp(?:ensation)?\s*&?\s*ben|"
    r"organigramma\s+funzional\w+|span\s+of\s+control|"
    # marketing / IT-operations
    r"\bcac\b|\bltv\b|\bctr\b|\bcpa\b|funnel\s+di\s+conversione|attribution|"
    r"lead\s+scoring|churn\s+rate|throughput|lead\s+time|\bsla\b|\bapi\b|"
    r"tempo\s+ciclo|colli\s+di\s+bottiglia)\b", re.I)

# Cifre economiche fornite spontaneamente (importi, percentuali) → segnale di dimestichezza.
_ECON_NUM = re.compile(
    r"(?:€|\beur\b|euro)\s*[\d.,]+|[\d.,]+\s*(?:€|\beur\b|euro|k\b|mila|milion\w+|mln)|\d+(?:[.,]\d+)?\s*%")

# Segnali di una dimensione PERSONALE/emotiva forte: spesso decisiva (disposto a perderci
# pur di uscire, urgenza soggettiva, rapporto logorato).
_EMOTIONAL = re.compile(
    r"\bnon\s+ne\s+posso\s+pi\w+\b|\bnon\s+(?:lo\s+)?sopporto\b|\bstuf\w+\b|\besaust\w+\b|"
    r"\blogorat\w+\b|\bstanco\s+(?:di|morto)\b|\bnon\s+mi\s+fido\b|\bbasta\b|\bvoglio\s+(?:solo\s+)?"
    r"(?:uscire|andarmene|chiudere|liberarmi)\b|\bmi\s+ha\s+stanc\w+\b|\btensioni?\b|"
    r"\blitig\w+\b|\brapporto\s+(?:rotto|finito|logorato|difficile)\b|\bstress\w*\b|"
    r"\bnotti\s+insonni\b|\bnon\s+dormo\b", re.I)


def estimate_client_profile(user_texts: list[str] | str) -> dict:
    """{'tecnicita': 'bassa|media|alta', 'emotivo': bool}. Basata SOLO sui messaggi utente
    (non su ciò che scrive il bot). Conservativa: in dubbio → 'media', comportamento neutro."""
    if isinstance(user_texts, str):
        blob = user_texts
    else:
        blob = " ".join(str(t or "") for t in (user_texts or []))
    blob = blob.strip()
    if not blob:
        return {"tecnicita": "media", "emotivo": False}
    tech = len(_TECH_TERMS.findall(blob)) + min(2, len(_ECON_NUM.findall(blob)))
    if tech >= 3:
        tecnicita = "alta"
    elif tech >= 1:
        tecnicita = "media"
    else:
        tecnicita = "bassa"
    emotivo = bool(_EMOTIONAL.search(blob))
    return {"tecnicita": tecnicita, "emotivo": emotivo}


def profile_hint(profile: dict) -> str:
    """Blocco di calibrazione per il system prompt. Vuoto quando non serve correggere nulla
    (interlocutore tecnico e non emotivo → comportamento di default)."""
    profile = profile or {}
    tec = profile.get("tecnicita")
    parts: list[str] = []
    # Si inietta SOLO quando c'è qualcosa da correggere: interlocutore poco tecnico
    # (evita la checklist tecnica) o forte componente emotiva. Con un interlocutore
    # tecnico e non emotivo il comportamento di default va già bene → nessun blocco.
    if tec == "bassa":
        parts.append(
            "l'interlocutore NON usa linguaggio tecnico: parla SEMPLICE, evita il gergo del "
            "dominio (finanziario, legale, fiscale, HR, marketing, tecnico) nei primi turni; "
            "se un termine tecnico serve davvero, spiegalo con parole comuni. NON dettare una "
            "checklist di dati o documenti: prima capisci il PROBLEMA e la PERSONA, i "
            "dettagli tecnici vengono molto dopo. Domande discorsive, una alla volta.")
    if profile.get("emotivo"):
        parts.append(
            "c'è una forte dimensione PERSONALE/emotiva: approfondiscila — è spesso una "
            "variabile DECISIVA (es.: «quanto conta risolvere in fretta rispetto a ottenere "
            "il risultato migliore?», «cosa la preoccupa di più?»). Vale molto più che "
            "chiedere subito un dato tecnico.")
    if not parts:
        return ""
    return "\nADATTAMENTO AL PROFILO — " + " ".join(parts) + "\n"


def hint_from_session(session: dict) -> str:
    """Comodità: estrae i messaggi utente dalla sessione e ritorna il blocco calibrazione.
    Fail-open (mai solleva: la costruzione del prompt non deve rompersi)."""
    try:
        msgs = (session or {}).get("messages") or []
        user_texts = [str(m.get("content") or "") for m in msgs[-8:]
                      if isinstance(m, dict) and m.get("role") == "user"]
        return profile_hint(estimate_client_profile(user_texts))
    except Exception:
        return ""
