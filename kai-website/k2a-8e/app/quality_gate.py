"""Quality gate pre-consegna del report (spec §12).

Ultimo controllo prima di consegnare PDF+Excel: se rileva difetti BLOCCANTI il
report non va consegnato. Difetti oggettivi e domain-agnostici (nessun hardcoding
per singolo cliente/boost):

BLOCCANTI
- oggetti/involucri JSON non sballati (`{type,$value}`, `{value}`, JSON-stringato);
- `[object Object]`, `undefined`, repr di dict finiti come testo;
- dato mancante (N/D) con semaforo VERDE;
- KPI placeholder (valore=target=1) con semaforo verde.

NON BLOCCANTI (warning)
- stesso valore ripetuto con etichette diverse / KPI duplicati tra sezioni.

Restituisce un report tecnico leggibile: codice, severità, posizione, causa
probabile, correzione consigliata.
"""

from __future__ import annotations

from typing import Any, Iterator

from . import normalize as NORM

SEVERITY_BLOCK = "block"
SEVERITY_WARN = "warn"

# Valori che rappresentano "dato mancante" (mai un semaforo verde sopra).
_MISSING_TOKENS = {"", "n/d", "nd", "n.d.", "n/a", "na", "-", "—", "–",
                   "dati non disponibili", "non disponibile", "da rilevare", "da raccogliere"}


def _finding(code: str, severity: str, location: str, cause: str, fix: str,
             value: Any = None) -> dict:
    f = {"code": code, "severity": severity, "location": location,
         "cause": cause, "fix": fix}
    if value is not None:
        f["value"] = value
    return f


def _is_missing(v: Any) -> bool:
    v = NORM.unwrap_value(v)
    if v is None:
        return True
    if isinstance(v, str) and v.strip().lower() in _MISSING_TOKENS:
        return True
    return False


def _is_wrapper_dict(v: Any) -> bool:
    """True se v è un dict-involucro ({type,$value}/{value}) non ancora sballato."""
    return isinstance(v, dict) and not isinstance(NORM.unwrap_value(v), dict)


def _num(v: Any):
    v = NORM.unwrap_value(v)
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return v
    return None


def _walk(obj: Any, path: str = "") -> Iterator[tuple[str, Any]]:
    """Percorre ricorsivamente la struttura, restituendo (path, valore)."""
    yield path, obj
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _walk(v, f"{path}.{k}" if path else str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _walk(v, f"{path}[{i}]")


def _iter_kpis(deliverable: Any) -> Iterator[tuple[str, dict]]:
    """Trova i dict che 'sono' KPI: hanno un semaforo e un valore."""
    for path, node in _walk(deliverable):
        if isinstance(node, dict) and "semaforo" in node and (
                "valore" in node or "value" in node):
            yield path, node


def _kpi_value(kpi: dict) -> Any:
    return kpi.get("valore", kpi.get("value"))


def run_report_quality_gate(deliverable: Any, workbook: Any = None,
                            evidence: Any = None) -> dict:
    """Esegue il gate. Ritorna {ok, blocking, warnings, findings, report}."""
    findings: list[dict] = []

    # 1) involucri JSON non sballati (stringhe con pattern-leak o dict-involucro residui)
    for path, val in _walk(deliverable):
        if isinstance(val, str):
            for why in NORM.find_leaked_wrappers(val):
                findings.append(_finding(
                    "leaked_wrapper", SEVERITY_BLOCK, path, why,
                    "Passa il valore da normalize.to_text() prima del render.", val[:80]))
        elif _is_wrapper_dict(val) and path:   # il root può essere un dict legittimo
            findings.append(_finding(
                "wrapper_dict", SEVERITY_BLOCK, path,
                "valore-involucro {type,$value}/{value} non sballato",
                "Sballa con normalize.unwrap_value() a monte del render.",
                str(val)[:80]))

    # 2) KPI: dato mancante o placeholder con semaforo verde
    seen_kpis: list[tuple[str, Any, str]] = []
    for path, kpi in _iter_kpis(deliverable):
        sem = str(NORM.unwrap_value(kpi.get("semaforo")) or "").strip().lower()
        val = _kpi_value(kpi)
        tgt = kpi.get("target")
        label = str(NORM.unwrap_value(kpi.get("nome") or kpi.get("label") or "")).strip()
        if sem == "verde" and _is_missing(val):
            findings.append(_finding(
                "missing_green", SEVERITY_BLOCK, path,
                f"KPI '{label or path}' senza valore ma con semaforo verde",
                "Dato mancante ⇒ nessun semaforo (status=not_available, displayValue='Dati non disponibili').",
                label))
        elif sem == "verde" and _num(val) == 1 and _num(tgt) == 1:
            findings.append(_finding(
                "placeholder_green", SEVERITY_BLOCK, path,
                f"KPI '{label or path}' con valore=target=1 e semaforo verde (segnatura placeholder)",
                "Non riempire i KPI mancanti con 1/verde: marcali not_available.",
                label))
        # raccolta per dedup (warning)
        if label:
            seen_kpis.append((label.lower(), NORM.unwrap_value(val), path))

    # 3) dedup (warning): stesso (etichetta, valore) ripetuto in più punti
    by_label: dict[str, list[tuple[Any, str]]] = {}
    for lbl, val, path in seen_kpis:
        by_label.setdefault(lbl, []).append((val, path))
    for lbl, occ in by_label.items():
        if len(occ) > 1 and len({str(v) for v, _ in occ}) == 1:
            findings.append(_finding(
                "duplicate_kpi", SEVERITY_WARN, ", ".join(p for _, p in occ),
                f"KPI '{lbl}' ripetuto identico in {len(occ)} punti",
                "Descrivi il KPI una sola volta; altrove richiamalo in forma sintetica (referencedIn)."))

    blocking = [f for f in findings if f["severity"] == SEVERITY_BLOCK]
    warnings = [f for f in findings if f["severity"] == SEVERITY_WARN]
    return {
        "ok": not blocking,
        "blocking": blocking,
        "warnings": warnings,
        "findings": findings,
        "report": format_report(findings),
    }


def format_report(findings: list[dict]) -> str:
    """Report tecnico leggibile del gate."""
    if not findings:
        return "Quality gate: nessun problema rilevato."
    lines = ["Quality gate — problemi rilevati:"]
    for f in findings:
        tag = "BLOCCANTE" if f["severity"] == SEVERITY_BLOCK else "warning"
        lines.append(f"[{tag}] {f['code']} @ {f['location']}")
        lines.append(f"    causa: {f['cause']}")
        lines.append(f"    correzione: {f['fix']}")
    return "\n".join(lines)
