"""LLM-driven analysis JSON generator (block-based).

Calls Claude Sonnet with:
- The master skill `report-premium-design` (always loaded as system anchor)
- The vertical skills mapped to the session's service_id
- The session context (collected_data, messages, uploaded files extracts)

The model returns a JSON payload conforming to the design system documented
in lib/skills/report-premium-design/SKILL.md (meta + blocks[]). The renderer
maps each block type to a Jinja2 partial — layout is deterministic.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

import anthropic

from ..settings import (
    ANTHROPIC_API_KEY,
    ANTHROPIC_PDF_MODEL,
    MAX_HISTORY_MESSAGES,
    MAX_MESSAGE_CHARS,
    PDF_SYSTEM_MAX_CHARS,
)
from .prompts import compact_messages
from .services import resolve_skills_for_session
from .skills import load_skill, load_skill_bundle

log = logging.getLogger(__name__)

# Master skill — defines the JSON schema and design composition rules.
MASTER_SKILL_NAME = "report-premium-design"


def _coalesce(*values: Any) -> Optional[str]:
    for v in values:
        if v is None:
            continue
        s = str(v).strip()
        if s:
            return s
    return None


def _build_context_block(session: dict) -> str:
    """Render session context as a compact text block for the LLM."""
    collected = session.get("collected_data") or {}
    extracted = collected.get("extractedData") or {}
    lines: List[str] = []
    fields = [
        ("Servizio Suite", collected.get("service_id")),
        ("Modalità", collected.get("mode")),
        ("Tier consigliato", collected.get("recommendedTier")),
        ("Servizio raccomandato", collected.get("recommendedServiceName")),
        ("Tipo di attività", _coalesce(collected.get("businessType"), extracted.get("businessType"))),
        ("Problema / obiettivo principale", _coalesce(collected.get("problem"), extracted.get("problem"))),
        ("Processo attuale", _coalesce(collected.get("currentProcess"), extracted.get("currentProcess"))),
        ("Obiettivo dichiarato", _coalesce(collected.get("goal"), extracted.get("goal"))),
        ("Urgenza", _coalesce(collected.get("urgency"), extracted.get("urgency"))),
        ("Dati disponibili", _coalesce(collected.get("dataAvailable"), extracted.get("dataAvailable"))),
        ("Integrazioni / tool esistenti", _coalesce(collected.get("integrations"), extracted.get("integrations"))),
        ("Budget", _coalesce(collected.get("budget"), extracted.get("budget"))),
        ("Note", _coalesce(collected.get("notes"), extracted.get("notes"))),
        ("Sintesi caso (auto)", _coalesce(collected.get("summary"), extracted.get("summary"))),
    ]
    for label, value in fields:
        if value:
            lines.append(f"- {label}: {value}")

    uploaded = collected.get("uploaded_files") or []
    if uploaded:
        lines.append("\nALLEGATI FORNITI DALL'UTENTE:")
        for f in uploaded[-4:]:
            name = f.get("name") or "file"
            method = f.get("extractionMethod") or "none"
            excerpt = (f.get("extractedText") or f.get("extractedSummary") or "").strip()[:1200]
            if excerpt:
                lines.append(f"- {name} (estrazione: {method})\n  {excerpt[:600]}{'…' if len(excerpt) > 600 else ''}")
            else:
                lines.append(f"- {name}: nessun testo estraibile")

    # URL analizzati: titoli, meta, H1-H3, schema, pagine interne crawlate.
    # PRIMA il contesto NON includeva questi dati e Sonnet inventava
    # title/H1/architettura. Ora i dati reali del sito arrivano al modello.
    urls = collected.get("analyzed_urls") or []
    if urls:
        lines.append("\nURL ANALIZZATI (dati reali estratti dal crawl):")
        for u in urls[-3:]:
            lines.append(f"\n• {u.get('url', '')}")
            if u.get("title"):
                lines.append(f"  <title>: {u['title']}")
            if u.get("meta_description"):
                lines.append(f"  meta description: {u['meta_description']}")
            if u.get("canonical"):
                lines.append(f"  canonical: {u['canonical']}")
            headings = u.get("headings") or []
            if headings:
                hs = "; ".join(f"{h['level'].upper()} «{h['text']}»" for h in headings[:10])
                lines.append(f"  intestazioni rilevate: {hs}")
            schema_types = u.get("schema_types") or []
            if schema_types:
                lines.append(f"  schema.org: {', '.join(schema_types)}")
            main = (u.get("main_content") or "").strip()
            if main:
                lines.append(f"  estratto contenuto ({u.get('word_count', 0)} parole): {main[:800]}{'…' if len(main) > 800 else ''}")
            # Pagine interne aggiuntive (fix crawl multipagina)
            extra = u.get("additional_pages") or []
            if extra:
                lines.append(f"  ALTRE PAGINE CRAWLATE ({len(extra)}):")
                for p in extra[:8]:
                    bits = [p.get("url", "")]
                    if p.get("title"):
                        bits.append(f"title=«{p['title']}»")
                    if p.get("h1"):
                        bits.append(f"H1=«{p['h1']}»")
                    if p.get("meta_description"):
                        bits.append(f"meta=«{p['meta_description'][:120]}»")
                    lines.append("    - " + " | ".join(bits))

    return "\n".join(lines) if lines else "Nessun dato strutturato disponibile."


_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*\n([\s\S]*?)\n```", re.IGNORECASE)


def _extract_json(text: str) -> Dict[str, Any]:
    """Robust JSON extraction. Handles fenced code blocks and stray prose."""
    if not text:
        raise ValueError("empty LLM response")
    text = text.strip()
    match = _JSON_FENCE_RE.search(text)
    candidate = match.group(1) if match else text
    candidate = candidate.strip()
    start = candidate.find("{")
    end = candidate.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("no JSON object in LLM response")
    return json.loads(candidate[start : end + 1])


def _build_skill_payload(session: dict) -> str:
    """Always-on master skill + vertical skills bundle."""
    master = load_skill(MASTER_SKILL_NAME, include_references=True) or ""
    vertical_names = resolve_skills_for_session(session)
    # Reserve ~12k chars for master skill, give the rest to verticals.
    master_chars = min(len(master), 14_000)
    vertical_budget = max(PDF_SYSTEM_MAX_CHARS - master_chars - 2_000, 30_000)
    vertical_bundle = load_skill_bundle(
        vertical_names,
        max_total_chars=vertical_budget,
        max_per_skill_chars=20_000,
        include_references=True,
    )
    master_section = (
        f"\n{'=' * 60}\n# MASTER SKILL: {MASTER_SKILL_NAME} (sempre applicata)\n{'=' * 60}\n\n"
        + master[:master_chars]
    )
    return master_section + "\n\n" + vertical_bundle


def generate_analysis_json(session: dict) -> Dict[str, Any]:
    """Call Sonnet with master + vertical skills + session context.

    Returns a parsed JSON object with `meta` and `blocks` keys, conforming
    to the design system in lib/skills/report-premium-design/SKILL.md.
    """
    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY not configured")

    skills_payload = _build_skill_payload(session)
    context_block = _build_context_block(session)
    history = compact_messages(
        session.get("messages") or [],
        max_messages=MAX_HISTORY_MESSAGES,
        max_chars_per_message=MAX_MESSAGE_CHARS,
    )
    history_text = "\n".join(
        f"[{m['role'].upper()}] {m['content']}" for m in history
    ) or "(nessuna cronologia)"

    today = datetime.now()
    today_human = today.strftime("%d/%m/%Y")
    italian_months = [
        "gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
        "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre",
    ]
    today_long = f"{today.day} {italian_months[today.month - 1]} {today.year}"
    plus3_month = italian_months[(today.month + 2) % 12].capitalize()
    plus6_month = italian_months[(today.month + 5) % 12].capitalize()
    plus12_month = italian_months[(today.month - 1) % 12].capitalize()
    plus3_year = today.year + (1 if today.month + 3 > 12 else 0)
    plus6_year = today.year + (1 if today.month + 6 > 12 else 0)
    plus12_year = today.year + 1

    system_prompt = (
        "Sei l'analista K2-AI che produce report premium per PMI italiane. "
        "Output: SOLO un oggetto JSON valido `{meta, blocks}` secondo lo schema "
        "definito nella MASTER SKILL allegata. Niente testo prima/dopo, niente code fence.\n\n"
        f"DATA CORRENTE: oggi è {today_long} ({today_human}). "
        f"Roadmap, KPI e milestone DEVONO partire da oggi e proiettarsi nel futuro "
        f"(es. 'Mese 3: {plus3_month} {plus3_year}', 'Mese 6: {plus6_month} {plus6_year}', "
        f"'Mese 12: {plus12_month} {plus12_year}'). MAI usare date passate o anni del training.\n\n"
        "REGOLE FERREE:\n"
        "- Italiano corretto (è, à, ù, ò, ì). Numeri italiani: €31.500 non $31,500.\n"
        "- Tono pragmatico, mai marketing, mai 'rivoluzionario'/'all'avanguardia'.\n"
        "- Ogni numero quantificato, mai 'X' o placeholder.\n"
        "- 6-10 blocchi totali, sempre executive_summary primo e conclusions ultimo.\n"
        "- Coerenza interna: stesso numero in blocchi diversi senza contraddizioni.\n"
        "- Adatta i titoli e le sezioni AL CASO SPECIFICO dell'utente (investimento, marketing, "
        "legale, finanziario, tecnico…). Non c'è una struttura fissa.\n"
        "- Usa SOLO i tipi di blocco documentati nella master skill.\n"
        "- VINCOLO DATI: se nel contesto trovi 'URL ANALIZZATI', usa ESATTAMENTE i title/H1/meta "
        "elencati. NON inventare title o H1 alternativi. Se un campo manca, scrivi 'non rilevato' "
        "invece di inventarlo. Se architettura sito ha più pagine crawlate, NON descriverla come "
        "'monopage'.\n"
        "- VINCOLO COMPETITOR: se non hai competitor reali nei dati di sessione, NON inventare "
        "'Competitor A/B/C' con DA fittizi. Dichiara esplicitamente che sono benchmark di mercato "
        "generici. Mai DA, posizioni o keyword rankate inventate per competitor specifici.\n\n"
        "SKILL E DESIGN SYSTEM:\n"
        f"{skills_payload}"
    )

    user_message = (
        "CONTESTO RACCOLTO DA K-BOT:\n"
        f"{context_block}\n\n"
        "CRONOLOGIA CONVERSAZIONE (riferimento integrativo):\n"
        f"{history_text}\n\n"
        "Genera ora il report JSON. Scegli i blocchi più adatti al tipo di analisi richiesta."
    )

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    log.info("Generating report JSON with model=%s skills=%d-chars", ANTHROPIC_PDF_MODEL, len(skills_payload))
    result = client.messages.create(
        model=ANTHROPIC_PDF_MODEL,
        max_tokens=8192,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
        timeout=180.0,
    )
    raw = "".join(b.text for b in result.content if getattr(b, "type", "") == "text")
    return _extract_json(raw)
