"""k2a_validation — validatore deliverable K2-AI portato in LIBRERIA (no MCP/stdio).

Pacchetto di verifica per l'8e: le funzioni core L1 (validate_blueprint) e
L2 (lint_deliverable) sono pure e importabili, separate dal wrapper FastMCP
di `k2a-mcp-deliverable`. Parità garantita: stesso `linter.py`, stesso
meta-schema.

Uso:
    from k2a_validation import validate_blueprint, lint_deliverable, default_meta_schema
    r1 = validate_blueprint(bp_dict, default_meta_schema())
    r2 = lint_deliverable(deliverable_dict, bp_dict)
"""
from .validation import (
    validate_blueprint,
    lint_deliverable,
    default_meta_schema,
)

__all__ = ["validate_blueprint", "lint_deliverable", "default_meta_schema"]
