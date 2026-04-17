import json
import re
import shutil
import unicodedata
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

from loguru import logger
from openai import OpenAI

from core.approval import approve, reject
from core.config import settings
from core.conversation import build_agent_conversation_context
from core.memory import invalidate_memory_cache, set_memory
from core.text import markdown_to_plain_text, truncate_text
from db.client import get_service_client
from db.models import AgentName
from interfaces.telegram.presentation import clean_preview, sanitize_user_error_message, visible_agent_label

DEFAULT_PROJECT_PHASES = ["Discovery", "Implementazione", "Test", "Consegna"]
UPLOADS_DIR = Path(__file__).resolve().parents[2] / "uploads"
DELETE_WORDS = ("elimina", "cancella", "rimuovi", "butta", "togli")
LIST_WORDS = ("lista", "mostra", "fammi vedere", "quali", "che", "dammi", "vedi")
CONFIRM_WORDS = {"conferma", "procedi", "si", "sì", "ok", "vai"}
CANCEL_WORDS = {"annulla", "stop", "no", "lascia perdere"}
GREETING_WORDS = {"ciao", "salve", "buongiorno", "buonasera", "hey", "hello", "hi", "hola"}

_openai_client: OpenAI | None = None
OBJECTIVE_HINTS = (
    "creare",
    "costruire",
    "sviluppare",
    "realizzare",
    "impostare",
    "automatizzare",
    "ottimizzare",
    "organizzare",
    "preparare",
    "scrivere",
    "analizzare",
    "generare",
    "trovare",
    "definire",
    "pianificare",
)


@dataclass
class AssistantResponse:
    text: str
    delegate: str | None = None
    pending_action: dict[str, Any] | None = None
    activate_agent_chat: str | None = None


def confirm_word(text: str) -> bool:
    return _normalize(text).strip() in CONFIRM_WORDS


def cancel_word(text: str) -> bool:
    return _normalize(text).strip() in CANCEL_WORDS


def handle_text_message(text: str) -> AssistantResponse:
    action = _heuristic_action(text) or _llm_action(text) or {"action": "quick_chat", "message": text}
    return execute_action(action)


def operational_shortcut(text: str) -> dict[str, Any] | None:
    """
    Intercetta solo i comandi operativi espliciti e non ambigui.
    Restituisce None per tutto il resto — il messaggio andrà a Giuseppina.
    NON gestisce: quick_chat, run_objective, run_agent, greetings.
    """
    lowered = _normalize(text)
    if not lowered:
        return {"action": "help"}

    if _contains_any(lowered, ("che lavori ci sono", "quali lavori ci sono", "quali commesse", "quali progetti",
                               "lista lavori", "lista commesse", "lista progetti", "mostra lavori",
                               "mostra le commesse", "fammi vedere i lavori", "fammi vedere le commesse")):
        return {"action": "list_projects"}

    if _contains_any(lowered, ("stato board", "come siamo messi", "situazione generale", "status board", "stato generale")):
        return {"action": "status"}

    if ("draft" in lowered or "approvaz" in lowered):
        if _contains_any(lowered, list(LIST_WORDS) + ["quanti"]):
            return {"action": "list_approvals"}
        if "approva" in lowered:
            approval_id = _extract_approval_id(text)
            return {"action": "approve_approval", "target_id": approval_id, "latest": approval_id is None}
        if "rifiuta" in lowered or "rigetta" in lowered:
            approval_id = _extract_approval_id(text)
            return {"action": "reject_approval", "target_id": approval_id, "latest": approval_id is None}

    if "log" in lowered and _contains_any(lowered, list(LIST_WORDS) + ["ultimi", "recenti"]):
        return {"action": "list_logs"}

    if "pipeline" in lowered and _contains_any(lowered, list(LIST_WORDS) + ["stato"]):
        return {"action": "list_pipeline"}

    if "memoria" in lowered and _contains_any(lowered, list(LIST_WORDS)):
        return {"action": "list_memory"}

    return None


def execute_pending_action(action: dict[str, Any]) -> AssistantResponse:
    return execute_action(action, confirmed=True)


def execute_action(action: dict[str, Any], confirmed: bool = False) -> AssistantResponse:
    action_name = (action.get("action") or "").strip()
    if not action_name:
        return _unknown_response()

    if action_name == "quick_chat":
        message = action.get("message") or ""
        return _quick_chat_response(message)
    if action_name == "status":
        return AssistantResponse("", delegate="status")
    if action_name == "list_approvals":
        return AssistantResponse("", delegate="approvals")
    if action_name == "list_logs":
        return AssistantResponse("", delegate="log")
    if action_name == "list_memory":
        return AssistantResponse("", delegate="memory")
    if action_name == "list_pipeline":
        return AssistantResponse("", delegate="pipeline")
    if action_name == "help":
        return AssistantResponse("", delegate="help")

    handlers = {
        "list_projects": _list_projects,
        "get_project": _get_project,
        "create_project": _create_project,
        "delete_project": _delete_project,
        "add_project_task": _add_project_task,
        "complete_project_task": _complete_project_task,
        "list_leads": _list_leads,
        "create_lead": _create_lead,
        "delete_lead": _delete_lead,
        "approve_approval": _approve_approval,
        "reject_approval": _reject_approval,
        "set_memory": _set_memory_action,
        "delete_memory": _delete_memory_action,
        "run_agent": _run_agent_action,
        "run_objective": _run_objective_action,
    }
    handler = handlers.get(action_name)
    if not handler:
        return _unknown_response()

    try:
        return handler(action, confirmed=confirmed)
    except Exception as exc:
        logger.exception(f"Errore azione Telegram assistant {action_name}: {exc}")
        return AssistantResponse(sanitize_user_error_message(exc))


def _normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_only = "".join(char for char in normalized if not unicodedata.combining(char))
    return ascii_only.lower().strip()


def _contains_any(text: str, items: tuple[str, ...]) -> bool:
    return any(item in text for item in items)


def _extract_after_keywords(text: str, keywords: tuple[str, ...]) -> str | None:
    for keyword in keywords:
        pattern = re.compile(rf"{keyword}\s+(?:il|la|lo|l'|di|del|della|dei|delle)?\s*(.+)$", re.IGNORECASE)
        match = pattern.search(text)
        if match:
            value = match.group(1).strip(" .,:;!?\"'")
            if value:
                return value
    return None


def _shorten_preview(value: Any, length: int = 160) -> str:
    return clean_preview(value, max_len=length)


def _parse_iso_date(value: Any) -> str | None:
    if not value:
        return None
    text = str(value).strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        return text
    return None


def _heuristic_action(text: str) -> dict[str, Any] | None:
    lowered = _normalize(text)

    if not lowered:
        return {"action": "help"}

    # Saluti e messaggi conversazionali brevi → risposta diretta senza agente
    words = lowered.split()
    if len(words) <= 3 and (words[0] in GREETING_WORDS or len(words) <= 1):
        return {"action": "quick_chat", "message": text}

    if _contains_any(lowered, ("che lavori ci sono", "quali lavori ci sono", "quali commesse", "quali progetti", "lista lavori", "lista commesse", "lista progetti", "mostra lavori", "mostra le commesse", "fammi vedere i lavori", "fammi vedere le commesse")):
        return {"action": "list_projects"}

    if _contains_any(lowered, ("stato board", "come siamo messi", "situazione generale", "status board", "stato generale")):
        return {"action": "status"}

    if "draft" in lowered or "approvaz" in lowered:
        if _contains_any(lowered, LIST_WORDS) or "quanti" in lowered:
            return {"action": "list_approvals"}
        if "approva" in lowered:
            approval_id = _extract_approval_id(text)
            return {"action": "approve_approval", "target_id": approval_id, "latest": approval_id is None}
        if "rifiuta" in lowered or "rigetta" in lowered:
            approval_id = _extract_approval_id(text)
            return {"action": "reject_approval", "target_id": approval_id, "latest": approval_id is None}

    if "log" in lowered and _contains_any(lowered, LIST_WORDS + ("ultimi", "recenti")):
        return {"action": "list_logs"}

    if "memoria" in lowered:
        if _contains_any(lowered, DELETE_WORDS):
            return {
                "action": "delete_memory",
                "target_name": _extract_after_keywords(text, ("memoria", "chiave", "key")),
            }
        if _contains_any(lowered, ("salva in memoria", "aggiorna memoria", "imposta memoria", "setta memoria")):
            return {"action": "set_memory", "parameters": {"raw_text": text}}
        return {"action": "list_memory"}

    if "pipeline" in lowered and _contains_any(lowered, LIST_WORDS + ("stato",)):
        return {"action": "list_pipeline"}

    if "lead" in lowered or "prospect" in lowered:
        if _contains_any(lowered, DELETE_WORDS):
            return {"action": "delete_lead", "target_name": _extract_after_keywords(text, ("lead", "prospect", "azienda"))}
        if _contains_any(lowered, ("crea lead", "nuovo lead", "aggiungi lead", "crea prospect", "aggiungi prospect")):
            return {"action": "create_lead", "parameters": {"raw_text": text}}
        if _contains_any(lowered, LIST_WORDS + ("quanti",)):
            return {"action": "list_leads"}

    if _contains_any(lowered, ("commessa", "commesse", "progetto", "progetti", "lavoro", "lavori")):
        if _contains_any(lowered, DELETE_WORDS):
            return {"action": "delete_project", "target_name": _extract_after_keywords(text, ("commessa", "progetto", "lavoro"))}
        if _contains_any(lowered, ("crea commessa", "nuova commessa", "crea progetto", "nuovo progetto", "aggiungi progetto", "aggiungi commessa")):
            return {"action": "create_project", "parameters": {"raw_text": text}}
        if _contains_any(lowered, ("aggiungi task", "crea task", "nuovo task")):
            return {"action": "add_project_task", "parameters": {"raw_text": text}}
        if _contains_any(lowered, ("completa task", "segna completato", "chiudi task")):
            return {"action": "complete_project_task", "parameters": {"raw_text": text}}
        if _contains_any(lowered, LIST_WORDS + ("stato", "dettagli")):
            return {"action": "get_project", "target_name": _extract_after_keywords(text, ("commessa", "progetto", "lavoro"))}

    resolved_agent = _resolve_agent_from_text(lowered)
    if resolved_agent and _contains_any(lowered, ("chiedi a", "usa", "fai lavorare", "esegui", "lancia")):
        return {"action": "run_agent", "agent_name": resolved_agent.value, "parameters": {"task": text}}

    if len(text.split()) >= 5 and any(mark in lowered for mark in OBJECTIVE_HINTS):
        return {"action": "run_objective", "parameters": {"objective": text}}

    return None


def _llm_action(text: str) -> dict[str, Any] | None:
    if not settings.openai_api_key.strip():
        return None

    prompt = (
        "Sei il router del bot Telegram di AI Board. "
        "Leggi la richiesta in italiano e restituisci SOLO JSON valido senza testo extra.\n"
        "Azioni supportate: "
        "status, list_projects, get_project, create_project, delete_project, add_project_task, complete_project_task, "
        "list_leads, create_lead, delete_lead, list_approvals, approve_approval, reject_approval, "
        "list_memory, set_memory, delete_memory, list_logs, list_pipeline, run_agent, run_objective, help, unknown.\n"
        "Campi ammessi nel JSON: action, target_name, target_id, agent_name, latest, notes, parameters.\n"
        "parameters può contenere: name, client_name, sector, offer_type, value_eur, start_date, end_date_estimated, "
        "title, due_date, company, pain_point, channel, key, value, category, task, objective.\n"
        "Regole: "
        "1) se l'utente chiede i lavori/progetti/commesse usa list_projects o get_project; "
        "2) se chiede di cancellare qualcosa usa delete_*; "
        "3) se chiede uno stato generale usa status; "
        "4) se chiede di far lavorare un agente usa run_agent; "
        "5) se esprime un obiettivo operativo concreto e dettagliato (minimo 8 parole con verbo d'azione) usa run_objective; "
        "6) se è un saluto, domanda generica, chiacchiera o messaggio breve usa unknown; "
        "7) se mancano dati obbligatori lascia i campi vuoti ma scegli comunque l'azione migliore. "
        "8) per run_objective usa SOLO parameters.objective con il testo integrale della richiesta, non usare title o altri campi. "
        "9) non inventare date, budget, KPI o altri valori se non sono esplicitamente presenti."
    )

    try:
        response = _get_openai_client().chat.completions.create(
            model=settings.default_openai_mini_model or settings.default_openai_model,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": text},
            ],
        )
        content = response.choices[0].message.content or "{}"
        payload = json.loads(content)
        if isinstance(payload, dict) and payload.get("action"):
            return payload
    except Exception as exc:
        logger.warning(f"Router LLM Telegram non disponibile: {exc}")
    return None


def _get_openai_client() -> OpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(api_key=settings.openai_api_key)
    return _openai_client


def _extract_approval_id(text: str) -> str | None:
    match = re.search(r"\b([0-9a-f]{8,36})\b", text, flags=re.IGNORECASE)
    if match:
        return match.group(1)
    return None


def _resolve_agent_from_text(normalized_text: str) -> AgentName | None:
    mapping = {
        "orchestrator": AgentName.ORCHESTRATOR,
        "orchestratore": AgentName.ORCHESTRATOR,
        "chief_of_staff": AgentName.CHIEF_OF_STAFF,
        "chief of staff": AgentName.CHIEF_OF_STAFF,
        "staff": AgentName.CHIEF_OF_STAFF,
        "content_engine": AgentName.CONTENT_ENGINE,
        "content engine": AgentName.CONTENT_ENGINE,
        "contenuti": AgentName.CONTENT_ENGINE,
        "marketing": AgentName.CONTENT_ENGINE,
        "sales_enablement": AgentName.SALES_ENABLEMENT,
        "sales enablement": AgentName.SALES_ENABLEMENT,
        "commerciale": AgentName.SALES_ENABLEMENT,
        "vendite": AgentName.SALES_ENABLEMENT,
        "lead generation": AgentName.SALES_ENABLEMENT,
        "solution_architect": AgentName.SOLUTION_ARCHITECT,
        "solution architect": AgentName.SOLUTION_ARCHITECT,
        "architetto": AgentName.SOLUTION_ARCHITECT,
        "finance": AgentName.FINANCE_KPI,
        "kpi": AgentName.FINANCE_KPI,
        "finanza": AgentName.FINANCE_KPI,
    }
    for key, agent in mapping.items():
        if key in normalized_text:
            return _canonical_agent(agent)
    return None


def _client():
    return get_service_client()


def _list_projects(action: dict[str, Any], confirmed: bool = False) -> AssistantResponse:
    projects = (
        _client()
        .table("projects")
        .select("id,name,client_name,status,progress_pct,offer_type,created_at")
        .order("created_at", desc=True)
        .limit(8)
        .execute()
        .data
        or []
    )
    if not projects:
        return AssistantResponse("Non ci sono ancora commesse attive nella dashboard.")

    lines = ["Queste sono le commesse presenti:\n"]
    for item in projects:
        client_name = item.get("client_name") or "Interno"
        status = item.get("status") or "active"
        progress = item.get("progress_pct") or 0
        lines.append(
            f"• {item.get('name')} — cliente: {client_name} — stato: {status} — avanzamento: {progress}%"
        )
    return AssistantResponse("\n".join(lines))


def _get_project(action: dict[str, Any], confirmed: bool = False) -> AssistantResponse:
    target = action.get("target_name") or action.get("target_id") or ""
    match = _find_project(target)
    if not match:
        return AssistantResponse("Non ho trovato la commessa richiesta. Dimmi il nome esatto o una parte del nome.")

    project = (
        _client()
        .table("projects")
        .select("*")
        .eq("id", match["id"])
        .single()
        .execute()
        .data
    )
    phases = (
        _client()
        .table("project_phases")
        .select("name,status")
        .eq("project_id", match["id"])
        .order("phase_order")
        .execute()
        .data
        or []
    )
    tasks = (
        _client()
        .table("project_tasks")
        .select("title,status")
        .eq("project_id", match["id"])
        .order("due_date")
        .limit(6)
        .execute()
        .data
        or []
    )
    documents = (
        _client()
        .table("project_documents")
        .select("id")
        .eq("project_id", match["id"])
        .execute()
        .data
        or []
    )

    phase_line = ", ".join(f"{item['name']}: {item['status']}" for item in phases) or "nessuna fase"
    task_line = ", ".join(f"{item['title']} [{item['status']}]" for item in tasks) or "nessun task"
    text = (
        f"Commessa: {project.get('name')}\n"
        f"Cliente: {project.get('client_name') or 'Interno'}\n"
        f"Settore: {project.get('sector') or '—'}\n"
        f"Offerta: {project.get('offer_type') or '—'}\n"
        f"Stato: {project.get('status') or 'active'}\n"
        f"Avanzamento: {project.get('progress_pct') or 0}%\n"
        f"Fasi: {phase_line}\n"
        f"Task: {task_line}\n"
        f"Documenti: {len(documents)}"
    )
    return AssistantResponse(text)


def _create_project(action: dict[str, Any], confirmed: bool = False) -> AssistantResponse:
    params = dict(action.get("parameters") or {})
    raw_text = params.pop("raw_text", "")
    if raw_text:
        llm_params = _extract_project_fields_with_llm(raw_text)
        params = {**llm_params, **params}

    name = params.get("name") or action.get("target_name")
    if not name:
        return AssistantResponse("Per creare una commessa mi serve almeno il nome. Esempio: crea commessa AI Workflow Setup per Studio Rossi.")

    payload = {
        "name": name,
        "client_name": params.get("client_name") or None,
        "sector": params.get("sector") or None,
        "offer_type": params.get("offer_type") or None,
        "value_eur": _safe_int(params.get("value_eur")),
        "start_date": _parse_iso_date(params.get("start_date")),
        "end_date_estimated": _parse_iso_date(params.get("end_date_estimated")),
        "status": "active",
    }
    client = _client()
    response = client.table("projects").insert(payload).execute()
    project = (response.data or [None])[0]
    if not project:
        return AssistantResponse("Non sono riuscito a creare la commessa.")

    client.table("project_phases").insert(
        [{"project_id": project["id"], "name": phase_name, "phase_order": index} for index, phase_name in enumerate(DEFAULT_PROJECT_PHASES, start=1)]
    ).execute()

    return AssistantResponse(
        f"Commessa creata con successo.\nNome: {project['name']}\nCliente: {project.get('client_name') or 'Interno'}\nID: {project['id'][:8]}..."
    )


def _delete_project(action: dict[str, Any], confirmed: bool = False) -> AssistantResponse:
    target = action.get("target_name") or action.get("target_id") or ""
    match = _find_project(target)
    if not match:
        return AssistantResponse("Non ho trovato la commessa da eliminare.")

    if not confirmed:
        return AssistantResponse(
            f"Sto per eliminare la commessa '{match['name']}'. Scrivi CONFERMA per procedere oppure ANNULLA.",
            pending_action={"action": "delete_project", "target_id": match["id"], "target_name": match["name"]},
        )

    project_id = match["id"]
    project_dir = UPLOADS_DIR / project_id
    if project_dir.exists():
        shutil.rmtree(project_dir, ignore_errors=True)

    client = _client()
    client.table("approvals").delete().eq("project_id", project_id).execute()
    client.table("agent_logs").delete().eq("project_id", project_id).execute()
    client.table("project_documents").delete().eq("project_id", project_id).execute()
    client.table("projects").delete().eq("id", project_id).execute()
    return AssistantResponse(f"Commessa eliminata: {match['name']}")


def _add_project_task(action: dict[str, Any], confirmed: bool = False) -> AssistantResponse:
    params = dict(action.get("parameters") or {})
    raw_text = params.pop("raw_text", "")
    if raw_text:
        llm_params = _extract_project_task_fields_with_llm(raw_text)
        params = {**llm_params, **params}

    project_match = _find_project(params.get("project_name") or action.get("target_name") or "")
    if not project_match:
        return AssistantResponse("Non ho capito a quale commessa aggiungere il task.")
    title = params.get("title")
    if not title:
        return AssistantResponse("Per aggiungere un task mi serve il titolo del task.")

    _client().table("project_tasks").insert(
        {
            "project_id": project_match["id"],
            "title": title,
            "due_date": _parse_iso_date(params.get("due_date")),
            "status": "pending",
        }
    ).execute()
    return AssistantResponse(f"Task aggiunto alla commessa '{project_match['name']}': {title}")


def _complete_project_task(action: dict[str, Any], confirmed: bool = False) -> AssistantResponse:
    params = dict(action.get("parameters") or {})
    raw_text = params.pop("raw_text", "")
    if raw_text:
        llm_params = _extract_project_task_fields_with_llm(raw_text)
        params = {**llm_params, **params}

    project_match = _find_project(params.get("project_name") or action.get("target_name") or "")
    if not project_match:
        return AssistantResponse("Non ho trovato la commessa del task da completare.")

    task_match = _find_project_task(project_match["id"], params.get("title") or params.get("task_title") or params.get("task_id") or "")
    if not task_match:
        return AssistantResponse("Non ho trovato il task da segnare come completato.")

    _client().table("project_tasks").update(
        {"status": "completed", "completed_at": datetime.now(UTC).isoformat()}
    ).eq("id", task_match["id"]).execute()
    return AssistantResponse(f"Task completato in '{project_match['name']}': {task_match['title']}")


def _list_leads(action: dict[str, Any], confirmed: bool = False) -> AssistantResponse:
    leads = (
        _client()
        .table("pipeline_leads")
        .select("id,name,company,status,score,next_action")
        .order("score", desc=True)
        .limit(8)
        .execute()
        .data
        or []
    )
    if not leads:
        return AssistantResponse("La pipeline è vuota.")

    lines = ["Questi sono i lead attuali:\n"]
    for item in leads:
        label = item.get("company") or item.get("name")
        lines.append(
            f"• {label} — stato: {item.get('status') or 'identified'} — score: {item.get('score') or '—'} — next: {item.get('next_action') or '—'}"
        )
    return AssistantResponse("\n".join(lines))


def _create_lead(action: dict[str, Any], confirmed: bool = False) -> AssistantResponse:
    params = dict(action.get("parameters") or {})
    raw_text = params.pop("raw_text", "")
    if raw_text:
        llm_params = _extract_lead_fields_with_llm(raw_text)
        params = {**llm_params, **params}

    name = params.get("name") or params.get("company") or action.get("target_name")
    if not name:
        return AssistantResponse("Per creare un lead mi serve almeno il nome dell'azienda o del contatto.")

    payload = {
        "name": params.get("name") or name,
        "company": params.get("company") or name,
        "sector": params.get("sector") or None,
        "pain_point": params.get("pain_point") or None,
        "channel": params.get("channel") or None,
        "status": "identified",
        "score": _safe_int(params.get("score")) or 5,
        "next_action": params.get("next_action") or "Qualifica iniziale",
        "next_action_date": _parse_iso_date(params.get("next_action_date")) or (date.today() + timedelta(days=2)).isoformat(),
    }
    response = _client().table("pipeline_leads").insert(payload).execute()
    lead = (response.data or [None])[0]
    if not lead:
        return AssistantResponse("Non sono riuscito a creare il lead.")

    return AssistantResponse(
        f"Lead creato.\nAzienda: {lead.get('company') or lead.get('name')}\nSettore: {lead.get('sector') or '—'}\nStato: {lead.get('status')}"
    )


def _delete_lead(action: dict[str, Any], confirmed: bool = False) -> AssistantResponse:
    target = action.get("target_name") or action.get("target_id") or ""
    match = _find_lead(target)
    if not match:
        return AssistantResponse("Non ho trovato il lead da eliminare.")

    if not confirmed:
        label = match.get("company") or match.get("name")
        return AssistantResponse(
            f"Sto per eliminare il lead '{label}'. Scrivi CONFERMA per procedere oppure ANNULLA.",
            pending_action={"action": "delete_lead", "target_id": match["id"], "target_name": label},
        )

    _client().table("pipeline_leads").delete().eq("id", match["id"]).execute()
    return AssistantResponse(f"Lead eliminato: {match.get('company') or match.get('name')}")


def _approve_approval(action: dict[str, Any], confirmed: bool = False) -> AssistantResponse:
    approval_row = _resolve_approval(action.get("target_id"), latest=bool(action.get("latest")))
    if not approval_row:
        return AssistantResponse("Non ho trovato il draft da approvare.")
    notes = action.get("notes")
    if approve(approval_row["id"], notes):
        return AssistantResponse(
            f"Draft approvato.\nArea: {visible_agent_label(approval_row.get('agent'))}"
        )
    return AssistantResponse("Non sono riuscito ad approvare il draft.")


def _reject_approval(action: dict[str, Any], confirmed: bool = False) -> AssistantResponse:
    approval_row = _resolve_approval(action.get("target_id"), latest=bool(action.get("latest")))
    if not approval_row:
        return AssistantResponse("Non ho trovato il draft da rifiutare.")
    notes = action.get("notes")
    if reject(approval_row["id"], notes):
        return AssistantResponse(
            f"Draft rifiutato.\nArea: {visible_agent_label(approval_row.get('agent'))}"
        )
    return AssistantResponse("Non sono riuscito a rifiutare il draft.")


def _set_memory_action(action: dict[str, Any], confirmed: bool = False) -> AssistantResponse:
    params = dict(action.get("parameters") or {})
    raw_text = params.get("raw_text", "")
    if raw_text and not params.get("key"):
        parsed = _extract_memory_fields_with_llm(raw_text)
        params = {**parsed, **params}

    key = params.get("key") or action.get("target_name")
    value = params.get("value")
    category = params.get("category") or (key.split(".")[0] if key and "." in key else "custom")
    if not key or value in (None, ""):
        return AssistantResponse("Per aggiornare la memoria mi servono almeno chiave e valore.")

    set_memory(key, value, category=category, updated_by="telegram_bot")
    return AssistantResponse(f"Memoria aggiornata:\n{key} = {value}")


def _delete_memory_action(action: dict[str, Any], confirmed: bool = False) -> AssistantResponse:
    key = action.get("target_name") or action.get("target_id")
    if not key:
        return AssistantResponse("Indicami la chiave memoria da eliminare.")

    match = _find_memory_key(key)
    if not match:
        return AssistantResponse("Non ho trovato la chiave memoria richiesta.")

    if not confirmed:
        return AssistantResponse(
            f"Sto per eliminare la chiave memoria '{match}'. Scrivi CONFERMA per procedere oppure ANNULLA.",
            pending_action={"action": "delete_memory", "target_name": match},
        )

    _client().table("shared_memory").delete().eq("key", match).execute()
    invalidate_memory_cache()
    return AssistantResponse(f"Chiave memoria eliminata: {match}")


def _run_agent_action(action: dict[str, Any], confirmed: bool = False) -> AssistantResponse:
    agent_name = _resolve_agent_identifier(action.get("agent_name"))
    if not agent_name:
        return AssistantResponse("Non ho riconosciuto l'agente richiesto.")

    task = (action.get("parameters") or {}).get("task") or action.get("target_name")
    if not task:
        return AssistantResponse("Indicami il task da eseguire per l'agente.")

    chat_context = {
        "chat_history": build_agent_conversation_context(agent_name, limit=12),
        "interface": "telegram",
        "channel": "telegram_agent_chat",
        "__board": {
            "content_type": "telegram_agent_chat",
            "requested_by": "telegram_agent_chat",
        },
    }
    result = _run_agent(agent_name, task, chat_context)
    if result.get("status") == "error":
        return AssistantResponse(sanitize_user_error_message(result.get("error")))

    preview = _shorten_preview(result.get("output"), 700)
    return AssistantResponse(
        f"Bozza pronta da {visible_agent_label(agent_name)}.\nStato: {result.get('status')}\n\n{preview}",
        activate_agent_chat=agent_name.value,
    )


def _run_objective_action(action: dict[str, Any], confirmed: bool = False) -> AssistantResponse:
    params = dict(action.get("parameters") or {})
    objective = (
        params.get("objective")
        or params.get("title")
        or params.get("request")
        or params.get("task")
        or action.get("target_name")
    )
    if not objective:
        return AssistantResponse("Descrivimi meglio l'obiettivo da passare a Giuseppina.")

    result = _run_objective(objective)
    if result.get("status") == "error":
        return AssistantResponse(sanitize_user_error_message(result.get("error")))

    preview = _shorten_preview(result.get("output"), 700)
    return AssistantResponse(
        f"Obiettivo preso in carico da Giuseppina.\n\n{preview}"
    )


def _quick_chat_response(text: str) -> AssistantResponse:
    """Risposta conversazionale diretta via LLM, senza creare task o approvazioni."""
    if not settings.openai_api_key.strip():
        return AssistantResponse("Pronto. Di cosa hai bisogno?")
    try:
        response = _get_openai_client().chat.completions.create(
            model=settings.default_openai_mini_model or settings.default_openai_model,
            temperature=0.7,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Sei K-AI, assistente del board AI di un business di consulenza. "
                        "Rispondi in italiano in modo diretto e conciso. "
                        "Se è un saluto, rispondi con un saluto breve e chiedi come puoi aiutare. "
                        "Non generare documenti né output strutturati a meno che non sia esplicitamente richiesto. "
                        "Parla come un collega di lavoro esperto, non come un assistente formale."
                    ),
                },
                {"role": "user", "content": text or "ciao"},
            ],
        )
        reply = response.choices[0].message.content or "Pronto."
        return AssistantResponse(reply)
    except Exception as exc:
        logger.warning(f"Quick chat fallita: {exc}")
        return AssistantResponse("Pronto. Di cosa hai bisogno?")


def _unknown_response() -> AssistantResponse:
    return AssistantResponse(
        "Non ho capito bene l'azione richiesta.\n"
        "Puoi scrivermi frasi come:\n"
        "• che lavori ci sono?\n"
        "• crea commessa AI Workflow Setup per Studio Rossi\n"
        "• elimina il lead Lux Fashion Group\n"
        "• fammi vedere i draft\n"
        "• approva l'ultimo draft\n"
        "• aggiorna memoria business.mission = ...\n"
        "• usa content engine per scrivere un post LinkedIn sul case study del sito"
    )


def _resolve_agent_identifier(value: Any) -> AgentName | None:
    if not value:
        return None
    text = str(value).strip()
    try:
        return _canonical_agent(AgentName(text))
    except Exception:
        pass
    return _resolve_agent_from_text(_normalize(text))


def _canonical_agent(agent: AgentName) -> AgentName:
    from core.orchestrator import resolve_agent_name

    return resolve_agent_name(agent)


def _run_agent(agent: AgentName, task: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    from core.orchestrator import run_agent

    return run_agent(agent, task, context)


def _run_objective(objective: str) -> dict[str, Any]:
    from core.orchestrator import run_objective

    return run_objective(objective)


def _find_project(query: str) -> dict[str, Any] | None:
    rows = (
        _client()
        .table("projects")
        .select("id,name,client_name,status,progress_pct")
        .order("created_at", desc=True)
        .limit(50)
        .execute()
        .data
        or []
    )
    return _find_best_match(rows, query, ("name", "client_name"))


def _find_lead(query: str) -> dict[str, Any] | None:
    rows = (
        _client()
        .table("pipeline_leads")
        .select("id,name,company,status,score")
        .order("created_at", desc=True)
        .limit(50)
        .execute()
        .data
        or []
    )
    return _find_best_match(rows, query, ("company", "name"))


def _find_project_task(project_id: str, query: str) -> dict[str, Any] | None:
    rows = (
        _client()
        .table("project_tasks")
        .select("id,title,status")
        .eq("project_id", project_id)
        .order("due_date")
        .execute()
        .data
        or []
    )
    return _find_best_match(rows, query, ("title",))


def _resolve_approval(target_id: str | None, latest: bool = False) -> dict[str, Any] | None:
    rows = (
        _client()
        .table("approvals")
        .select("id,agent,status,created_at,content_preview")
        .in_("status", ["draft", "review"])
        .order("created_at", desc=True)
        .limit(20)
        .execute()
        .data
        or []
    )
    if not rows:
        return None
    if latest or not target_id:
        return rows[0]
    target = str(target_id).lower()
    for item in rows:
        if str(item.get("id", "")).lower().startswith(target):
            return item
    return None


def _find_memory_key(query: str) -> str | None:
    rows = _client().table("shared_memory").select("key").execute().data or []
    best = _find_best_match(rows, query, ("key",))
    return best.get("key") if best else None


def _find_best_match(rows: list[dict[str, Any]], query: str, fields: tuple[str, ...]) -> dict[str, Any] | None:
    if not rows:
        return None
    cleaned_query = _normalize(query)
    if not cleaned_query:
        return None

    best_score = 0.0
    best_row = None
    for row in rows:
        haystack = " ".join(str(row.get(field) or "") for field in fields)
        normalized = _normalize(haystack)
        if cleaned_query in normalized:
            score = 1.0
        else:
            tokens = set(cleaned_query.split())
            token_hits = sum(1 for token in tokens if token and token in normalized)
            score = token_hits / max(len(tokens), 1)
        if score > best_score:
            best_score = score
            best_row = row
    return best_row if best_score >= 0.34 else None


def _safe_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(str(value).replace(".", "").replace(",", "").strip())
    except Exception:
        return None


def _extract_project_fields_with_llm(text: str) -> dict[str, Any]:
    return _extract_fields_with_llm(
        text,
        "Estrai i campi per creare una commessa. Restituisci JSON con: name, client_name, sector, offer_type, value_eur, start_date, end_date_estimated.",
    )


def _extract_lead_fields_with_llm(text: str) -> dict[str, Any]:
    return _extract_fields_with_llm(
        text,
        "Estrai i campi per creare un lead. Restituisci JSON con: name, company, sector, pain_point, channel, score, next_action, next_action_date.",
    )


def _extract_memory_fields_with_llm(text: str) -> dict[str, Any]:
    return _extract_fields_with_llm(
        text,
        "Estrai i campi per aggiornare la memoria. Restituisci JSON con: key, value, category.",
    )


def _extract_project_task_fields_with_llm(text: str) -> dict[str, Any]:
    return _extract_fields_with_llm(
        text,
        "Estrai i campi per gestire un task di progetto. Restituisci JSON con: project_name, title, task_title, due_date.",
    )


def _extract_fields_with_llm(text: str, instruction: str) -> dict[str, Any]:
    if not settings.openai_api_key.strip():
        return {}
    try:
        response = _get_openai_client().chat.completions.create(
            model=settings.default_openai_mini_model or settings.default_openai_model,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": instruction + " Se un campo manca, usa stringa vuota.",
                },
                {"role": "user", "content": text},
            ],
        )
        content = response.choices[0].message.content or "{}"
        payload = json.loads(content)
        return payload if isinstance(payload, dict) else {}
    except Exception as exc:
        logger.warning(f"Estrazione campi Telegram assistant non disponibile: {exc}")
        return {}
