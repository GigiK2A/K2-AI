"""Gate fail-closed per i report premium non-8e."""
from __future__ import annotations

import re
from typing import Any, Iterable


class ReportQualityError(ValueError):
    pass


_BROKEN = re.compile(
    r"(?:\[\s*BOZZA\s+OFFLINE\s*\]|Segnaposto deterministico|override_locale|"
    r"ANTHROPIC_API_KEY|\bTBD\b|\bTODO\b|\[\s*(?:cliente|citt[aà]|regione)\s*\])", re.I)
_GENERIC_META = {"", "cliente", "azienda", "nome cliente / progetto", "—", "-", "n/d"}

# Disclaimer footer di default (fail-safe): iniettato se il modello lo omette o produce un
# testo privo di riserva. Le keyword di riserva usano lo STEM ("verific" copre verificare/
# verificate/verifica…, "sostitu" copre non sostituisce/sostitutivo) così un disclaimer
# genuino con inflessione diversa NON viene sovrascritto inutilmente.
_DISCLAIMER_KEYWORDS = ("verific", "non sostitu", "sostitu", "orientament")
_DEFAULT_DISCLAIMER = (
    "Documento generato a scopo di orientamento sulla base dei dati raccolti in sessione e "
    "di benchmark di mercato. Non sostituisce una consulenza professionale: verificare con "
    "strumenti, fonti e professionisti dedicati prima di decisioni operative."
)


def _ensure_footer_disclaimer(analysis: dict) -> None:
    """Fail-safe NON bloccante: se manca un disclaimer footer valido, iniettane uno di
    default. Non solleva mai — un report per il resto valido non deve fallire per questo."""
    footer = analysis.get("footer")
    if not isinstance(footer, dict):
        footer = {}
        analysis["footer"] = footer
    disc = str(footer.get("disclaimer") or "").strip()
    if not disc or not any(k in disc.lower() for k in _DISCLAIMER_KEYWORDS):
        footer["disclaimer"] = _DEFAULT_DISCLAIMER
_PROJECTION = re.compile(r"(?:proiez|scenario|forecast|prevision|stimat[oa])", re.I)
_ASSUMPTION = re.compile(r"(?:assunzion|ipotesi esplicita|scenario illustrativo|da validare)", re.I)
_NUMBER = re.compile(r"(?:€\s*)?\d+(?:[.,]\d+)?\s*(?:%|€|x\b)?", re.I)


def _strings(v: Any) -> Iterable[str]:
    if isinstance(v, str):
        yield v
    elif isinstance(v, dict):
        for x in v.values():
            yield from _strings(x)
    elif isinstance(v, list):
        for x in v:
            yield from _strings(x)


def _meta_has_client(meta: dict) -> bool:
    lines = meta.get("client_meta_lines") or meta.get("subtitle_lines") or []
    if isinstance(lines, str):
        lines = [lines]
    return any(
        str(x).strip().lower() not in _GENERIC_META
        and not re.match(r"^(?:generato|codice|periodo|documento|versione)\b", str(x).strip(), re.I)
        for x in lines if str(x).strip()
    )


def validate_report(analysis: dict, category: str = "generic") -> dict:
    # Fail-safe deterministico: garantisci sempre un disclaimer footer (NON blocca).
    if isinstance(analysis, dict):
        _ensure_footer_disclaimer(analysis)

    errors: list[str] = []
    flat = "\n".join(_strings(analysis))
    if _BROKEN.search(flat):
        errors.append("placeholder o token interno presente nel report")

    meta = analysis.get("meta") or {}
    if not isinstance(meta, dict) or not _meta_has_client(meta):
        errors.append("metadati cliente/progetto mancanti o generici")

    blocks = analysis.get("blocks") or []
    for i, block in enumerate(blocks):
        if not isinstance(block, dict):
            continue
        if block.get("type") == "kpi_grid":
            for j, item in enumerate(block.get("items") or []):
                if not isinstance(item, dict):
                    continue
                if "verified" not in item:
                    errors.append(f"KPI {i}.{j} senza provenienza verified")
                if item.get("verified") is False and not str(item.get("note") or "").strip():
                    errors.append(f"KPI {i}.{j} stimato senza nota/assunzioni")
        if block.get("type") == "data_table":
            title_intro = f"{block.get('title','')} {block.get('intro','')}"
            rows_text = " ".join(_strings(block.get("rows") or []))
            if _PROJECTION.search(title_intro) and _NUMBER.search(rows_text):
                callout = block.get("callout") or {}
                assumptions = f"{block.get('intro','')} {callout.get('label','')} {callout.get('body','')}"
                if not _ASSUMPTION.search(assumptions):
                    errors.append(f"tabella proiettiva '{block.get('title','')}' senza assunzioni esplicite")

    if category == "bilancio":
        for block in blocks:
            if isinstance(block, dict) and block.get("type") == "executive_summary":
                score = block.get("score") or (block.get("gauge") or {}).get("value")
                breakdown = block.get("score_breakdown") or block.get("breakdown")
                if score is not None and not breakdown:
                    errors.append("score finanziario senza breakdown e criteri riproducibili")

    if errors:
        raise ReportQualityError("report bloccato dal quality gate: " + "; ".join(dict.fromkeys(errors)))
    return analysis
