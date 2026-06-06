"""Gate L1 + L2 — delega alla libreria REALE di Luca (k2a_validation).

L1 = validate_blueprint(blueprint, meta_schema) → blueprint vs meta-schema.
L2 = lint_deliverable(lint_instance, blueprint) → regole linter R01-R12.
Niente più implementazione locale: si usa il codice consegnato (D-043).
"""
from __future__ import annotations

from k2a_validation import validate_blueprint as _l1
from k2a_validation import lint_deliverable as _l2

from . import assets


def l1(blueprint: dict) -> dict:
    return _l1(blueprint, assets.meta_schema())


def l2(lint_instance: dict, blueprint: dict) -> dict:
    return _l2(lint_instance, blueprint)
