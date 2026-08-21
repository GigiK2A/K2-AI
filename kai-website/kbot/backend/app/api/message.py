"""POST /api/kbot/message — chat turn against an existing session.

Mirror of api/kbot/message.ts in the site.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re as _re
from typing import List, Optional

import anthropic
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..lib import sessions, engine, readiness, web_search, quality_gate
from ..lib import conversation_memory
from ..lib import conversations_index
from ..lib.analytics import track_server
from ..lib.auth import AuthUser, optional_user
from ..lib import profile as profile_lib
from ..lib import fact_grounding
from ..lib.limiter import limiter
from ..lib.url_fetcher import UrlFetchError, fetch_url_content
from ..lib.prompts import (
    append_system_text,
    build_history,
    build_system_blocks,
    extract_summary,
    normalize_assistant_reply,
    sanitize_unverified_legal_citations,
    strip_summary_block,
)
from ..lib.services import normalize_service_id, resolve_skills_for_session
from ..settings import (
    ANTHROPIC_API_KEY,
    ANTHROPIC_MODEL,
    HISTORY_CHAR_BUDGET,
    MAX_HISTORY_MESSAGES,
    MAX_MESSAGE_CHARS,
)

router = APIRouter()
log = logging.getLogger(__name__)

# Rileva URL incollati in chat anche SENZA schema: http(s)://, www., o dominio nudo
# con TLD comune (es. "studioX.com", "sito.it/pagina"). Evita le email (lookbehind @).
_URL_RE = _re.compile(
    r"(?:https?://|www\.)[^\s<>\"')\]]{2,}"
    r"|(?<![@\w/.])(?:[a-z0-9](?:[a-z0-9-]{0,40}[a-z0-9])?\.)+"
    r"(?:it|com|net|org|io|eu|ai|co|info|biz|dev|app|cloud|online|shop|store|tech|me|uk|de|fr|es|us|gov|edu|news|agency|studio|consulting|email)"
    r"(?:/[^\s<>\"')\]]*)?",
    _re.IGNORECASE)
_MAX_AUTO_URLS = 2  # max URLs to auto-fetch per message turn


def _normalize_url(u: str) -> str:
    u = (u or "").strip().rstrip(".,;:!?)>]\"'")
    if not u.lower().startswith(("http://", "https://")):
        u = "https://" + u
    return u


def _extract_urls(text: str) -> list[str]:
    seen, out = set(), []
    for m in _URL_RE.findall(text or ""):
        nu = _normalize_url(m)
        if nu.lower() not in seen:
            seen.add(nu.lower()); out.append(nu)
    return out[:_MAX_AUTO_URLS]


async def _auto_fetch_urls(text: str, collected: dict) -> dict:
    """Detect URLs in text, fetch any not already in session, return updated collected."""
    urls = _extract_urls(text)
    if not urls:
        return collected
    existing = {u.get("url") for u in (collected.get("analyzed_urls") or [])}
    new_entries = list(collected.get("analyzed_urls") or [])
    for url in urls:
        if url in existing:
            continue
        if len(new_entries) >= 5:
            break
        try:
            data = await fetch_url_content(url)
            new_entries.append(data)
            existing.add(url)
        except (UrlFetchError, Exception):
            pass  # silent — don't block the chat turn
    collected = dict(collected)
    collected["analyzed_urls"] = new_entries
    return collected


class MessageBody(BaseModel):
    sessionId: str = Field(..., alias="session_id")
    serviceId: Optional[str] = Field(default=None, alias="service_id")
    message: Optional[str] = None
    messages: Optional[List[dict]] = None
    forcedSkills: Optional[List[str]] = Field(default=None, alias="forced_skills")

    class Config:
        populate_by_name = True


def _check_ownership(session: dict, user: Optional[AuthUser]) -> None:
    owner = session.get("user_id")
    if owner and (not user or user.id != owner):
        raise HTTPException(status_code=403, detail="not your session")


def _new_user_messages(body: MessageBody) -> List[dict]:
    if body.message and body.message.strip():
        return [{"role": "user", "content": body.message.strip()}]
    if body.messages:
        return [
            {"role": m.get("role", "user"), "content": str(m.get("content") or "")}
            for m in body.messages
            if str(m.get("content") or "").strip()
        ]
    return []


# ---- Gate intervista: nessun modello può saltare le domande generando in anticipo ----
# Le regex di governo (procedi/ready/not-ready/urgenza/summary/diagnosi) vivono in
# lib/signals.py (SSOT testata): erano sparse in 3 file e le divergenze hanno già
# prodotto bug reali (negazione matchata come readiness; soglie gate divergite).
from ..lib import signals

_MIN_INTERVIEW_TURNS = 2  # allineato al prompt (logica consulente): una domanda di
# comprensione, poi la Stop Rule/readiness può far partire il report. Era 4 → sopprimeva
# il summary anche quando il bot si fermava presto (bug "stop rapido → report non generato").


def _interview_gate_active(merged_messages: list) -> bool:
    """True se siamo ancora in fase intervista: < _MIN_INTERVIEW_TURNS turni utente e
    l'utente NON ha chiesto esplicitamente di procedere."""
    turns = sum(1 for m in (merged_messages or []) if isinstance(m, dict) and m.get("role") == "user")
    if turns >= _MIN_INTERVIEW_TURNS:
        return False
    last_user = next((str(m.get("content") or "") for m in reversed(merged_messages or [])
                      if isinstance(m, dict) and m.get("role") == "user"), "")
    return not bool(signals.PROCEDI_RE.search(last_user))


def _analysis_streak_reached(merged_messages: list, raw_text: str, need: int = 2) -> bool:
    """Regola hard (Luca): se il bot fornisce analisi/raccomandazioni/conclusioni per >= `need`
    turni assistant CONSECUTIVI (incluso quello corrente), la soglia per il report è superata —
    è un indicatore OGGETTIVO che i dati bastano. Backstop deterministico: il modello locale
    continua a rimandare la generazione anche quando potrebbe già produrla."""
    if not signals.provides_analysis(strip_summary_block(raw_text or "")):
        return False
    streak = 1
    for m in reversed(merged_messages or []):
        if not isinstance(m, dict) or m.get("role") != "assistant":
            continue  # i turni user interlacciano: si ignorano
        if signals.provides_analysis(str(m.get("content") or "")):
            streak += 1
            if streak >= need:
                return True
        else:
            break  # sequenza consecutiva interrotta
    return streak >= need


def _extract_gated_summary(raw_text: str, merged_messages: list, collected: Optional[dict] = None):
    """Estrae summary + stato diagnostico; SOPPRIME il summary se in fase intervista o se
    l'utente ha chiesto di continuare la consulenza (report_hold). Il visibile è ripulito
    da ENTRAMBI i blocchi macchina (summary + diagnosi)."""
    from ..lib.prompts import extract_diagnosi, strip_diagnosi_block
    summary = extract_summary(raw_text)
    diagnosi = extract_diagnosi(raw_text)
    # Guardia normativa: citazioni con numero verificate contro il corpus 8e restano,
    # le altre vengono de-specificate. Fail-closed → strip puro (mai fail-open).
    from ..lib import norme_guard, deadline_guard, finance_guard, output_quality
    visible = finance_guard.sanitize(deadline_guard.sanitize(norme_guard.sanitize(
        normalize_assistant_reply(strip_summary_block(strip_diagnosi_block(raw_text))))))
    # OUTPUT QUALITY ENGINE (ultimo miglio, review "AI Proof"): l'utente non vede mai
    # HTML/template/placeholder/artefatti tecnici/tipografia sporca. Fail-open.
    visible = output_quality.polish(visible)
    if summary and _interview_gate_active(merged_messages):
        summary = None
        if len((visible or "").strip()) < 5:
            visible = ("Prima di preparare il report mi servono ancora un paio di dettagli. "
                       "Qual è l'obiettivo concreto che vuoi ottenere con questa analisi?")
    # HOLD: l'utente vuole continuare a ragionare → il report NON si propone, anche se il
    # modello ha emesso il blocco (rispetto della volontà utente, vincolante a codice).
    if summary and collected and collected.get("report_hold"):
        summary = None
        if len((visible or "").strip()) < 5:
            visible = ("Restiamo sulla diagnosi, come hai chiesto. Qual è l'aspetto che vuoi "
                       "approfondire per primo?")
    return visible, summary, diagnosi


def _update_report_hold(collected: dict, last_user_text: str) -> bool:
    """Consenso alla generazione (sticky tra i turni). Comanda l'UTENTE:
    - un PROCEDI esplicito → sblocca (l'utente CHIEDE il report);
    - una richiesta di continuare la consulenza / non generare → blocca;
    - altrimenti resta com'era (il blocco NON si auto-rimuove col passare dei turni).
    Ritorna il valore corrente. È la traduzione a CODICE di 'rispetta la volontà utente'
    (review calo ordini): nessun trigger automatico può scavalcarlo."""
    txt = last_user_text or ""
    if signals.PROCEDI_HARD_RE.search(txt):
        hold = False
    elif signals.wants_to_continue(txt):
        hold = True
    else:
        hold = bool(collected.get("report_hold"))
    collected["report_hold"] = hold
    return hold


def _postprocess_turn(client, system_prompt, messages: list, merged_messages: list,
                      raw_text: str, collected: Optional[dict] = None) -> str:
    """Finalize CONDIVISA del turno (path sync E streaming — la duplicazione dei due
    path aveva già prodotto divergenze: il fallback readiness esisteva solo sullo
    streaming). Ordine: forced-summary → quality gate."""
    raw_text = _ensure_summary_block(client, system_prompt, messages, raw_text,
                                     merged_messages, collected)
    _last_user = next((str(m.get("content") or "") for m in reversed(merged_messages or [])
                       if isinstance(m, dict) and m.get("role") == "user"), "")
    raw_text = quality_gate.review(client, ANTHROPIC_MODEL, merged_messages, raw_text,
                                   user_procedi=bool(signals.PROCEDI_HARD_RE.search(_last_user)))
    return raw_text


def _apply_summary_contract(collected: dict, summary: dict) -> None:
    """Valida il payload CONSULENZA_SUMMARY e imposta lo STATO deliverable persistente
    (review flusso deliverable). Valido → READY_FOR_GENERATION + version + generation in
    extractedData (trigger strutturato). Non valido → INVALID_SUMMARY, loggato, nessun crash."""
    from ..lib import summary_contract, deliverable_state
    model, err = summary_contract.validate_summary(summary)
    if model is None:
        log.warning("kbot: CONSULENZA_SUMMARY non valido (%s) — raw=%r", err, str(summary)[:400])
        deliverable_state.set_state(collected, deliverable_state.INVALID_SUMMARY)
        return
    ed = dict(collected.get("extractedData") or {})
    ed["generation"] = model.generation.model_dump()
    ed["summary_version"] = summary_contract.summary_version(summary)
    collected["extractedData"] = ed
    deliverable_state.set_state(collected, deliverable_state.READY_FOR_GENERATION)


def _persist_diagnosi(collected: dict, diagnosi: Optional[dict]) -> None:
    """Persiste lo stato diagnostico del bot (memoria di lavoro tra i turni): ipotesi,
    dato mancante, FASE e CONFIDENZA. Confidenza/fase alimentano il pre-flight di
    generazione (una diagnosi non solida non deve produrre report)."""
    if isinstance(diagnosi, dict) and diagnosi.get("ipotesi"):
        _conf = str(diagnosi.get("confidenza") or "").strip().lower() or None
        _fase = str(diagnosi.get("fase") or "").strip().lower() or None

        def _norm_ip(i: dict) -> dict:
            out = {"t": i["t"], "s": i.get("s") or "aperta"}
            try:
                p = int(round(float(i.get("p"))))
                out["p"] = max(0, min(100, p))
            except (TypeError, ValueError):
                pass  # p opzionale: se il modello non la emette, non inventarla
            return out

        collected["diagnosi"] = {
            "ipotesi": [_norm_ip(i) for i in diagnosi.get("ipotesi") or []
                        if isinstance(i, dict) and i.get("t")][:4],
            "manca": diagnosi.get("manca"),
            "confidenza": _conf if _conf in ("bassa", "media", "alta") else None,
            "fase": _fase if _fase in ("esplorazione", "diagnosi", "validazione",
                                       "piano", "pronto") else None,
        }


def _ensure_summary_block(client, system_prompt, messages: list, raw_text: str,
                          merged_messages: list, collected: Optional[dict] = None) -> str:
    """Forza il blocco CONSULENZA_SUMMARY SOLO quando l'utente lo chiede ESPLICITAMENTE
    (PROCEDI). Policy (review calo ordini): la generazione è una CONSEGUENZA della volontà
    utente, non un automatismo. NON si forza più su 'streak di analisi' (la quantità di
    dati non è mai criterio sufficiente) né sulla sola auto-dichiarazione di readiness del
    bot: se il bot ha davvero concluso la diagnosi, emette il blocco da solo seguendo la
    STOP RULE del prompt. No-op se il blocco c'è già o se l'utente ha chiesto di continuare
    (report_hold). Ritorna raw_text."""
    if extract_summary(raw_text):
        return raw_text
    # HOLD: l'utente ha chiesto di continuare la consulenza → nessuna forzatura possibile.
    if collected and collected.get("report_hold"):
        return raw_text
    # ENFORCEMENT PROCEDI (eval 100, 17 lug: 7× 'ecco i dati… procedi' ignorati da
    # gpt-oss): l'UNICO trigger che forza il summary dal server è la richiesta ESPLICITA
    # dell'utente (variante STRETTA: mai 'procedura'/'come procediamo?').
    _last_user = next((str(m.get("content") or "") for m in reversed(merged_messages or [])
                       if isinstance(m, dict) and m.get("role") == "user"), "")
    if not bool(signals.PROCEDI_HARD_RE.search(_last_user)):
        return raw_text
    try:
        _motivo = "L'utente ha chiesto ESPLICITAMENTE di procedere col report."
        focus = list(messages) + [
            {"role": "assistant", "content": (strip_summary_block(raw_text) or "Ho informazioni sufficienti.")[:4000]},
            {"role": "user", "content": (
                f"{_motivo} Emetti ORA SOLO il blocco "
                "CONSULENZA_SUMMARY_START ... CONSULENZA_SUMMARY_END (una riga JSON) con i campi "
                "del caso discusso: reportType, businessType, objective, scope, dataAvailable, "
                "deadline, notes (le assunzioni e i dati mancanti), summary. NIENTE altro testo.")},
        ]
        resp = client.messages.create(
            model=ANTHROPIC_MODEL, max_tokens=1400, system=system_prompt,
            messages=focus, timeout=60.0,
        )
        block = "".join(getattr(b, "text", "") for b in resp.content if getattr(b, "type", "") == "text")
        if extract_summary(block):
            log.info("kbot: blocco CONSULENZA_SUMMARY forzato dal fallback readiness")
            return f"{raw_text}\n\n{block}"
    except Exception:
        log.exception("kbot: forced-summary fallback fallito (proseguo senza)")
    return raw_text


def _recompute_boost(collected: dict, merged_messages: list, summary: Optional[dict]) -> None:
    """Ricalcola boost_suggerito a OGNI turno (>=3 turni utente), sull'intento CORRENTE.

    Gira anche SENZA summary: l'intento esplicito vive nel testo dell'UTENTE, quindi una
    richiesta SEO corregge subito un boost finance stantio di un turno precedente. Allinea
    il boost alle SKILL (che già si ricalcolano per-turno → era l'asimmetria che faceva
    apparire FinanceBoost su una richiesta SEO). Muta `collected` in place; non solleva mai.
    """
    _user_turns = sum(
        1 for _m in (merged_messages or [])
        if isinstance(_m, dict) and _m.get("role") == "user"
    )
    if _user_turns < 3:        # MINIMO 3 turni utili (come il prompt) → niente pannello precoce
        return
    try:
        from ..lib import catalog as _catalog
        # L'intento REALE è nei messaggi dell'UTENTE: passato come user_text, entra in PASS 1
        # di suggest_boost DAVANTI al reportType LLM (che può riflettere il SITO letto, non la
        # richiesta). Un match esplicito vince anche sul tag_pillar d'ingresso.
        _utext = " ".join(
            str(_m.get("content") or "") for _m in (merged_messages or [])
            if isinstance(_m, dict) and _m.get("role") == "user"
        )[-2000:]
        _base = summary or (collected.get("extractedData") or {})
        # TELEMETRIA ROUTING (motivazione loggata): domini + score + confidenza. Persistita
        # in collected così il pre-flight di generazione la può leggere senza ricalcolare.
        _rb = _catalog.route_breakdown(_base, user_text=_utext)
        collected["route_confidence"] = _rb
        log.info("kbot routing: top=%s score=%s confident=%s scores=%s",
                 _rb.get("top"), _rb.get("score"), _rb.get("confident"), _rb.get("scores"))
        _explicit = _catalog.suggest_boost(_base, explicit_only=True, user_text=_utext)
        _current = collected.get("boost_suggerito")
        if _explicit is not None:
            collected["boost_suggerito"] = _explicit["id"]
            collected["boost_suggerito_label"] = _explicit.get("label")
        elif not _current and not collected.get("tag_pillar"):
            # Nessun boost ancora scelto e nessun tag pillar → primo routing (anche default).
            _boost = _catalog.suggest_boost(_base, user_text=_utext)
            if _boost:
                collected["boost_suggerito"] = _boost["id"]
                collected["boost_suggerito_label"] = _boost.get("label")
        elif _current:
            # Boost già scelto ma nessun match ESPLICITO ora: l'utente può aver cambiato
            # argomento in modo non-esplicito (con tag_pillar presente il ramo sopra non
            # scattava → boost STANTIO). Valuta un match non-esplicito e aggiorna SOLO se è
            # chiaramente diverso e NON è il fallback generico (niente oscillazioni deboli).
            _boost = _catalog.suggest_boost(_base, user_text=_utext)
            if (_boost and _boost["id"] != _current
                    and _boost["id"] != _catalog._BOOST_DEFAULT):
                collected["boost_suggerito"] = _boost["id"]
                collected["boost_suggerito_label"] = _boost.get("label")
    except Exception:
        pass  # il routing non deve mai bloccare la chat


async def _required_fields_hint(collected: dict) -> str:
    """Istruzione per il prompt: i campi OBBLIGATORI del boost già instradato
    (`boost_suggerito`), così il bot li raccoglie PRIMA di dichiararsi pronto invece di
    emettere un summary su input parziali → 8e Gate 0 → vicolo cieco. Degrada a '' se il
    boost non è ancora noto o il form 8e non è raggiungibile (la chat non si rompe mai)."""
    boost = collected.get("boost_suggerito")
    if not boost:
        return ""
    try:
        form = await engine.get_form(boost)
    except Exception:
        return ""
    # consulenza ricca = il bot ha già prodotto diagnosi/analisi → la consulenza è la fonte
    # del report, NON si chiedono i campi di analisi del template (bug routing 18 lug).
    _ed = collected.get("extractedData") or {}
    consulenza_ricca = bool(collected.get("diagnosi")) or len(str(_ed.get("notes") or "")) > 40 or (
        bool(str(_ed.get("objective") or "").strip()) and bool(str(_ed.get("scope") or "").strip()))
    # DIAGNOSI IN CORSO (review HR): finché la diagnosi non è solida, NON spingere i campi-form
    # del boost (es. ControlBoost → costi/personale) — è ciò che faceva chiedere "il dettaglio
    # dei costi salariali" mentre il caso era organizzativo. Durante la diagnosi si discriminano
    # le ipotesi, non si compila un form. I campi restano gestiti dal pre-flight alla generazione.
    _diag = collected.get("diagnosi") or {}
    _conf = str(_diag.get("confidenza") or "").lower()
    _fase = str(_diag.get("fase") or "").lower()
    # I campi-form tecnici del boost si spingono SOLO quando la diagnosi è SOLIDA (i dati
    # tecnici vengono TARDI: prima si capisce problema e persona). Finché non è solida —
    # inclusi i PRIMI turni, quando ancora non c'è un blocco diagnosi — si sopprime. Prima
    # il gate aveva un buco al turno 1 (diagnosi vuota → non sopprimeva → checklist tecnica).
    still_diagnosing = not (_conf == "alta" or _fase in ("piano", "pronto"))
    return readiness.required_fields_hint(
        form.get("campi") or [], boost_label=collected.get("boost_suggerito_label"),
        consulenza_ricca=consulenza_ricca or still_diagnosing)


@router.post("/message")
@limiter.limit("30/minute")
async def post_message(
    request: Request,
    body: MessageBody,
    background: BackgroundTasks,
    user: Optional[AuthUser] = Depends(optional_user),
):
    session = sessions.get_session(body.sessionId)
    if not session:
        raise HTTPException(status_code=404, detail="session not found")
    _check_ownership(session, user)

    new_msgs = _new_user_messages(body)
    if not new_msgs:
        raise HTTPException(status_code=400, detail="empty message")

    # Override service_id if provided this turn.
    collected = dict(session.get("collected_data") or {})
    incoming_service = normalize_service_id(body.serviceId)
    if incoming_service:
        collected["service_id"] = incoming_service

    merged_messages = sessions.append_messages(session, new_msgs)

    # Auto-fetch any URLs the user just pasted
    last_user_text = new_msgs[-1]["content"] if new_msgs else ""
    collected = await _auto_fetch_urls(last_user_text, collected)
    # Consenso/HOLD alla generazione (sticky): l'utente comanda.
    _update_report_hold(collected, last_user_text)

    # Persist forced skills (UI may toggle them on/off) into collected_data.
    if body.forcedSkills is not None:
        forced = [s for s in (body.forcedSkills or []) if isinstance(s, str) and s.strip()]
        collected["forced_skills"] = forced

    session_for_prompt = {**session, "collected_data": collected, "messages": merged_messages,
                          "_profilo": profile_lib.load(session.get("user_id"))}
    skills = resolve_skills_for_session(session_for_prompt)
    # Merge user-forced skills on top (deduped, order-preserving).
    forced_skills: list[str] = list(collected.get("forced_skills") or [])
    if forced_skills:
        seen = set(skills)
        for fs in forced_skills:
            if fs and fs not in seen:
                skills.append(fs)
                seen.add(fs)
    req_hint = await _required_fields_hint(collected)
    # System prompt in BLOCCHI: il bundle skill viaggia in un blocco proprio marcato per la
    # cache (letture a 0,1×), tutto ciò che cambia ogni turno resta nel blocco volatile —
    # appenderlo al blocco cacheato ne cambierebbe i byte e azzererebbe gli hit.
    system_prompt = build_system_blocks(skills, session_for_prompt, required_fields_hint=req_hint)
    if web_search.enabled():
        system_prompt = append_system_text(system_prompt, web_search.SYSTEM_HINT)
    # GROUNDING FORZATO (filosofia: la risposta si costruisce dalla CONOSCENZA, non dalla
    # memoria del modello): fatto specifico, conformità, provider nominato o richiesta
    # esplicita → il server recupera la fonte PRIMA del turno e la inietta (il contesto
    # recente qualifica il tema, es. provider in audit GDPR). best-effort in thread.
    _recent_ctx = " ".join(str(m.get("content") or "") for m in merged_messages[-8:]
                           if isinstance(m, dict) and m.get("role") == "user")[-1500:]
    _gb = await asyncio.to_thread(fact_grounding.ground_block, last_user_text, _recent_ctx)
    if _gb:
        system_prompt = append_system_text(system_prompt, _gb)
    history = build_history(merged_messages, MAX_HISTORY_MESSAGES, MAX_MESSAGE_CHARS,
                           HISTORY_CHAR_BUDGET)

    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not configured")
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    try:
        # web_search abilitato: il modello cerca DAVVERO quando l'utente lo chiede, invece
        # di promettere una ricerca che non fa. L'helper gestisce pause_turn + fallback.
        result = web_search.create_with_web_search(
            client,
            model=ANTHROPIC_MODEL,
            # max_tokens generoso: serve per i report finali. 1200 era ok per
            # chat brevi ma segava i report a metà. Alzato a 16000 per lasciare
            # spazio ai modelli reasoning (es. gpt-oss locale) che spendono token
            # nel thinking prima della risposta.
            max_tokens=16000,
            system=system_prompt,
            messages=history,
            timeout=120.0,
        )
    except anthropic.APITimeoutError:
        log.exception("Anthropic API timeout")
        raise HTTPException(status_code=504, detail="K-BOT è temporaneamente lento, riprova tra qualche secondo.")
    except anthropic.APIError:
        log.exception("Anthropic API error")
        raise HTTPException(status_code=502, detail="Errore upstream temporaneo. Riprova.")

    raw_text = "".join(
        block.text for block in result.content if getattr(block, "type", "") == "text"
    )
    # Finalize CONDIVISA (stessa catena del path streaming): forced-summary + quality gate.
    raw_text = _postprocess_turn(client, system_prompt, history, merged_messages, raw_text, collected)
    usage = getattr(result, "usage", None)
    # Persist: STESSA funzione del path streaming. Prima era duplicata qui in linea, ed è
    # esattamente il tipo di divergenza che questo file documenta a ogni commento («il
    # fallback readiness esisteva solo sullo streaming»): ora memoria di conversazione,
    # tocco su `updated_at` e sintesi progressiva girano per costruzione su entrambi i path.
    user_visible, summary, updated = _persist_assistant_turn(
        session, body.sessionId, merged_messages, collected, raw_text, skills
    )
    _user_turns = sum(1 for m in merged_messages if isinstance(m, dict) and m.get("role") == "user")
    track_server(
        distinct_id=body.sessionId,
        event="message_processed",
        properties={
            "role": "assistant",
            "tokens_in": getattr(usage, "input_tokens", None) if usage else None,
            "tokens_out": getattr(usage, "output_tokens", None) if usage else None,
            "cache_read": getattr(usage, "cache_read_input_tokens", None) if usage else None,
            "cache_write": getattr(usage, "cache_creation_input_tokens", None) if usage else None,
            "model": ANTHROPIC_MODEL,
            # telemetria qualità chat: quanti turni serve l'intake, quando esce il summary,
            # se il bot mantiene lo stato diagnostico — per vedere i trend senza stress test.
            # cache_read/cache_write: se cache_read resta a 0 turno dopo turno, il prefisso
            # stabile non sta facendo hit (qualcosa lo precede e cambia).
            "user_turns": _user_turns,
            "summary_emitted": bool(summary),
            "diagnosi_tracked": bool(signals.DIAGNOSI_RE.search(raw_text)),
            "history_msgs": len(history),
            "history_chars": sum(len(m.get("content") or "") for m in history),
        },
    )
    # Sintesi progressiva DOPO la risposta: non entra nella latenza del turno visibile.
    background.add_task(conversation_memory.refresh_if_stale,
                        client, ANTHROPIC_MODEL, body.sessionId, len(history))

    return {
        "message": user_visible,
        "summary": summary,
        "nextAction": "show_summary" if summary else "continue",
        "session": sessions.public_session(updated),
    }


# ---------------------------------------------------------------------------
# Streaming variant (Server-Sent Events).
# ---------------------------------------------------------------------------


async def _prepare_turn(body: MessageBody, user: Optional[AuthUser]):
    """Shared setup: load session, append user msg, fetch URLs, build prompt."""
    session = sessions.get_session(body.sessionId)
    if not session:
        raise HTTPException(status_code=404, detail="session not found")
    _check_ownership(session, user)

    new_msgs = _new_user_messages(body)
    if not new_msgs:
        raise HTTPException(status_code=400, detail="empty message")

    collected = dict(session.get("collected_data") or {})
    incoming_service = normalize_service_id(body.serviceId)
    if incoming_service:
        collected["service_id"] = incoming_service

    merged_messages = sessions.append_messages(session, new_msgs)
    last_user_text = new_msgs[-1]["content"] if new_msgs else ""
    collected = await _auto_fetch_urls(last_user_text, collected)
    # Consenso/HOLD alla generazione (sticky): l'utente comanda.
    _update_report_hold(collected, last_user_text)

    session_for_prompt = {**session, "collected_data": collected, "messages": merged_messages,
                          "_profilo": profile_lib.load(session.get("user_id"))}
    skills = resolve_skills_for_session(session_for_prompt)
    req_hint = await _required_fields_hint(collected)
    system_prompt = build_system_blocks(skills, session_for_prompt, required_fields_hint=req_hint)
    if web_search.enabled():
        system_prompt = append_system_text(system_prompt, web_search.SYSTEM_HINT)
    # NB: il GROUNDING FORZATO (ricerca web proattiva) NON avviene qui: nello stream gira
    # DOPO l'heartbeat (event_gen), così una ricerca lenta non tiene fermo il primo byte
    # (rischio 524 all'edge). Vedi post_message_stream.
    history = build_history(merged_messages, MAX_HISTORY_MESSAGES, MAX_MESSAGE_CHARS,
                           HISTORY_CHAR_BUDGET)

    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not configured")

    return session, merged_messages, collected, system_prompt, history, skills


def _persist_assistant_turn(
    session: dict,
    body_session_id: str,
    merged_messages: list,
    collected: dict,
    raw_text: str,
    skills: Optional[List[str]] = None,
) -> tuple[str, Optional[dict], dict]:
    """Apply summary extraction + persist assistant message. Returns (user_visible, summary, updated_session)."""
    user_visible, summary, diagnosi = _extract_gated_summary(raw_text, merged_messages, collected)
    _persist_diagnosi(collected, diagnosi)

    updated_messages = sessions.append_messages(
        {**session, "messages": merged_messages},
        [{"role": "assistant", "content": user_visible}],
    )
    if summary:
        collected.update(
            {k: v for k, v in summary.items() if v is not None and v != ""}
        )
        collected["extractedData"] = {**(collected.get("extractedData") or {}), **summary}
        collected["analysis_ready"] = True
        _apply_summary_contract(collected, summary)
    # Boost ricalcolato FUORI da `if summary:`, a OGNI turno, sull'intento corrente
    # (come le skill): chiude l'asimmetria che lasciava un boost stantio sul bottone.
    _recompute_boost(collected, merged_messages, summary)

    # Always expose skills used in this turn so the UI panel can render them
    # (mirror of the non-streaming branch — era assente nello stream).
    if skills is not None:
        existing_extracted = dict(collected.get("extractedData") or {})
        existing_extracted["used_skills"] = list(skills)
        collected["extractedData"] = existing_extracted

    new_step = int(session.get("step") or 1) + 1
    updated = sessions.update_session(
        body_session_id,
        {
            "messages": updated_messages,
            "collected_data": collected,
            "step": new_step,
        },
    )
    profile_lib.update_after_turn(updated)  # memoria cross-sessione (fail-open)
    # La riga in sidebar deve risalire quando la chat viene usata: `kbot_conversations.
    # updated_at` era toccato solo da un PATCH del frontend (rinomina/bind), quindi la
    # cronologia restava ordinata per data di CREAZIONE e una chat vecchia ripresa oggi
    # rimaneva in fondo. Best-effort, non blocca il turno.
    conversations_index.touch_by_session(body_session_id)
    return user_visible, summary, updated


def _sse(event_data: dict) -> str:
    return f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"


@router.post("/message/stream")
@limiter.limit("30/minute")
async def post_message_stream(
    request: Request,
    body: MessageBody,
    user: Optional[AuthUser] = Depends(optional_user),
):
    session, merged_messages, collected, system_prompt, history, skills = await _prepare_turn(body, user)
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    # Testi per il grounding proattivo (calcolati qui, eseguito DOPO l'heartbeat).
    _users_for_ground = [str(m.get("content") or "") for m in merged_messages
                         if isinstance(m, dict) and m.get("role") == "user"]
    _last_user_text = _users_for_ground[-1] if _users_for_ground else ""
    _recent_user_text = " ".join(_users_for_ground[-6:])[-1500:]

    async def event_gen():
        # HEARTBEAT immediato: flush del primo byte PRIMA della chiamata LLM (che può tardare
        # per i retry Anthropic). L'edge (Cloudflare) vede lo stream partito e risponde 200
        # con body vivo, invece di un 524/timeout su time-to-first-byte che il frontend
        # mostra come "errore invio messaggio". È un COMMENTO SSE (riga ':'): il client lo
        # ignora (nessuna riga 'data:'), zero impatto sul parsing.
        yield ": ok\n\n"
        # GROUNDING FORZATO ("webresearch effettivo"): sul modello locale il tool-use
        # discrezionale non parte quasi mai → quando l'ultimo messaggio richiede fatti/
        # norme/documentazione (fatto specifico, conformità, provider nominato, richiesta
        # esplicita), il SERVER cerca ORA (OpenAI) e inietta i risultati nel prompt.
        # Best-effort in thread, fail-open; gira dopo l'heartbeat → niente 524.
        sys_prompt = system_prompt
        try:
            _gb = await asyncio.to_thread(
                fact_grounding.ground_block, _last_user_text, _recent_user_text)
            if _gb:
                sys_prompt = append_system_text(sys_prompt, _gb)
                yield ": search-done\n\n"   # commento SSE: tiene vivo lo stream, il client lo ignora
        except Exception:
            log.warning("grounding proattivo fallito (fail-open)", exc_info=True)
        raw_buffer: list[str] = []
        usage = None
        # Scrubber dello stream (bug UX "continua a ragionare e poi cambia messaggio"):
        # i blocchi-macchina in coda (DIAGNOSI_STATO/CONSULENZA_SUMMARY) NON si streammano
        # in diretta — raw_buffer resta completo per il post-processing.
        scrub = signals.StreamScrubber()
        # web_search è un CLIENT-tool agganciato a OpenAI (il path streaming è quello LIVE
        # della chat usato dal frontend). Loop: stream Claude → se chiama web_search,
        # eseguiamo la ricerca via OpenAI e proseguiamo lo stream coi risultati.
        use_search = web_search.enabled()
        tools = [web_search.web_search_tool()] if use_search else None
        messages = list(history)
        rounds, max_rounds = 0, 4
        try:
            while True:
                stream_kwargs: dict = dict(
                    model=ANTHROPIC_MODEL,
                    max_tokens=16000,
                    system=sys_prompt,
                    messages=messages,
                    timeout=120.0,
                )
                if tools:
                    stream_kwargs["tools"] = tools
                # Anthropic SDK sync streaming context manager — iterate token deltas.
                with client.messages.stream(**stream_kwargs) as stream:
                    for text_chunk in stream.text_stream:
                        if await request.is_disconnected():
                            log.info("kbot stream: client disconnected mid-response")
                            return
                        if not text_chunk:
                            continue
                        raw_buffer.append(text_chunk)
                        visible_chunk = scrub.feed(text_chunk)
                        if visible_chunk:
                            yield _sse({"delta": visible_chunk})
                    final = stream.get_final_message()
                usage = getattr(final, "usage", None)
                # Claude ha chiamato web_search? esegui la ricerca OpenAI e continua.
                if not tools or getattr(final, "stop_reason", None) != "tool_use" or rounds >= max_rounds:
                    break
                tool_results = web_search.execute_tool_uses(final.content)
                if not tool_results:
                    break
                messages = [
                    *messages,
                    {"role": "assistant", "content": final.content},
                    {"role": "user", "content": tool_results},
                ]
                rounds += 1
        except anthropic.APITimeoutError:
            log.exception("Anthropic stream timeout")
            yield _sse({"error": "K-BOT è temporaneamente lento, riprova tra qualche secondo."})
            return
        except anthropic.APIError:
            log.exception("Anthropic stream error")
            yield _sse({"error": "Errore upstream temporaneo. Riprova."})
            return
        except Exception:
            log.exception("Unexpected stream error")
            yield _sse({"error": "Errore imprevisto durante lo stream."})
            return

        # coda residua dello scrubber (prosa trattenuta dall'holdback, mai marker)
        _tail = scrub.flush()
        if _tail:
            yield _sse({"delta": _tail})

        raw_text = "".join(raw_buffer)
        # Finalize CONDIVISA coi due path: forced-summary + quality gate (vedi _postprocess_turn).
        raw_text = _postprocess_turn(client, system_prompt, messages, merged_messages, raw_text, collected)
        _user_turns = sum(1 for m in merged_messages if isinstance(m, dict) and m.get("role") == "user")
        track_server(
            distinct_id=body.sessionId,
            event="message_processed",
            properties={
                "role": "assistant",
                "tokens_in": getattr(usage, "input_tokens", None) if usage else None,
                "tokens_out": getattr(usage, "output_tokens", None) if usage else None,
                "cache_read": getattr(usage, "cache_read_input_tokens", None) if usage else None,
                "cache_write": getattr(usage, "cache_creation_input_tokens", None) if usage else None,
                "model": ANTHROPIC_MODEL,
                "stream": True,
                "user_turns": _user_turns,
                "summary_emitted": bool(extract_summary(raw_text)),
                "diagnosi_tracked": bool(signals.DIAGNOSI_RE.search(raw_text)),
                "history_msgs": len(history),
                "history_chars": sum(len(m.get("content") or "") for m in history),
            },
        )
        try:
            user_visible, summary, updated = _persist_assistant_turn(
                session, body.sessionId, merged_messages, collected, raw_text, skills
            )
        except Exception:
            log.exception("Failed to persist streamed assistant turn")
            yield _sse({"error": "Errore salvataggio risposta."})
            return

        yield _sse(
            {
                "done": True,
                "message": user_visible,
                "summary": summary,
                "nextAction": "show_summary" if summary else "continue",
                "session": sessions.public_session(updated),
            }
        )
        # Sintesi progressiva: DOPO l'evento `done`, quindi a risposta già consegnata. Il
        # generatore continua a girare dopo l'ultimo yield: è il posto giusto per il lavoro
        # che non deve pesare sul turno. Best-effort in thread (chiamata Anthropic sync).
        try:
            await asyncio.to_thread(
                conversation_memory.refresh_if_stale,
                client, ANTHROPIC_MODEL, body.sessionId, len(history))
        except Exception:
            log.warning("sintesi conversazione (stream) fallita (fail-open)", exc_info=True)

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
