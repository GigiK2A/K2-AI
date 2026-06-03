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
    ANTHROPIC_PDF_MULTI_CALL,
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
        # Enumera ESPLICITAMENTE tutti gli URL crawlati così Sonnet non può
        # "non vedere" privacy/cookie/note-legali e inventare numero diverso.
        all_urls = []
        for u in urls:
            home = u.get("url", "")
            if home:
                all_urls.append(home)
            for p in (u.get("additional_pages") or []):
                pu = p.get("url", "")
                if pu and pu not in all_urls:
                    all_urls.append(pu)
        lines.append(f"\n⚠️ PAGINE INDICIZZABILI = {total_pages} ⚠️")
        lines.append(f"ELENCO COMPLETO URL CRAWLATI ({total_pages} pagine):")
        for idx, url in enumerate(all_urls[:30], 1):
            lines.append(f"  {idx}. {url}")
        lines.append(f"OBBLIGATORIO usare {total_pages} (non altri numeri) nei blocchi 'pagine "
                     f"indicizzabili', 'metriche SEO', 'architettura', 'punti forza'. "
                     f"VIETATO scrivere '7 pagine' o conteggi parziali. Includi privacy/cookie/"
                     f"note-legali nel conteggio (sono pagine indicizzabili come le altre).")
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


# ---------------------------------------------------------------------------
# Report profile: classifier + per-type prompt sections.
#
# Sonnet riceve linee guida differenti in base al reportType estratto dalla
# chat. Senza questo, il prompt forzava score formula SEO (4 dim × 25pt) e
# schema conclusions con KPI 30/60/90 anche su bilancio/business plan dove
# non ha senso → punteggi arbitrari, sezioni vuote, schema rigido.
# ---------------------------------------------------------------------------

def _classify_report(report_type: Optional[str]) -> str:
    """Mappa reportType (stringa libera dalla chat) in categoria enum."""
    rt = (report_type or "").lower()
    if any(k in rt for k in ("seo", "audit seo", "posizionamento ricerca", "ricerca organica", "indicizz")):
        return "seo"
    if any(k in rt for k in ("bilancio", "salute finanziaria", "controllo gestione", "flussi cassa", "cash flow")):
        return "bilancio"
    if any(k in rt for k in ("business plan", "piano industriale", "piano strategico")):
        return "business_plan"
    if any(k in rt for k in ("fattibilit", "feasibility")):
        return "fattibilita"
    if any(k in rt for k in ("due diligence", "dd commercial", "dd operativ")):
        return "due_diligence"
    if any(k in rt for k in ("investiment", "roi", "payback", "npv", "irr")):
        return "investimento"
    if any(k in rt for k in ("processi", "as-is", "to-be", "mappatura process", "lean", "bottleneck")):
        return "processi"
    if any(k in rt for k in ("mercato", "settore", "ricerca settoriale", "studio mercato", "tam", "sam")):
        return "mercato"
    if any(k in rt for k in ("sentiment", "reputation", "reputazione")):
        return "sentiment"
    if any(k in rt for k in ("competitiv", "benchmark")):
        return "competitivo"
    if any(k in rt for k in ("calendario", "editorial", "piano contenuti", "piano editoriale",
                             "content plan", "content calendar", "contenuti social", "contenuti",
                             "post social", "social media", "instagram", "linkedin", "redazionale",
                             "newsletter", "bozze", "copywriting")):
        return "contenuti"
    if any(k in rt for k in ("marketing", "funnel", "customer journey", "positioning", "posizionamento mark")):
        return "marketing"
    if any(k in rt for k in ("dati", "dataset", "data analysis")):
        return "custom_data"
    return "generic"


_SCORE_RUBRICS: Dict[str, str] = {
    "seo": (
        "RUBRIC SCORE SEO (somma 4 dim × 25pt = totale 0-100):\n"
        "  1. Technical SEO (max 25): HTTPS=5, mobile=5, sitemap=4, robots=3, schema.org=5, canonical=3\n"
        "  2. Content & On-page (max 25): title unici=5, meta desc≥90%=5, H1 unico=5, alt-text≥80%=5, internal links≥3/pg=5\n"
        "  3. Architecture (max 25): pagine indicizzabili ≥10=10 (5-9=6, <5=2), blog=8, cluster=7\n"
        "  4. Off-page & Authority (max 25): backlink≥20=10, DA≥20=10, menzioni brand=5. Se non misurabile→12 fissi, dichiarare 'non misurato'\n"
    ),
    "bilancio": (
        "RUBRIC SCORE SALUTE FINANZIARIA (somma 4 dim × 25pt):\n"
        "  1. Liquidità (max 25): current ratio≥1.5=10, quick ratio≥1=8, DSO<60gg=7\n"
        "  2. Redditività (max 25): EBITDA margin≥10%=10, ROE≥8%=8, ROI≥5%=7\n"
        "  3. Solvibilità (max 25): leverage≤2x=10, debt/equity≤1=8, copertura interessi≥3x=7\n"
        "  4. Crescita (max 25): CAGR ricavi 3yr≥5%=10, margine in crescita=8, working capital efficienza=7\n"
        "Se metrica non disponibile (no file bilancio in sessione)→assegna 12pt fissi per dimensione e marca 'non misurato'.\n"
    ),
    "business_plan": (
        "RUBRIC SCORE BUSINESS PLAN (somma 4 dim × 25pt):\n"
        "  1. Mercato/Demand (max 25): TAM credibile=10, SAM realistico=8, segmentazione=7\n"
        "  2. Modello/Offering (max 25): value prop chiara=10, pricing logico=8, differenziazione=7\n"
        "  3. Finanza/Sostenibilità (max 25): break-even <24m=10, cash burn coperto=8, unit economics positivi=7\n"
        "  4. Esecuzione (max 25): team competente=10, roadmap 12m=8, KPI tracciabili=7\n"
    ),
    "fattibilita": (
        "RUBRIC SCORE FATTIBILITÀ (somma 4 dim × 25pt):\n"
        "  1. Tecnica (max 25): tecnologia disponibile=10, complessità integrazione=8, skill team=7\n"
        "  2. Mercato (max 25): domanda dimostrata=10, competizione gestibile=8, willingness to pay=7\n"
        "  3. Finanza (max 25): CapEx sostenibile=10, payback <36m=8, ROI positivo=7\n"
        "  4. Tempistica (max 25): MVP <6m=10, rollout <12m=8, dependencies note=7\n"
    ),
    "investimento": (
        "RUBRIC SCORE INVESTIMENTO (somma 4 dim × 25pt):\n"
        "  1. Ritorno (max 25): IRR≥15%=10, NPV>0=8, ROI≥20%=7\n"
        "  2. Tempo recupero (max 25): payback <2y=10, <4y=15, >4y=8\n"
        "  3. Rischio (max 25): scenario stress positivo=10, hedge attivi=8, downside limitato=7\n"
        "  4. Strategia (max 25): allineamento obiettivi=10, exit pianificata=8, scalabilità=7\n"
    ),
    "generic": (
        "SCORE QUALITATIVO: per analisi senza rubric numerica obbligatoria (processi/sentiment/due\n"
        "diligence/mercato/competitivo/marketing/custom_data), OMETTI il campo score nell'executive_summary\n"
        "e usa invece un giudizio sintetico in 'body' (es. 'Maturità complessiva: media-alta; gap critico\n"
        "su X'). NIENTE numero arbitrario tipo '62/100' senza criteri.\n"
    ),
}
# Alias per categorie senza rubric specifica
for _k in ("due_diligence", "processi", "mercato", "sentiment", "competitivo", "marketing", "custom_data", "contenuti"):
    _SCORE_RUBRICS[_k] = _SCORE_RUBRICS["generic"]


_REQUIRED_BLOCKS: Dict[str, str] = {
    "seo": (
        "BLOCCHI OBBLIGATORI AUDIT SEO (oltre exec_summary + conclusions):\n"
        "  a) data_table 'Keyword target identificate' columns=[Keyword, Volume mensile, KD, Intent, Priorità], ≥8 righe reali da crawl/web_search\n"
        "  b) data_table 'Analisi competitor' columns=[Competitor, URL, Pagine indicizzate, DA stimato, Gap], ≥3 righe da web_search REALI\n"
    ),
    "bilancio": (
        "BLOCCHI OBBLIGATORI ANALISI BILANCIO:\n"
        "  a) data_table 'Indici di bilancio' columns=[Indice, Valore, Benchmark settore, Stato, Note], ≥6 righe (current ratio, ROE, ROI, EBITDA margin, leverage, DSO)\n"
        "  b) data_table 'Proiezione P&L 3 anni' columns=[Voce, Anno 1, Anno 2, Anno 3, CAGR], ≥5 righe (Ricavi, COGS, EBITDA, Net income, Cash flow op)\n"
        "  c) two_column 'Punti forza / Aree miglioramento' (forza=verde / aree=rosso)\n"
    ),
    "marketing": (
        "BLOCCHI OBBLIGATORI ANALISI MARKETING:\n"
        "  a) data_table 'Channel mix' columns=[Canale, Spesa %, CAC stimato, Conversion rate, ROAS], ≥4 righe (Search, Social, Email, Direct)\n"
        "  b) data_table 'Funnel conversion' columns=[Stage, Volume, Conversion %, Tempo medio], ≥4 righe (Awareness, Interest, Decision, Action)\n"
        "  c) two_column 'Posizionamento forte / Gap competitivo'\n"
    ),
    "contenuti": (
        "BLOCCHI OBBLIGATORI PIANO CONTENUTI / CALENDARIO EDITORIALE:\n"
        "  a) data_table 'Pilastri di contenuto' columns=[Pilastro, Obiettivo, Mix %, Esempi di tema], ≥3 righe\n"
        "  b) data_table 'Calendario editoriale' columns=[Data, Giorno, Pilastro, Titolo, Gancio/Copy breve, Formato, CTA]\n"
        "     UNA RIGA PER OGNI USCITA del periodo richiesto (es. 3 post/sett per 3 mesi ≈ 36-40 righe).\n"
        "     ⚠ ECCEZIONE alla regola 'array max 8 voci': QUESTA tabella DEVE elencare TUTTE le uscite,\n"
        "     anche 40, dalla data di oggi in poi. NIENTE troncamenti, niente 'Post 1/Post 2' generici:\n"
        "     titoli e ganci concreti del settore del cliente. Tieni Titolo ≤60 char e Gancio ≤90 char\n"
        "     per restare compatto. Date assolute progressive nei giorni di pubblicazione richiesti.\n"
        "  c) two_column 'Tono di voce e linee guida / Cose da evitare'\n"
    ),
    "business_plan": (
        "BLOCCHI OBBLIGATORI BUSINESS PLAN:\n"
        "  a) data_table 'Proiezione finanziaria 5 anni' columns=[Voce, Y1, Y2, Y3, Y4, Y5], ≥6 righe (Ricavi, COGS, OPEX, EBITDA, CapEx, Cash flow)\n"
        "  b) data_table 'Roadmap milestone 12 mesi' columns=[Mese, Milestone, KPI atteso, Owner], ≥6 righe con date assolute dal corrente\n"
        "  c) two_column 'Punti forza modello / Rischi go-to-market'\n"
    ),
    "fattibilita": (
        "BLOCCHI OBBLIGATORI ANALISI FATTIBILITÀ:\n"
        "  a) data_table 'Risk register' columns=[Rischio, Probabilità, Impatto, Mitigazione, Owner], ≥5 righe\n"
        "  b) data_table 'Investment summary' columns=[Voce, Ammontare €, Note], ≥4 righe (CapEx, OPEX 1y, Working capital, Total)\n"
        "  c) two_column 'Driver di successo / Mancanze critiche'\n"
    ),
    "due_diligence": (
        "BLOCCHI OBBLIGATORI DUE DILIGENCE:\n"
        "  a) data_table 'Red flags' columns=[Area, Red flag, Severità, Evidenza, Azione raccomandata], ≥4 righe (Legal, Fiscal, Commercial, Operational)\n"
        "  b) data_table 'Checklist documentale' columns=[Area, Documento richiesto, Stato (✓/✕/?), Note], ≥6 righe\n"
        "  c) two_column 'Strengths / Concerns'\n"
    ),
    "investimento": (
        "BLOCCHI OBBLIGATORI ANALISI INVESTIMENTO:\n"
        "  a) data_table 'Cash flow scenari' columns=[Anno, Best case, Base case, Worst case], ≥5 righe (Y1-Y5)\n"
        "  b) data_table 'Metriche di ritorno' columns=[Metrica, Valore, Soglia decisione, Verdetto], righe per IRR, NPV, Payback, ROI, breakeven\n"
        "  c) two_column 'Upside / Downside'\n"
    ),
    "processi": (
        "BLOCCHI OBBLIGATORI ANALISI PROCESSI:\n"
        "  a) data_table 'Bottleneck' columns=[Processo, Bottleneck, Impatto (h/sett), Causa, Azione TO-BE], ≥4 righe\n"
        "  b) data_table 'KPI as-is vs to-be' columns=[KPI, As-is, To-be target, Δ %, Time-to-impact], ≥4 righe\n"
        "  c) two_column 'Quick wins / Trasformazioni strutturali'\n"
    ),
    "mercato": (
        "BLOCCHI OBBLIGATORI STUDIO MERCATO:\n"
        "  a) data_table 'Mercato' columns=[Segmento, TAM €, SAM €, SOM €, CAGR %], ≥3 righe\n"
        "  b) data_table 'Competitor mappati' columns=[Player, Quota %, Pricing, Posizionamento, Forza], ≥4 righe da web_search REALI\n"
        "  c) two_column 'Trend favorevoli / Headwinds'\n"
    ),
    "sentiment": (
        "BLOCCHI OBBLIGATORI ANALISI SENTIMENT:\n"
        "  a) data_table 'Sentiment per canale' columns=[Canale, Volume menzioni, Positive %, Neutral %, Negative %], ≥4 righe\n"
        "  b) data_table 'Top criticità ricorrenti' columns=[Tema, Frequenza, Sentiment, Esempio testuale, Azione], ≥4 righe\n"
        "  c) two_column 'Punti di forza percepiti / Aree di criticità reputation'\n"
    ),
    "competitivo": (
        "BLOCCHI OBBLIGATORI ANALISI COMPETITIVA:\n"
        "  a) data_table 'Benchmark competitor' columns=[Competitor, Quota %, Prezzo medio, Differenziazione, Note], ≥4 righe REALI da web_search\n"
        "  b) data_table 'Feature comparison' columns=[Feature, Cliente, Competitor1, Competitor2, Gap], ≥5 righe\n"
        "  c) two_column 'Vantaggi competitivi / Gap strategici'\n"
    ),
    "custom_data": (
        "BLOCCHI OBBLIGATORI ANALISI DATI:\n"
        "  a) data_table 'Statistiche descrittive' columns=[Variabile, N, Media, Mediana, Min, Max, Std], dipende dataset\n"
        "  b) data_table 'Correlazioni / pattern rilevati' columns=[Pattern, Variabili, Evidenza, Significatività, Implicazione], ≥3 righe\n"
        "  c) narrative 'Insight chiave' (≥150 parole)\n"
    ),
    "generic": (
        "BLOCCHI RACCOMANDATI: oltre exec_summary + conclusions, includi almeno 1 data_table\n"
        "rilevante al tema e 1 two_column 'forza/gap' o equivalente. 4-6 blocchi totali.\n"
    ),
}


_CONCLUSIONS_SCHEMAS: Dict[str, str] = {
    "seo": (
        "  left.heading='3 problemi principali' · body_html=<ol> 3 problemi · heading_variant='alert'\n"
        "  right.heading='3 azioni immediate (settimana 1-2)' · right.milestones=[azione1, azione2, KPI 30/60/90]\n"
    ),
    "bilancio": (
        "  left.heading='3 rischi finanziari principali' · body_html=<ol> 3 rischi (liquidità/marginalità/leverage)\n"
        "  right.heading='Leve di miglioramento' · right.milestones=[\n"
        "    Riduzione DSO/working capital | Ottimizzazione costi | KPI bilancio 90/180/365gg]\n"
    ),
    "marketing": (
        "  left.heading='3 gap di posizionamento' · body_html=<ol> 3 gap rispetto a competitor/audience\n"
        "  right.heading='Iniziative growth' · right.milestones=[\n"
        "    Campaign quick-win | Sviluppo channel | KPI marketing 30/60/90gg (CAC, ROAS, conv rate)]\n"
    ),
    "contenuti": (
        "  left.heading='3 priorità del piano contenuti' · body_html=<ol> 3 priorità (coerenza pilastri, cadenza sostenibile, CTA verso obiettivo)\n"
        "  right.heading='Come partire (prime 2 settimane)' · right.milestones=[\n"
        "    Setup asset/template | Prime uscite + hashtag/keyword | KPI 30/60/90gg (reach, salvataggi, click, lead)]\n"
    ),
    "business_plan": (
        "  left.heading='3 rischi go-to-market' · body_html=<ol> 3 rischi su mercato/competizione/esecuzione\n"
        "  right.heading='Milestone chiave 12 mesi' · right.milestones=[\n"
        "    Mese 3 milestone | Mese 6 milestone | KPI 12 mesi (revenue/CAC/burn)]\n"
    ),
    "fattibilita": (
        "  left.heading='3 fattori di rischio critici' · body_html=<ol> 3 rischi tecnici/mercato/finanziari\n"
        "  right.heading='Raccomandazione go/no-go' · right.milestones=[\n"
        "    Decisione | Pre-condizioni | KPI di go-decision]\n"
    ),
    "due_diligence": (
        "  left.heading='3 red flag prioritarie' · body_html=<ol> 3 issue critiche\n"
        "  right.heading='Azioni di mitigazione/follow-up' · right.milestones=[\n"
        "    Azione legale | Azione fiscale/finanziaria | KPI di monitoring post-deal]\n"
    ),
    "investimento": (
        "  left.heading='3 rischi di investimento' · body_html=<ol> rischio mercato/tecnologico/finanziario\n"
        "  right.heading='Decisione + condizioni' · right.milestones=[\n"
        "    Verdetto (go/conditional/no-go) | Condizioni go | KPI monitoring 90/180gg]\n"
    ),
    "processi": (
        "  left.heading='3 colli di bottiglia critici' · body_html=<ol> 3 bottleneck con impatto h/sett\n"
        "  right.heading='Iniziative TO-BE' · right.milestones=[\n"
        "    Quick win 30gg | Trasformazione 90gg | KPI TO-BE 6 mesi]\n"
    ),
    "mercato": (
        "  left.heading='3 trend chiave' · body_html=<ol> 3 trend con evidenza (CAGR, regolamentazione, tecnologia)\n"
        "  right.heading='Opportunità di mercato' · right.milestones=[\n"
        "    Segmento prioritario | Strategia entry | KPI go-to-market 6/12 mesi]\n"
    ),
    "sentiment": (
        "  left.heading='3 criticità reputation prioritarie' · body_html=<ol> 3 cluster di criticità\n"
        "  right.heading='Azioni di response' · right.milestones=[\n"
        "    Azione immediata <7gg | Strategia 30/60gg | KPI sentiment monitoring]\n"
    ),
    "competitivo": (
        "  left.heading='3 gap strategici principali' · body_html=<ol> 3 gap vs competitor\n"
        "  right.heading='Iniziative di differenziazione' · right.milestones=[\n"
        "    Quick win competitivo | Sviluppo medium-term | KPI quota/posizionamento]\n"
    ),
    "custom_data": (
        "  left.heading='3 insight principali dai dati' · body_html=<ol> 3 finding (con riferimento numerico)\n"
        "  right.heading='Azioni data-driven' · right.milestones=[\n"
        "    Decisione tattica | Approfondimento richiesto | KPI di monitoring]\n"
    ),
    "generic": (
        "  left.heading='3 problemi/insight principali' · body_html=<ol> 3 punti chiave\n"
        "  right.heading='Azioni raccomandate' · right.milestones=[\n"
        "    Azione 1 | Azione 2 | KPI 30/60/90gg]\n"
    ),
}


_FOOTER_DISCLAIMERS: Dict[str, str] = {
    "seo": "Le stime di traffico, volume keyword e proiezioni sono basate su benchmark di mercato. I dati reali possono variare. Verificare con Google Search Console e strumenti di analisi dedicati.",
    "bilancio": "Le proiezioni finanziarie sono basate sui dati di bilancio forniti e su benchmark di settore. Verificare con il commercialista e dati gestionali aggiornati.",
    "marketing": "Le stime di CAC, conversion e ROAS sono benchmark di mercato. I valori reali dipendono da budget, creatività e audience. Verificare con Analytics e piattaforme ads.",
    "contenuti": "Piano editoriale basato sugli obiettivi e sul materiale forniti. Adattare i contenuti al calendario reale dell'azienda e alle linee guida di brand. Le metriche social vanno verificate negli insight delle piattaforme.",
    "business_plan": "Le proiezioni economico-finanziarie sono basate su assunzioni esplicitate nel documento. Soggette a revisione in base a evoluzione mercato ed esecuzione.",
    "fattibilita": "L'analisi è basata sui dati forniti e su benchmark pubblici. Decisione finale richiede validazione tecnica e commerciale approfondita.",
    "due_diligence": "Documento di sintesi preliminare. Non sostituisce due diligence legale, fiscale e commerciale completa di professionisti qualificati.",
    "investimento": "Le metriche di ritorno sono stime su scenari forniti. Investimenti soggetti a rischio di mercato e operativo. Non costituisce consulenza finanziaria.",
    "processi": "Analisi basata su mappatura AS-IS raccolta. Le proiezioni TO-BE richiedono validazione operativa e change management.",
    "mercato": "Dati di mercato basati su fonti pubbliche citate. Stime TAM/SAM/SOM soggette a metodologia. Aggiornare con ricerche primarie per decisioni operative.",
    "sentiment": "Analisi basata su menzioni rilevate. Sentiment soggetto a interpretazione algoritmica. Verificare a campione su rilevazioni manuali.",
    "competitivo": "Benchmark competitor basati su fonti pubbliche e stime di settore. Dati interni concorrenti non verificabili senza accesso diretto.",
    "custom_data": "Analisi statistica sui dati forniti. Conclusioni dipendenti da qualità e completezza del dataset.",
    "generic": "Le stime e proiezioni sono basate sui dati raccolti in sessione e su benchmark di mercato. Verificare con strumenti e fonti dedicate per decisioni operative.",
}


def _build_report_profile(report_type: Optional[str]) -> Dict[str, str]:
    """Ritorna sezioni di prompt customizzate per il reportType detected."""
    cat = _classify_report(report_type)
    return {
        "category": cat,
        "score_rubric": _SCORE_RUBRICS.get(cat, _SCORE_RUBRICS["generic"]),
        "required_blocks": _REQUIRED_BLOCKS.get(cat, _REQUIRED_BLOCKS["generic"]),
        "conclusions_schema": _CONCLUSIONS_SCHEMAS.get(cat, _CONCLUSIONS_SCHEMAS["generic"]),
        "footer_disclaimer": _FOOTER_DISCLAIMERS.get(cat, _FOOTER_DISCLAIMERS["generic"]),
    }


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


def _run_llm_call(
    client: anthropic.Anthropic,
    system_blocks: list,
    user_message: str,
    *,
    max_tokens: int = 16000,
    use_web_search: bool = True,
    timeout: float = 120.0,
    max_hops: int = 4,
    web_search_uses: int = 4,
    label: str = "llm",
) -> str:
    """Single Sonnet call con rate-limit backoff + web_search server-side loop.

    Ritorna il testo raw del modello (no JSON parse). Helper riusato da
    single-call e da ciascuna fase del multi-call orchestrator.
    """
    delays = [12, 25, 45]
    tools = (
        [{"type": "web_search_20250305", "name": "web_search", "max_uses": web_search_uses}]
        if use_web_search else []
    )

    def _create(messages: List[Dict[str, Any]]):
        last_exc: Optional[Exception] = None
        for attempt, delay in enumerate([0] + delays):
            if delay:
                log.warning("Rate-limited, retry %d/%d after %ds", attempt, len(delays), delay)
                time.sleep(delay)
            try:
                kwargs: Dict[str, Any] = dict(
                    model=ANTHROPIC_PDF_MODEL,
                    max_tokens=max_tokens,
                    system=system_blocks,
                    messages=messages,
                    timeout=timeout,
                )
                if tools:
                    kwargs["tools"] = tools
                return client.messages.create(**kwargs)
            except anthropic.RateLimitError as exc:
                last_exc = exc
                continue
        raise last_exc if last_exc else RuntimeError("rate-limit retry loop exhausted")

    conversation: List[Dict[str, Any]] = [{"role": "user", "content": user_message}]
    call_start = time.monotonic()
    for hop in range(max_hops):
        hop_start = time.monotonic()
        result = _create(conversation)
        log.info("LLM[%s] hop=%d duration=%.1fs stop=%s", label, hop, time.monotonic() - hop_start, getattr(result, "stop_reason", None))
        stop = getattr(result, "stop_reason", None)
        if stop == "tool_use":
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
        text = "".join(b.text for b in result.content if getattr(b, "type", "") == "text")
        log.info("LLM[%s] DONE total=%.1fs text_len=%d", label, time.monotonic() - call_start, len(text))
        return text
    log.warning("LLM[%s] EXHAUSTED max_hops=%d after %.1fs", label, max_hops, time.monotonic() - call_start)
    return ""


def _generate_multi_call(
    client: anthropic.Anthropic,
    system_blocks: list,
    base_user_message: str,
) -> Dict[str, Any]:
    """3 chiamate Sonnet sequenziali: exec_summary (web_search), body, conclusions.

    Risolve il problema 'ultimo blocco troncato' quando il report singolo eccede
    max_tokens. Ogni call ha output ridotto (8k/12k/4k token) → no troncamento.
    Cache hit su system prompt dopo prima call → costo input scontato 90%.
    """
    # FASE 1/3 — meta + executive_summary + footer (web_search per benchmark/competitor)
    ua = base_user_message + (
        "\n\n=== FASE 1/3 — EMETTI SOLO QUESTO JSON ===\n"
        "{\n"
        '  "meta": {title, subtitle, kicker, sector, date},\n'
        '  "executive_summary": {type:"executive_summary", title, body, score, '
        'score_breakdown:[4 dimensioni con items dettagliati]},\n'
        '  "footer": {disclaimer}\n'
        "}\n"
        "Usa web_search per dati benchmark/competitor REALI. Output: solo l'oggetto, "
        "niente prosa fuori, niente altri blocchi corpo né conclusions."
    )
    raw_a = _run_llm_call(client, system_blocks, ua, max_tokens=8000, use_web_search=True, label="A.exec_summary")
    payload_a = _extract_json(raw_a)
    meta = payload_a.get("meta") or {}
    exec_summary = payload_a.get("executive_summary") or {}
    footer = payload_a.get("footer") or {}
    log.info("Multi-call A: meta=%s exec_summary_score=%s", bool(meta), exec_summary.get("score"))

    # FASE 2/3 — body blocks (no web_search, già usato in fase 1)
    ub = base_user_message + (
        "\n\n=== FASE 2/3 — EMETTI SOLO QUESTO JSON ===\n"
        '{"blocks": [ ...4-6 blocchi corpo... ]}\n'
        "TIPI AMMESSI: kpi_grid, two_column, data_table, action_list, risk_mitigation, narrative.\n"
        "VIETATO: executive_summary, conclusions (già emessi in fase 1/3 e separati in fase 3/3).\n\n"
        "Contesto già emesso (NON ripetere, sintetizza coerente):\n"
        f"  meta.title = {str(meta.get('title',''))[:120]}\n"
        f"  score totale = {exec_summary.get('score')}/100\n"
        f"  exec_summary.title = {str(exec_summary.get('title',''))[:120]}\n\n"
        "Output: solo l'oggetto {blocks}, niente prosa, niente footer, niente meta."
    )
    raw_b = _run_llm_call(client, system_blocks, ub, max_tokens=12000, use_web_search=False, label="B.body")
    payload_b = _extract_json(raw_b)
    body_blocks = payload_b.get("blocks") or []
    if not isinstance(body_blocks, list):
        body_blocks = []
    log.info("Multi-call B: body_blocks=%d", len(body_blocks))

    # FASE 3/3 — conclusions con CONTESTO COMPLETO delle fasi precedenti.
    # Bug v12: conclusions emetteva "dati insufficienti" perché riceveva solo
    # un sommario degli altri blocchi → no specificità. Fix: passa JSON compatto
    # exec_summary + body_blocks così Sonnet può citare numeri/nomi/problemi reali.
    exec_compact = {
        "score": exec_summary.get("score"),
        "title": str(exec_summary.get("title") or "")[:120],
        "body": str(exec_summary.get("body") or "")[:400],
        "score_breakdown": exec_summary.get("score_breakdown") or [],
    }
    context_payload = json.dumps(
        {"executive_summary": exec_compact, "body_blocks": body_blocks[:8]},
        ensure_ascii=False,
    )
    if len(context_payload) > 12000:
        context_payload = context_payload[:12000] + "...}"
    uc = base_user_message + (
        "\n\n=== FASE 3/3 — EMETTI SOLO QUESTO JSON ===\n"
        "{\n"
        '  "conclusions": {\n'
        '    type:"conclusions", title:"Conclusioni e Prossimi Passi",\n'
        '    left:{heading:"3 problemi principali", heading_variant:"alert", '
        'body_html:"<ol><li>...</li><li>...</li><li>...</li></ol>"},\n'
        '    right:{heading:"3 azioni immediate (settimana 1-2)", '
        'milestones:[{label,tone,items:[]}, ..., '
        '{label:"KPI 30/60/90 giorni", tone:"neutral", items:["30gg:...","60gg:...","90gg:..."]}]}\n'
        "  }\n"
        "}\n\n"
        "REQUISITI STRINGENTI:\n"
        "- left.body_html: ≥30 parole sui 3 problemi principali. CITA numeri/nomi/"
        "metriche reali dal contesto sotto. NIENTE placeholder tipo 'dati insufficienti'.\n"
        "- right.milestones ≥3 voci: 2 azioni concrete (con step puntuali in items) + "
        "1 KPI 30/60/90 con baseline numerica.\n\n"
        "=== CONTESTO FASI 1+2 (usa questi dati per concludere) ===\n"
        f"{context_payload}\n\n"
        "Output: solo l'oggetto {conclusions}, niente prosa fuori."
    )
    raw_c = _run_llm_call(client, system_blocks, uc, max_tokens=4000, use_web_search=False, label="C.conclusions")
    payload_c = _extract_json(raw_c)
    conclusions = payload_c.get("conclusions") or {}
    log.info("Multi-call C: conclusions=%s", bool(conclusions.get("left") or conclusions.get("right")))

    return {
        "meta": meta,
        "blocks": [exec_summary] + body_blocks + ([conclusions] if conclusions else []),
        "footer": footer,
    }


def generate_analysis_json(session: dict) -> Dict[str, Any]:
    """Call Sonnet with master + vertical skills + session context.

    Returns a parsed JSON object with `meta` and `blocks` keys, conforming
    to the design system in lib/skills/report-premium-design/SKILL.md.
    """
    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY not configured")

    skills_payload = _build_skill_payload(session)
    context_block = _build_context_block(session)

    # Profile per reportType: rubric score / blocchi obbligatori / conclusions
    # schema / footer disclaimer specifici per il tipo di analisi richiesto.
    collected = session.get("collected_data") or {}
    extracted = collected.get("extractedData") or {}
    # deliverableType ("calendario editoriale", "tabella"…) guida la categoria
    # tanto quanto reportType (il tema). Li concateniamo: così un calendario
    # social diventa categoria "contenuti" anche se reportType resta "marketing".
    report_type_raw = " ".join(
        str(v) for v in (
            extracted.get("deliverableType"),
            collected.get("deliverableType"),
            extracted.get("reportType"),
            collected.get("reportType"),
        ) if v
    )
    profile = _build_report_profile(report_type_raw)
    log.info("Report profile: reportType=%r → category=%s", report_type_raw, profile["category"])

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
        "- JSON COMPATTO: ogni stringa max 350 caratteri, ogni array max 8 voci "
        "(ECCEZIONE: le data_table di tipo calendario/elenco temporale elencano UNA riga per "
        "uscita/periodo, anche 40 — vedi blocchi obbligatori), no spazi superflui. Tieni l'output "
        "compatto ma COMPLETO: non troncare i calendari.\n"
        "- Coerenza interna: stesso numero in blocchi diversi senza contraddizioni.\n"
        "- Adatta i titoli e le sezioni AL CASO SPECIFICO dell'utente.\n"
        "- Usa SOLO i tipi di blocco documentati nella master skill.\n\n"
        f"RUBRIC SCORE (per reportType={profile['category']}):\n"
        f"{profile['score_rubric']}\n"
        "FORMATO BREAKDOWN OBBLIGATORIO nell'executive_summary (campo score_breakdown) "
        "QUANDO la rubric è numerica (4 dim × 25pt): array di 4 oggetti con shape\n"
        "  {label, value (int), max:25, items:[{name, points (int), max (int), status: ok|warning|alert}]}\n"
        "REGOLA AUREA: value dimensione = SOMMA points items. Score totale = SOMMA value 4 dimensioni.\n"
        "Verifica aritmetica prima di emettere. STESSO INPUT → STESSO SCORE.\n"
        "Per reportType qualitativi (vedi rubric sopra), OMETTI il campo `score` e `score_breakdown`,\n"
        "metti un giudizio sintetico in `body` (es. 'Maturità: media-alta').\n\n"
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
        "  • KPI_GRID — separa value / note / verified, NON concatenare:\n"
        "    ❌ {\"value\":\"180-250 vis/mese [non verificato — richiede GSC]\"}\n"
        "    ✅ {\"value\":\"180–250 vis/mese\",\"note\":\"† richiede GSC/Analytics\",\"verified\":false}\n"
        "    Regola: `value` è SOLO il numero/range secco (max 20 char). `note` contiene "
        "il disclaimer/contesto (max 80 char). `verified` è boolean: true se il dato viene "
        "da fonte misurata in questa sessione (Analytics, GSC, crawl reale, file caricato), "
        "false se è stima/proiezione. Il renderer aggiunge automaticamente il dagger † per "
        "verified:false. Non includere il dagger manualmente nel value.\n"
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
        "(es. 'da X a Y visite/mese'). Se baseline non disponibile, scrivilo esplicitamente.\n"
        f"  • BLOCCHI OBBLIGATORI per reportType={profile['category']}:\n"
        f"{profile['required_blocks']}"
        "    Posiziona i data_table specifici PRIMA delle conclusions. Skippare uno = report incompleto.\n\n"
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
        "  • CONCLUSIONS BLOCK: il LAST blocco DEVE essere type='conclusions' con shape:\n"
        "    {type:'conclusions', title:'Conclusioni e Prossimi Passi',\n"
        "     left:{heading, heading_variant:'alert', body_html:'<ol><li>...3 items...</li></ol>'},\n"
        "     right:{heading, milestones:[{label,tone,items:[]}, ...]}}\n"
        f"    HEADING + MILESTONES adattati al reportType={profile['category']}:\n"
        f"{profile['conclusions_schema']}"
        "    NOMI CHIAVE OBBLIGATORI: right.milestones (NON 'actions', 'steps', 'tasks').\n"
        "    Ogni milestone con label+items+tone. Mai colonna right vuota.\n"
        f"  • FOOTER DISCLAIMER: il campo 'footer.disclaimer' del JSON DEVE contenere ESATTAMENTE:\n"
        f"    '{profile['footer_disclaimer']}'\n\n"
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
    log.info(
        "Generating report JSON model=%s skills=%d-chars multi_call=%s",
        ANTHROPIC_PDF_MODEL, len(skills_payload), ANTHROPIC_PDF_MULTI_CALL,
    )

    # Prompt caching: skills payload è stabile tra chiamate → 90% sconto su cache hit.
    # cache_control sul system prompt finale (ultimo blocco testuale).
    system_blocks = [
        {"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}},
    ]

    if ANTHROPIC_PDF_MULTI_CALL:
        try:
            parsed = _generate_multi_call(client, system_blocks, user_message)
            parsed = _sanitize_hallucinations(parsed)
            parsed = _validate_and_repair(parsed, client, system_blocks, user_message)
            return parsed
        except (ValueError, json.JSONDecodeError, RuntimeError) as exc:
            log.warning("Multi-call generation failed (%s), falling back to single-call", exc)

    raw = _run_llm_call(client, system_blocks, user_message, max_tokens=16000, use_web_search=True, label="single")
    if not raw:
        raise RuntimeError("LLM returned no text block (web_search loop esaurito)")
    try:
        parsed = _extract_json(raw)
        parsed = _sanitize_hallucinations(parsed)
        # Pipeline validation: rigenera blocchi problematici prima del render.
        parsed = _validate_and_repair(parsed, client, system_blocks, user_message)
        return parsed
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


def _sanitize_recursive(value: Any, ctx: dict, parent_keys: tuple = ()) -> Any:
    if isinstance(value, dict):
        # KPI item shape: contiene `value` + (`label` o `verified`).
        # Marca contesto per evitare riapplicare regex inline su .value già
        # normalizzato in _normalize_kpi_blocks.
        is_kpi_item = "value" in value and ("label" in value or "verified" in value)
        out = {}
        for k, v in value.items():
            child_parents = parent_keys + (k,)
            if is_kpi_item and k == "value" and isinstance(v, str):
                out[k] = v  # leave as-is, già normalizzato
            else:
                out[k] = _sanitize_recursive(v, ctx, child_parents)
        return out
    if isinstance(value, list):
        # Filtra elementi vuoti: stringhe blank, dict senza testo, oggetti
        # incompleti (es. {"text":""}). Era causa di bullet vuoti pagina 3.
        cleaned: list = []
        for v in value:
            sub = _sanitize_recursive(v, ctx, parent_keys)
            if isinstance(sub, str) and not sub.strip():
                ctx["fixed"] += 1
                continue
            if isinstance(sub, dict):
                # Drop dict senza alcuna stringa non-vuota
                if not any(isinstance(x, str) and x.strip() for x in sub.values()):
                    ctx["fixed"] += 1
                    continue
            cleaned.append(sub)
        return cleaned
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


_INLINE_DISCLAIMER_RE = re.compile(r"\s*[\[(]\s*([^\])]+?)\s*[\])]")
_DISCLAIMER_KEYWORDS = ("non verificato", "stima", "da verificare", "richiede", "fonte", "proiezione")


def _split_kpi_value_disclaimer(item: Dict[str, Any]) -> bool:
    """Sposta disclaimer inline da `value` a `note` + setta `verified=False`.

    Sonnet a volte concatena '[non verificato — richiede GSC]' dentro `value`,
    distruggendo la tipografia della card KPI (8 righe di disclaimer al posto
    del numero secco). Separiamo il dato dal disclaimer, marchiamo unverified.
    Ritorna True se ha modificato l'item.
    """
    value = str(item.get("value") or "")
    if not value:
        return False
    changed = False
    m = _INLINE_DISCLAIMER_RE.search(value)
    if m and any(k in m.group(1).lower() for k in _DISCLAIMER_KEYWORDS):
        disclaimer = m.group(1).strip()
        item["value"] = (value[:m.start()] + value[m.end():]).strip(" ·,-—")
        existing = str(item.get("note") or "").strip()
        item["note"] = f"† {disclaimer}" if not existing else f"{existing} · {disclaimer}"
        item["verified"] = False
        changed = True
    elif _TRAFFIC_RE.search(value) or _KEYWORD_POS_RE.search(value):
        if item.get("verified") is None:
            item["verified"] = False
            if not item.get("note"):
                item["note"] = "† richiede GSC/Analytics"
            changed = True
    return changed


def _normalize_kpi_blocks(analysis: Dict[str, Any]) -> int:
    """Pre-pass: normalizza kpi_grid items (split value/note/verified)."""
    fixed = 0
    for block in analysis.get("blocks") or []:
        if not isinstance(block, dict) or block.get("type") != "kpi_grid":
            continue
        items = block.get("items") or block.get("kpis") or block.get("cards") or []
        for item in items:
            if isinstance(item, dict) and _split_kpi_value_disclaimer(item):
                fixed += 1
    return fixed


def _sanitize_hallucinations(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Catch-all regex per pattern di hallucination che Sonnet emette nonostante
    il prompt. Sostituisce numeri secchi con tag "[non verificato]" e applica
    correzioni context-aware (es. sede K2-AI = Perugia)."""
    ctx: dict = {"fixed": 0}
    # KPI normalize PRIMA del walk ricorsivo: evita doppia tag inline.
    kpi_fixed = _normalize_kpi_blocks(analysis)
    if kpi_fixed:
        log.info("Post-gen sanitizer normalized %d KPI items", kpi_fixed)
    # Detection sede K2-AI dal flatten dell'intero JSON (cerca P.IVA o "Perugia").
    flat = json.dumps(analysis, ensure_ascii=False)
    ctx["force_perugia"] = bool(_PERUGIA_HINT.search(flat))
    cleaned = _sanitize_recursive(analysis, ctx)
    if ctx["fixed"]:
        log.info("Post-gen sanitizer fixed %d hallucination patterns", ctx["fixed"])
    return cleaned


# =============================================================================
# Pipeline validation post-generation (layer 4 dell'architettura).
# Verifica determinismi prima del render PDF: blocchi non vuoti, score = somma
# sotto-dimensioni, date future, sede non default. Per blocchi falliti retry
# targeted invece di rigenerare l'intero report.
# =============================================================================

def _block_content_length(block: dict) -> int:
    """Calcola la lunghezza testo totale del blocco (escluso titolo)."""
    total = 0
    for k, v in block.items():
        if k in ("type", "title"):
            continue
        if isinstance(v, str):
            total += len(v.strip())
        elif isinstance(v, dict):
            total += _block_content_length(v)
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, str):
                    total += len(item)
                elif isinstance(item, dict):
                    total += _block_content_length(item)
    return total


_WORD_COUNT_RE = re.compile(r"\b\w{2,}\b", re.UNICODE)


def _strip_html_tags(s: str) -> str:
    return re.sub(r"<[^>]+>", " ", s or "")


def _validate_conclusions(block: dict) -> Optional[str]:
    """Conclusions strutturale: left.body_html ≥ 30 parole + right.milestones ≥ 2."""
    left = block.get("left") or {}
    right = block.get("right") or {}
    left_text = _strip_html_tags(str(left.get("body_html") or left.get("body") or ""))
    left_words = len(_WORD_COUNT_RE.findall(left_text))
    if left_words < 30:
        return f"conclusions.left troppo corto ({left_words} parole, serve ≥30 sui 3 problemi principali)"
    milestones = right.get("milestones") or right.get("actions") or right.get("steps") or []
    valid_milestones = [
        m for m in milestones
        if isinstance(m, dict) and (m.get("items") or m.get("body_html") or m.get("body"))
    ]
    if len(valid_milestones) < 2:
        return f"conclusions.right.milestones insufficienti ({len(valid_milestones)} validi, serve ≥2 fra azioni + KPI 30/60/90)"
    return None


def _validate_action_list(block: dict) -> Optional[str]:
    """Action list: almeno 3 actions con title non vuoto."""
    actions = block.get("actions") or block.get("items") or []
    valid = [
        a for a in actions
        if isinstance(a, dict) and (a.get("title") or a.get("action") or a.get("label"))
    ]
    if len(valid) < 3:
        return f"action_list: solo {len(valid)} azioni valide (servono ≥3 con title)"
    return None


def _validate_kpi_grid(block: dict) -> Optional[str]:
    """KPI grid: almeno 2 items con value non vuoto."""
    items = block.get("items") or block.get("kpis") or block.get("cards") or []
    valid = [i for i in items if isinstance(i, dict) and str(i.get("value") or "").strip()]
    if len(valid) < 2:
        return f"kpi_grid: solo {len(valid)} item con value (servono ≥2)"
    return None


_STRUCTURAL_VALIDATORS = {
    "conclusions": _validate_conclusions,
    "action_list": _validate_action_list,
    "kpi_grid": _validate_kpi_grid,
}

# Soglie minime di contenuto utile per tipo blocco. Sotto questo threshold
# il blocco è scheletro/placeholder → rigenera. Override del check generico
# 80 char per dare richieste mirate al LLM.
_REQUIRED_MIN_CHARS = {
    "conclusions": 300,
    "narrative": 150,
    "narrative_split": 150,
    "two_column": 200,
    "action_list": 120,
    "risk_mitigation": 150,
    "data_table": 150,
    "executive_summary": 200,
    "kpi_grid": 80,
}


_REQUIRED_BLOCK_TYPES = ("executive_summary", "conclusions")


def _detect_missing_required_blocks(analysis: dict) -> List[Dict[str, Any]]:
    """Issue per blocchi obbligatori mancanti (executive_summary, conclusions).

    Sonnet ogni tanto skippa exec_summary o conclusions in single-call quando
    output troncato. Block_idx=-1 + insert_position dice al repair di inserire
    invece di sostituire un blocco esistente.
    """
    issues: List[Dict[str, Any]] = []
    blocks = analysis.get("blocks") or []
    present_types = {b.get("type") for b in blocks if isinstance(b, dict)}
    for required in _REQUIRED_BLOCK_TYPES:
        if required not in present_types:
            issues.append({
                "block_idx": -1,
                "block_type": required,
                "reason": (
                    f"blocco obbligatorio '{required}' MANCANTE — generalo ex-novo "
                    f"con tutti i campi previsti dalla master skill"
                ),
                "insert_position": "first" if required == "executive_summary" else "last",
            })
    return issues


def _validate_blocks(analysis: dict) -> List[Dict[str, Any]]:
    """Ritorna lista di issue {block_idx, block_type, reason} da riparare."""
    issues: List[Dict[str, Any]] = []
    blocks = analysis.get("blocks") or []
    issues.extend(_detect_missing_required_blocks(analysis))
    for i, b in enumerate(blocks):
        if not isinstance(b, dict):
            issues.append({"block_idx": i, "block_type": "unknown", "reason": "non-dict block"})
            continue
        btype = b.get("type") or "unknown"
        # Validator strutturale per block type noto (più strict di char count).
        struct = _STRUCTURAL_VALIDATORS.get(btype)
        if struct:
            reason = struct(b)
            if reason:
                issues.append({"block_idx": i, "block_type": btype, "reason": reason})
                continue
        clen = _block_content_length(b)
        min_chars = _REQUIRED_MIN_CHARS.get(btype, 80)
        if clen < min_chars:
            issues.append({
                "block_idx": i,
                "block_type": btype,
                "reason": f"contenuto insufficiente per type={btype} ({clen} char, serve >={min_chars}). Espandi con dati specifici, numeri, nomi, scadenze.",
            })
    return issues


def _validate_score_math(analysis: dict) -> Optional[str]:
    """Verifica aritmetica score: totale == somma dimensioni == somma items per dim.

    Tre check in cascata:
      1. somma 4 value dimensioni ≈ totale (tolleranza 2pt)
      2. ogni dimensione: somma points dei suoi items == value della dimensione
      3. nessun item supera il proprio max
    Ritorna primo issue trovato, None se tutto ok.
    """
    blocks = analysis.get("blocks") or []
    for b in blocks:
        if not isinstance(b, dict) or b.get("type") != "executive_summary":
            continue
        score = b.get("score") or b.get("gauge_value")
        breakdown = b.get("score_breakdown") or b.get("breakdown")
        if score is None or not isinstance(breakdown, list):
            return None
        try:
            total = int(score)
        except (ValueError, TypeError):
            return None
        dim_values: List[int] = []
        for dim in breakdown:
            if not isinstance(dim, dict):
                continue
            try:
                dv = int(dim.get("value") or dim.get("score") or 0)
            except (ValueError, TypeError):
                continue
            dim_values.append(dv)
            items = dim.get("items") or []
            if isinstance(items, list) and items:
                points_sum = 0
                for it in items:
                    if not isinstance(it, dict):
                        continue
                    try:
                        p = int(it.get("points") or 0)
                        mx = int(it.get("max") or 0)
                        if mx and p > mx:
                            return f"score: item '{it.get('name','?')}' di '{dim.get('label','?')}' supera max ({p}>{mx})"
                        points_sum += p
                    except (ValueError, TypeError):
                        continue
                if abs(points_sum - dv) > 1:
                    return f"score: dimensione '{dim.get('label','?')}' value={dv} ≠ somma items={points_sum}"
        if dim_values and abs(sum(dim_values) - total) > 2:
            return f"score totale {total} ≠ somma dimensioni {sum(dim_values)}"
    return None


def _repair_block(
    client: anthropic.Anthropic,
    system_blocks: list,
    user_message: str,
    full_analysis: dict,
    issue: dict,
) -> Optional[dict]:
    """Targeted retry: chiede a Sonnet di rigenerare SOLO il blocco fallito.

    Ritorna il blocco riparato, o None se retry fallisce. Niente web_search
    (più veloce, riusa contesto già caricato in cache).
    """
    idx = issue["block_idx"]
    btype = issue["block_type"]
    reason = issue["reason"]
    is_insert = idx < 0
    other_blocks_summary = []
    for i, b in enumerate(full_analysis.get("blocks") or []):
        if i == idx or not isinstance(b, dict):
            continue
        other_blocks_summary.append(f"  [{i}] type={b.get('type')} title={b.get('title','')[:60]}")
    if is_insert:
        action = f"GENERA EX-NOVO un blocco type='{btype}' (mancante nel report)"
    else:
        action = f"RIEMETTI il blocco #{idx} (type='{btype}')"
    repair_user = (
        f"Problema: {reason}.\n\n"
        f"Altri blocchi del report (riferimento, NON riemetterli):\n"
        + "\n".join(other_blocks_summary) +
        f"\n\n{action} come oggetto JSON valido secondo lo schema master. "
        f"Niente fence markdown, niente prosa fuori. Solo l'oggetto.\n\n"
        f"CONTESTO ORIGINALE:\n{user_message[:4000]}"
    )
    try:
        retry = client.messages.create(
            model=ANTHROPIC_PDF_MODEL,
            max_tokens=4096,
            system=system_blocks,
            messages=[{"role": "user", "content": repair_user}],
            timeout=120.0,
        )
    except Exception:
        log.exception("Block repair LLM call failed")
        return None
    text = "".join(b.text for b in retry.content if getattr(b, "type", "") == "text").strip()
    if not text:
        return None
    try:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1:
            return None
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None


def _validate_and_repair(
    analysis: dict,
    client: anthropic.Anthropic,
    system_blocks: list,
    user_message: str,
) -> dict:
    """Pipeline validation completa post-gen.

    1. Identifica blocchi quasi-vuoti (<80 char).
    2. Per ognuno: targeted retry isolato (no web_search).
    3. Sostituisce in-place se riparato.
    4. Logga statistiche per visibilità.
    5. Sanitizer hallucination re-applicato sui blocchi nuovi.
    """
    issues = _validate_blocks(analysis)
    score_issue = _validate_score_math(analysis)
    if not issues and not score_issue:
        return analysis
    log.info("Validation pipeline: %d block issues + score_issue=%s", len(issues), bool(score_issue))
    # Cap retry a 4 issue per evitare loop costosi.
    for issue in issues[:4]:
        repaired = _repair_block(client, system_blocks, user_message, analysis, issue)
        if not (repaired and isinstance(repaired, dict)):
            continue
        idx = issue.get("block_idx", -1)
        if idx >= 0:
            analysis["blocks"][idx] = repaired
            log.info("Repaired block #%d (type=%s)", idx, issue["block_type"])
        else:
            # Insert missing required block at correct position.
            pos = issue.get("insert_position", "last")
            if pos == "first":
                analysis["blocks"].insert(0, repaired)
            else:
                analysis["blocks"].append(repaired)
            log.info("Inserted missing required block (type=%s, pos=%s)", issue["block_type"], pos)
    return _sanitize_hallucinations(analysis)
