from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Request, status
from loguru import logger
from openai import OpenAI
from pydantic import BaseModel, Field, field_validator

from core import notion_board
from core.config import settings
from core.email import send_confirmation_email
from core.text import markdown_to_telegram_html
from db.client import get_service_client
from interfaces.telegram.notifier import notify_sync, send_long_message, send_message

router = APIRouter(prefix="/api/intake", tags=["public-intake"])

MAX_CHAT_MESSAGES = 24
MAX_CHAT_MESSAGE_LENGTH = 2000
CHAT_ALLOWED_ROLES = {"user", "assistant"}
K_BOT_AGENT_NAME = "solution_architect"
K_BOT_SYSTEM_PROMPT = """Sei K-BOT, il qualificatore iniziale di K2-AI.

Il tuo unico compito è capire se il caso del visitatore ha potenziale reale per un intervento AI, poi indirizzarlo verso il contatto con il team.

Processo obbligatorio — prima di concludere devi aver raccolto TUTTI e TRE questi elementi:
1. Come funziona oggi il processo (cosa succede, chi lo fa, con quali strumenti)
2. Dove si perde tempo o qualità (il punto esatto di attrito)
3. Volumi o frequenza (quante volte a settimana/mese, quanti documenti, ecc.)

Se uno di questi manca, fai la domanda corrispondente. Una domanda alla volta, concreta e breve.

Stile delle domande:
- Mantieni sempre gli stessi paletti di raccolta (processo attuale, attrito, volumi/frequenza).
- Evita formulazioni identiche in turni consecutivi: varia leggermente lessico e apertura frase, mantenendo lo stesso significato.
- Non fare domande multiple nello stesso turno.

Solo quando hai i tre elementi:
- Esprimi la valutazione in una frase: "il caso ha potenziale", "serve più chiarezza su X", oppure "questo caso non è adatto a un intervento AI"
- Se ha potenziale, invita a contattarci scrivendo /contatti.html su una riga separata, da solo, senza testo attorno

Regole sempre attive:
- Rispondi in italiano (o nella lingua dell'utente se diversa)
- Massimo 3-4 frasi per risposta
- NON dare soluzioni, NON spiegare come implementare nulla, NON suggerire strumenti o architetture
- Non fare preventivi, non promettere risultati, non inventare casi studio o metriche
- Non chiedere dati sensibili
"""

K_BOT_INTERNAL_ANALYSIS_PROMPT = """Sei un consulente senior di K2-AI. Devi analizzare il caso di un potenziale cliente e produrre una scheda interna operativa per il team.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FRAMEWORK DI CLASSIFICAZIONE (usa sempre questo)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Le 4 categorie possibili, con i loro segnali:

■ AUTOMAZIONE (n8n, Make, Zapier)
→ Processo deterministico: regole fisse, input strutturati (email standard, form, Excel)
→ Si connettono strumenti già esistenti (CRM + email + Sheets)
→ Alta frequenza, bassa complessità (notifiche, sync, report automatici)
→ Budget €500–€3.000, time-to-market 1–4 settimane
→ NON scegliere se: serve capire testo variabile, eccezioni frequenti, clienti finali lo usano

■ SOFTWARE CUSTOM (SaaS, app, piattaforma)
→ Il software è il prodotto stesso, da vendere o mostrare a clienti finali
→ Logica di business proprietaria, UI/UX su misura
→ Requisiti di sicurezza/compliance (GDPR, PCI), scalabilità enterprise
→ Budget >€15.000, timeline >2 mesi
→ NON scegliere se: nessuna validazione di mercato, no risorse per manutenzione, timeline <2 settimane

■ AI / LLM (Claude, GPT, RAG, fine-tuning)
→ Testo variabile, ambiguo o in linguaggio naturale (email, recensioni, richieste)
→ Serve generare contenuti, classificare testo, estrarre da documenti non strutturati (PDF, email)
→ Chatbot/assistente su domande aperte, FAQ intelligenti, sentiment
→ NON scegliere se: task puramente meccanico, dati tutti strutturati, precisione 100% obbligatoria

  Sotto-scelte per AI/LLM:
  - Prompt Engineering: il modello sa già farlo, serve guidarlo → classificazione email con esempi
  - RAG: serve rispondere su documenti/dati aziendali → chatbot su manuale interno
  - Fine-tuning: serve tono/stile molto specifico → AI con brand voice preciso

■ AI AGENT (agenti autonomi multi-step)
→ Task multi-step con percorso non sempre prevedibile
→ Deve combinare più strumenti in modo dinamico (web, email, DB, API)
→ Ragionamento e adattamento in base a risultati intermedi
→ Es: ricerca lead autonoma, monitoring competitor, redazione report con fonti variabili
→ NON scegliere se: task semplice e deterministico (overkill), budget limitato, no supervisione umana

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PROTOCOLLO DI CLASSIFICAZIONE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Il processo è deterministico (regole fisse) o variabile (dipende dal contenuto)?
   → Deterministico: Automazione o Software Custom
   → Variabile: AI/LLM o AI Agent
2. Se deterministico: il software è il prodotto da vendere? → SÌ = Software Custom, NO = Automazione
3. Se variabile: serve un singolo step AI o più step con strumenti multipli? → Singolo = LLM, Multi = Agent
4. Budget e timeline sono compatibili con la soluzione?
5. Ci sono red flag? (budget irrealistico, non sa descrivere input/output, vuole replicare tool esistente, no piano manutenzione)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STRUTTURA DELLA SCHEDA DA PRODURRE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**CATEGORIA CONSIGLIATA**
[Una sola: Automazione / Software Custom / AI/LLM / AI Agent]
Motivo in 1–2 frasi secche basate sui segnali sopra.

**PROBLEMA**
Processo attuale, attrito principale, dove si perde tempo/qualità.

**CONTESTO OPERATIVO**
Team coinvolto, strumenti già in uso, volumi/frequenza, vincoli.

**SOLUZIONE TECNICA**
Strumenti specifici, architettura, flusso dati, integrazioni. Esempio: "n8n self-hosted con nodo Gmail → parser LLM (GPT-4o mini) → scrittura su Airtable → notifica Slack". Sii concreto, non generico.

**LEVA PRINCIPALE**
Quale singola automazione/AI ha impatto immediato e perché.

**RISCHI E RED FLAG**
Cosa potrebbe bloccare o complicare. Segnala se il caso ha red flag dal framework.

**DOMANDE PER IL PRIMO CONTATTO**
2–3 domande specifiche da fare al cliente per validare e affinare.

Sii tecnico e diretto. Zero frasi generiche. Se i dati sono insufficienti per classificare, dillo esplicitamente e indica quale informazione manca.
"""

INTERNAL_ANALYSIS_REQUIRED_SECTIONS = (
    "CATEGORIA CONSIGLIATA",
    "PROBLEMA",
    "CONTESTO OPERATIVO",
    "SOLUZIONE TECNICA",
    "LEVA PRINCIPALE",
    "RISCHI E RED FLAG",
    "DOMANDE PER IL PRIMO CONTATTO",
)

_openai_client: OpenAI | None = None


class ContactIntakePayload(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=5, max_length=160)
    company_role: str = Field(default="", max_length=120)
    sector: str = Field(default="", max_length=80)
    message: str = Field(min_length=10, max_length=3000)
    internal_context: str = Field(default="", max_length=4000)
    source_page: str = Field(default="contatti", max_length=80)
    website: str = Field(default="", max_length=120)

    @field_validator("name", "company_role", "sector", "message", "source_page", mode="before")
    @classmethod
    def _clean_text(cls, value: str) -> str:
        return str(value or "").strip()

    @field_validator("email", mode="before")
    @classmethod
    def _clean_email(cls, value: str) -> str:
        return str(value or "").strip().lower()

    @field_validator("email")
    @classmethod
    def _validate_email(cls, value: str) -> str:
        if "@" not in value or "." not in value.split("@")[-1]:
            raise ValueError("Email non valida")
        return value


class KBotMessage(BaseModel):
    role: str = Field(min_length=4, max_length=16)
    content: str = Field(min_length=1, max_length=MAX_CHAT_MESSAGE_LENGTH)

    @field_validator("role", mode="before")
    @classmethod
    def _clean_role(cls, value: str) -> str:
        return str(value or "").strip().lower()

    @field_validator("role")
    @classmethod
    def _validate_role(cls, value: str) -> str:
        if value not in CHAT_ALLOWED_ROLES:
            raise ValueError("Ruolo non valido")
        return value

    @field_validator("content", mode="before")
    @classmethod
    def _clean_content(cls, value: str) -> str:
        return str(value or "").strip()


class KBotChatPayload(BaseModel):
    session_id: str
    source_page: str = Field(default="k-bot", max_length=80)
    messages: list[KBotMessage]

    @field_validator("session_id", mode="before")
    @classmethod
    def _clean_session_id(cls, value: str) -> str:
        return str(value or "").strip()

    @field_validator("session_id")
    @classmethod
    def _validate_session_id(cls, value: str) -> str:
        uuid.UUID(value)
        return value

    @field_validator("source_page", mode="before")
    @classmethod
    def _clean_source_page(cls, value: str) -> str:
        return str(value or "").strip()

    @field_validator("messages")
    @classmethod
    def _validate_messages(cls, value: list[KBotMessage]) -> list[KBotMessage]:
        if not value:
            raise ValueError("La conversazione è vuota")
        if len(value) > MAX_CHAT_MESSAGES:
            raise ValueError("Troppi messaggi")
        return value


def _get_openai_client() -> OpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(api_key=settings.openai_api_key)
    return _openai_client


def _latest_user_message(messages: list[KBotMessage]) -> str:
    for item in reversed(messages):
        if item.role == "user":
            return item.content
    return ""


def _first_user_message(messages: list[KBotMessage]) -> str:
    for item in messages:
        if item.role == "user":
            return item.content
    return ""


def _last_assistant_message(messages: list[KBotMessage]) -> str:
    for item in reversed(messages):
        if item.role == "assistant":
            return item.content
    return ""


def _kbot_fallback_question(messages: list[KBotMessage]) -> str:
    variants = [
        "Per capire se il caso regge: qual è il passaggio preciso in cui oggi perdi più tempo o qualità?",
        "Per valutare bene il caso, mi manca un dettaglio operativo: in quale punto del flusso si crea più attrito?",
        "Mi serve un dato in più per qualificare la richiesta: dove si blocca o rallenta davvero il processo?",
        "Ultimo pezzo utile per una valutazione affidabile: qual è la fase che oggi vi fa perdere più tempo?",
        "Per chiudere la diagnosi iniziale, indicami il punto esatto in cui cala qualità o si accumula ritardo.",
    ]
    user_chars = sum(len(item.content) for item in messages if item.role == "user")
    index = (user_chars + len(messages)) % len(variants)
    return variants[index]


def _format_kbot_task_description(payload: KBotChatPayload, request: Request) -> str:
    latest_user_message = _latest_user_message(payload.messages) or "Nessun messaggio utente disponibile."

    return (
        "Sessione diagnosi pubblica K-BOT.\n\n"
        f"Session ID: {payload.session_id}\n"
        f"Pagina: {payload.source_page}\n\n"
        "Ultimo messaggio utente:\n"
        f"{latest_user_message}"
    )


def _serialize_messages(messages: list[KBotMessage]) -> list[dict[str, str]]:
    return [{"role": item.role, "content": item.content} for item in messages]


def _generate_internal_analysis_sync(messages: list[KBotMessage]) -> str:
    """Genera via LLM una scheda interna dettagliata della sessione K-BOT."""
    if not settings.openai_api_key.strip():
        return ""
    model_name = settings.default_openai_model
    conversation = "\n".join(
        f"{'Cliente' if m.role == 'user' else 'K-BOT'}: {m.content}"
        for m in messages
    )
    try:
        response = _get_openai_client().chat.completions.create(
            model=model_name,
            temperature=0.3,
            max_tokens=1400,
            messages=[
                {"role": "system", "content": K_BOT_INTERNAL_ANALYSIS_PROMPT},
                {"role": "user", "content": f"Conversazione K-BOT:\n\n{conversation}"},
            ],
        )
        return (response.choices[0].message.content or "").strip()
    except Exception as exc:
        logger.warning(f"Errore analisi interna K-BOT: {exc}")
        return ""


async def _dispatch_kbot_internal_analysis(session_id: str, messages: list[KBotMessage]) -> None:
    """Genera la scheda interna e la invia a Telegram + aggiorna il task."""
    loop = asyncio.get_event_loop()
    analysis = await loop.run_in_executor(None, _generate_internal_analysis_sync, messages)
    if not analysis:
        return

    first_user_msg = _first_user_message(messages)
    header = (
        f"Diagnosi K-BOT completata\n"
        f"Sessione: {session_id[:8]}...\n"
        f"Problema: {first_user_msg[:120]}\n"
        f"{'─' * 40}\n\n"
    )
    await send_long_message(header + analysis)

    try:
        if notion_board.notion_enabled():
            task_id = _find_notion_kbot_task_id(session_id)
            if task_id:
                notion_board.update_task_status(task_id, "pending", analysis[:1800])
        else:
            client = get_service_client()
            client.table("tasks").update({
                "notes": analysis[:1000],
                "status": "pending",
                "updated_at": datetime.now(UTC).isoformat(),
            }).eq("id", session_id).execute()
    except Exception as exc:
        logger.warning(f"Errore aggiornamento task analisi K-BOT {session_id}: {exc}")


def _generate_internal_analysis_from_context_sync(context: str) -> str:
    """Genera la scheda interna a partire dal contesto testuale (usato all'invio del form)."""
    if not settings.openai_api_key.strip():
        return ""
    model_name = settings.default_openai_model
    try:
        response = _get_openai_client().chat.completions.create(
            model=model_name,
            temperature=0.3,
            max_tokens=1400,
            messages=[
                {"role": "system", "content": K_BOT_INTERNAL_ANALYSIS_PROMPT},
                {"role": "user", "content": f"Contesto del caso:\n\n{context}"},
            ],
        )
        return (response.choices[0].message.content or "").strip()
    except Exception as exc:
        logger.warning(f"Errore analisi interna da form: {exc}")
        return ""


def _build_contact_internal_message(payload: "ContactIntakePayload", analysis: str | None = None) -> str:
    header = (
        f"Nuovo contatto dal sito\n"
        f"Nome: {payload.name}\n"
        f"Email: {payload.email}\n"
        f"Azienda: {payload.company_role or 'Non indicato'}\n"
        f"Settore: {payload.sector or 'Non indicato'}\n"
        f"Origine: {payload.source_page}\n"
        f"{'─' * 40}\n\n"
    )
    if analysis and analysis.strip():
        return header + analysis.strip()

    parts = []
    if payload.internal_context:
        parts.append(f"Contesto K-BOT:\n{payload.internal_context}")
    parts.append(f"Messaggio dal form:\n{payload.message}")
    return header + "\n\n".join(parts)


def _analysis_has_section(content: str, section_name: str) -> bool:
    import re

    pattern = re.compile(rf"(?im)^\s*(?:\*\*)?{re.escape(section_name)}(?:\*\*)?\s*$")
    return bool(pattern.search(content or ""))


def _normalize_contact_internal_analysis(payload: "ContactIntakePayload", analysis: str | None) -> str:
    base = (analysis or "").strip()
    fallback_sections: dict[str, str] = {
        "CATEGORIA CONSIGLIATA": (
            "Dati ancora parziali. Primo contatto utile per classificare il caso "
            "tra Automazione, Software Custom, AI/LLM o AI Agent."
        ),
        "PROBLEMA": payload.message.strip() or "Non specificato.",
        "CONTESTO OPERATIVO": payload.internal_context.strip() or "Non specificato.",
        "SOLUZIONE TECNICA": "Da definire dopo la prima call di qualificazione.",
        "LEVA PRINCIPALE": "Confermare il punto di attrito con impatto più alto su tempo o qualità.",
        "RISCHI E RED FLAG": "Brief incompleto o obiettivi non misurati prima dell'avvio operativo.",
        "DOMANDE PER IL PRIMO CONTATTO": (
            "1. Quale fase del processo oggi crea il collo di bottiglia principale?\n"
            "2. Quali strumenti usa il team in questa fase?\n"
            "3. Quali volumi/frequenze gestite ogni settimana o mese?"
        ),
    }

    if not base:
        return "\n\n".join(
            f"**{section}**\n{fallback_sections[section]}" for section in INTERNAL_ANALYSIS_REQUIRED_SECTIONS
        )

    missing = [section for section in INTERNAL_ANALYSIS_REQUIRED_SECTIONS if not _analysis_has_section(base, section)]
    if not missing:
        return base

    additions = "\n\n".join(f"**{section}**\n{fallback_sections[section]}" for section in missing)
    return f"{base}\n\n{additions}".strip()


async def _dispatch_contact_internal_analysis(
    payload: "ContactIntakePayload",
    *,
    client_id: str | None = None,
    intake_page_id: str | None = None,
) -> None:
    """Genera e invia a Telegram la scheda interna quando il form contatti viene inviato."""
    parts = []
    if payload.internal_context:
        parts.append(f"Contesto K-BOT:\n{payload.internal_context}")
    parts.append(f"Messaggio dal form:\n{payload.message}")
    full_context = "\n\n".join(parts)

    loop = asyncio.get_event_loop()
    raw_analysis = await loop.run_in_executor(
        None, _generate_internal_analysis_from_context_sync, full_context
    )
    analysis = _normalize_contact_internal_analysis(payload, raw_analysis)

    full_message = _build_contact_internal_message(payload, analysis)
    await send_long_message(markdown_to_telegram_html(full_message), parse_mode="HTML")

    if notion_board.notion_enabled() and client_id:
        try:
            target_page = intake_page_id
            if not target_page:
                target_page = notion_board.create_client_intake_subpage(
                    client_id=client_id,
                    contact_name=payload.name,
                    email=payload.email,
                    message=payload.message,
                    source_page=payload.source_page,
                    internal_context=payload.internal_context or "",
                )
            notion_board.append_markdown_section_to_page(
                target_page,
                heading="Scheda interna operativa",
                content=analysis,
            )
            notion_board.append_markdown_section_to_page(
                target_page,
                heading="Messaggio completo inviato su Telegram",
                content=full_message,
            )
        except Exception as exc:
            logger.warning(f"Errore salvataggio scheda interna su Notion: {exc}")


def _find_notion_kbot_task_id(session_id: str) -> str | None:
    try:
        for task in notion_board.list_tasks():
            haystack = "\n".join([task.get("title") or "", task.get("description") or "", task.get("notes") or ""])
            if session_id in haystack:
                return task.get("id")
    except Exception as exc:
        logger.warning(f"Errore ricerca task Notion K-BOT {session_id}: {exc}")
    return None


def _upsert_kbot_task(payload: KBotChatPayload, request: Request) -> str | None:
    if notion_board.notion_enabled():
        title_seed = _first_user_message(payload.messages) or "Nuova diagnosi"
        notes = (
            f"Sessione K-BOT: {payload.session_id}\n"
            f"Origine: {payload.source_page}\n"
            f"Ultimo aggiornamento: {datetime.now(UTC).isoformat()}\n"
            f"Messaggi: {len(payload.messages)}"
        )
        existing_id = _find_notion_kbot_task_id(payload.session_id)
        if existing_id:
            notion_board.update_task_status(existing_id, "running", notes)
            return existing_id
        return notion_board.create_task(
            title=f"Diagnosi K-BOT — {title_seed}"[:120],
            description=_format_kbot_task_description(payload, request),
            assigned_to=K_BOT_AGENT_NAME,
            priority=3,
            status="running",
            requested_by="website_k_bot",
            notes=notes,
            task_type="AI",
        )

    client = get_service_client()
    now_iso = datetime.now(UTC).isoformat()
    title_seed = _first_user_message(payload.messages) or "Nuova diagnosi"
    task_payload: dict[str, Any] = {
        "title": f"Diagnosi K-BOT — {title_seed}"[:120],
        "description": _format_kbot_task_description(payload, request),
        "assigned_to": K_BOT_AGENT_NAME,
        "requested_by": "website_k_bot",
        "status": "running",
        "priority": 3,
        "input_data": {
            "source": "website_k_bot",
            "session_id": payload.session_id,
            "source_page": payload.source_page,
            "messages": _serialize_messages(payload.messages),
        },
        "updated_at": now_iso,
    }

    try:
        existing = (
            client.table("tasks")
            .select("id")
            .eq("id", payload.session_id)
            .limit(1)
            .execute()
            .data
            or []
        )
        if existing:
            client.table("tasks").update(task_payload).eq("id", payload.session_id).execute()
        else:
            client.table("tasks").insert(
                {
                    "id": payload.session_id,
                    **task_payload,
                    "created_at": now_iso,
                }
            ).execute()
    except Exception as exc:
        logger.warning(f"Errore aggiornamento task K-BOT {payload.session_id}: {exc}")
    return payload.session_id


def _log_kbot_turn(payload: KBotChatPayload, assistant_message: str, model_name: str, task_id: str | None = None) -> None:
    if notion_board.notion_enabled():
        try:
            notion_board.create_agent_log(
                agent=K_BOT_AGENT_NAME,
                task_id=task_id or _find_notion_kbot_task_id(payload.session_id),
                action="Turno diagnosi K-BOT",
                input_summary=_latest_user_message(payload.messages)[:220],
                output_summary=assistant_message[:220],
                status="done",
                llm_provider="openai",
                llm_model=model_name,
            )
            if task_id:
                notion_board.update_task_status(task_id, "running", assistant_message[:500])
        except Exception as exc:
            logger.warning(f"Errore log turno K-BOT Notion {payload.session_id}: {exc}")
        return

    client = get_service_client()
    user_message = _latest_user_message(payload.messages)

    try:
        client.table("agent_logs").insert(
            {
                "agent": K_BOT_AGENT_NAME,
                "task_id": payload.session_id,
                "action": "Turno diagnosi K-BOT",
                "llm_provider": "openai",
                "llm_model": model_name,
                "input_summary": user_message[:220],
                "output_summary": assistant_message[:220],
                "status": "done",
                "created_at": datetime.now(UTC).isoformat(),
            }
        ).execute()
        client.table("tasks").update(
            {
                "notes": assistant_message[:500],
                "updated_at": datetime.now(UTC).isoformat(),
            }
        ).eq("id", payload.session_id).execute()
    except Exception as exc:
        logger.warning(f"Errore log turno K-BOT {payload.session_id}: {exc}")


def _generate_kbot_reply(messages: list[KBotMessage]) -> tuple[str, str]:
    if not settings.openai_api_key.strip():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servizio K-BOT temporaneamente non disponibile",
        )

    model_name = settings.default_openai_mini_model or settings.default_openai_model
    response = _get_openai_client().chat.completions.create(
        model=model_name,
        temperature=0.4,
        max_tokens=320,
        messages=[
            {"role": "system", "content": K_BOT_SYSTEM_PROMPT},
            *[{"role": item.role, "content": item.content} for item in messages],
        ],
    )
    message = response.choices[0].message.content if response.choices else ""
    content = (message or "").strip()
    if not content:
        content = _kbot_fallback_question(messages)
    else:
        previous_assistant = _last_assistant_message(messages).strip()
        if previous_assistant and content.lower() == previous_assistant.lower():
            content = _kbot_fallback_question(messages)
    return content, model_name


def _notes_from_payload(payload: ContactIntakePayload, request: Request) -> str:
    submitted_at = datetime.now(UTC).isoformat()
    parts = [
        f"Email: {payload.email}",
        f"Azienda / ruolo: {payload.company_role or 'Non indicato'}",
        f"Settore: {payload.sector or 'Non indicato'}",
        f"Origine: {payload.source_page}",
        f"Inviato il: {submitted_at}",
        "",
        "Messaggio:",
        payload.message,
    ]
    if payload.internal_context:
        parts += ["", "─" * 40, "Contesto K-BOT:", payload.internal_context]
    return "\n".join(parts)


@router.post("/contact")
async def create_contact_intake(request: Request):
    try:
        body = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payload JSON non valido") from exc

    try:
        payload = ContactIntakePayload.model_validate(body)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Dati del form non validi") from exc

    if payload.website:
        return {"ok": True}

    lead_id = str(uuid.uuid4())
    task_id: str | None = str(uuid.uuid4())
    now_iso = datetime.now(UTC).isoformat()
    notes = _notes_from_payload(payload, request)

    if notion_board.notion_enabled():
        try:
            intake_bundle = notion_board.create_pipeline_lead_from_contact(
                name=payload.name,
                email=payload.email,
                company_role=payload.company_role or "",
                sector=payload.sector or "Altro",
                message=payload.message,
                source_page=payload.source_page,
                internal_context=payload.internal_context or "",
            )
            client_id = intake_bundle["client_id"]
            project_id = intake_bundle["project_id"]
            lead_id = intake_bundle["lead_id"]
            intake_page_id = notion_board.create_client_intake_subpage(
                client_id=client_id,
                contact_name=payload.name,
                email=payload.email,
                message=payload.message,
                source_page=payload.source_page,
                internal_context=payload.internal_context or "",
                project_id=project_id,
                lead_id=lead_id,
                task_id=None,
            )
            notion_board.create_agent_log(
                agent="lead_generation",
                task_id=None,
                project_id=project_id,
                action="Nuovo lead acquisito dal sito",
                input_summary=f"{payload.name} · {payload.email}",
                output_summary=(payload.message[:220] + "…") if len(payload.message) > 220 else payload.message,
                status="pending",
            )
            task_id = None
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Non sono riuscito a registrare la richiesta in Notion",
            ) from exc

        asyncio.create_task(
            _dispatch_contact_internal_analysis(
                payload,
                client_id=client_id,
                intake_page_id=intake_page_id,
            )
        )
        asyncio.create_task(
            send_confirmation_email(
                to_email=payload.email,
                name=payload.name,
                company_role=payload.company_role or None,
                message=payload.message,
            )
        )
        return {"ok": True, "client_id": client_id, "project_id": project_id, "lead_id": lead_id, "task_id": task_id}

    client = get_service_client()

    pipeline_row = {
        "id": lead_id,
        "name": payload.name,
        "company": payload.company_role or None,
        "sector": payload.sector or None,
        "channel": "website_contact_form",
        "pain_point": payload.message[:240],
        "offer_fit": "Richiesta inbound dal sito K2-AI",
        "status": "identified",
        "next_action": "Ricontattare il lead e qualificare il caso",
        "notes": notes,
        "created_at": now_iso,
        "updated_at": now_iso,
    }

    task_row = {
        "id": task_id,
        "title": f"Nuovo lead dal sito — {payload.name}"[:120],
        "description": (
            f"Lead inbound dal sito K2-AI.\n\n"
            f"Nome: {payload.name}\n"
            f"Email: {payload.email}\n"
            f"Azienda / ruolo: {payload.company_role or 'Non indicato'}\n"
            f"Settore: {payload.sector or 'Non indicato'}\n"
            f"Pagina di origine: {payload.source_page}\n\n"
            f"Messaggio:\n{payload.message}"
        ),
        "assigned_to": "lead_generation",
        "requested_by": "website_contact_form",
        "status": "pending",
        "priority": 2,
        "input_data": {
            "lead_id": lead_id,
            "source": "website_contact_form",
            "contact": {
                "name": payload.name,
                "email": payload.email,
                "company_role": payload.company_role,
                "sector": payload.sector,
            },
            "message": payload.message,
        },
        "created_at": now_iso,
        "updated_at": now_iso,
    }

    log_row = {
        "agent": "lead_generation",
        "task_id": task_id,
        "action": "Nuovo lead acquisito dal sito",
        "input_summary": f"{payload.name} · {payload.email}",
        "output_summary": (payload.message[:220] + "…") if len(payload.message) > 220 else payload.message,
        "status": "pending",
        "created_at": now_iso,
    }

    try:
        client.table("pipeline_leads").insert(pipeline_row).execute()
        client.table("tasks").insert(task_row).execute()
        client.table("agent_logs").insert(log_row).execute()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Non sono riuscito a registrare la richiesta nel board",
        ) from exc

    asyncio.create_task(_dispatch_contact_internal_analysis(payload))
    asyncio.create_task(
        send_confirmation_email(
            to_email=payload.email,
            name=payload.name,
            company_role=payload.company_role or None,
            message=payload.message,
        )
    )

    return {"ok": True, "lead_id": lead_id, "task_id": task_id}


def _notify_new_contact(payload: "ContactIntakePayload") -> None:
    company_line = f"Azienda: {payload.company_role}" if payload.company_role else ""
    sector_line = f"Settore: {payload.sector}" if payload.sector else ""
    details = "\n".join(filter(None, [company_line, sector_line]))
    parts = [
        "Nuovo contatto dal sito",
        "",
        f"Nome: {payload.name}",
        f"Email: {payload.email}",
    ]
    if details:
        parts.append(details)
    parts += ["", "Messaggio:", payload.message]
    if payload.internal_context:
        parts += ["", "─" * 40, "Contesto K-BOT:", payload.internal_context]
    text = "\n".join(parts).strip()
    notify_sync(send_long_message(markdown_to_telegram_html(text), parse_mode="HTML"))


@router.post("/kbot-chat")
async def create_kbot_chat_turn(request: Request):
    try:
        body = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payload JSON non valido") from exc

    try:
        payload = KBotChatPayload.model_validate(body)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Dati chat non validi") from exc

    task_id = _upsert_kbot_task(payload, request)

    try:
        assistant_message, model_name = _generate_kbot_reply(payload.messages)
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning(f"Errore generazione risposta K-BOT {payload.session_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="K-BOT non riesce a rispondere in questo momento",
        ) from exc

    _log_kbot_turn(payload, assistant_message, model_name, task_id)

    return {
        "ok": True,
        "session_id": payload.session_id,
        "message": assistant_message,
    }
