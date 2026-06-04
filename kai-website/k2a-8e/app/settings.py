"""8e settings — env-driven, loaded once."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Auth backend-to-backend (il K-BOT chiama l'8e con questa chiave).
API_KEY = os.environ.get("K2A_8E_API_KEY", "dev-key")
API_KEY_NEXT = os.environ.get("K2A_8E_API_KEY_NEXT")  # rotazione zero-downtime (G6)

# Anthropic (filiera Sonnet). Senza chiave → modalità offline deterministica
# (template), così smoke test e dev girano senza rete.
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = os.environ.get("K2A_8E_MODEL", "claude-sonnet-4-5")
ANTHROPIC_PEER_MODEL = os.environ.get("K2A_8E_PEER_MODEL", "claude-haiku-4-5")

# Asset di dominio (di Luca). Se presenti, l'8e li usa; altrimenti fixture locali.
# - K2A_SKILLS_DIR: repo k2a-skills (blueprints/<id>.blueprint.json + <id>/schemas/*)
# - snapshot: grounding/legalboost.snapshot.json (generato da build_snapshot.py)
SKILLS_DIR = os.environ.get("K2A_SKILLS_DIR")  # es. /path/to/k2a-skills
FIXTURES_DIR = ROOT / "fixtures"
SNAPSHOT_PATH = Path(
    os.environ.get("K2A_8E_SNAPSHOT", str(ROOT / "grounding" / "legalboost.snapshot.json"))
).resolve()

# Output locale (Phase-1). In produzione → upload Supabase lato K-BOT (membrana G2).
OUT_DIR = Path(os.environ.get("K2A_8E_OUT_DIR", str(ROOT / "_out"))).resolve()

ENGINE_VERSION = os.environ.get("K2A_8E_VERSION", "0.1.0-phase1")

# Catalogo chiuso: in Phase-1 solo LegalBoost è instradabile.
CATALOGO_CHIUSO = {
    "flusso-legalboost-pmi": "flusso-legalboost-pmi.boost",
    "check-legale-express": "check-legale-express.check",
}
CONFIDENCE_REFUSE_THRESHOLD = 0.4

# Timeout hard job (oltre → error). Membrana G7.
JOB_TIMEOUT_S = int(os.environ.get("K2A_8E_JOB_TIMEOUT", "240"))
