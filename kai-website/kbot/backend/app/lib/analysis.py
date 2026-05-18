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
        # Conteggio TOTALE pagine viste (homepage + additional_pages) — il
        # modello deve usarlo nel report invece di "7 pagine visibili nel menu".
        total_pages = 0
        for u in urls:
            total_pages += 1  # homepage stessa
            total_pages += len(u.get("additional_pages") or [])
        lines.append(f"\nTOTALE PAGINE CRAWLATE (homepage + interne): {total_pages}")
        lines.append("→ Questo è il conteggio AUTORITATIVO delle pagine del sito. "
                     "Usalo nei blocchi 'pagine indicizzabili', 'architettura', 'metriche'. "
                     "NON usare conteggi parziali (es. solo menu) come totali.")
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
                for p in extra[:20]:
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
        "quando rilevante. Dopo le ricerche, sintetizza nel JSON solo dati con fonte URL reale "
        "ottenuta dalle ricerche. Se web_search non ritorna risultati utili, scrivi 'dato non "
        "disponibile — verificare con [tool dedicato]' invece di inventare.\n\n"
        "REGOLE OUTPUT:\n"
        "- Italiano corretto (è, à, ù, ò, ì). Numeri italiani: €31.500 non $31,500.\n"
        "- Tono pragmatico, mai marketing, mai 'rivoluzionario'/'all'avanguardia'.\n"
        "- Ogni numero quantificato, mai 'X' o placeholder.\n"
        "- 6-8 blocchi totali (mai oltre 8), sempre executive_summary primo e conclusions ultimo.\n"
        "- JSON COMPATTO: ogni stringa max 350 caratteri, ogni array max 8 voci, "
        "no spazi superflui. Output deve stare in 14k tokens.\n"
        "- Coerenza interna: stesso numero in blocchi diversi senza contraddizioni.\n"
        "- Adatta i titoli e le sezioni AL CASO SPECIFICO dell'utente.\n"
        "- Usa SOLO i tipi di blocco documentati nella master skill.\n\n"
        "RUBRIC SCORE DETERMINISTICO (eseguilo sempre per ogni audit):\n"
        "Lo score 0-100 deve essere calcolato sommando 4 sotto-dimensioni di 25 punti ciascuna\n"
        "(mostrate nel breakdown del blocco executive_summary o kpi_grid):\n"
        "  1. Technical SEO (0-25): HTTPS, mobile-friendly, sitemap.xml, robots.txt, "
        "canonical, schema.org. Conta i presenti, parti da 0.\n"
        "  2. Content & On-page (0-25): title unici, meta description, H1 coerenti, "
        "alt-text, internal linking. Conta presenti su totale pagine.\n"
        "  3. Architecture (0-25): n. pagine indicizzabili (≥10 → 25, 5-9 → 15, <5 → 5), "
        "presenza blog, struttura cluster.\n"
        "  4. Off-page & Authority (0-25): backlink rilevati (se misurati), DA reale, "
        "menzioni brand. Se non misurabile → 12 (stima neutrale, dichiarare 'non misurato').\n"
        "Lo score finale = somma 4 dimensioni. STESSO INPUT → STESSO SCORE. Esponi sempre "
        "il breakdown nel report. NIENTE score oscillanti tra run sullo stesso sito.\n\n"
        "CATEGORIA 1 — ERRORI DI DATI (vietati assoluti):\n"
        "  • DATI INVENTATI: VIETATO affermare metriche non estratte da fonte reale in questa "
        "sessione. Niente 'keyword in top X: N attuali' senza GSC. Niente 'Domain Authority: N' "
        "senza Ahrefs/Moz. Niente 'traffico mensile: N visite' senza Analytics. Se manca, scrivi "
        "esplicitamente 'dato non disponibile — verificare con [tool]'.\n"
        "  • FONTI INVENTATE: VIETATO citare 'fonte: Semrush 2026' o 'fonte: studio Growthfounders' "
        "se NON hai realmente eseguito quella web_search in questa sessione e ricevuto quel "
        "risultato. Sbagliato: 'fonte: Semrush maggio 2026' (inventato). Corretto: 'stima basata "
        "su benchmark di mercato — verificare con [tool] per dati live'.\n"
        "  • CONTEGGI SITO: usa il conteggio COMPLETO degli URL crawlati (homepage + sitemap + "
        "pagine interne). Non solo quelli nel menu principale.\n"
        "  • DATI ON-PAGE: estrai title/H1/meta SOLO dai dati 'URL ANALIZZATI' del contesto. Se "
        "un campo manca, scrivi 'non rilevato — verificare manualmente'. Mai inventare title/H1.\n"
        "  • COMPETITOR ANONIMI: VIETATO 'Competitor A/B/C' con dati stimati. Solo due scelte: "
        "(1) competitor REALI nominati con fonte web_search, (2) omettere il blocco competitor e "
        "descrivere il mercato in generale senza tabelle simulate.\n"
        "  • COMPETITOR NON VERIFICATI: ogni nome competitor citato DEVE essere accompagnato da "
        "un URL fonte ottenuto da web_search REALMENTE eseguita in questa sessione. Nomi plausibili "
        "ma non verificati (es. 'Digital Automations', 'Yellow Tech', 'Castaldo Solutions') con "
        "metriche specifiche ('12+ articoli', '300+ agenti in produzione', 'DA 38') = INVENZIONE "
        "anche se i nomi suonano reali. Senza URL fonte → non includere il competitor.\n"
        "  • DATO MERCATO/SETTORE: numeri di mercato (es. 'mercato italiano agenti AI vale 1,8 "
        "miliardi €', '84% delle PMI non usa AI', 'CAGR +50%') DEVONO avere fonte URL inline "
        "(report Anitec-Assinform, ISTAT, Politecnico Milano, ecc) verificata via web_search. "
        "Senza fonte → 'stima di settore — fonte da verificare' o ometti il numero.\n"
        "  • SEDE AZIENDA: la sede legale del cliente (città, regione) NON va mai assunta. Estraila "
        "ESATTAMENTE dal contesto sessione (URL crawlati, file caricati, P.IVA). Se non rilevata, "
        "scrivi 'sede da verificare'. VIETATO scrivere 'Milano/Italia', 'Roma' o altre città di "
        "default. (Caso K2-AI: sede a Perugia, non Milano.)\n\n"
        "CATEGORIA 2 — ERRORI DI OUTPUT (verifica prima di emettere JSON):\n"
        "  • NIENTE SEZIONI VUOTE: ogni blocco dichiarato DEVE avere contenuto sostanziale. "
        "Il blocco 'conclusions' OBBLIGATORIAMENTE deve contenere: 3 problemi principali in "
        "ordine di priorità, 3 azioni immediate per questa settimana, KPI con cui misurare il "
        "successo a 30/60/90 giorni. Mai solo il titolo.\n"
        "  • SCORE CON BREAKDOWN: ogni numero secco (es. '62/100') deve essere accompagnato da "
        "almeno 3-4 sotto-dimensioni con punteggio separato che mostrano la composizione.\n"
        "  • RACCOMANDAZIONI STRUTTURATE: ogni azione consigliata DEVE avere: priorità "
        "(alta/media/bassa) + impatto stimato + complessità/tempo di esecuzione. Mancano tutti "
        "e tre = riga inutile.\n"
        "  • KPI CON BASELINE: target tipo '+25% traffico' DEVE includere il punto di partenza "
        "(es. 'da X a Y visite/mese'). Se baseline non disponibile, scrivilo esplicitamente.\n\n"
        "CATEGORIA 3 — CREDIBILITÀ (mai compromettere):\n"
        "  • BENCHMARK ETICHETTATI: stime di mercato vanno dichiarate come tali. 'Mediana del "
        "settore (stima di mercato)' invece di 'Mediana 2,1%' come se fosse un dato cliente.\n"
        "  • PROIEZIONI CON ASSUNZIONI: '180-250 visite/mese a 12 mesi' richiede di esplicitare "
        "CTR stimato, posizione media attesa, volume keyword usato. Senza assunzioni il numero è "
        "arbitrario e perde valore.\n"
        "  • ONESTÀ INCERTEZZA: dato non verificabile (es. backlink senza Majestic/Ahrefs) "
        "= 'non misurato — richiede tool dedicato'. Mai 'N/A perché sito nuovo' o altre "
        "assunzioni mascherate da fatti.\n\n"
        "CATEGORIA 4 — STANDARD VISIVI:\n"
        "  • STATUS BADGES COERENTI: usa simboli/varianti coerenti in tutto il report — "
        "'success'/✓ = OK, 'warning'/⚠ = parziale, 'alert'/✗ = critico. Mai mischiare stili.\n"
        "  • TABELLE COMPLETE: ogni tabella ha intestazioni chiare, unità di misura esplicite "
        "(€, %, mesi, ore/sett), e colonna 'priorità' o 'stato' quando elenca azioni.\n"
        "  • CONCLUSIONS BLOCK: il LAST blocco DEVE essere di type 'conclusions' con questa "
        "shape ESATTA — usa SOLO le chiavi indicate, non variarne i nomi:\n"
        "    {\"type\":\"conclusions\",\"title\":\"Conclusioni e Prossimi Passi\",\n"
        "     \"left\":{\"heading\":\"3 problemi principali\",\"heading_variant\":\"alert\",\n"
        "             \"body_html\":\"<ol><li>Problema 1...</li><li>Problema 2...</li><li>Problema 3...</li></ol>\"},\n"
        "     \"right\":{\"heading\":\"3 azioni immediate (settimana 1)\",\n"
        "              \"milestones\":[\n"
        "                {\"label\":\"Azione 1\",\"tone\":\"alert\",\"items\":[\"step concreto a\",\"step b\"]},\n"
        "                {\"label\":\"Azione 2\",\"tone\":\"warning\",\"items\":[\"step a\",\"step b\"]},\n"
        "                {\"label\":\"KPI 30/60/90 giorni\",\"tone\":\"neutral\",\"items\":[\"30gg: ...\",\"60gg: ...\",\"90gg: ...\"]}\n"
        "              ]}}\n"
        "    NOMI CHIAVE OBBLIGATORI: right.milestones (NON 'actions', 'steps', 'tasks'). "
        "Ogni milestone con label+items+tone. Mai colonna right vuota.\n"
        "  • FOOTER DISCLAIMER: il campo 'footer.disclaimer' del JSON DEVE contenere: "
        "'Le stime di traffico, volume keyword e proiezioni sono basate su benchmark di mercato. "
        "I dati reali possono variare. Verificare con Google Search Console e strumenti di analisi "
        "dedicati.' (esattamente questa frase).\n\n"
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
                    max_tokens=16000,
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
    try:
        parsed = _extract_json(raw)
        return _sanitize_hallucinations(parsed)
    except (ValueError, json.JSONDecodeError) as exc:
        # JSON troncato o malformato (max_tokens esaurito, virgola mancante, ecc).
        # Retry singolo chiedendo a Sonnet di riemettere SOLO un JSON valido,
        # senza tools né web_search (output puro, niente prosa).
        log.warning("JSON parse fallita (%s), retry compact mode", exc)
        repair_user = (
            "Il JSON precedente era invalido o troncato. RIEMETTI ORA solo l'oggetto "
            "{meta, blocks} valido, compatto, senza commenti né testo fuori. "
            "Mantieni 6-8 blocchi massimo, ogni blocco essenziale. Niente fence markdown.\n\n"
            f"CONTESTO ORIGINALE:\n{user_message[:6000]}"
        )
        retry = client.messages.create(
            model=ANTHROPIC_PDF_MODEL,
            max_tokens=16000,
            system=system_blocks,
            messages=[{"role": "user", "content": repair_user}],
            timeout=180.0,
        )
        repaired = "".join(b.text for b in retry.content if getattr(b, "type", "") == "text")
        return _sanitize_hallucinations(_extract_json(repaired))


# Pattern di hallucination tipici da bonificare post-generation.
# Sonnet ignora le regole prompt ~10% delle volte → catch-all deterministico.
_TRAFFIC_RE = re.compile(
    r"(~?\s*\d+(?:[.,]\d+)?\s*(?:visit[ei]|sessioni|impression(?:i|s)?|click)\s*/\s*mese)",
    re.IGNORECASE,
)
_KEYWORD_POS_RE = re.compile(
    r"(~?\s*\d+\s+keyword\s+(?:posizionat[ei]|in\s+top[-\s]?\d+))",
    re.IGNORECASE,
)
_PERUGIA_HINT = re.compile(r"(Perugia|03655920548)", re.IGNORECASE)
_FORBIDDEN_CITIES = re.compile(r"\b(Milano|Roma|Torino|Napoli|Bologna)\b\s*(?:/Italia|,?\s*Italia)?", re.IGNORECASE)
_UNSOURCED_PCT_RE = re.compile(r"(\d+\s*%)\s+(?:di|delle|degli)\s+(?:PMI|aziende|imprese)\b(?!.{0,80}(?:fonte|http|istat|anitec|polimi|politecnico))", re.IGNORECASE)


def _sanitize_recursive(value: Any, ctx: dict) -> Any:
    if isinstance(value, dict):
        return {k: _sanitize_recursive(v, ctx) for k, v in value.items()}
    if isinstance(value, list):
        return [_sanitize_recursive(v, ctx) for v in value]
    if isinstance(value, str):
        s = value
        # Traffico/visite con numero secco senza disclaimer → tag stima
        if _TRAFFIC_RE.search(s) and "stima" not in s.lower() and "non disponibile" not in s.lower():
            s = _TRAFFIC_RE.sub(r"\1 [non verificato — richiede GSC/Analytics]", s)
            ctx["fixed"] += 1
        # Keyword posizionate dichiarate come fatto
        if _KEYWORD_POS_RE.search(s) and "stima" not in s.lower():
            s = _KEYWORD_POS_RE.sub(r"\1 [non verificato — richiede GSC]", s)
            ctx["fixed"] += 1
        # Sede inventata: se contesto cita Perugia/P.IVA K2-AI, sostituisci Milano/Roma con Perugia
        if ctx.get("force_perugia") and _FORBIDDEN_CITIES.search(s):
            s = _FORBIDDEN_CITIES.sub("Perugia", s)
            ctx["fixed"] += 1
        return s
    return value


def _sanitize_hallucinations(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Catch-all regex per pattern di hallucination che Sonnet emette nonostante
    il prompt. Sostituisce numeri secchi con tag "[non verificato]" e applica
    correzioni context-aware (es. sede K2-AI = Perugia)."""
    ctx: dict = {"fixed": 0}
    # Detection sede K2-AI dal flatten dell'intero JSON (cerca P.IVA o "Perugia").
    flat = json.dumps(analysis, ensure_ascii=False)
    ctx["force_perugia"] = bool(_PERUGIA_HINT.search(flat))
    cleaned = _sanitize_recursive(analysis, ctx)
    if ctx["fixed"]:
        log.info("Post-gen sanitizer fixed %d hallucination patterns", ctx["fixed"])
    return cleaned
