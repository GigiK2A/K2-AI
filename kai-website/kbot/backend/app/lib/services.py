"""Suite AI services registry — Python mirror of src/data/suiteAiServices.ts.

Keep in sync manually when the TS source changes.
Source of truth: /Volumes/PARASSITA/K-AI/kai-website/src/data/suiteAiServices.ts
"""
from __future__ import annotations

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


def resolve_skills_for_session(session: dict) -> List[str]:
    """Mirror of resolveSkillNamesForSession() in api/kbot/_shared.ts.

    Priority:
      1. collected_data.service_id
      2. fallback: base skill only
    """
    collected = session.get("collected_data") or {}
    service_id = normalize_service_id(collected.get("service_id"))
    skills = get_service_skills(service_id)
    if not skills:
        return [BASE_SKILL]
    # Prepend base skill if not already there.
    if BASE_SKILL not in skills:
        skills = [BASE_SKILL] + skills
    return skills
