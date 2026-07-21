"""Normalizzazione centralizzata dei valori prima del rendering (PDF/Excel).

Bug critico osservato nei report: nell'output finale comparivano oggetti JSON
grezzi al posto del solo testo, es.

    {"type": "string", "$value": "Rischio complessivo medio..."}

o `[object Object]`. Causa: la coercizione valore→testo (render._scalar_str/_rich,
helper di styling) chiudeva con `str(v)`, che su un dict stampa il dict.

Questo modulo fornisce UN solo punto di verità per "scartare l'involucro" attorno
a un valore, qualunque forma abbia:
- stringhe / numeri / bool / None;
- array;
- wrapper `{type, $value}` e `{value}` (structured output / SDK / parser);
- JSON serializzato per errore come stringa ('{"$value": "x"}');
- wrapper annidati.

`unwrap_value(v)` → il valore "nudo" (scalare/list/dict) senza involucri.
`to_text(v)` → stringa da mostrare (unwrap + join delle liste).
`find_leaked_wrappers(text)` → pattern residui che NON devono finire in un report
(usato dal quality gate pre-consegna).
"""

from __future__ import annotations

import json
import re
from typing import Any

# Chiavi che indicano un "involucro" attorno al valore reale, non un dato di dominio.
# NB: NON includiamo le chiavi italiane dei KPI ("valore", "value_it") — quelle sono dati.
_WRAPPER_VALUE_KEYS = ("$value", "value", "text", "content", "output")
_WRAPPER_META_KEYS = {"type", "$type", "kind", "format", "role", "annotations", "citations"}

_MAX_UNWRAP_DEPTH = 8


def _looks_like_json(s: str) -> bool:
    t = s.strip()
    return len(t) >= 2 and t[0] in "{[" and t[-1] in "}]"


def unwrap_value(v: Any, _depth: int = 0) -> Any:
    """Restituisce il valore reale togliendo ogni involucro noto.

    Ricorsivo e a prova di ciclo (cap di profondità). Non solleva mai: in caso di
    dubbio restituisce il valore così com'è.
    """
    if _depth >= _MAX_UNWRAP_DEPTH:
        return v

    # Stringa che in realtà è un JSON serializzato (es. structured output stringato).
    if isinstance(v, str):
        if _looks_like_json(v):
            try:
                parsed = json.loads(v)
            except (ValueError, TypeError):
                return v
            # Solo se il parse cambia forma in qualcosa di "sballabile" lo seguiamo.
            if isinstance(parsed, (dict, list)):
                return unwrap_value(parsed, _depth + 1)
        return v

    # Dizionario-involucro: {type, $value}, {value}, {text}, ...
    if isinstance(v, dict):
        keys = set(v.keys())
        for key in _WRAPPER_VALUE_KEYS:
            if key in v:
                # È un involucro solo se le ALTRE chiavi sono meta (type/kind/...) o assenti.
                other = keys - {key}
                if not other or other <= _WRAPPER_META_KEYS:
                    return unwrap_value(v[key], _depth + 1)
        # Dizionario di dominio reale (es. KPI {nome, valore, semaforo}) → invariato.
        return v

    # Lista: sballa ogni elemento.
    if isinstance(v, list):
        return [unwrap_value(item, _depth + 1) for item in v]

    # Scalare (int/float/bool/None) → invariato.
    return v


def to_text(v: Any) -> str:
    """Valore → stringa da mostrare. Unwrap + join delle liste. Mai stampa un dict grezzo."""
    v = unwrap_value(v)
    if v is None:
        return ""
    if isinstance(v, bool):
        return "Sì" if v else "No"
    if isinstance(v, list):
        parts = [to_text(item) for item in v]
        return ", ".join(p for p in parts if p)
    if isinstance(v, dict):
        # Un dict non-involucro non è testo: non stampiamo mai la sua repr Python.
        # Il quality gate segnalerà se una struttura è arrivata fin qui.
        return ""
    return str(v)


# ── Guard pre-render / quality gate ───────────────────────────────────────────
# Pattern che, se presenti nel testo finale, indicano un valore non normalizzato.
_LEAK_PATTERNS = [
    (r'"\$value"', "wrapper $value non sballato"),
    (r'"type"\s*:\s*"string"', "wrapper {type:string} non sballato"),
    (r'\[object Object\]', "oggetto JS stampato come [object Object]"),
    (r'(?<![\w/.-])undefined(?![\w])', "letterale 'undefined' in output"),
    (r"\{'\$?value'", "repr Python di un dict-involucro"),
]
_LEAK_RE = [(re.compile(p), why) for p, why in _LEAK_PATTERNS]


def find_leaked_wrappers(text: Any) -> list[str]:
    """Ritorna le descrizioni dei pattern-involucro trovati nel testo (vuoto = pulito)."""
    s = "" if text is None else str(text)
    found: list[str] = []
    for rx, why in _LEAK_RE:
        if rx.search(s):
            found.append(why)
    return found
