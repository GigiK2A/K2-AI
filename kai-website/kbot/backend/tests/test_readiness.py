"""Regression tests for the chat↔8e required-fields decoupling bug.

Real chat (studioassociatoevolution.com, marketing/StrategyBoost): the bot said
"ho tutto quello che serve" and fired generation, but StrategyBoost's form requires
`competitor` + `obiettivo_strategico`, which the conversation never collected. The
autofill correctly omits un-said fields → 8e Gate 0 fail-closes with
`insufficient_or_inconsistent_input` → the user sees a generic dead-end.

`readiness.py` is the deterministic, shared decision ("which required fields are
still missing?") used both to pre-flight the generate call AND to tell the chat bot
what to ask for. Pure, no app imports — loaded standalone like services.py tests.
"""
from __future__ import annotations

import importlib.util
import os

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_standalone(rel_path: str, name: str):
    spec = importlib.util.spec_from_file_location(name, os.path.join(_BACKEND, rel_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


readiness = _load_standalone("app/lib/readiness.py", "kbot_readiness_under_test")


# StrategyBoost form projected by 8e /v1/form (required → obbligatorio).
STRATEGY_CAMPI = [
    {"id": "descrizione_azienda", "obbligatorio": True,
     "label": "settore, prodotti/servizi, clienti target, anno fondazione, dipendenti, fatturato"},
    {"id": "competitor", "obbligatorio": True, "label": "2-3 competitor principali"},
    {"id": "obiettivo_strategico", "obbligatorio": True,
     "label": "cosa vuole ottenere nei prossimi 1-3 anni"},
    {"id": "settore_ateco", "obbligatorio": False, "label": "codice ATECO"},
]


def test_missing_required_flags_uncollected_required_fields():
    """The exact failing chat: only descrizione_azienda was deducible."""
    inputs = {"descrizione_azienda": "Studio ingegneria, progettazione, 10 dip, 2M",
              "ragione_sociale": "Studio Associato Evolution"}
    missing = readiness.missing_required(STRATEGY_CAMPI, inputs)
    ids = [c["id"] for c in missing]
    assert ids == ["competitor", "obiettivo_strategico"]


def test_missing_required_empty_when_all_required_present():
    inputs = {
        "descrizione_azienda": "Studio ingegneria",
        "competitor": [{"nome": "Studio Rossi"}, {"nome": "Tecnoprogetti"}],
        "obiettivo_strategico": "Crescere del 30% in 2 anni",
    }
    assert readiness.missing_required(STRATEGY_CAMPI, inputs) == []


def test_missing_required_treats_empty_values_as_missing():
    """An empty list/string is as useless as an absent key."""
    inputs = {"descrizione_azienda": "x", "competitor": [], "obiettivo_strategico": ""}
    ids = [c["id"] for c in readiness.missing_required(STRATEGY_CAMPI, inputs)]
    assert ids == ["competitor", "obiettivo_strategico"]


def test_missing_required_ignores_optional_fields():
    inputs = {"descrizione_azienda": "x", "competitor": [{"nome": "A"}],
              "obiettivo_strategico": "y"}
    # settore_ateco is optional and absent → must NOT be flagged.
    assert readiness.missing_required(STRATEGY_CAMPI, inputs) == []


def test_format_missing_labels_uses_human_labels():
    missing = readiness.missing_required(STRATEGY_CAMPI, {"descrizione_azienda": "x"})
    text = readiness.format_missing_labels(missing)
    assert "2-3 competitor principali" in text
    assert "cosa vuole ottenere nei prossimi 1-3 anni" in text


def test_required_fields_hint_lists_required_labels_for_chat():
    hint = readiness.required_fields_hint(STRATEGY_CAMPI, boost_label="StrategyBoost")
    # The chat bot must learn it needs these BEFORE declaring readiness.
    assert "competitor" in hint.lower()
    assert "obiettivo" in hint.lower()
    # Optional fields are not forced on the user.
    assert "ateco" not in hint.lower()


def test_required_fields_hint_empty_when_no_required():
    assert readiness.required_fields_hint([], boost_label="X") == ""
    assert readiness.required_fields_hint(
        [{"id": "a", "obbligatorio": False, "label": "a"}], boost_label="X") == ""
