"""8e settings — env-driven, loaded once. Consuma gli asset reali (handoff v2.27)."""
from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Auth backend-to-backend.
API_KEY = os.environ.get("K2A_8E_API_KEY", "dev-key")
API_KEY_NEXT = os.environ.get("K2A_8E_API_KEY_NEXT")  # rotazione (membrana G6)

# Entitlement JWT (membrana G1) — segreto condiviso col K-BOT (HS256).
ENTITLEMENT_SECRET = os.environ.get("K2A_ENTITLEMENT_SECRET")

# Anthropic (filiera). Senza chiave → offline deterministico (template).
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = os.environ.get("K2A_8E_MODEL", "claude-sonnet-4-5")
# Modello "light" per sezioni meccaniche (liste/kpi/scalari): tiering di costo.
# Default = stesso modello → tiering DISATTIVO finché non si setta un modello più
# economico (es. claude-haiku-4-5). L'analisi core resta sempre su MODEL.
ANTHROPIC_MODEL_LIGHT = os.environ.get("K2A_8E_MODEL_LIGHT", ANTHROPIC_MODEL)
# Se la chiave è presente ma la chiamata fallisce: dev=degrada offline; prod=rilancia.
# Default true (dev). In produzione settare K2A_8E_ALLOW_OFFLINE=false.
ALLOW_OFFLINE_FALLBACK = (os.environ.get("K2A_8E_ALLOW_OFFLINE", "true").lower()
                          in ("1", "true", "yes"))

# Asset reali (handoff Luca v2.27), vendorizzati nel repo.
BLUEPRINTS_DIR = Path(os.environ.get("K2A_BLUEPRINTS_DIR", str(ROOT / "blueprints"))).resolve()
MANIFEST_PATH = BLUEPRINTS_DIR / "manifest.json"
SNAPSHOT_PATH = Path(
    os.environ.get("K2A_8E_SNAPSHOT", str(ROOT / "grounding" / "grounding-snapshot.json"))
).resolve()
BOOST_PLACEHOLDERS_PATH = ROOT / "grounding" / "boost_placeholders.json"
CATALOG_PATH = Path(os.environ.get("K2A_8E_CATALOG", str(ROOT / "catalog" / "catalog.json"))).resolve()

OUT_DIR = Path(os.environ.get("K2A_8E_OUT_DIR", str(ROOT / "_out"))).resolve()
ENGINE_VERSION = os.environ.get("K2A_8E_VERSION", "0.2.0-phase1-realassets")

# --- Catalogo chiuso Phase-1: SOLO LegalBoost (pilota) -------------------
# manifest mappa 15 service_id → skill. In Phase-1 sono instradabili solo i
# service_id serviti dal blueprint LegalBoost (gli altri → out_of_catalog).
def _manifest_services() -> dict:
    try:
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8")).get("services", {})
    except Exception:
        return {}


# Catalogo chiuso = TUTTI i 15 service_id del manifest (12 boost). LegalBoost +
# FiscoBoost usano l'assembly dedicato (voci-shape); gli altri il generatore
# generico schema-driven. Restringibile via K2A_8E_PILOT_ONLY=1 (solo LegalBoost).
PILOT_SKILL = "flusso-legalboost-pmi"
_PILOT_ONLY = os.environ.get("K2A_8E_PILOT_ONLY", "0") in ("1", "true", "yes")
CATALOGO_CHIUSO = {
    sid: v for sid, v in _manifest_services().items()
    if (not _PILOT_ONLY) or v.get("skill") == PILOT_SKILL
}
# Skill con assembly DEDICATO (hybrid prosa+meta, output-schema specifico).
# Solo LegalBoost: gli altri 11 (FiscoBoost incluso) hanno schemi diversi →
# generatore generico schema-driven.
VOCI_SHAPE_SKILLS = {"flusso-legalboost-pmi"}

CONFIDENCE_REFUSE_THRESHOLD = 0.4
JOB_TIMEOUT_S = int(os.environ.get("K2A_8E_JOB_TIMEOUT", "240"))

# Rate-limit per chiave Bearer su /v1/deliverables (anti-abuse). 0 = disattivo.
RL_MAX = int(os.environ.get("K2A_8E_RL_MAX", "30"))
RL_WINDOW_S = int(os.environ.get("K2A_8E_RL_WINDOW", "60"))
