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
import time
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
    """Always-on master skill + vertical skills bundle.

    Caps aggressivi per rispettare rate limit Anthropic (Sonnet 30k TPM su
    questa org). Total target: <50k chars (~12.5k tokens).
    """
    master = load_skill(MASTER_SKILL_NAME, include_references=False) or ""
    vertical_names = resolve_skills_for_session(session)
    master_chars = min(len(master), 8_000)
    # Vertical budget = PDF_SYSTEM_MAX_CHARS (55k default) - master (~8k) - boilerplate (~2k) ≈ 45k
    vertical_budget = max(PDF_SYSTEM_MAX_CHARS - master_chars - 2_000, 15_000)
    vertical_bundle = load_skill_bundle(
        vertical_names,
        max_total_chars=vertical_budget,
        max_per_skill_chars=6_000,
        include_references=False,
    )
    master_section = (
        f"\n{'=' * 60}\n# MASTER SKILL: {MASTER_SKILL_NAME}\n{'=' * 60}\n\n"
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
        "Output finale: SOLO un oggetto JSON valido `{meta, blocks}` secondo lo schema "
        "definito nella MASTER SKILL allegata. Niente testo prima/dopo il JSON, niente code fence.\n\n"
        f"DATA CORRENTE: oggi è {today_long} ({today_human}). "
        f"Roadmap, KPI e milestone DEVONO partire da oggi e proiettarsi nel futuro "
        f"(es. 'Mese 3: {plus3_month} {plus3_year}', 'Mese 6: {plus6_month} {plus6_year}', "
        f"'Mese 12: {plus12_month} {plus12_year}'). MAI usare date passate o anni del training.\n\n"
        "STRUMENTO web_search DISPONIBILE — USALO PRIMA DEL JSON:\n"
        "Hai accesso a un tool `web_search` (max 6 ricerche). DEVI usarlo PRIMA di emettere il JSON "
        "per verificare: (a) competitor reali del settore/mercato del cliente, (b) volumi keyword "
        "e CPC indicativi se l'analisi è SEO/SEM, (c) benchmark di settore (margini, conversion "
        "rate, costi medi), (d) normative/eventi recenti rilevanti, (e) qualunque numero o nome "
        "che non sia già nel contesto sessione. Strategia query: italiano, specifica, geo-Italia "
        "quando rilevante (es. 'consulenza AI PMI Italia 2026 competitor', 'benchmark conversion "
        "rate SaaS B2B Italia'). Dopo le ricerche, sintetizza nel JSON solo dati con fonte.\n\n"
        "REGOLE FERREE:\n"
        "- Italiano corretto (è, à, ù, ò, ì). Numeri italiani: €31.500 non $31,500.\n"
        "- Tono pragmatico, mai marketing, mai 'rivoluzionario'/'all'avanguardia'.\n"
        "- Ogni numero quantificato, mai 'X' o placeholder.\n"
        "- 6-10 blocchi totali, sempre executive_summary primo e conclusions ultimo.\n"
        "- Coerenza interna: stesso numero in blocchi diversi senza contraddizioni.\n"
        "- Adatta i titoli e le sezioni AL CASO SPECIFICO dell'utente (investimento, marketing, "
        "legale, finanziario, tecnico…). Non c'è una struttura fissa.\n"
        "- Usa SOLO i tipi di blocco documentati nella master skill.\n\n"
        "VINCOLI DI INTEGRITÀ — NESSUNA HALLUCINATION:\n"
        "- VINCOLO DATI SITO: se nel contesto trovi 'URL ANALIZZATI', usa ESATTAMENTE i title/H1/meta "
        "elencati. NON inventare title o H1 alternativi. Se un campo manca, scrivi 'non rilevato' "
        "invece di inventarlo. Se architettura sito ha più pagine crawlate, NON descriverla come "
        "'monopage'.\n"
        "- VINCOLO COMPETITOR: VIETATO inventare 'Competitor A/B/C' con DA/keyword rankate fittizi. "
        "Solo due scelte ammesse: (1) competitor REALI nominati esplicitamente con fonte web_search "
        "(es. 'cribis.com', 'atoka.io'), (2) omettere il blocco competitor. Mai placeholder anonimi.\n"
        "- VINCOLO METRICHE: ogni numero che NON sia stato direttamente fornito dal cliente "
        "(via chat/file/URL crawl) o verificato via web_search DEVE essere etichettato come "
        "'stima di mercato (range tipico)' con range esplicito, mai numero secco inventato. "
        "Es. sbagliato: 'DA competitor: 38'. Es. corretto: 'DA tipico mid-market SaaS B2B Italia: "
        "15-40 (stima di mercato, non rilevazione diretta)'.\n"
        "- VINCOLO FONTI: ogni blocco con dati esterni (keyword, competitor, normative, benchmark) "
        "DEVE includere nel campo 'note' o 'source' un riferimento alla fonte web_search con URL e "
        f"data di verifica ({today_human}). Niente fonte = niente numero specifico.\n"
        "- VINCOLO ONESTÀ: se un dato non è verificabile (es. backlink profile senza accesso "
        "Majestic/Ahrefs), scrivi 'non misurato — richiede tool dedicato (Ahrefs/Semrush)' invece "
        "di assumere 'N/A — sito nuovo'.\n\n"
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

    # Web search tool — Anthropic server-side, niente handler lato nostro.
    # Il modello decide quando cercare; loop finché non emette stop_reason="end_turn"
    # con testo finale (il JSON). max_uses limita il costo (~$10/1000 search).
    tools = [{"type": "web_search_20250305", "name": "web_search", "max_uses": 6}]

    # Prompt caching: skills payload è stabile tra chiamate → 90% sconto su cache hit.
    # cache_control sul system prompt finale (ultimo blocco testuale).
    system_blocks = [
        {"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}},
    ]

    def _create_with_backoff(messages: List[Dict[str, Any]]):
        """Retry su 429 con backoff esponenziale (rate limit Anthropic per minuto)."""
        delays = [12, 25, 45]  # finestra rate-limit Anthropic = 60s, backoff sotto 1 min
        last_exc: Optional[Exception] = None
        for attempt, delay in enumerate([0] + delays):
            if delay:
                log.warning("Rate-limited, retry %d/%d after %ds", attempt, len(delays), delay)
                time.sleep(delay)
            try:
                return client.messages.create(
                    model=ANTHROPIC_PDF_MODEL,
                    max_tokens=8192,
                    system=system_blocks,
                    tools=tools,
                    messages=messages,
                    timeout=240.0,
                )
            except anthropic.RateLimitError as exc:
                last_exc = exc
                continue
        raise last_exc if last_exc else RuntimeError("rate-limit retry loop exhausted")

    conversation: List[Dict[str, Any]] = [{"role": "user", "content": user_message}]
    raw = ""
    for _hop in range(8):  # safety cap: max 8 round-trip se il modello tool-spamma
        result = _create_with_backoff(conversation)
        stop = getattr(result, "stop_reason", None)
        # Server-side web_search: server_tool_use + web_search_tool_result blocks
        # vengono già rinviati al modello automaticamente — non serve gestirli.
        # Iteriamo solo se stop_reason == "tool_use" (client-side tool, raro qui).
        if stop == "tool_use":
            # Echo assistant turn + dummy tool_result per chiudere il ciclo.
            conversation.append({"role": "assistant", "content": result.content})
            tool_uses = [b for b in result.content if getattr(b, "type", "") == "tool_use"]
            if not tool_uses:
                break
            conversation.append({
                "role": "user",
                "content": [
                    {"type": "tool_result", "tool_use_id": tu.id, "content": "[no client-side tool wired]"}
                    for tu in tool_uses
                ],
            })
            continue
        raw = "".join(b.text for b in result.content if getattr(b, "type", "") == "text")
        break
    if not raw:
        raise RuntimeError("LLM returned no text block (web_search loop esaurito)")
    return _extract_json(raw)
