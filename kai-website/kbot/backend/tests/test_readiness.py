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


def test_has_identity_detects_usable_company_name():
    """Il Gate 0 dell'8e ESIGE un nome-cliente (display_name). Il pre-flight deve saperlo
    riconoscere per nominarlo tra i dati mancanti, invece di lasciarlo cadere nel Gate 0
    (che poi dà un errore generico). Mirror di 8e quality.display_name."""
    assert readiness.has_identity({"ragione_sociale": "Studio Evolution"}) is True
    assert readiness.has_identity({"azienda": "ACME Srl"}) is True
    # descrizione breve = nominale → accettata (come 8e)
    assert readiness.has_identity({"descrizione_azienda": "Studio di ingegneria di Perugia"}) is True


def test_has_identity_false_when_missing_or_generic():
    assert readiness.has_identity({}) is False
    assert readiness.has_identity({"ragione_sociale": ""}) is False
    assert readiness.has_identity({"ragione_sociale": "azienda"}) is False  # generico
    # descrizione LUNGA (>100) NON conta come identità (quirk reale di 8e display_name)
    long_desc = "Studio di ingegneria, progettazione, clienti privati e società, " * 3
    assert readiness.has_identity({"descrizione_azienda": long_desc}) is False


def test_required_fields_hint_empty_when_no_required():
    assert readiness.required_fields_hint([], boost_label="X") == ""
    assert readiness.required_fields_hint(
        [{"id": "a", "obbligatorio": False, "label": "a"}], boost_label="X") == ""


# --- Bug M: array a enum opzionale con valori inventati non deve far rifiutare l'8e ---
_ENUM_SCHEMA = {
    "type": "object",
    "required": ["ragione_sociale"],
    "properties": {
        "ragione_sociale": {"type": "string"},
        "tratta_dati_personali": {
            "type": "array",
            "items": {"type": "string",
                      "enum": ["clienti", "dipendenti", "marketing", "fornitori", "videosorveglianza"]},
        },
    },
}


def test_drop_invalid_optional_sanitizes_enum_array_keeps_valid():
    # autofill mescola valori validi ('clienti') e inventati ('email','ip') → filtra ai validi
    inputs = {"ragione_sociale": "Moda Srl",
              "tratta_dati_personali": ["clienti", "email", "marketing", "ip"]}
    out, dropped = readiness.drop_invalid_optional(_ENUM_SCHEMA, inputs)
    assert out["tratta_dati_personali"] == ["clienti", "marketing"]
    assert "tratta_dati_personali" not in dropped  # sanitizzato, non scartato


def test_drop_invalid_optional_drops_enum_array_when_all_invalid():
    # tutti fuori enum (il caso reale del Test #5) → scarta il campo, niente refuse 8e
    inputs = {"ragione_sociale": "Moda Srl",
              "tratta_dati_personali": ["anagrafe_cliente", "email", "cronologia_acquisti", "ip"]}
    out, dropped = readiness.drop_invalid_optional(_ENUM_SCHEMA, inputs)
    assert "tratta_dati_personali" not in out
    assert "tratta_dati_personali" in dropped
