"""Cross-check numerico dell'autofill (bug "EBITDA 720.000 → 230.000", eval lug 2026).

L'estrazione degli input passa per un LLM che può trascrivere male una cifra. Il
cross-check deterministico scarta i campi numerici il cui valore NON compare nel corpus
visto dall'LLM: meglio un report preliminare con un dato in meno che un numero sbagliato.
"""
from __future__ import annotations

import types
import sys

# shim leggeri per ambienti senza le dipendenze runtime (il codice sotto test è puro)
for _name, _attrs in (("dotenv", {"load_dotenv": lambda *a, **k: False}),):
    if _name not in sys.modules:
        _m = types.ModuleType(_name)
        [setattr(_m, k, v) for k, v in _attrs.items()]
        sys.modules[_name] = _m

from app.lib.autofill import (  # noqa: E402
    _corpus_numbers,
    _number_in_corpus,
    drop_unverified_numbers,
)

CHAT = (
    "utente: fatturato 2025 circa 4,5 mln, EBITDA 720.000 euro, utile netto 230.000. "
    "Abbiamo 60 dipendenti e crediti scaduti per 180k. Margine Nord tra 12 e 13%."
)


def _campi(*ids, tipo="number"):
    return {i: {"id": i, "tipo": tipo} for i in ids}


def test_corpus_riconosce_formati_it_en_e_abbreviati():
    nums = _corpus_numbers(CHAT)
    assert _number_in_corpus(720000, nums)      # '720.000' formato IT
    assert _number_in_corpus(230000, nums)      # idem
    assert _number_in_corpus(4500000, nums)     # '4,5 mln'
    assert _number_in_corpus(180000, nums)      # '180k'
    assert _number_in_corpus(60, nums)          # intero nudo
    assert not _number_in_corpus(555000, nums)  # mai detto


def test_numero_trascritto_male_viene_scartato():
    # il bug reale: l'LLM copia l'utile netto (230000) nel campo EBITDA
    out = {"ebitda": 230000.0, "utile_netto": 230000.0, "fatturato": 4500000.0}
    filtered, dropped = drop_unverified_numbers(out, _campi("ebitda", "utile_netto", "fatturato"), CHAT)
    # 230000 esiste in chat (è l'utile) → il check da solo non può sapere a QUALE campo
    # appartiene: passa. Ma un numero MAI detto viene scartato:
    out2 = {"ebitda": 715000.0}
    filtered2, dropped2 = drop_unverified_numbers(out2, _campi("ebitda"), CHAT)
    assert "ebitda" not in filtered2 and dropped2 == ["ebitda=715000.0"]
    assert set(filtered) == {"ebitda", "utile_netto", "fatturato"} and not dropped


def test_valore_inventato_di_sana_pianta_scartato():
    # classe multi-filiale: 'trend fatturato 100.000' mai fornito in chat
    out = {"fatturato": 100000.0, "n_dipendenti": 60}
    filtered, dropped = drop_unverified_numbers(
        out, _campi("fatturato") | _campi("n_dipendenti", tipo="integer"), CHAT)
    assert "fatturato" not in filtered
    assert filtered.get("n_dipendenti") == 60


def test_media_non_dichiarata_e_assunzione_e_viene_scartata():
    # l'utente ha detto '12-13%': 12.5 è una media inventata, non un dato
    out = {"margine_pct": 12.5}
    filtered, dropped = drop_unverified_numbers(out, _campi("margine_pct"), CHAT)
    assert "margine_pct" not in filtered


def test_enum_e_testo_non_toccati():
    campi = {"priorita": {"id": "priorita", "tipo": "number", "enum": [1, 2, 3]},
             "settore": {"id": "settore", "tipo": "string"}}
    out = {"priorita": 3, "settore": "manifatturiero"}
    filtered, dropped = drop_unverified_numbers(out, campi, CHAT)
    assert filtered == out and not dropped


def test_bilanci_verificati_ma_mai_scartati():
    # gli importi di bilancio (trascrizione da documento) producono solo un log
    out = {"bilanci": [{"anno": 2025, "voci": [
        {"sezione": "attivo", "descrizione": "crediti", "importo": 999999.0}]}]}
    filtered, dropped = drop_unverified_numbers(out, {"bilanci": {"id": "bilanci", "tipo": "array"}}, CHAT)
    assert filtered["bilanci"] and not dropped
