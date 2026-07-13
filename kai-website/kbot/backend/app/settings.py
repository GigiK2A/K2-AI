"""Environment-driven settings. Loaded once at import time."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
# .env.local overrides shell env (developer file is source of truth).
# .env is a non-overriding default (lowest priority).
load_dotenv(ROOT / ".env", override=False)
load_dotenv(ROOT / ".env.local", override=True)


def _env(name: str, *fallbacks: str, default: Optional[str] = None) -> Optional[str]:
    for key in (name, *fallbacks):
        value = os.environ.get(key)
        if value:  # empty strings treated as missing
            return value
    return default


ANTHROPIC_API_KEY = _env("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = _env("ANTHROPIC_MODEL", "CLAUDE_MODEL", default="claude-haiku-4-5")
ANTHROPIC_PDF_MODEL = _env("ANTHROPIC_PDF_MODEL", default="claude-sonnet-4-5")
# Multi-call generation: spezza il JSON in 3 chiamate (exec_summary, body, conclusions)
# per evitare troncamento ultime sezioni con report lunghi. Default OFF — feature
# flag per safe rollout. Attivare con ANTHROPIC_PDF_MULTI_CALL=1.
ANTHROPIC_PDF_MULTI_CALL = (_env("ANTHROPIC_PDF_MULTI_CALL", default="0") or "0").lower() in ("1", "true", "yes")

# OpenAI — usato ESCLUSIVAMENTE per la web search (override cosciente della regola
# "no OpenAI" deciso dall'owner, giu 2026). Tutto il resto resta su Claude/Anthropic.
# Il tool `web_search` di Claude è un client-tool il cui handler chiama l'API OpenAI
# (Responses API). Senza chiave la ricerca è disattivata (degrado safe). Vedi lib/web_search.py.
OPENAI_API_KEY = _env("OPENAI_API_KEY")
OPENAI_SEARCH_MODEL = _env("OPENAI_SEARCH_MODEL", default="gpt-4.1-mini")

SUPABASE_URL = _env("NEXT_PUBLIC_SUPABASE_URL", "SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = _env(
    "SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_SERVICE_KEY", "SUPABASE_KEY"
)
SUPABASE_JWT_SECRET = _env("SUPABASE_JWT_SECRET")  # legacy HS256, optional fallback
SUPABASE_JWT_JWKS_URL = _env(
    "SUPABASE_JWT_JWKS_URL",
    default=(f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json" if SUPABASE_URL else None),
)
SUPABASE_ANON_KEY = _env("NEXT_PUBLIC_SUPABASE_ANON_KEY", "SUPABASE_ANON_KEY")

STRIPE_SECRET_KEY = _env("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = _env("STRIPE_WEBHOOK_SECRET")
STRIPE_API_VERSION = _env("STRIPE_API_VERSION", default="2024-12-18.acacia")
REPORT_PRICE_EUR_CENTS = int(_env("REPORT_PRICE_EUR_CENTS", default="1900") or "1900")

RESEND_API_KEY = _env("RESEND_API_KEY")
REPORT_FROM_EMAIL = _env("REPORT_FROM_EMAIL", default="K2-AI <noreply@k2-ai.it>")
KBOT_NOTIFY_EMAIL = _env("KBOT_NOTIFY_EMAIL")

FRONTEND_URL = _env("FRONTEND_URL", default="http://localhost:3000")
SITE_URL = _env("NEXT_PUBLIC_SITE_URL", "SITE_URL", default="https://www.k2-ai.it")
INTERNAL_API_KEY = _env("INTERNAL_API_KEY")

# Porta locale del backend (Railway inietta PORT). Default 8000 come da uvicorn dev.
PORT = int(_env("PORT", default="8000") or "8000")

# M12 — base URL per le chiamate INTERNE server-to-server (es. webhook Stripe →
# generate-pdf con INTERNAL_API_KEY). NON derivare mai da request.base_url (dipende
# dall'header Host, spoofabile → l'INTERNAL_API_KEY finirebbe a un host attaccante).
# Il backend chiama sé stesso su loopback. Override esplicito con INTERNAL_BASE_URL.
INTERNAL_BASE_URL = _env("INTERNAL_BASE_URL", default=f"http://127.0.0.1:{PORT}")

# Ambiente di deploy (production/staging/dev). Usato dal guard paywall all'avvio.
ENVIRONMENT = _env("ENVIRONMENT", "ENV", "RAILWAY_ENVIRONMENT", default="development")

# FREE MODE = bypass del paywall, SOLO per demo/dev. Default OFF (=produzione):
# la generazione dei deliverable 8e richiede pagamento (vedi _mint_entitlement →
# 402 se non pagato). Per una demo: KBOT_FREE_MODE=1 + K2A_8E_ENTITLEMENT_DEV=true.
KBOT_FREE_MODE = (_env("KBOT_FREE_MODE", default="0") or "0").lower() in ("1", "true", "yes")

# FAKE PAYMENT = paywall PIENO (prezzo + bottone Sblocca veri), ma il "pagamento"
# è simulato: POST /checkout/boost/demo marca la sessione paid come farebbe il
# webhook Stripe, senza Stripe né addebito. Serve a provare tutta la catena
# prezzo→paga→sblocca→genera. Default OFF. Distinto da FREE_MODE (che invece NON
# mostra prezzo né pagamento). Con FAKE_PAYMENT serve comunque ENTITLEMENT_SECRET
# perché la generazione passa dall'entitlement reale (status=paid → mint → 8e).
KBOT_FAKE_PAYMENT = (_env("KBOT_FAKE_PAYMENT", default="0") or "0").lower() in ("1", "true", "yes")

# AGENTE A2: i Boost "che ragionano" (AdvisorBoost) generati da un agente tool-use
# (lib/boost_agent.py) che chiama i MCP di Luca, invece della pipeline 8e. Default
# OFF: opt-in quando ci sono crediti + il quant pronto. Vedi lib/boost_agent.py.
K2A_BOOST_AGENT = (_env("K2A_BOOST_AGENT", default="0") or "0").lower() in ("1", "true", "yes")
# servizi instradati all'agente A2 (CSV), se K2A_BOOST_AGENT attivo.
K2A_BOOST_AGENT_SERVIZI = [
    s.strip() for s in (_env("K2A_BOOST_AGENT_SERVIZI", default="checkup_advisor") or "").split(",") if s.strip()
]

# Default to k2-ai.it production origins. Never default to "*" with credentials.
# Override via KBOT_CORS_ORIGINS env var (comma-separated) for dev/staging.
_DEFAULT_CORS = ",".join([
    "https://www.k2-ai.it",
    "https://k2-ai.it",
    "https://k-ai.it",
    "https://www.k-ai.it",
    FRONTEND_URL,  # dev only — usually http://localhost:3000
])
CORS_ORIGINS = [
    o.strip()
    for o in (_env("KBOT_CORS_ORIGINS", default=_DEFAULT_CORS) or _DEFAULT_CORS).split(",")
    if o.strip() and o.strip() != "*"  # explicit guard: never allow wildcard
]

# Skill loader looks here first (consolidated repo), then falls back to local copy.
SKILLS_DIR = Path(
    _env("KBOT_SKILLS_DIR", default=str(ROOT.parent.parent / "lib" / "skills"))
).resolve()

# Storage bucket names (Supabase Storage), shared with the site.
STORAGE_UPLOADS_BUCKET = _env("STORAGE_UPLOADS_BUCKET", default="kbot-uploads")
STORAGE_REPORTS_BUCKET = _env("STORAGE_REPORTS_BUCKET", default="kbot-reports")

# Catalog (fonte unica prezzi/servizi/percorsi). Interim: file committato in
# app/data/catalog.json. Target: generato da k2a-catalogo (vedi
# docs/interfaccia-kbot-8e.md §2). Override con KBOT_CATALOG_PATH.
CATALOG_PATH = Path(
    _env("KBOT_CATALOG_PATH", default=str(ROOT / "app" / "data" / "catalog.json"))
).resolve()

# Motore 8e (generazione deliverable). Vuoto in dev → si usa il MOCK locale
# (kbot/mock-8e). Vedi docs/interfaccia-kbot-8e.md.
ENGINE_8E_BASE_URL = _env("K2A_8E_BASE_URL", default="http://localhost:8800")
# Bearer backend→8e. DEFAULT allineato a quello dell'8e (app/settings.py) così con
# env non settato combaciano comunque (fix "missing bearer" → motore non disponibile).
ENGINE_8E_API_KEY = _env("K2A_8E_API_KEY", default="k2a-8e-internal-loopback")

# Entitlement JWT (membrana G1) — segreto condiviso K-BOT↔8e (HS256).
ENTITLEMENT_SECRET = _env("K2A_ENTITLEMENT_SECRET")
ENTITLEMENT_TTL_S = int(_env("K2A_ENTITLEMENT_TTL", default="900") or "900")  # 15 min

# Prompt size limits, mirroring api/kbot/_shared.ts.
CHAT_SYSTEM_MAX_CHARS = int(_env("CHAT_SYSTEM_MAX_CHARS", default="26000") or "26000")
PDF_SYSTEM_MAX_CHARS = int(_env("PDF_SYSTEM_MAX_CHARS", default="55000") or "55000")
MAX_HISTORY_MESSAGES = int(_env("MAX_HISTORY_MESSAGES", default="12") or "12")
MAX_MESSAGE_CHARS = int(_env("MAX_MESSAGE_CHARS", default="900") or "900")

# PostHog Cloud EU (server-side). Empty → analytics disabled (no-op).
POSTHOG_API_KEY = _env("POSTHOG_API_KEY")
POSTHOG_HOST = _env("POSTHOG_HOST", default="https://eu.i.posthog.com")


def _is_production() -> bool:
    return (ENVIRONMENT or "").strip().lower() in ("production", "prod")


def paywall_bypass_active() -> bool:
    """True se un flag di bypass del paywall è attivo (demo/dev)."""
    return bool(KBOT_FREE_MODE or KBOT_FAKE_PAYMENT)


def assert_paywall_safe() -> None:
    """Guard anti-misconfig: in produzione un flag di bypass del paywall
    (KBOT_FREE_MODE / KBOT_FAKE_PAYMENT) è quasi certamente un errore e
    aprirebbe la generazione dei deliverable senza pagamento.

    Fail-closed: in produzione con un bypass attivo l'avvio viene INTERROTTO
    (RuntimeError). Se il bypass è davvero voluto (es. promo temporanea), va
    dichiarato esplicitamente con KBOT_ALLOW_PAYWALL_BYPASS=1 — così resta una
    scelta cosciente e non una misconfig silenziosa.
    """
    if _is_production() and paywall_bypass_active():
        import logging

        _active = [
            name for name, on in (
                ("KBOT_FREE_MODE", KBOT_FREE_MODE),
                ("KBOT_FAKE_PAYMENT", KBOT_FAKE_PAYMENT),
            ) if on
        ]
        _allow_override = (_env("KBOT_ALLOW_PAYWALL_BYPASS", default="") or "").strip().lower() in ("1", "true", "yes")
        msg = (
            "SECURITY: paywall BYPASS attivo in PRODUCTION (%s). I deliverable 8e "
            "verrebbero generati SENZA pagamento. Disattiva questi flag o correggi "
            "ENVIRONMENT se non è davvero produzione." % ", ".join(_active)
        )
        if _allow_override:
            logging.getLogger(__name__).error(
                "%s [consentito da KBOT_ALLOW_PAYWALL_BYPASS]", msg
            )
        else:
            raise RuntimeError(
                msg + " Avvio interrotto (fail-closed). Per consentirlo "
                "intenzionalmente imposta KBOT_ALLOW_PAYWALL_BYPASS=1."
            )
