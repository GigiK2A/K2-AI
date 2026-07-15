"""Endpoint deliverable: il K-BOT instrada all'8e e fa da proxy di stato.

POST /api/kbot/deliverables          → crea un job 8e per il servizio acquistato
GET  /api/kbot/deliverables/{job_id} → stato job (polling lato frontend)
GET  /api/kbot/engine/health         → liveness 8e (debug)

Entitlement (membrana G1): in Phase-1 il token è un placeholder. Quando il binding
billing→entitlement sarà pronto, il token JWT verrà rilasciato al pagamento e
verificato dall'8e. Qui si verifica solo che il servizio sia pagato sulla sessione.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
from typing import Optional

from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field

from .. import settings
from ..lib import engine, sessions, catalog, entitlement, autofill, readiness, research
from ..lib.auth import AuthUser, optional_user, require_user
from ..lib.storage import upload_pdf, upload_bytes, download_bytes
from ..lib.supabase_admin import get_admin_client
from ..settings import STORAGE_REPORTS_BUCKET

router = APIRouter()
log = logging.getLogger(__name__)


_ALIGN_SYSTEM = (
    "Sei l'OUTPUT ALIGNMENT CHECKER di K2-AI. Ricevi gli ultimi messaggi del CLIENTE, il "
    "DOCUMENTO che il sistema sta per generare e il CATALOGO dei documenti disponibili. "
    "PRIMA della generazione verifica:\n"
    "1) Qual è la DECISIONE che il cliente deve prendere?\n"
    "2) Il documento scelto è quello MEGLIO ADATTO **TRA QUELLI IN CATALOGO** a rispondervi?\n"
    "3) Le azioni tipiche di quel documento sarebbero ESEGUIBILI DAL CLIENTE?\n"
    "REGOLE DI BLOCCO (aligned=false SOLO in questi due casi):\n"
    "A) SOGGETTO SBAGLIATO: il cliente sta VALUTANDO un'altra azienda (acquisizione/M&A, "
    "fornitore, partner) e il documento darebbe azioni gestionali per l'azienda ANALIZZATA "
    "(risanare la SUA liquidità, recuperare i SUOI crediti) invece che per il cliente. In tal "
    "caso indica in servizio_suggerito il documento giusto dal catalogo (es. la due diligence).\n"
    "B) IN CATALOGO ESISTE un documento CHIARAMENTE più adatto di quello scelto: indicane "
    "l'id ESATTO in servizio_suggerito.\n"
    "SE NESSUN documento in catalogo copre meglio il caso: aligned=true ANCHE se quello scelto "
    "è solo parzialmente adatto — un report utile che copre il caso (anche multidominio, al suo "
    "interno) è MEGLIO di nessun report. Non bloccare mai senza un'alternativa reale.\n"
    "Rispondi SOLO con l'oggetto JSON: {\"aligned\":bool,\"decisione\":\"…\","
    "\"servizio_suggerito\":\"<id dal catalogo>\"|null,\"motivo\":\"…\"}. "
    "Nel dubbio: aligned=true."
)


def _alignment_check(session: dict, servizio: dict) -> Optional[dict]:
    """OUTPUT ALIGNMENT CHECKER (eval M&A 15 lug): mai generare un documento del dominio
    sbagliato. Il caso che l'ha reso necessario: conversazione "acquistare un concorrente"
    instradata su FinanceBoost → piano di risanamento del TARGET, azioni rivolte al
    soggetto sbagliato, zero risposte a «lo compro? il prezzo è giusto?». Un report
    sbagliato ma credibile è PEGGIO di nessun report.

    CATALOG-AWARE (fix vicolo cieco 15 lug): il primo checker bloccava StrategyBoost su
    un caso HR/organizzativo… ma il catalogo NON HA un boost HR → 409 ripetuti e nessun
    deliverable per l'utente. Ora il checker vede il catalogo reale e blocca SOLO se
    esiste un'alternativa concreta (che ritorna in servizio_suggerito, così il frontend
    rigenera da solo con quella) o se il soggetto è sbagliato (M&A). Senza alternativa
    reale → passa: un report parzialmente adatto che copre il caso è meglio di niente.

    Ritorna il dict SOLO su aligned=false con servizio_suggerito VALIDO e diverso;
    None in ogni altro caso (fail-open). KBOT_ALIGNMENT_CHECK=0 per disattivare."""
    if (os.environ.get("KBOT_ALIGNMENT_CHECK", "1") or "1").lower() not in ("1", "true", "yes"):
        return None
    try:
        import anthropic
        msgs = [str(m.get("content") or "")[:400] for m in (session.get("messages") or [])
                if isinstance(m, dict) and m.get("role") == "user"][-6:]
        if not msgs:
            return None
        label = servizio.get("label") or servizio.get("nome") or servizio.get("id") or ""
        desc = str(servizio.get("descrizione") or servizio.get("description") or "")[:300]
        # catalogo reale: solo documenti davvero generabili e vendibili
        _cat = [s for s in catalog.lista_servizi()
                if catalog.is_8e_generabile(s.get("id", "")) and catalog.is_vendibile(s.get("id", ""))]
        cat_txt = "\n".join(f"- {s['id']}: {s.get('label') or s.get('nome') or s['id']}" for s in _cat)
        user = ("MESSAGGI DEL CLIENTE (ultimi turni):\n- " + "\n- ".join(msgs) +
                f"\n\nDOCUMENTO CHE STA PER ESSERE GENERATO: {servizio.get('id')} — {label}" +
                (f" ({desc})" if desc else "") +
                f"\n\nCATALOGO DEI DOCUMENTI DISPONIBILI:\n{cat_txt}" +
                "\n\nVerifica l'allineamento e rispondi SOLO col JSON.")
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        resp = client.messages.create(
            model=settings.ANTHROPIC_MODEL, max_tokens=400,
            system=_ALIGN_SYSTEM,
            messages=[{"role": "user", "content": user}], timeout=60.0,
        )
        out = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
        s, e = out.find("{"), out.rfind("}")
        v = json.loads(out[s:e + 1]) if 0 <= s < e else None
        if not (isinstance(v, dict) and v.get("aligned") is False):
            return None
        sug = str(v.get("servizio_suggerito") or "").strip()
        # ANTI-VICOLO-CIECO deterministico: senza un'alternativa REALE (id valido,
        # generabile, vendibile, diverso da quello scelto) NON si blocca mai.
        if (not sug or sug == servizio.get("id")
                or not catalog.is_8e_generabile(sug) or not catalog.is_vendibile(sug)):
            log.info("alignment: dubbio senza alternativa reale (sugg=%r) → passa", sug or None)
            return None
        v["servizio_suggerito"] = sug
        log.warning("alignment: DISALLINEATO — %s → suggerito %s (decisione=%r)",
                    servizio.get("id"), sug, v.get("decisione"))
        return v
    except Exception:
        log.warning("alignment check fallito (fail-open)", exc_info=True)
    return None


def _conversation_fp(session: dict, servizio_id: str) -> str:
    """Fingerprint della conversazione per il riuso degli input auto-compilati.

    L'autofill è una chiamata LLM: a ogni /auto riformula gli input in modo
    leggermente diverso → i prompt delle sezioni 8e cambiano → la cache
    per-sezione ("spezzetta e riunisci") non fa mai hit e un retry dopo timeout
    riparte da zero. Con conversazione INVARIATA riusiamo gli input persistiti:
    prompt identici → sezioni riusate → il retry COMPLETA il report."""
    coll = session.get("collected_data") or {}
    basis = [
        servizio_id,
        [str(m.get("content") or "") for m in (session.get("messages") or []) if isinstance(m, dict)],
        sorted(str(f.get("name") or "") for f in (coll.get("uploaded_files") or [])),
        sorted(str(u.get("url") or "") for u in (coll.get("analyzed_urls") or [])),
    ]
    return hashlib.sha256(json.dumps(basis, ensure_ascii=False).encode("utf-8")).hexdigest()

PREVIEW_LIMIT_MESE = 2  # gate W8, A/B 2 vs 3 post-live


def _session_company(session: dict) -> Optional[str]:
    """Denominazione nota dalla sessione: il motore 8e la richiede per identificare e
    personalizzare il report (gate identità di quality.py). Fallback se l'autofill non
    l'ha estratta dal bilancio."""
    collected = session.get("collected_data") or session.get("collected") or {}
    extracted = collected.get("extractedData") or {}
    for src in (collected, extracted):
        for k in ("ragione_sociale", "companyName", "businessName", "clientName", "azienda"):
            v = src.get(k)
            if isinstance(v, str) and v.strip():
                return v.strip()
    return None


class DeliverableBody(BaseModel):
    sessionId: str = Field(..., alias="session_id")
    servizioId: str = Field(..., alias="servizio_id")
    inputs: dict = Field(default_factory=dict)

    class Config:
        populate_by_name = True


def _check_ownership(session: dict, user: Optional[AuthUser]) -> None:
    owner = session.get("user_id")
    if owner and (not user or user.id != owner):
        raise HTTPException(status_code=403, detail="not your session")


def _session_for_job(job_id: str) -> Optional[dict]:
    """Reverse-lookup: la sessione che possiede questo job_id 8e/agente.

    Il job viene persistito su `collected_data.deliverable_job_id` da create/auto
    (stesso file). Interroghiamo `kbot_sessions` filtrando sul campo JSONB. Ritorna
    la riga sessione oppure None se nessuna sessione rivendica il job.
    """
    try:
        client = get_admin_client()
        res = (
            client.table("kbot_sessions")
            .select("*")
            .eq("collected_data->>deliverable_job_id", job_id)
            .limit(1)
            .execute()
        )
        rows = res.data or []
        return rows[0] if rows else None
    except Exception:
        # Errore di lookup → trattiamo come "non verificabile" a valle (fail-closed).
        log.warning("lookup sessione per job %s fallito", job_id, exc_info=True)
        return None


def _authorize_job_download(job_id: str, user: Optional[AuthUser]) -> dict:
    """Gate C1 per i download di deliverable (pdf/xlsx/stato): lega il job alla
    sessione proprietaria e ne verifica pagamento + (quando possibile) ownership.

    Il `job_id` da solo NON è più autorizzazione sufficiente (era IDOR + bypass
    paywall): chi lo indovinasse/intercettasse poteva scaricare il documento di un
    altro cliente SENZA aver pagato. Ora:
      1. risolviamo la sessione che possiede il job (persistita a generazione);
      2. **paywall** — la sessione DEVE essere pagata (402), salvo KBOT_FREE_MODE.
         Questo chiude il bypass del paywall a prescindere dall'autenticazione;
      3. **ownership** — se il chiamante presenta un JWT valido, DEVE essere il
         proprietario della sessione (403).

    VINCOLO ARCHITETTURALE (perché non si impone SEMPRE il JWT): PDF ed Excel
    vengono scaricati via NAVIGAZIONE del browser (`<a href>` / apertura tab) e il
    polling di stato via `fetch` senza header — nessuno dei due può allegare un
    `Authorization: Bearer`. Imporre il JWT qui romperebbe tutti i download legittimi.
    Quindi: paywall SEMPRE (fail-closed) + ownership imposta solo quando un token è
    presente. Il `job_id` resta la capability opaca per la navigazione anonima, ma
    non basta più a superare il paywall né a leggere una sessione altrui se ti
    autentichi come un altro utente. Irrobustimento futuro (signed URL / token
    per-job) è un follow-up infra.

    FAIL-CLOSED: se nessuna sessione rivendica il job (job orfano/legacy generato
    prima di questo binding, o lookup fallito) NON serviamo il file → 403. Meglio
    negare un raro download legacy che lasciare aperto un accesso non pagato.
    """
    session = _session_for_job(job_id)
    if not session:
        raise HTTPException(status_code=403, detail="download non autorizzato per questo job")
    # Ownership: imposta SOLO se il chiamante è autenticato (JWT presente e valido).
    # Con user=None (navigazione browser) non possiamo distinguere → resta il paywall.
    if user is not None and session.get("user_id") and session["user_id"] != user.id:
        raise HTTPException(status_code=403, detail="not your session")
    # Paywall: SEMPRE, anche senza autenticazione. Chiude il bypass IDOR-paywall.
    if session.get("status") != "paid" and not settings.KBOT_FREE_MODE:
        raise HTTPException(status_code=402, detail="documento non pagato")
    return session


def _mint_entitlement(session: dict, servizio_id: str, tier: Optional[str] = None) -> Optional[str]:
    """Entitlement JWT (G1) se il servizio risulta pagato. Firmato HS256, verificato
    stateless dall'8e. Fallback al placeholder solo se il segreto non è configurato
    (dev senza K2A_ENTITLEMENT_SECRET)."""
    # FREE MODE (K-BOT ufficiale senza paywall): genera anche senza pagamento
    # (token comunque mintato; l'8e con K2A_8E_ENTITLEMENT_DEV=true lo accetta).
    # Con KBOT_FREE_MODE=0 il gate "servizio non pagato" torna attivo.
    if session.get("status") != "paid" and not settings.KBOT_FREE_MODE:
        return None
    token = entitlement.mint(
        user_id=session.get("user_id"),
        service_id=servizio_id,
        tier=tier,
        session_id=str(session.get("id")),
    )
    return token or f"dev-unsigned-{session.get('id')}-{servizio_id}"


async def _get_job(job_id: str) -> dict:
    """Stato job da QUALSIASI sorgente: store locale dell'agente A2 o motore 8e. Così
    poll/pdf/xlsx/json/save passano dagli stessi endpoint per entrambi i tipi di job."""
    from ..lib import agent_jobs
    if agent_jobs.is_agent_job(job_id):
        j = agent_jobs.get(job_id)
        if not j:
            raise HTTPException(status_code=404, detail="job non trovato")
        return j
    return await engine.get_deliverable(job_id)


def _durable_pdf_path(session_id: str, job_id: str) -> str:
    return f"deliverables/{session_id}/{job_id}.pdf"


def _durable_json_path(session_id: str, job_id: str) -> str:
    return f"deliverables/{session_id}/{job_id}.json"


async def _persist_durable(session: dict, job_id: str, job: dict) -> None:
    """C4 — appena l'8e riporta il job 'rendered', persiste PDF+JSON su Supabase
    Storage così il deliverable PAGATO sopravvive a un restart dell'8e (il job store
    dell'8e è in-memory: al redeploy Railway il job sparisce e il polling andrebbe in
    404 → vicolo cieco su un documento già pagato). Idempotente (salta se già salvato
    per questo job) e best-effort assoluto: non deve MAI rompere il polling di stato.
    """
    sid = str(session.get("id") or session.get("session_id") or "")
    if not sid or not job_id:
        return
    if (job or {}).get("status") != "rendered":
        return
    collected = dict(session.get("collected_data") or {})
    if collected.get("deliverable_saved_job") == job_id and collected.get("deliverable_pdf_url"):
        return  # già durevole per questo job
    try:
        content, _ = await engine.fetch_output(job_id, "pdf")
        pdf_url = upload_bytes(bucket=STORAGE_REPORTS_BUCKET,
                               path=_durable_pdf_path(sid, job_id), content=content,
                               content_type="application/pdf")
        collected["deliverable_pdf_url"] = pdf_url
    except Exception:
        log.warning("C4 auto-save PDF fallita per job %s (best-effort)", job_id, exc_info=True)
        return  # senza PDF durevole non marchiamo saved: si riproverà al prossimo poll
    # JSON (per il modello Excel on-demand): best-effort separato, non blocca il PDF.
    try:
        raw, _ = await engine.fetch_output(job_id, "json")
        upload_bytes(bucket=STORAGE_REPORTS_BUCKET,
                     path=_durable_json_path(sid, job_id), content=raw,
                     content_type="application/json")
        collected["deliverable_json_saved"] = True
    except Exception:
        log.warning("C4 auto-save JSON fallita per job %s (best-effort)", job_id, exc_info=True)
    collected["deliverable_saved_job"] = job_id
    try:
        sessions.update_session(sid, {"pdf_url": collected.get("deliverable_pdf_url"),
                                      "collected_data": collected})
    except Exception:
        log.warning("C4 persist URL durevoli fallita per job %s", job_id, exc_info=True)


async def _maybe_route_agent(session: dict, servizio_id: str, servizio: dict,
                             bg: BackgroundTasks) -> Optional[dict]:
    """Se l'agente A2 è attivo per il servizio e il quant è disponibile, instrada al job
    ASINCRONO dell'agente (boost_agent → render 8e). Ritorna {job_id, status} o None →
    fallback alla pipeline 8e (degrado safe: quant giù / skill assente non rompe nulla)."""
    from ..lib import boost_agent, agent_jobs
    if not settings.K2A_BOOST_AGENT or servizio_id not in settings.K2A_BOOST_AGENT_SERVIZI:
        return None
    if not boost_agent.mcp_quant.available():
        log.warning("agent A2 on ma quant non disponibile → fallback pipeline per %s", servizio_id)
        return None
    blueprint = str(servizio.get("blueprint_id") or "").replace(".boost", "")
    skill_path = settings.SKILLS_DIR / blueprint / "SKILL.md"
    if not blueprint or not skill_path.exists():
        log.warning("agent A2: skill mancante (%s) → fallback pipeline", blueprint)
        return None
    skill_text = skill_path.read_text(encoding="utf-8")
    sezioni = _AGENT_SEZIONI.get(servizio_id, _AGENT_SEZIONI_DEFAULT)
    try:
        form = await engine.get_form(servizio_id)
        campi = form.get("campi") or []
    except engine.EngineError:
        campi = []
    job_id = agent_jobs.create(servizio_id)
    bg.add_task(agent_jobs.run, job_id, session, servizio_id, skill_text, sezioni, campi)
    return {"job_id": job_id, "status": "routed", "auth_level": "FULL",
            "routed_blueprint": blueprint, "source": "agent_a2"}


@router.post("/deliverables")
async def create(body: DeliverableBody, bg: BackgroundTasks,
                 user: Optional[AuthUser] = Depends(optional_user)):
    session = sessions.get_session(body.sessionId)
    if not session:
        raise HTTPException(status_code=404, detail="session not found")
    _check_ownership(session, user)

    servizio = catalog.get_servizio(body.servizioId)
    if not servizio:
        raise HTTPException(status_code=404, detail="servizio non a catalogo")

    # Solo i servizi generabili via 8e passano di qui; gli high-touch no.
    if not catalog.is_8e_generabile(body.servizioId):
        raise HTTPException(status_code=409,
                            detail="servizio non generabile via 8e (high-touch)")

    entitlement_token = _mint_entitlement(session, body.servizioId, tier=servizio.get("tipo"))
    if not entitlement_token:
        raise HTTPException(status_code=402, detail="servizio non pagato")

    # A2 — se il servizio è instradato all'agente (flag + quant), job async dell'agente.
    agent_res = await _maybe_route_agent(session, body.servizioId, servizio, bg)
    if agent_res is not None:
        try:
            collected = dict(session.get("collected_data") or {})
            collected["deliverable_job_id"] = agent_res.get("job_id")
            collected["deliverable_service"] = body.servizioId
            sessions.update_session(body.sessionId, {"collected_data": collected})
        except Exception:
            log.warning("persist agent job fallita (non bloccante)", exc_info=True)
        return agent_res

    # L'8e instrada per service_id (chiave manifest = id catalog, stessa fonte
    # k2a-catalogo); è l'8e a risolvere service_id→blueprint internamente.
    try:
        res = await engine.create_deliverable(
            service_id=body.servizioId,
            inputs=body.inputs,
            entitlement_token=entitlement_token,
            tier=servizio.get("tipo"),
            auth_level="FULL",
        )
    except engine.EnginePaymentRequired:
        raise HTTPException(status_code=402, detail="entitlement rifiutato dall'8e")
    except engine.EngineRefused as r:
        raise HTTPException(status_code=422, detail={"reason": r.reason, "message": r.message})
    except engine.EngineError as e:
        # M1 — non esporre il dettaglio grezzo dell'errore 8e al client (può contenere
        # URL/host interni). Loggato sopra con contesto; al client messaggio generico.
        log.warning("8e error: %s", e, exc_info=True)
        raise HTTPException(status_code=502, detail="motore non disponibile, riprova tra poco")

    # Persisti il job dentro collected_data (JSONB esistente), NON come colonne
    # top-level: deliverable_job_id/deliverable_service NON esistono come colonne
    # di kbot_sessions → un update con quei nomi darebbe 500. Il polling usa
    # comunque il job_id dalla response, non dalla sessione. Best-effort: un
    # fallimento di persistenza non deve far fallire la generazione già avviata.
    try:
        collected = dict(session.get("collected_data") or {})
        collected["deliverable_job_id"] = res.get("job_id")
        collected["deliverable_service"] = body.servizioId
        # C4 — persisti input+auth_level: permettono di RIGENERARE gratis (sessione già
        # pagata) se il job va perso a un restart dell'8e, senza rifare l'autofill.
        collected["deliverable_inputs"] = body.inputs
        collected["deliverable_auth_level"] = "FULL"
        collected.pop("deliverable_saved_job", None)  # nuovo job → invalida la copia durevole vecchia
        collected.pop("deliverable_pdf_url", None)
        sessions.update_session(body.sessionId, {"collected_data": collected})
    except Exception:
        log.warning("persist deliverable job fallita (non bloccante)", exc_info=True)
    return res


class AutoBody(BaseModel):
    sessionId: str = Field(..., alias="session_id")
    servizioId: Optional[str] = Field(default=None, alias="servizio_id")

    class Config:
        populate_by_name = True


@router.post("/deliverables/auto")
async def auto_deliverable(body: AutoBody, bg: BackgroundTasks,
                           user: Optional[AuthUser] = Depends(optional_user)):
    """Genera il documento SENZA form: il boost è quello già instradato dalla chat
    (o ridedotto dal caso), e gli input 8e sono AUTO-COMPILATI dalla conversazione
    e dai file/bilanci caricati. È il flusso 'chiedi → raccogli → genera. Punto.'."""
    session = sessions.get_session(body.sessionId)
    if not session:
        raise HTTPException(status_code=404, detail="session not found")
    _check_ownership(session, user)

    collected = dict(session.get("collected_data") or {})
    servizio_id = body.servizioId or collected.get("boost_suggerito")
    if not servizio_id:
        # ridedotto dal riepilogo/estratto + TESTO UTENTE. L'intento esplicito vive nei
        # messaggi: se il summary è sparso (o la chat è < 3 turni, quindi _recompute_boost
        # non ha ancora fissato boost_suggerito), "salute finanziaria" deve comunque
        # instradare a FinanceBoost, non cadere sul default ControlBoost.
        summary = {**(collected.get("extractedData") or {}), **collected}
        _utext = " ".join(
            str(m.get("content") or "") for m in (session.get("messages") or [])
            if isinstance(m, dict) and m.get("role") == "user"
        )[-2000:]
        sug = catalog.suggest_boost(summary, user_text=_utext)
        servizio_id = sug["id"] if sug else None
    if not servizio_id or not catalog.is_8e_generabile(servizio_id):
        raise HTTPException(status_code=409, detail="nessun documento generabile per questa conversazione")
    if not catalog.is_vendibile(servizio_id):
        raise HTTPException(status_code=409, detail={
            "reason": "non_vendibile",
            "servizio_id": servizio_id,
            "message": "Questo documento sarà disponibile col motore di valutazione (in arrivo). "
                       "Per ora posso prepararti un altro report.",
        })
    servizio = catalog.get_servizio(servizio_id)

    # Campi richiesti dal boost → auto-compilazione dai dati della conversazione.
    form_schema = None
    try:
        form = await engine.get_form(servizio_id)
        campi = form.get("campi") or []
        form_schema = form.get("schema")
    except engine.EngineError:
        campi = []
    # INPUT STABILI TRA I TENTATIVI: se la conversazione è invariata dall'ultimo /auto
    # per lo stesso boost, riusa gli input già estratti — (a) salta la chiamata LLM di
    # autofill, (b) prompt 8e identici → i checkpoint per-sezione fanno hit e il retry
    # dopo un timeout COMPLETA il report invece di ripartire da zero.
    _fp = _conversation_fp(session, servizio_id)
    if (collected.get("deliverable_inputs") and collected.get("deliverable_service") == servizio_id
            and collected.get("deliverable_inputs_fp") == _fp):
        inputs = dict(collected["deliverable_inputs"])
        log.info("auto: input riusati (conversazione invariata) → checkpoint 8e riusabili")
    else:
        inputs = autofill.extract_inputs(session, campi)
    if not inputs.get("ragione_sociale"):
        _name = _session_company(session)
        if _name:
            inputs["ragione_sociale"] = _name

    # Ricerca web PRE-GATE: i campi OBBLIGATORI *ricercabili* mancanti (competitor, dati
    # di mercato) li CERCHIAMO DAVVERO sul web invece di rimandarli all'utente — è la
    # differenza tra "l'agente chiede i competitor" e "l'agente va a cercarli". Solo dati
    # pubblici/esterni con provenienza; mai dati privati del cliente. Best-effort: no-op
    # se la web search è spenta o l'API non risponde (flusso invariato → no regressioni).
    pre_missing = readiness.missing_required(campi, inputs)
    if pre_missing:
        try:
            found, fonti = research.research_missing_fields(session, campi, pre_missing, inputs)
        except Exception:  # difesa: la ricerca non deve MAI bloccare la generazione
            found, fonti = {}, []
            log.warning("research pre-gate fallita (non bloccante)", exc_info=True)
        if found:
            inputs.update(found)
            collected["web_research"] = {
                **(collected.get("web_research") or {}),
                "servizio_id": servizio_id,
                "fields": list(found.keys()),
                "fonti": fonti,
            }
            try:
                sessions.update_session(body.sessionId, {"collected_data": collected})
            except Exception:
                log.warning("persist web_research fallita (non bloccante)", exc_info=True)

    # Scarta i campi OPZIONALI con valori palesemente invalidi vs schema 8e (es.
    # competitor = NOMI contro un campo che esige URL): un dato opzionale sbagliato non
    # deve far rifiutare la generazione. I required restano gestiti da missing_required.
    inputs, _dropped_opt = readiness.drop_invalid_optional(form_schema, inputs)
    if _dropped_opt:
        log.info("auto: scartati opzionali invalidi %s (servizio %s)", _dropped_opt, servizio_id)

    # Pre-flight required (PRIMA del paywall): i campi OBBLIGATORI del boost devono
    # esserci PRIMA di spendere — e prima di far pagare — una generazione. Se la chat
    # non li ha raccolti, l'autofill li omette (giusto: niente invenzioni) e l'8e li
    # rifiuterebbe come `insufficient_or_inconsistent_input`, mostrando all'utente un
    # vicolo cieco generico. Qui NOMINIAMO cosa manca → il frontend lo rimanda in chat
    # e si rigenera. (Se il form 8e non è raggiungibile, campi=[] → nessun blocco: si
    # lascia decidere all'8e.)
    missing = readiness.missing_required(campi, inputs)
    needs_identity = not readiness.has_identity(inputs)  # il Gate 0 dell'8e esige il nome cliente
    # Dedup (bug UX): se manca l'identità, non elencare ANCHE il campo 'ragione_sociale'
    # del form → prima usciva doppio ("la ragione sociale; Ragione sociale o nome…").
    missing_non_identity = [c for c in missing if c.get("id") != "ragione_sociale"]

    auth_level = "FULL"
    if needs_identity:
        # UNICO blocco vero: senza il nome dell'azienda non possiamo intestare il documento.
        labels = readiness.format_missing_labels(missing_non_identity)
        msg = "la ragione sociale (nome dell'azienda)" + (f"; {labels}" if labels else "")
        miss_ids = ["ragione_sociale"] + [c.get("id") for c in missing_non_identity]
        raise HTTPException(status_code=409, detail={
            "reason": "needs_input",
            "servizio_id": servizio_id,
            "missing": miss_ids,
            "message": (
                f"Per generare «{servizio.get('label') or servizio_id}» mi serve almeno: "
                f"{msg}. Scrivimelo in chat e premi di nuovo Genera."
            ),
        })
    if missing_non_identity:
        # Mancano campi ma NON l'identità → REPORT PRELIMINARE: si genera comunque con i
        # dati disponibili + ipotesi etichettate, invece del vicolo cieco. A pagamento come
        # il completo; l'utente completa i dati e raffina senza ripagare. La ricerca web ha
        # già provato a riempire i campi pubblici (competitor/mercato) qui sopra.
        auth_level = "PARTIAL"
        collected["deliverable_preliminare"] = [c.get("id") for c in missing_non_identity]
        log.info("auto: report PRELIMINARE per %s, campi stimati=%s",
                 servizio_id, [c.get("id") for c in missing_non_identity])

    # OUTPUT ALIGNMENT CHECKER — PRIMA del paywall: mai chiedere un pagamento (né
    # generare) per un documento del dominio sbagliato. Vedi _alignment_check.
    # Salta quando servizio_id è passato ESPLICITAMENTE nel body: è una scelta
    # dell'utente o il retry del frontend sul servizio suggerito → rigiudicarla
    # creerebbe un loop di suggerimenti (flip-flop).
    _mis = None if body.servizioId else _alignment_check(session, servizio)
    if _mis:
        _sug = _mis["servizio_suggerito"]
        _sug_srv = catalog.get_servizio(_sug) or {}
        raise HTTPException(status_code=409, detail={
            "reason": "misaligned_deliverable",
            "servizio_id": servizio_id,
            # il frontend rigenera DA SOLO con il servizio suggerito (niente vicolo cieco)
            "servizio_suggerito": _sug,
            "suggested_label": _sug_srv.get("label") or _sug,
            "message": (
                f"Il documento instradato ({servizio.get('label') or servizio_id}) non risponde alla "
                f"decisione che devi prendere ({str(_mis.get('decisione') or 'la tua richiesta')[:140]}). "
                f"Preparo invece: {_sug_srv.get('label') or _sug}."
            ),
        })

    # Paywall reale (KBOT_FREE_MODE off): se non pagato → 402 con i dati per il
    # checkout del boost (il frontend apre Stripe e al ritorno genera).
    entitlement_token = _mint_entitlement(session, servizio_id, tier=servizio.get("tipo"))
    if not entitlement_token:
        raise HTTPException(status_code=402, detail={
            "reason": "payment_required",
            "servizio_id": servizio_id,
            "label": servizio.get("label"),
            "prezzo_eur": catalog.prezzo_eur(servizio_id),
        })

    # A2 — instrada all'agente async se attivo per il servizio (altrimenti pipeline 8e).
    agent_res = await _maybe_route_agent(session, servizio_id, servizio, bg)
    if agent_res is not None:
        try:
            collected["deliverable_job_id"] = agent_res.get("job_id")
            collected["deliverable_service"] = servizio_id
            collected["deliverable_label"] = servizio.get("label")
            sessions.update_session(body.sessionId, {"collected_data": collected})
        except Exception:
            log.warning("persist agent job (auto) fallita (non bloccante)", exc_info=True)
        return {**agent_res, "servizio_id": servizio_id, "label": servizio.get("label")}

    try:
        res = await engine.create_deliverable(
            service_id=servizio_id, inputs=inputs,
            entitlement_token=entitlement_token, tier=servizio.get("tipo"), auth_level=auth_level,
        )
    except engine.EnginePaymentRequired:
        raise HTTPException(status_code=402, detail="entitlement rifiutato dall'8e")
    except engine.EngineRefused as r:
        raise HTTPException(status_code=422, detail={"reason": r.reason, "message": r.message})
    except engine.EngineError as e:
        # M1 — non esporre il dettaglio grezzo dell'errore 8e al client (può contenere
        # URL/host interni). Loggato sopra con contesto; al client messaggio generico.
        log.warning("8e error: %s", e, exc_info=True)
        raise HTTPException(status_code=502, detail="motore non disponibile, riprova tra poco")

    try:
        collected["deliverable_job_id"] = res.get("job_id")
        collected["deliverable_service"] = servizio_id
        collected["deliverable_label"] = servizio.get("label")
        # C4 — input+auth_level per la rigenerazione gratuita post-restart (vedi /recover).
        collected["deliverable_inputs"] = inputs
        collected["deliverable_inputs_fp"] = _fp  # riuso input su retry (checkpoint 8e)
        collected["deliverable_auth_level"] = auth_level
        collected.pop("deliverable_saved_job", None)  # nuovo job → copia durevole vecchia non valida
        collected.pop("deliverable_pdf_url", None)
        sessions.update_session(body.sessionId, {"collected_data": collected})
    except Exception:
        log.warning("persist deliverable job (auto) fallita (non bloccante)", exc_info=True)

    return {**res, "servizio_id": servizio_id, "label": servizio.get("label")}


_AGENT_SEZIONI = {
    "checkup_advisor": ["executive_summary", "analisi_bilancio", "analisi_settore",
                        "posizionamento_vrio", "opzioni_strategiche", "piano_36_mesi",
                        "enterprise_value", "azioni_prioritarie", "cruscotto_kpi", "disclaimer"],
}
_AGENT_SEZIONI_DEFAULT = ["executive_summary", "analisi", "enterprise_value", "azioni_prioritarie", "disclaimer"]


@router.post("/deliverables/agent")
async def agent_deliverable(body: AutoBody, user: Optional[AuthUser] = Depends(optional_user)):
    """A2 — genera un Boost 'che ragiona' (AdvisorBoost) con l'AGENTE tool-use
    (lib/boost_agent.py) che chiama i MCP di Luca per ogni numero, invece della
    pipeline 8e. Attivo solo con K2A_BOOST_AGENT=1 e servizio in K2A_BOOST_AGENT_SERVIZI.
    Stesso gate dell'auto (ownership + entitlement). CONSUMA CREDITI (loop modello).
    NB: sincrono (prima versione) → in prod va reso job async come il motore 8e."""
    from ..lib import boost_agent
    if not settings.K2A_BOOST_AGENT:
        raise HTTPException(status_code=403, detail="agente A2 non abilitato (K2A_BOOST_AGENT=0)")
    session = sessions.get_session(body.sessionId)
    if not session:
        raise HTTPException(status_code=404, detail="session not found")
    _check_ownership(session, user)

    collected = dict(session.get("collected_data") or {})
    servizio_id = body.servizioId or collected.get("boost_suggerito")
    if not servizio_id or servizio_id not in settings.K2A_BOOST_AGENT_SERVIZI:
        raise HTTPException(status_code=409, detail="servizio non instradato all'agente A2")
    servizio = catalog.get_servizio(servizio_id)
    if not servizio:
        raise HTTPException(status_code=404, detail="servizio non a catalogo")

    if not boost_agent.mcp_quant.available():
        raise HTTPException(status_code=503, detail="MCP quant non disponibile nel backend")

    try:
        form = await engine.get_form(servizio_id)
        campi = form.get("campi") or []
    except engine.EngineError:
        campi = []
    inputs = autofill.extract_inputs(session, campi)
    if not inputs.get("ragione_sociale"):
        _name = _session_company(session)
        if _name:
            inputs["ragione_sociale"] = _name

    entitlement_token = _mint_entitlement(session, servizio_id, tier=servizio.get("tipo"))
    if not entitlement_token:
        raise HTTPException(status_code=402, detail={
            "reason": "payment_required", "servizio_id": servizio_id,
            "label": servizio.get("label"), "prezzo_eur": catalog.prezzo_eur(servizio_id)})

    # skill di dominio: blueprint_id (es. "flusso-advisorboost-pmi.boost") → cartella skill
    blueprint = str(servizio.get("blueprint_id") or "").replace(".boost", "")
    skill_path = settings.SKILLS_DIR / blueprint / "SKILL.md"
    if not skill_path.exists():
        raise HTTPException(status_code=500, detail=f"skill non trovata: {blueprint}")
    skill_text = skill_path.read_text(encoding="utf-8")
    sezioni = _AGENT_SEZIONI.get(servizio_id, _AGENT_SEZIONI_DEFAULT)

    res = boost_agent.run_boost_agent(skill_text, inputs, servizio_id, sezioni=sezioni)
    if not res.get("delivered"):
        raise HTTPException(status_code=422, detail={
            "reason": "agent_refused", "problemi": res.get("problemi"),
            "message": "L'agente non ha prodotto un deliverable conforme (provenienza/sezioni)."})
    return {"servizio_id": servizio_id, "label": servizio.get("label"),
            "deliverable": res["deliverable"], "metrics": res.get("metrics"),
            "provenance_calls": len(res.get("provenance_calls") or [])}


# --- Gate Preview (W8): gratis, max 2/mese, utente registrato -------------

class PreviewBody(BaseModel):
    sessionId: str = Field(..., alias="session_id")
    servizioId: str = Field(..., alias="servizio_id")
    inputs: dict = Field(default_factory=dict)

    class Config:
        populate_by_name = True


@router.post("/preview")
async def create_preview(body: PreviewBody, user: AuthUser = Depends(require_user)):
    """Anteprima gratuita (score + criticità #1). Richiede utente registrato e
    consuma una delle 2 preview/mese. L'8e compone solo l'assaggio (auth PREVIEW).
    """
    session = sessions.get_session(body.sessionId)
    if not session:
        raise HTTPException(status_code=404, detail="session not found")
    _check_ownership(session, user)

    if not catalog.is_8e_generabile(body.servizioId):
        raise HTTPException(status_code=409, detail="servizio non generabile via 8e")

    # Gate contatore: incremento atomico con cap (funzione SQL).
    ym = datetime.now(timezone.utc).strftime("%Y-%m")
    try:
        client = get_admin_client()
        rpc = client.rpc("kbot_preview_consume",
                         {"p_user": user.id, "p_ym": ym, "p_limit": PREVIEW_LIMIT_MESE}).execute()
        new_count = rpc.data
    except Exception as exc:
        log.warning("preview counter error: %s", exc)
        raise HTTPException(status_code=503, detail="contatore preview non disponibile")

    if new_count is None:
        # quota esaurita → invita al documento (Gate Documento)
        raise HTTPException(status_code=409,
                            detail={"reason": "preview_quota_exhausted",
                                    "limit": PREVIEW_LIMIT_MESE,
                                    "message": "Hai esaurito le anteprime gratuite del mese. "
                                               "Sblocca il documento completo."})

    servizio = catalog.get_servizio(body.servizioId)
    try:
        res = await engine.create_deliverable(
            service_id=body.servizioId,
            inputs=body.inputs,
            auth_level="PREVIEW",
            tier=(servizio or {}).get("tipo"),
        )
    except engine.EngineRefused as r:
        raise HTTPException(status_code=422, detail={"reason": r.reason, "message": r.message})
    except engine.EngineError as e:
        log.warning("8e preview error: %s", e, exc_info=True)
        raise HTTPException(status_code=502, detail="motore non disponibile, riprova tra poco")

    return {**res, "preview_count": new_count, "preview_limit": PREVIEW_LIMIT_MESE}


@router.get("/deliverables/{job_id}")
async def status(job_id: str, user: Optional[AuthUser] = Depends(optional_user)):
    # C1 — il polling di stato espone outputs/citazioni del deliverable: legato a
    # sessione+owner+pagamento come i download.
    session = _authorize_job_download(job_id, user)
    from ..lib import agent_jobs
    try:
        job = await _get_job(job_id)
    except engine.EngineError:
        # C4 — job perso sul motore 8e (store in-memory azzerato da un restart/redeploy).
        # NON è un vicolo cieco su un documento pagato:
        collected = session.get("collected_data") or {}
        if collected.get("deliverable_pdf_url"):
            # …ne abbiamo una copia DUREVOLE su Storage → il documento è pronto lo stesso.
            return {"status": "rendered", "recovered": True,
                    "pdf_url": collected.get("deliverable_pdf_url"),
                    "outputs": {"pdf": True,
                                "xlsx": bool(collected.get("deliverable_json_saved"))}}
        # …nessuna copia: segnaliamo RIGENERABILE (già pagato, nessun riaddebito) invece
        # di un 502 muto → il frontend può rilanciare via POST /deliverables/recover.
        log.warning("engine status error for job %s → recoverable", job_id, exc_info=True)
        return {"status": "expired", "recoverable": True,
                "servizio_id": collected.get("deliverable_service"),
                "message": "La generazione è scaduta sul motore. Rilancia il documento: "
                           "è già pagato, non ti verrà riaddebitato."}
    # C4 — appena renderizzato, rendi il deliverable DUREVOLE (best-effort, non blocca
    # la risposta): da qui in poi sopravvive a un restart dell'8e. Solo job 8e, non A2.
    if isinstance(job, dict) and job.get("status") == "rendered" and not agent_jobs.is_agent_job(job_id):
        try:
            await _persist_durable(session, job_id, job)
        except Exception:
            log.warning("persist durable (status) fallita job %s", job_id, exc_info=True)
    return job


@router.get("/deliverables/{job_id}/pdf")
async def deliverable_pdf(job_id: str, user: Optional[AuthUser] = Depends(optional_user)):
    """Serve il PDF del deliverable generato dal motore 8e. L'8e gira in un container
    Railway SEPARATO: il filesystem NON è condiviso, quindi il PDF si scarica dai
    byte via HTTP (engine.fetch_output) e non da un path locale.

    C1 — download legato a sessione+owner+pagamento: il `job_id` da solo non basta
    più (era IDOR + bypass paywall)."""
    from fastapi.responses import Response
    session = _authorize_job_download(job_id, user)
    try:
        content, _ = await engine.fetch_output(job_id, "pdf")
    except engine.EngineError as e:
        if str(e) == "not_ready":
            raise HTTPException(status_code=409, detail="documento non ancora pronto")
        # C4 — job perso sull'8e (restart): servi la copia DUREVOLE su Storage se c'è.
        sid = str(session.get("id") or "")
        durable = download_bytes(bucket=STORAGE_REPORTS_BUCKET,
                                 path=_durable_pdf_path(sid, job_id)) if sid else None
        if durable:
            return Response(content=durable, media_type="application/pdf",
                            headers={"Content-Disposition": 'attachment; filename="report-k2ai.pdf"'})
        if str(e) == "not_found":
            raise HTTPException(status_code=404, detail="pdf non disponibile")
        # M1 — messaggio generico al client; dettaglio nei log.
        log.warning("fetch_output error for job %s", job_id, exc_info=True)
        raise HTTPException(status_code=502, detail="motore non disponibile, riprova tra poco")
    return Response(content=content, media_type="application/pdf",
                    headers={"Content-Disposition": 'attachment; filename="report-k2ai.pdf"'})


@router.get("/deliverables/{job_id}/xlsx")
async def deliverable_xlsx(job_id: str, user: Optional[AuthUser] = Depends(optional_user)):
    """Excel 'modello vivo' del deliverable Boost — il 2° file del bundle (oltre al
    PDF). Scarica il deliverable.json dall'8e via HTTP (filesystem NON condiviso,
    l'8e è un servizio separato) e lo rende un Excel multi-foglio editabile
    (opzioni scorate, iniziative, KPI...). On-demand, deterministico.

    C1 — download legato a sessione+owner+pagamento (vedi deliverable_pdf)."""
    import json as _json
    from fastapi.responses import Response
    from ..lib.xlsx_renderer import render_deliverable_8e_xlsx
    session = _authorize_job_download(job_id, user)
    raw = None
    try:
        raw, _ = await engine.fetch_output(job_id, "json")
    except engine.EngineError as e:
        if str(e) == "not_ready":
            raise HTTPException(status_code=409, detail="documento non ancora pronto")
        # C4 — job perso sull'8e (restart): rileggi il JSON DUREVOLE su Storage se c'è.
        sid = str(session.get("id") or "")
        raw = download_bytes(bucket=STORAGE_REPORTS_BUCKET,
                             path=_durable_json_path(sid, job_id)) if sid else None
        if raw is None:
            if str(e) == "not_found":
                raise HTTPException(status_code=404, detail="modello Excel non disponibile per questo documento")
            # M1 — messaggio generico al client; dettaglio nei log.
            log.warning("fetch_output error for job %s", job_id, exc_info=True)
            raise HTTPException(status_code=502, detail="motore non disponibile, riprova tra poco")
    try:
        deliverable = _json.loads(raw.decode("utf-8"))
        data = render_deliverable_8e_xlsx(deliverable)
    except Exception as exc:
        log.warning("xlsx render fallito per %s: %s", job_id, exc)
        raise HTTPException(status_code=500, detail="impossibile generare il modello Excel")
    return Response(content=data,
                    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": 'attachment; filename="modello-k2ai.xlsx"'})


class SaveDeliverableBody(BaseModel):
    sessionId: str = Field(..., alias="session_id")
    jobId: str = Field(..., alias="job_id")

    class Config:
        populate_by_name = True


@router.post("/deliverables/save")
async def save_deliverable(body: SaveDeliverableBody,
                           user: Optional[AuthUser] = Depends(optional_user)):
    """Rende DURATURO il deliverable 8e: carica il PDF (effimero in /tmp) su
    Supabase Storage e lo lega alla sessione → compare in dashboard/storico.
    Idempotente: se già salvato per questo job, ritorna l'URL esistente."""
    session = sessions.get_session(body.sessionId)
    if not session:
        raise HTTPException(status_code=404, detail="session not found")
    _check_ownership(session, user)

    collected = dict(session.get("collected_data") or {})
    if collected.get("deliverable_saved_job") == body.jobId and session.get("pdf_url"):
        return {"pdf_url": session["pdf_url"], "cached": True}

    # Scarica il PDF dall'8e via HTTP (filesystem NON condiviso: servizio separato).
    try:
        content, _ = await engine.fetch_output(body.jobId, "pdf")
    except engine.EngineError as e:
        if str(e) == "not_found":
            raise HTTPException(status_code=404, detail="pdf non disponibile")
        if str(e) == "not_ready":
            raise HTTPException(status_code=409, detail="documento non ancora pronto")
        # M1 — messaggio generico al client; dettaglio nei log.
        log.warning("fetch_output error for job %s", body.jobId, exc_info=True)
        raise HTTPException(status_code=502, detail="motore non disponibile, riprova tra poco")

    public_url = upload_pdf(
        bucket=STORAGE_REPORTS_BUCKET,
        path=f"deliverables/{body.sessionId}/{body.jobId}.pdf",
        content=content,
    )
    # Label leggibile del servizio per la dashboard/storico.
    servizio_id = collected.get("deliverable_service") or ""
    servizio = catalog.get_servizio(servizio_id) if servizio_id else None
    collected["deliverable_saved_job"] = body.jobId
    collected["deliverable_pdf_url"] = public_url
    if servizio:
        collected["deliverable_label"] = servizio.get("label")
    sessions.update_session(body.sessionId, {"pdf_url": public_url, "collected_data": collected})
    return {"pdf_url": public_url}


class RecoverBody(BaseModel):
    sessionId: str = Field(..., alias="session_id")

    class Config:
        populate_by_name = True


@router.post("/deliverables/recover")
async def recover_deliverable(body: RecoverBody,
                              user: Optional[AuthUser] = Depends(optional_user)):
    """C4 — recupera un deliverable pagato il cui job è andato perso a un restart
    dell'8e (store job in-memory). NON riaddebita: la sessione è già pagata, si
    re-minta l'entitlement e si rilancia la generazione con gli STESSI input persistiti.

    Ordine (anti-storm): (1) se esiste una copia DUREVOLE su Storage → è già pronto;
    (2) se il job corrente è ancora vivo sull'8e → lo si restituisce (niente doppione);
    (3) altrimenti si rigenera. Gate ownership + paywall come gli altri endpoint.
    """
    session = sessions.get_session(body.sessionId)
    if not session:
        raise HTTPException(status_code=404, detail="session not found")
    _check_ownership(session, user)

    collected = dict(session.get("collected_data") or {})
    servizio_id = collected.get("deliverable_service")
    if not servizio_id:
        raise HTTPException(status_code=409, detail="nessun documento da recuperare per questa sessione")

    # (1) copia durevole già presente → pronto, niente rigenerazione.
    if collected.get("deliverable_pdf_url"):
        return {"status": "rendered", "recovered": True,
                "pdf_url": collected.get("deliverable_pdf_url"),
                "job_id": collected.get("deliverable_saved_job"),
                "servizio_id": servizio_id}

    # (2) job corrente ancora vivo sull'8e → restituiscilo (evita doppioni/storm).
    cur = collected.get("deliverable_job_id")
    if cur:
        try:
            j = await _get_job(cur)
            if isinstance(j, dict) and j.get("status") in ("routed", "running", "validating", "rendered"):
                return {**j, "job_id": cur, "servizio_id": servizio_id}
        except engine.EngineError:
            pass  # perso → si rigenera sotto

    # (3) rigenerazione: paywall (già pagato → token) + input persistiti (o re-autofill).
    servizio = catalog.get_servizio(servizio_id) or {}
    entitlement_token = _mint_entitlement(session, servizio_id, tier=servizio.get("tipo"))
    if not entitlement_token:
        raise HTTPException(status_code=402, detail="documento non pagato")
    inputs = collected.get("deliverable_inputs") or {}
    auth_level = collected.get("deliverable_auth_level") or "FULL"
    if not inputs:
        try:
            campi = (await engine.get_form(servizio_id)).get("campi") or []
        except engine.EngineError:
            campi = []
        inputs = autofill.extract_inputs(session, campi)
        if not inputs.get("ragione_sociale"):
            _name = _session_company(session)
            if _name:
                inputs["ragione_sociale"] = _name
    try:
        res = await engine.create_deliverable(
            service_id=servizio_id, inputs=inputs,
            entitlement_token=entitlement_token, tier=servizio.get("tipo"), auth_level=auth_level,
        )
    except engine.EngineRefused as r:
        raise HTTPException(status_code=422, detail={"reason": r.reason, "message": r.message})
    except engine.EngineError as e:
        log.warning("recover 8e error per %s: %s", servizio_id, e, exc_info=True)
        raise HTTPException(status_code=502, detail="motore non disponibile, riprova tra poco")

    collected["deliverable_job_id"] = res.get("job_id")
    collected.pop("deliverable_saved_job", None)
    try:
        sessions.update_session(body.sessionId, {"collected_data": collected})
    except Exception:
        log.warning("persist recover job fallita (non bloccante)", exc_info=True)
    return {**res, "recovered": True, "servizio_id": servizio_id, "label": servizio.get("label")}


@router.get("/deliverables/form/{servizio_id}")
async def deliverable_form(servizio_id: str):
    """Campi che il deliverable richiede — il frontend li mostra per raccogliere
    gli input del cliente prima di generare."""
    if not catalog.is_8e_generabile(servizio_id):
        raise HTTPException(status_code=409, detail="servizio non generabile via 8e")
    try:
        return await engine.get_form(servizio_id)
    except engine.EngineError as e:
        log.warning("get_form error for %s", servizio_id, exc_info=True)
        raise HTTPException(status_code=502, detail="motore non disponibile, riprova tra poco")


@router.get("/engine/health")
async def engine_health():
    return await engine.health()


@router.get("/boost-catalog")
def boost_catalog():
    """Elenco dei servizi generabili via 8e (per il selettore nel pannello: se il
    routing automatico sbaglia, l'utente sceglie il documento giusto)."""
    items = []
    for s in catalog.lista_servizi():
        sid = s.get("id")
        if sid and catalog.is_8e_generabile(sid):
            items.append({
                "id": sid,
                "label": s.get("label") or sid,
                "ambito": s.get("ambito") or s.get("tipo") or "",
            })
    items.sort(key=lambda x: x["label"])
    return {"servizi": items}
