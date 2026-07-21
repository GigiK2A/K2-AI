"""Test del normalizzatore centrale dei valori (app/normalize.py) e del suo uso
nel rendering. Copre il Bug A (oggetti JSON grezzi nel PDF) e parte del Test 8
della spec (nessun placeholder tecnico)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import normalize as NORM  # noqa: E402


# ── Test 1 (spec): wrapper {type,$value} → solo il valore ──────────────────────
def test_unwrap_type_value_wrapper():
    assert NORM.to_text({"type": "string", "$value": "Testo corretto"}) == "Testo corretto"
    assert NORM.unwrap_value({"type": "string", "$value": "Testo"}) == "Testo"


def test_unwrap_value_wrapper():
    assert NORM.to_text({"value": "X"}) == "X"
    assert NORM.to_text({"text": "Y"}) == "Y"


def test_unwrap_nested_wrapper():
    nested = {"type": "object", "$value": {"value": "profondo"}}
    assert NORM.to_text(nested) == "profondo"


def test_unwrap_json_string():
    assert NORM.to_text('{"type":"string","$value":"da stringa"}') == "da stringa"
    assert NORM.to_text('{"value": 42}') == "42"


def test_scalars_and_none():
    assert NORM.to_text("ciao") == "ciao"
    assert NORM.to_text(None) == ""
    assert NORM.to_text(True) == "Sì"
    assert NORM.to_text(False) == "No"
    assert NORM.to_text(42) == "42"


def test_list_joins():
    assert NORM.to_text(["a", "b", "c"]) == "a, b, c"
    assert NORM.to_text([{"$value": "x"}, {"$value": "y"}]) == "x, y"


def test_domain_dict_is_preserved_not_unwrapped():
    # Un KPI reale {nome, valore, semaforo} NON è un involucro → resta dict.
    kpi = {"nome": "Ritardi", "valore": 22, "semaforo": "rosso"}
    assert NORM.unwrap_value(kpi) == kpi
    # value_it/valore (chiavi italiane di dominio) non vengono sballate
    assert NORM.unwrap_value({"valore": 10}) == {"valore": 10}


def test_domain_dict_not_treated_as_wrapper_when_has_real_siblings():
    # {value, unit} non è un semplice involucro: ha una sorella non-meta → resta.
    d = {"value": 100, "unit": "EUR"}
    assert NORM.unwrap_value(d) == d


# ── Guard pre-render (quality gate) ────────────────────────────────────────────
def test_find_leaked_wrappers_detects_patterns():
    assert NORM.find_leaked_wrappers('{"type": "string", "$value": "x"}')
    assert NORM.find_leaked_wrappers("qualcosa [object Object] qui")
    assert NORM.find_leaked_wrappers("valore undefined")
    assert NORM.find_leaked_wrappers("testo pulito e normale") == []


# ── Integrazione col rendering reale ───────────────────────────────────────────
def test_render_scalar_str_unwraps():
    from app import render
    assert render._scalar_str({"type": "string", "$value": "Rischio medio"}) == "Rischio medio"
    # un dict non-involucro non deve mai finire come str(dict)
    out = render._scalar_str({"nome": "X", "valore": 1})
    assert "{" not in out and "'" not in out


def test_render_rich_unwraps_and_escapes():
    from app import render
    out = render._rich({"$value": "Testo <b>grassetto</b> & simboli"})
    assert "$value" not in out
    assert "[object Object]" not in out
    # il testo reale è presente (escaped)
    assert "Testo" in out
