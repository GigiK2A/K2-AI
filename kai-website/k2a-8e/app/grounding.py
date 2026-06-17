"""Gate di GROUNDING / integrità — accanto a L1/L2 (il linter R01-R12 di Luca).

Cattura la classe di difetti che il linter STRUTTURALE non vede e che nessun
calc.py intercetta sui boost QUALITATIVI (Strategy/Marketing/Web): confabulazione,
promesse non mantenute, fatti asseriti senza fonte, segnaposto trapelati. È il
gemello del gate deterministico di Finance, portato sul lato qualitativo — dove il
modello "sembra sicuro" proprio perché niente lo può smentire.

Deterministico, no LLM. Gira sul JSON generato (i blocchi prima del render).
Ritorna findings con severità: 'block' (non si consegna) o 'warn' (si annota).
"""
from __future__ import annotations

import re
from typing import Any, Iterable

# Segnaposto/template che NON devono MAI trapelare in un deliverable venduto.
_PLACEHOLDER_PATTERNS: list[tuple[str, str]] = [
    (r"\[\s*citt[aà]\s*\]", "segnaposto [città]"),
    (r"\[\s*regione\s*\]", "segnaposto [regione]"),
    (r"\[\s*mese\s*/?\s*anno\s*\]", "segnaposto [mese/anno]"),
    (r"\bDM\s*FER\s*-?\s*X\b", "norma-segnaposto 'DM FER-X'"),
    (r"\bFER\s*-\s*X\b", "segnaposto 'FER-X'"),
    (r"\bregolamento\s+FER-?X\b", "segnaposto 'Regolamento FER-X'"),
    (r"\[[a-zàèéìòù ]{2,24}\]", "segnaposto generico [...]"),
]
_COVER_GENERICA = {"", "cliente", "—", "-", "n/d", "azienda", "la tua azienda"}


def _walk_strings(v: Any) -> Iterable[str]:
    if isinstance(v, str):
        yield v
    elif isinstance(v, dict):
        for x in v.values():
            yield from _walk_strings(x)
    elif isinstance(v, list):
        for x in v:
            yield from _walk_strings(x)


def _collect_priorities(deliverable: dict) -> list[str]:
    """Raccoglie i valori di campi 'priorità/priorita/priority' nelle iniziative."""
    found: list[str] = []

    def rec(v: Any) -> None:
        if isinstance(v, dict):
            for k, val in v.items():
                if re.fullmatch(r"priorit[aà]|priority", str(k).strip().lower()) and isinstance(val, str) and val.strip():
                    found.append(val.strip())
                else:
                    rec(val)
        elif isinstance(v, list):
            for x in v:
                rec(x)

    rec(deliverable)
    return found


def integrity_findings(deliverable: dict, *, citazioni: list | None = None,
                       inputs: dict | None = None) -> list[dict]:
    citazioni = citazioni or []
    findings: list[dict] = []
    full = "\n".join(_walk_strings(deliverable))

    # 1. SEGNAPOSTO TRAPELATI → block (output rotto/non professionale)
    for pat, desc in _PLACEHOLDER_PATTERNS:
        m = re.search(pat, full, re.I)
        if m:
            findings.append({"code": "placeholder_leak", "severity": "block",
                             "dettaglio": f"{desc}: \"{m.group(0)}\""})

    # 2. COVER non personalizzata → warn
    cliente = str((deliverable.get("meta") or {}).get("cliente") or "").strip()
    if cliente.lower() in _COVER_GENERICA:
        findings.append({"code": "cover_non_personalizzata", "severity": "warn",
                         "dettaglio": f"meta.cliente generico ('{cliente or 'vuoto'}') invece del nome reale"})

    # 3. NUMERI ESTERNI (target normativi/UE/mercato) asseriti senza essere tra le
    #    citazioni grounded → warn. È il 'FER al 72%' inventato del report Strategy.
    grounded = " ".join(_walk_strings(citazioni))
    grounded_nums = set(re.findall(r"\d+(?:[.,]\d+)?", grounded))
    for m in re.finditer(
        r"(?:target|obiettiv\w*|UE|europ\w*|direttiv\w*|regolament\w*|RED\s*III|PNIEC|FER)[^.]{0,70}?(\d{1,3}(?:[.,]\d+)?)\s*%",
        full, re.I):
        num = m.group(1)
        if num not in grounded_nums:
            findings.append({"code": "numero_esterno_non_grounded", "severity": "warn",
                             "dettaglio": f"'{num}%' asserito come fatto normativo/di mercato senza citazione grounded"})

    # 3b. DEPTH-vs-DATA → warn: deliverable ricco su input scarni = la RADICE del
    #     generico (16 pagine sicure su 4 fatti + 'non ho dati'). Non blocca, ma
    #     segnala che l'analisi è probabilmente archetipo, non QUESTO cliente.
    sostanziali = sum(1 for v in _walk_strings(inputs or {}) if len(str(v).strip()) >= 3)
    if inputs is not None and sostanziali < 5 and len(full) > 4000:
        findings.append({"code": "input_povero", "severity": "warn",
                         "dettaglio": f"deliverable ricco (~{len(full)} caratteri) su soli {sostanziali} dati "
                                      f"cliente sostanziali: rischio analisi generica/archetipo, non specifica"})

    # 4. PRIORITÀ indifferenziate → warn (la 'lettura prioritizzata' promessa è vuota)
    prios = _collect_priorities(deliverable)
    if len(prios) >= 3 and len({p.lower() for p in prios}) == 1:
        findings.append({"code": "priorita_indifferenziate", "severity": "warn",
                         "dettaglio": f"tutte le {len(prios)} iniziative hanno priorità '{prios[0]}': "
                                      f"il documento promette priorità ma non le differenzia"})

    # dedup (stesso code+dettaglio)
    seen, uniq = set(), []
    for f in findings:
        key = (f["code"], f["dettaglio"])
        if key not in seen:
            seen.add(key)
            uniq.append(f)
    return uniq


def blocks(findings: list[dict]) -> list[dict]:
    return [f for f in findings if f.get("severity") == "block"]
