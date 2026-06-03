"""Suite AI services registry — Python mirror of src/data/suiteAiServices.ts.

Keep in sync manually when the TS source changes.
Source of truth: /Volumes/PARASSITA/K-AI/kai-website/src/data/suiteAiServices.ts
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional, TypedDict


class SuiteAiService(TypedDict):
    id: str
    name: str
    skills: List[str]
    recommended_tier: str  # HOST | WEB | STUDIO


SUITE_AI_SERVICES: List[SuiteAiService] = [
    {"id": "P01", "name": "Agenti AI Email & CRM", "skills": ["draft-outreach", "pipeline-review", "email-sequence", "crm-customer-experience", "sales-strategy", "lead-qualification"], "recommended_tier": "WEB"},
    {"id": "P02", "name": "Automazioni Amministrative", "skills": ["contabilita-bilancio", "analisi-bilancio-pmi", "budget-forecast-pmi", "programmazione-controllo", "reconciliation"], "recommended_tier": "HOST"},
    {"id": "P03", "name": "AI Legale & Contratti", "skills": ["diritto-italiano", "diritto-societario-italiano", "it-law-privacy-ai", "antitrust-concorrenza-ue", "review-contract", "triage-nda"], "recommended_tier": "WEB"},
    {"id": "P04", "name": "AI Ingegneria & Progettazione", "skills": ["verifica-statica", "gestione-cantiere-tlc", "psc-coordinamento-sicurezza", "direzione-lavori", "progettista-strutturale", "capitolato-speciale"], "recommended_tier": "STUDIO"},
    {"id": "P05", "name": "Microapp Documenti Tecnici", "skills": ["documentation", "runbook", "technical-writing", "pdf-extraction", "template-generation"], "recommended_tier": "HOST"},
    {"id": "P06", "name": "AI Customer Service", "skills": ["ticket-triage", "draft-response", "kb-article", "customer-escalation", "sentiment-analysis"], "recommended_tier": "HOST"},
    {"id": "P07", "name": "RAG & Knowledge Base", "skills": ["search", "knowledge-synthesis", "memory-management", "digest", "rag-pipeline"], "recommended_tier": "WEB"},
    {"id": "P08", "name": "AI Compliance & Audit", "skills": ["sox-testing", "compliance-check", "sicurezza-lavoro", "transizione5", "de-minimis", "audit-trail"], "recommended_tier": "WEB"},
    {"id": "P09", "name": "AI Controllo di Gestione", "skills": ["financial-statements", "variance-analysis", "cruscotto-direzionale", "budget-forecast-pmi", "pricing-optimizer", "programmazione-controllo"], "recommended_tier": "STUDIO"},
    {"id": "P10", "name": "Integrazione Gestionali & ERP", "skills": ["system-design", "sql-queries", "change-request", "code-review", "api-integration", "data-pipeline"], "recommended_tier": "STUDIO"},
    {"id": "P11", "name": "AI Marketing & Brand", "skills": ["brand-voice", "campaign-plan", "content-creation", "seo-audit", "keyword-strategy", "digital-marketing-performance"], "recommended_tier": "WEB"},
    {"id": "P12", "name": "AI Consulenza Strategica PMI", "skills": ["analisi-bilancio-pmi", "analisi-settore-pmi", "piano-crescita-pmi", "budget-forecast-pmi", "marketing-strategico"], "recommended_tier": "STUDIO"},
    {"id": "P13", "name": "AI Agevolazioni & Bandi", "skills": ["flusso-agevolazioni-pmi", "verifica-transizione5", "sabatini", "simest", "credito-rd", "de-minimis"], "recommended_tier": "WEB"},
    {"id": "P14", "name": "AI Edilizia & Costruzioni", "skills": ["flusso-buildboost", "progettista-strutturale", "psc-coordinamento-sicurezza", "direzione-lavori", "gestione-cantiere-tlc", "capitolato-speciale"], "recommended_tier": "STUDIO"},
    {"id": "P15", "name": "AI HR & People", "skills": ["recruiting-pipeline", "interview-prep", "onboarding", "performance-review", "comp-analysis"], "recommended_tier": "WEB"},
    {"id": "P16", "name": "AI Real Estate & Tokenizzazione", "skills": ["tgc-orchestratore", "tokenizzazione-immobiliare", "analisi-settore-pmi", "financial-statements", "diritto-societario-italiano"], "recommended_tier": "STUDIO"},
    {"id": "P17", "name": "AI Data & Analytics", "skills": ["analyze", "sql-queries", "build-dashboard", "machine-learning", "statistica-applicata", "data-pipeline"], "recommended_tier": "STUDIO"},
    {"id": "P18", "name": "AI Design & UX", "skills": ["design-critique", "design-system", "accessibility-review", "ux-copy", "user-research"], "recommended_tier": "WEB"},
    {"id": "P19", "name": "AI Energia & Efficienza", "skills": ["diagnosi-energetica-ege", "impianti-termici-hvac", "impianti-elettrici", "cci-impianti-produzione"], "recommended_tier": "WEB"},
    {"id": "P20", "name": "AI Hospitality", "skills": ["flusso-hostboost-ricettive", "check-host-express", "property-management-revenue"], "recommended_tier": "HOST"},
]

_BY_ID: Dict[str, SuiteAiService] = {s["id"]: s for s in SUITE_AI_SERVICES}
VALID_SERVICE_IDS = set(_BY_ID.keys())
DEFAULT_SERVICE_ID = "P12"  # AI Consulenza Strategica PMI

# Fallback skill always loaded as base (mirrors site).
BASE_SKILL = "diagnosi-ai-operativa-pmi"


def normalize_service_id(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    return str(value).strip().upper()


def get_service(service_id: Optional[str]) -> Optional[SuiteAiService]:
    sid = normalize_service_id(service_id)
    if not sid:
        return None
    return _BY_ID.get(sid)


def get_service_skills(service_id: Optional[str]) -> List[str]:
    svc = get_service(service_id)
    if not svc:
        return []
    return list(svc["skills"])


# Intent detection — keyword → service mapping. Necessario perché in modalità
# chat libera (no widget Suite) service_id resta None e la sessione caricava
# solo BASE_SKILL ("diagnosi-ai-operativa-pmi") indipendentemente dall'intent
# reale dell'utente (es. audit SEO).
_INTENT_KEYWORDS: Dict[str, List[str]] = {
    "P01": ["email", "crm", "lead generation", "outreach", "campagna email", "sales pipeline", "agenti email"],
    "P02": ["amministr", "fatture", "fatturazione elettronica", "contabilità", "riconciliazion", "scadenz", "bilancio", "bilanci", "analisi bilancio", "budget", "forecast"],
    "P03": ["contratto", "contratti", "legale", "gdpr", "privacy policy", "nda", "diritto societario", "antitrust"],
    "P04": ["ingegneria", "progettazione", "cantiere", "strutturale", "psc", "direzione lavori", "capitolato"],
    "P05": ["microapp", "documento tecnico", "template generation", "runbook", "documentation"],
    "P06": ["customer service", "ticket", "supporto cliente", "knowledge base helpdesk", "sentiment"],
    "P07": ["rag", "knowledge base", "embedding", "retrieval", "memoria documentale"],
    "P08": ["compliance", "audit interno", "transizione 5", "audit trail", "sox", "sicurezza lavoro"],
    "P09": ["controllo di gestione", "kpi", "cruscotto", "variance analysis", "budget forecast", "pricing"],
    "P10": ["erp", "integrazione gestionale", "api integration", "data pipeline", "sql"],
    "P11": ["seo", "audit seo", "audit del sito", "audit sito", "keyword", "ranking google", "brand voice",
            "marketing", "campagna marketing", "content strategy", "digital marketing", "sem", "social",
            "posizionamento organico", "serp", "metadata", "title tag", "h1", "schema.org",
            # Contenuti / editoriale / social — deliverable di content (calendario, post, copy)
            "calendario editoriale", "calendario contenuti", "calendario", "piano editoriale",
            "piano contenuti", "contenuti social", "contenuti", "post instagram", "post social",
            "instagram", "linkedin", "facebook", "tiktok", "reel", "caption", "copy", "editoriale",
            "social media", "newsletter"],
    "P12": ["consulenza strategica", "piano crescita", "analisi settore", "strategia pmi", "go-to-market"],
    "P13": ["bandi", "agevolazioni", "sabatini", "simest", "credito r&d", "de minimis"],
    "P14": ["edilizia", "costruzioni", "buildboost"],
    "P15": ["hr", "recruiting", "selezione personale", "onboarding", "performance review", "compensation"],
    "P16": ["real estate", "tokenizzazione", "tgc"],
    "P17": ["data analytics", "machine learning", "dashboard analytics", "statistica"],
    "P18": ["design", "ux", "design system", "accessibility", "user research"],
    "P19": ["energia", "efficienza energetica", "hvac", "diagnosi energetica"],
    "P20": ["hospitality", "ricettiva", "hotel", "revenue management"],
}


def infer_service_id_from_session(session: dict) -> Optional[str]:
    """Inferisci il service dall'INTENTO dell'utente, non dal dominio del sito.

    L'intento esplicito (cosa l'utente vuole FARE, nei suoi messaggi) pesa molto
    più del contesto-fonte (di cosa parla il sito/file analizzato). Senza questa
    distinzione, un sito di ingegneria faceva vincere P04/P19 anche quando
    l'utente chiedeva un calendario social (P11) → caricava le skill sbagliate.

    Scansiona TUTTI i messaggi utente (non solo gli ultimi 6) così l'intento
    iniziale ("calendario instagram") non scivola fuori finestra in chat lunghe.
    Restituisce il service con score più alto (≥2). None se debole/ambiguo.
    """
    collected = session.get("collected_data") or {}
    messages = session.get("messages") or []

    # (1) Intento utente — tutto ciò che l'utente ha scritto.
    user_parts: List[str] = [
        m["content"] for m in messages
        if isinstance(m, dict) and m.get("role") == "user" and isinstance(m.get("content"), str)
    ]
    # (2) Contesto-fonte — di cosa parlano sito/file (solo tie-breaker).
    aux_parts: List[str] = []
    for u in collected.get("analyzed_urls") or []:
        for k in ("title", "summary", "meta_description"):
            if isinstance(u.get(k), str):
                aux_parts.append(u[k])
    for f in collected.get("uploaded_files") or []:
        if isinstance(f.get("name"), str):
            aux_parts.append(f["name"])

    if not user_parts and not aux_parts:
        return None

    def _norm(parts: List[str]) -> str:
        return re.sub(r"\s+", " ", " \n ".join(parts).lower())

    user_hay = _norm(user_parts)
    aux_hay = _norm(aux_parts)

    USER_WEIGHT = 3   # l'intento esplicito domina
    AUX_WEIGHT = 1    # il dominio del sito/file conta solo a parità

    scores: Dict[str, int] = {}
    for sid, kws in _INTENT_KEYWORDS.items():
        score = 0
        for kw in kws:
            pat = rf"\b{re.escape(kw)}\b"  # word-boundary: niente match parziali rumorosi
            score += USER_WEIGHT * len(re.findall(pat, user_hay))
            score += AUX_WEIGHT * len(re.findall(pat, aux_hay))
        if score > 0:
            scores[sid] = score
    if not scores:
        return None
    best_sid, best_score = max(scores.items(), key=lambda kv: kv[1])
    if best_score < 2:  # soglia minima per evitare match casuali
        return None
    return best_sid


def resolve_skills_for_session(session: dict) -> List[str]:
    """Risolvi le skill in base a (1) service_id esplicito, (2) intent
    inferito da messaggi+URL+file, (3) fallback BASE_SKILL.

    Storia: prima ritornava SOLO BASE_SKILL quando service_id era None,
    quindi in tutte le chat libere si attivava una sola skill
    (`diagnosi-ai-operativa-pmi`) indipendentemente dall'intent reale.
    """
    collected = session.get("collected_data") or {}
    service_id = normalize_service_id(collected.get("service_id"))
    if not service_id:
        service_id = infer_service_id_from_session(session)
    skills = get_service_skills(service_id)
    if not skills:
        return [BASE_SKILL]
    if BASE_SKILL not in skills:
        skills = [BASE_SKILL] + skills
    return skills
