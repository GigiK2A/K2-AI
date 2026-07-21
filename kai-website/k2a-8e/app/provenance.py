"""Provenienza dei numeri nel report (spec §2/§3, Test 2).

Nessun numero deve comparire come dato reale se non ha una fonte verificabile.
Ogni metrica può dichiarare `source` (+ eventuale `sourceReference`/`assumptionNote`);
`validate_metric` verifica che un valore dichiarato come dato dell'utente/documento
esista davvero nell'evidence store, altrimenti è un errore bloccante.

Retro-compatibile: le metriche SENZA `source` non vengono validate qui (le copre il
resto della pipeline di grounding), così non si generano falsi positivi sui KPI
esistenti. La validazione scatta solo quando una metrica dichiara la sua provenienza.
"""

from __future__ import annotations

from typing import Any, Iterable

from . import normalize as NORM

# Provenienze ammesse (spec §2).
USER_PROVIDED = "user_provided"
UPLOADED_DOCUMENT = "uploaded_document"
SYSTEM_CALCULATED = "system_calculated"
BENCHMARK = "benchmark"
ASSUMPTION = "assumption"
EXAMPLE = "example"
MISSING = "missing"

VALID_SOURCES = {USER_PROVIDED, UPLOADED_DOCUMENT, SYSTEM_CALCULATED,
                 BENCHMARK, ASSUMPTION, EXAMPLE, MISSING}

# Fonti per cui il VALORE deve esistere nell'evidence store (dati "reali").
_MUST_BE_GROUNDED = {USER_PROVIDED, UPLOADED_DOCUMENT}

_MISSING_DISPLAY = {"", "dati non disponibili", "n/d", "nd", "n/a", "da rilevare", "da raccogliere"}


def _as_number(v: Any):
    v = NORM.unwrap_value(v)
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        t = v.strip().replace("€", "").replace("%", "").replace(" ", "")
        if not t:
            return None
        # Convenzione italiana: la virgola è il decimale, il punto separa le migliaia.
        if "," in t:
            t = t.replace(".", "").replace(",", ".")   # 1.234,56 → 1234.56
        else:
            t = t.replace(".", "")                       # 1.000 → 1000 (millesimi, non 1,0)
        try:
            return float(t)
        except ValueError:
            return None
    return None


def build_evidence(*sources: Any) -> set:
    """Costruisce l'insieme dei valori verificabili (numeri normalizzati + stringhe)
    percorrendo ricorsivamente inputs e/o documenti. Usato come evidence store."""
    ev: set = set()

    def _walk(obj: Any) -> None:
        obj = NORM.unwrap_value(obj)
        if isinstance(obj, dict):
            for v in obj.values():
                _walk(v)
        elif isinstance(obj, list):
            for v in obj:
                _walk(v)
        else:
            n = _as_number(obj)
            if n is not None:
                ev.add(round(n, 4))
            elif isinstance(obj, str) and obj.strip():
                ev.add(obj.strip().lower())

    for s in sources:
        _walk(s)
    return ev


def value_in_evidence(value: Any, evidence: Iterable) -> bool:
    """True se il valore è ancorato nell'evidence store (match numerico con tolleranza
    o match stringa). Un evidence vuoto/None → non si può verificare → False."""
    ev = set(evidence or [])
    if not ev:
        return False
    n = _as_number(value)
    if n is not None:
        r = round(n, 4)
        if r in ev:
            return True
        # tolleranza 0.5% per arrotondamenti
        return any(isinstance(e, float) and abs(e - r) <= max(abs(r) * 0.005, 0.01) for e in ev)
    s = NORM.to_text(value).strip().lower()
    return bool(s) and s in ev


def _finding(code: str, severity: str, location: str, cause: str, fix: str) -> dict:
    return {"code": code, "severity": severity, "location": location, "cause": cause, "fix": fix}


def validate_metric(metric: dict, evidence: Iterable, location: str = "") -> list[dict]:
    """Valida una metrica con provenienza dichiarata. Ritorna findings (vuoto = ok).

    - user_provided / uploaded_document: il valore DEVE esistere nell'evidence store;
    - missing: il valore DEVE essere nullo/'Dati non disponibili';
    - benchmark/assumption/example/system_calculated: ammessi (non devono esistere
      tra i dati reali; benchmark/assumption vanno solo marcati graficamente altrove).
    """
    if not isinstance(metric, dict):
        return []
    source = str(metric.get("source") or "").strip().lower()
    if not source:
        return []   # nessuna provenienza dichiarata → non validata qui
    label = str(NORM.unwrap_value(metric.get("label") or metric.get("nome") or "")).strip()
    loc = location or label or "metric"
    value = metric.get("value", metric.get("valore"))
    out: list[dict] = []

    if source not in VALID_SOURCES:
        out.append(_finding("source_non_valida", "block", loc,
                            f"source '{source}' non riconosciuta",
                            f"Usa una fra: {', '.join(sorted(VALID_SOURCES))}."))
        return out

    if source in _MUST_BE_GROUNDED:
        if not value_in_evidence(value, evidence):
            out.append(_finding(
                "ungrounded_metric", "block", loc,
                f"'{label or loc}' dichiarata {source} ma il valore {NORM.to_text(value)!r} "
                "non esiste nell'evidence store",
                "Non presentare come dato reale un valore non verificabile: "
                "marcalo assumption/benchmark o rimuovilo."))
    elif source == MISSING:
        disp = NORM.to_text(value).strip().lower()
        if value is not None and disp not in _MISSING_DISPLAY:
            out.append(_finding(
                "missing_con_valore", "warn", loc,
                f"'{label or loc}' è 'missing' ma porta un valore ({NORM.to_text(value)})",
                "Un dato missing non deve avere valore numerico: usa null/'Dati non disponibili'."))
    return out
