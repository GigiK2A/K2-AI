import asyncio
import json
import uuid
from datetime import UTC, datetime
from functools import partial
from io import BytesIO
from pathlib import Path
from typing import Any, Callable

from loguru import logger
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from core.action_guard import cancel_pending_confirmation, has_pending_confirmation, pop_pending_confirmation
from core.rate_limit import check_dedup, check_dedup_update_id, check_rate_limit
from core.session_state import add_turn, build_context_for_agent
from core.approval import approve, get_approval, get_pending_approvals, reject
from core.business_audit import log_business_action
from core.config import settings
from core.memory import set_memory
from core.notion_tools import set_current_session
from core.orchestrator import chat_agent, run_agent, run_objective
from core.text import markdown_to_plain_text, truncate_text
from core.undo import describe_undo, execute_undo, has_undo, load_session_from_supabase, pop_undo
from db.client import get_service_client
from db.models import AgentName
from interfaces.telegram.assistant import cancel_word, confirm_word, execute_action, execute_pending_action, handle_text_message, operational_shortcut
from interfaces.telegram.keyboards import approval_keyboard
from interfaces.telegram.presentation import (
    approval_is_recent,
    clean_preview,
    sanitize_user_error_message,
    smart_truncate,
    visible_agent_label,
)

PENDING_ATTACHMENTS_KEY = "pending_telegram_attachments"
TELEGRAM_CHAT_UPLOADS_DIR = Path(__file__).resolve().parents[2] / "uploads" / "chat" / "telegram"

# ── Queue leggera per-chat ───────────────────────────────────────────────────
# Previene processing concorrente dello stesso chat_id.
# Se arrivano 2 messaggi rapidi, il secondo aspetta che il primo finisca.
_CHAT_LOCKS: dict[str, asyncio.Lock] = {}


def _get_chat_lock(chat_id: str) -> asyncio.Lock:
    if chat_id not in _CHAT_LOCKS:
        _CHAT_LOCKS[chat_id] = asyncio.Lock()
    return _CHAT_LOCKS[chat_id]

TEXT_ATTACHMENT_EXTENSIONS = {
    ".txt", ".md", ".markdown", ".csv", ".json", ".log",
    ".xml", ".html", ".htm", ".py", ".js", ".ts", ".sql",
    ".yml", ".yaml",
}

CHAT_EXIT_PHRASES = {
    "esci dalla chat",
    "chiudi chat",
    "stop chat",
    "termina chat",
    "fine chat",
}


def _extract_attachment_excerpt(filename: str, content: bytes) -> str | None:
    """Estrae testo da un allegato Telegram per passarlo all'agente."""
    suffix = Path(filename).suffix.lower()
    if suffix in TEXT_ATTACHMENT_EXTENSIONS:
        text = content.decode("utf-8", errors="ignore").strip()
        return truncate_text(text, 6000) if text else None
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader
            reader = PdfReader(BytesIO(content))
            chunks = [(page.extract_text() or "").strip() for page in reader.pages[:5]]
            text = "\n\n".join(chunk for chunk in chunks if chunk)
            return truncate_text(text, 6000) if text else None
        except Exception as exc:
            logger.warning(f"Estratto PDF non disponibile per {filename}: {exc}")
    if suffix == ".docx":
        try:
            from docx import Document as DocxDocument
            doc = DocxDocument(BytesIO(content))
            text = "\n".join(p.text.strip() for p in doc.paragraphs if p.text.strip())
            return truncate_text(text, 6000) if text else None
        except Exception as exc:
            logger.warning(f"Estratto DOCX non disponibile per {filename}: {exc}")
    return None


async def _download_telegram_file(file_obj: Any, destination: Path) -> bytes:
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        payload = await file_obj.download_as_bytearray()
        file_bytes = bytes(payload)
        destination.write_bytes(file_bytes)
        return file_bytes
    except Exception:
        await file_obj.download_to_drive(custom_path=str(destination))
        return destination.read_bytes()


async def _collect_telegram_attachments(update: Update) -> list[dict[str, Any]]:
    """Scarica e prepara gli allegati da un messaggio Telegram."""
    if not update.message:
        return []
    message = update.message
    user_id = str(update.effective_user.id) if update.effective_user else "anon"
    timestamp_dir = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    target_dir = TELEGRAM_CHAT_UPLOADS_DIR / user_id / timestamp_dir
    attachments: list[dict[str, Any]] = []

    async def _append_file(filename: str, source: Any) -> None:
        safe_name = Path(filename).name
        saved_path = target_dir / safe_name
        telegram_file = await source.get_file()
        file_bytes = await _download_telegram_file(telegram_file, saved_path)
        attachments.append({
            "name": safe_name,
            "path": str(saved_path),
            "web_path": "/uploads/" + str(saved_path.relative_to(TELEGRAM_CHAT_UPLOADS_DIR.parent.parent)).replace("\\", "/"),
            "size_bytes": len(file_bytes),
            "excerpt": _extract_attachment_excerpt(safe_name, file_bytes),
        })

    if message.document:
        filename = message.document.file_name or f"document_{message.document.file_unique_id}"
        await _append_file(filename, message.document)
    if message.photo:
        largest = message.photo[-1]
        await _append_file(f"photo_{largest.file_unique_id}.jpg", largest)

    return attachments


def _get_pending_attachments(context: ContextTypes.DEFAULT_TYPE) -> list[dict[str, Any]]:
    value = context.user_data.get(PENDING_ATTACHMENTS_KEY, [])
    return value if isinstance(value, list) else []


def _store_pending_attachments(context: ContextTypes.DEFAULT_TYPE, attachments: list[dict[str, Any]]) -> None:
    if attachments:
        context.user_data[PENDING_ATTACHMENTS_KEY] = attachments
    else:
        context.user_data.pop(PENDING_ATTACHMENTS_KEY, None)


def _pop_pending_attachments(context: ContextTypes.DEFAULT_TYPE) -> list[dict[str, Any]]:
    attachments = _get_pending_attachments(context)
    context.user_data.pop(PENDING_ATTACHMENTS_KEY, None)
    return attachments


def _classify_attachment_intent(text: str) -> str:
    """
    Determina come l'utente vuole usare l'allegato:
    - 'analyze': vuole un'analisi/estrazione dal documento
    - 'context': il documento è contesto di supporto per una domanda
    - 'execute': vuole un'azione concreta basata sul documento
    - 'unknown': nessun testo — il bot deve dedurre
    """
    if not text:
        return "unknown"
    lowered = text.lower()
    execute_hints = ("crea", "genera", "scrivi", "produci", "lancia", "esegui", "costruisci", "aggiungi", "inserisci")
    analyze_hints = ("analizza", "dimmi cosa", "cosa contiene", "cosa dice", "riassumi", "estrai", "leggi", "interpreta", "valuta")
    context_hints = ("basandoti su", "usando questo", "considera questo", "tenendo conto", "in base a", "rispetto a questo")
    if any(h in lowered for h in execute_hints):
        return "execute"
    if any(h in lowered for h in analyze_hints):
        return "analyze"
    if any(h in lowered for h in context_hints):
        return "context"
    return "unknown"


def _build_task_with_attachments(text: str, attachments: list[dict[str, Any]]) -> str:
    """
    Costruisce il testo del task includendo gli estratti degli allegati.
    Aggiunge hint esplicito su come usare il contenuto in base all'intento rilevato.
    """
    base = str(text or "").strip()
    if not attachments:
        return base or "Rispondi in modo utile e operativo."

    intent = _classify_attachment_intent(base)

    # Hint specifico per tipo di intento
    intent_hints = {
        "execute": (
            "Il fondatore ha allegato un documento e vuole che tu esegua un'azione concreta basandoti su di esso. "
            "Usa il contenuto estratto come base per l'azione richiesta, non come argomento da riassumere."
        ),
        "analyze": (
            "Il fondatore vuole un'analisi del documento allegato. "
            "Concentrati sul contenuto estratto, identifica i punti chiave, le implicazioni operative e le azioni che ne derivano."
        ),
        "context": (
            "Il documento allegato è contesto di supporto per la risposta. "
            "Usalo per rispondere in modo più preciso alla domanda del fondatore, senza fare un riassunto del documento."
        ),
        "unknown": (
            "Il fondatore ha allegato un documento senza istruzioni esplicite. "
            "Determina autonomamente se vuole un'analisi, un'azione operativa o se il documento è contesto. "
            "Se non è chiaro, chiedi direttamente."
        ),
    }

    if not base:
        base = "Analizza il documento allegato e rispondi in modo utile e operativo."

    lines = [base, "", "## Allegato ricevuto"]
    for index, item in enumerate(attachments[:4], start=1):
        name = item.get("name", "allegato")
        size = item.get("size_bytes", 0)
        size_str = f" · {size // 1024}KB" if size > 1024 else (f" · {size}B" if size else "")
        lines.append(f"**File {index}: {name}{size_str}**")
        excerpt = str(item.get("excerpt") or "").strip()
        if excerpt:
            lines.append("Contenuto estratto:")
            lines.append(truncate_text(excerpt, 2500))
        else:
            lines.append("_(contenuto non estraibile — file binario o vuoto)_")
        lines.append("")

    lines.append(f"**Istruzione:** {intent_hints[intent]}")
    return "\n".join(lines)


def _format_plan_for_telegram(output: str) -> str:
    """Converte un piano JSON dell'Orchestrator in testo leggibile."""
    try:
        plan = json.loads(output)
        if not isinstance(plan, dict) or "tasks" not in plan:
            return truncate_text(markdown_to_plain_text(output), 700)
        lines = []
        if plan.get("plan_title"):
            lines.append(f"Piano: {plan['plan_title']}")
        tasks = plan.get("tasks") or []
        lines.append(f"\n{len(tasks)} task generati:")
        for i, task in enumerate(tasks[:5], 1):
            agent = visible_agent_label(task.get("agent", "?"))
            title = str(task.get("title", ""))
            priority = task.get("priority", "")
            lines.append(f"{i}. [{agent}] {title}" + (f" (p{priority})" if priority else ""))
        return "\n".join(lines)
    except (json.JSONDecodeError, TypeError):
        return truncate_text(markdown_to_plain_text(output), 700)


async def _dispatch_plan_tasks_background(objective_output: str) -> None:
    """Esegue i task del piano dell'Orchestrator in background, uno per uno."""
    try:
        plan = json.loads(objective_output)
        tasks = plan.get("tasks") or []
    except (json.JSONDecodeError, TypeError):
        return

    from core.orchestrator import resolve_agent_name
    from interfaces.telegram.notifier import notify_sync, notify_error

    for task_item in tasks[:5]:
        agent_str = str(task_item.get("agent", "")).strip()
        title = str(task_item.get("title", "")).strip()
        description = str(task_item.get("description", "")).strip()
        inputs = task_item.get("inputs") or {}
        if not agent_str or not (title or description):
            continue
        try:
            agent_name = resolve_agent_name(AgentName(agent_str))
        except (ValueError, Exception):
            logger.warning(f"Agente non valido nel piano: {agent_str}")
            continue

        task_text = title
        if description:
            task_text += f"\n\n{description}"
        if inputs:
            try:
                task_text += f"\n\n## Input\n{json.dumps(inputs, ensure_ascii=False, indent=2)}"
            except Exception:
                pass

        try:
            result = await asyncio.to_thread(run_agent, agent_name, task_text)
            if result.get("status") == "error":
                logger.warning(f"Agente {agent_str} fallito nel piano: {result.get('error')}")
        except Exception as exc:
            logger.error(f"Errore esecuzione task piano ({agent_str}): {exc}")
            notify_sync(notify_error(agent_str, str(exc)))


def is_authorized(update: Update) -> bool:
    user = update.effective_user
    return bool(user and str(user.id) == str(settings.telegram_chat_id))


def truncate(text: str, max_len: int = 3800) -> str:
    """Converte markdown in testo piano e tronca al limite Telegram.

    Se tronca, cerca di spezzare su una riga vuota o a fine paragrafo
    per evitare frasi monche.
    """
    return smart_truncate(text, max_len=max_len, suffix="\n\n[output troncato]")


async def run_sync(func: Callable[..., Any], *args, **kwargs) -> Any:
    """Esegue una funzione sync in executor per non bloccare il bot."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, partial(func, *args, **kwargs))


async def run_agent_async(agent_name: AgentName, task: str, context: dict | None = None) -> dict:
    return await run_sync(run_agent, agent_name, task, context)


async def chat_agent_async(agent_name: AgentName, message: str, context: dict | None = None) -> str:
    return await run_sync(chat_agent, agent_name, message, context)


async def run_objective_async(objective: str) -> dict:
    return await run_sync(run_objective, objective)


def _telegram_agent_chat_context(_agent_name: AgentName) -> dict[str, Any]:
    # Niente chat_history (Giuseppina la carica autonomamente in chat()),
    # niente metadata tecnici che inquinano il prompt LLM.
    return {}


def _load_status_snapshot() -> tuple[int, list[dict], dict[str, int]]:
    client = get_service_client()
    pending = get_pending_approvals()
    tasks_resp = (
        client.table("tasks")
        .select("title,status,assigned_to,created_at")
        .order("created_at", desc=True)
        .limit(5)
        .execute()
    )
    tasks = tasks_resp.data or []

    leads_resp = client.table("pipeline_leads").select("status").execute()
    leads = leads_resp.data or []
    lead_counts: dict[str, int] = {}
    for lead in leads:
        status = lead["status"]
        lead_counts[status] = lead_counts.get(status, 0) + 1

    return len(pending), tasks, lead_counts


def _load_memory_index() -> dict[str, list[str]]:
    client = get_service_client()
    resp = client.table("shared_memory").select("key,category,updated_at").order("category").execute()
    rows = resp.data or []
    by_cat: dict[str, list[str]] = {}
    for row in rows:
        by_cat.setdefault(row["category"], []).append(row["key"])
    return by_cat


def _load_recent_logs() -> list[dict]:
    client = get_service_client()
    resp = (
        client.table("agent_logs")
        .select("agent,action,status,llm_model,duration_ms,created_at")
        .order("created_at", desc=True)
        .limit(10)
        .execute()
    )
    return resp.data or []


def _load_pipeline() -> list[dict]:
    client = get_service_client()
    resp = (
        client.table("pipeline_leads")
        .select("name,company,status,score,next_action,next_action_date")
        .order("score", desc=True)
        .execute()
    )
    return resp.data or []


def _save_approval_note(approval_id: str, note: str) -> None:
    client = get_service_client()
    client.table("approvals").update({"founder_notes": note}).eq("id", approval_id).execute()


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update) or not update.message:
        return
    context.user_data["active_agent_chat"] = AgentName.ORCHESTRATOR.value
    text = (
        "AI Board attivo. Sono Giuseppina — dimmi cosa vuoi fare.\n\n"
        "Puoi scrivermi qualsiasi obiettivo, caricare documenti o fare domande.\n"
        "Coinvolgerò i giusti agenti del board quando necessario.\n\n"
        "_Comandi rapidi:_\n"
        "/agent — parla con un agente specifico\n"
        "/approvals — draft in attesa\n"
        "/status — stato pipeline\n"
        "/help — tutti i comandi"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start_handler(update, context)


async def schedule_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /schedule - mostra i prossimi job programmati
    /schedule run <job_id> - forza l'esecuzione immediata di un job
    """
    if not is_authorized(update) or not update.message:
        return

    from core.scheduler import ROME, scheduler

    if context.args and context.args[0] == "run" and len(context.args) >= 2:
        job_id = context.args[1]
        job = scheduler.get_job(job_id)
        if not job:
            available = ", ".join(f"`{item.id}`" for item in scheduler.get_jobs()) or "nessuno"
            await update.message.reply_text(
                f"Job non trovato: `{job_id}`\nJob disponibili: {available}",
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        msg = await update.message.reply_text(
            f"Esecuzione manuale: `{job_id}`...",
            parse_mode=ParseMode.MARKDOWN,
        )
        try:
            result = job.func()
            success = await result if asyncio.iscoroutine(result) else result
        except Exception as exc:
            logger.error(f"Errore esecuzione manuale job {job_id}: {exc}")
            await msg.edit_text(
                f"Job `{job_id}` non completato.\n{sanitize_user_error_message(exc)}",
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        if success is False:
            await msg.edit_text(
                f"Job `{job_id}` terminato con errore. Controlla notifiche e log.",
                parse_mode=ParseMode.MARKDOWN,
            )
            return

        await msg.edit_text(
            f"Job `{job_id}` eseguito. Controlla /approvals per il draft.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    jobs = scheduler.get_jobs()
    if not jobs:
        await update.message.reply_text("Nessun job schedulato.")
        return

    text = "*Job schedulati:*\n\n"
    for job in jobs:
        next_run = job.next_run_time
        next_str = next_run.astimezone(ROME).strftime("%a %d/%m %H:%M") if next_run else "—"
        text += f"• `{job.id}` — {job.name}\nProssimo: {next_str}\n\n"

    text += "_Usa `/schedule run <id>` per eseguire subito_"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def skip_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update) or not update.message:
        return
    if "pending_reject" in context.user_data:
        approval_id = context.user_data.pop("pending_reject")
        success = await run_sync(reject, approval_id, None)
        if success:
            await update.message.reply_text("Draft rifiutato.")
        else:
            await update.message.reply_text("Non sono riuscita a salvare il rifiuto. Riprova.")
        return
    await update.message.reply_text("Nessuna operazione da saltare.")


async def task_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update) or not update.message:
        return
    if not context.args:
        await update.message.reply_text(
            "Uso: `/task <descrivi l'obiettivo>`\n"
            "Esempio: `/task Trova 5 prospect B&B da contattare questa settimana`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    objective = " ".join(context.args)
    msg = await update.message.reply_text(f"Elaborazione obiettivo...\n`{objective[:80]}`", parse_mode=ParseMode.MARKDOWN)
    result = await run_objective_async(objective)

    if result["status"] == "error":
        await msg.edit_text(sanitize_user_error_message(result.get("error")))
        return

    raw_output = result.get("output", "")
    plan_text = _format_plan_for_telegram(raw_output)
    approval_id = result.get("approval_id")
    keyboard = approval_keyboard(approval_id) if approval_id else None
    await msg.edit_text(f"Piano generato\n\n{plan_text}\n\nAvvio agenti in background...", reply_markup=keyboard)
    asyncio.create_task(_dispatch_plan_tasks_background(raw_output))


async def agent_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Redirect: tutto passa da Giuseppina. /agent è rimasto per compatibilità."""
    if not is_authorized(update) or not update.message:
        return

    task = " ".join(context.args) if context.args else ""
    if task:
        msg = await update.message.reply_text("Giuseppina ci pensa...", parse_mode=ParseMode.MARKDOWN)
        orchestrator_ctx = _telegram_agent_chat_context(AgentName.ORCHESTRATOR)
        result = await run_agent_async(AgentName.ORCHESTRATOR, task, orchestrator_ctx)
        if result["status"] == "error":
            await msg.edit_text(sanitize_user_error_message(result.get("error")))
            return
        output = truncate(result.get("output", ""))
        approval_id = result.get("approval_id")
        keyboard = approval_keyboard(approval_id) if approval_id else None
        context.user_data["active_agent_chat"] = AgentName.ORCHESTRATOR.value
        await msg.edit_text(
            f"Giuseppina\n\n{output}\n\n[Chat attiva: scrivi \"esci dalla chat\" per chiuderla]",
            reply_markup=keyboard,
        )
    else:
        await update.message.reply_text(
            "Scrivi direttamente il tuo messaggio — Giuseppina gestisce tutto."
        )


async def approvals_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update) or not update.message:
        return

    pending = await run_sync(get_pending_approvals)
    if not pending:
        await update.message.reply_text("Nessun draft in attesa di approvazione.")
        return

    recent_pending = [item for item in pending if approval_is_recent(item.get("created_at"))]
    shown = recent_pending or pending
    await update.message.reply_text(f"{len(shown)} draft in attesa:")
    for item in shown[:5]:
        agent = visible_agent_label(item.get("agent", "?"))
        preview = clean_preview(item.get("content_preview", ""), 220)
        created = item.get("created_at", "")[:16].replace("T", " ")
        # Calcola età in ore se possibile
        age_str = ""
        try:
            from datetime import UTC, datetime
            raw = item.get("created_at", "")
            if raw:
                raw_str = str(raw).replace("Z", "+00:00")
                created_dt = datetime.fromisoformat(raw_str)
                if not created_dt.tzinfo:
                    created_dt = created_dt.replace(tzinfo=UTC)
                age_h = int((datetime.now(UTC) - created_dt).total_seconds() / 3600)
                age_str = f" ({age_h}h fa)"
        except Exception:
            pass
        text = (
            f"Area: {agent}{age_str}\n"
            f"Creato: {created}\n"
            f"Anteprima:\n{preview}"
        )
        await update.message.reply_text(
            text,
            reply_markup=approval_keyboard(item["id"]),
        )

    if len(shown) > 5:
        await update.message.reply_text(
            f"... e altri {len(shown) - 5} draft. Vedi dashboard per tutti.",
        )
    hidden_old = len(pending) - len(shown)
    if hidden_old > 0:
        await update.message.reply_text(
            f"Ho nascosto {hidden_old} draft molto vecchi per mantenere l'elenco pulito."
        )


async def status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update) or not update.message:
        return

    pending_count, tasks, lead_counts = await run_sync(_load_status_snapshot)

    def _esc(s: str) -> str:
        """Escape markdown special chars in dynamic content."""
        return s.replace("_", r"\_").replace("*", r"\*").replace("`", r"\`").replace("[", r"\[")

    text = "*Status AI Board*\n\n"
    text += f"*Draft in attesa:* {pending_count}\n\n"
    if tasks:
        text += "*Task recenti:*\n"
        for task in tasks:
            agent_name = _esc(visible_agent_label(task.get("assigned_to")))
            title = _esc(task['title'][:40])
            task_status = _esc(str(task['status']))
            text += f"  • `{agent_name}` — {title} [{task_status}]\n"

    if lead_counts:
        text += "\n*Pipeline lead:*\n"
        for status, count in lead_counts.items():
            text += f"  • {_esc(str(status))}: {count}\n"

    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def memory_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update) or not update.message:
        return

    if context.args and context.args[0] == "set" and len(context.args) >= 3:
        key = context.args[1]
        value = " ".join(context.args[2:])
        category = key.split(".")[0] if "." in key else "custom"
        await run_sync(set_memory, key, value, category, "founder")
        await update.message.reply_text(
            f"Memoria aggiornata:\n`{key}` = `{value[:100]}`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    by_cat = await run_sync(_load_memory_index)
    if not by_cat:
        await update.message.reply_text("Memoria condivisa vuota.")
        return

    text = "*Memoria condivisa*\n\n"
    for cat, keys in by_cat.items():
        text += f"*{cat.upper()}*\n"
        for key in keys:
            text += f"  `{key}`\n"
        text += "\n"
    text += "_Usa `/memory set <chiave> <valore>` per aggiornare_"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def log_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update) or not update.message:
        return

    rows = await run_sync(_load_recent_logs)
    if not rows:
        await update.message.reply_text("Nessun log disponibile.")
        return

    text = "*Ultimi log del board:*\n\n"
    for row in rows:
        ts = row["created_at"][:16].replace("T", " ")
        status_emoji = "✓" if row["status"] in ("draft", "done", "approved") else "✗"
        ms = row.get("duration_ms", 0)
        area = visible_agent_label(row.get("agent"))
        text += (
            f"{status_emoji} `{area}` [{row.get('llm_model', '?')}]\n"
            f"   {row['action'][:50]}...\n"
            f"   {ts} — {ms}ms\n\n"
        )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def pipeline_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update) or not update.message:
        return

    leads = await run_sync(_load_pipeline)
    if not leads:
        await update.message.reply_text(
            "Pipeline vuota.\nUsa `/agent lead_generation <brief>` per generare prospect.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    by_status: dict[str, list[dict]] = {}
    for lead in leads:
        by_status.setdefault(lead["status"], []).append(lead)

    status_order = [
        "identified",
        "qualified",
        "contacted",
        "call_scheduled",
        "proposal_sent",
        "negotiation",
        "won",
        "lost",
    ]
    text = "*Pipeline lead:*\n\n"
    for status in status_order:
        group = by_status.get(status, [])
        if not group:
            continue
        text += f"*{status.upper().replace('_', ' ')}* ({len(group)})\n"
        for lead in group[:3]:
            score = lead.get("score", "?")
            company = lead.get("company", "")
            name = lead["name"]
            next_action = (lead.get("next_action") or "—")[:40]
            text += f"  • {name}"
            if company:
                text += f" ({company})"
            text += f" [score: {score}]\n"
            text += f"    → {next_action}\n"
        if len(group) > 3:
            text += f"    _...e altri {len(group) - 3}_\n"
        text += "\n"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update) or not update.callback_query:
        return

    # Dedup su update_id: callback duplicati (retry Telegram) → drop silenzioso
    if update.update_id and check_dedup_update_id(update.update_id):
        return

    query = update.callback_query
    await query.answer()
    parts = query.data.split(":", 2) if query.data else []
    action = parts[0] if parts else ""

    if action == "approve" and len(parts) >= 2:
        approval_id = parts[1]
        success = await run_sync(approve, approval_id)
        if success:
            await query.edit_message_reply_markup(reply_markup=None)
            await query.message.reply_text("Approvato.")
        else:
            await query.message.reply_text("Non sono riuscita ad approvare il draft. Riprova.")
        return

    if action == "reject" and len(parts) >= 2:
        approval_id = parts[1]
        context.user_data["pending_reject"] = approval_id
        await query.message.reply_text(
            "Motivo del rifiuto (opzionale):\nRispondi con il testo o scrivi /skip per saltare."
        )
        return

    if action == "view" and len(parts) >= 2:
        approval_id = parts[1]
        approval = await run_sync(get_approval, approval_id)
        if not approval:
            await query.message.reply_text("Approval non trovato.")
            return
        full = approval.get("full_content", {})
        output = full.get("output", "Nessun output")
        await query.message.reply_text(truncate(output), reply_markup=approval_keyboard(approval_id))
        return

    if action == "note" and len(parts) >= 2:
        approval_id = parts[1]
        context.user_data["pending_note"] = approval_id
        await query.message.reply_text("Scrivi la nota da aggiungere a questo draft:")
        return

    if action == "select_agent" and len(parts) >= 2:
        agent_str = parts[1]
        context.user_data["selected_agent"] = agent_str
        await query.message.reply_text(
            f"Area selezionata: {visible_agent_label(agent_str)}\n\nScrivi il task da eseguire:",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    if action == "cancel":
        context.user_data.clear()
        await query.edit_message_reply_markup(reply_markup=None)
        await query.message.reply_text("Operazione annullata.")
        return

    if action == "back":
        context.user_data.clear()
        await query.message.reply_text("Usa /help per vedere i comandi disponibili.")
        return

    logger.warning(f"Callback non gestita: {query.data}")
    await query.message.reply_text("Azione non riconosciuta.")


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update) or not update.message or not update.message.text:
        return

    # ── Dedup primaria su update_id: Telegram può reinviare lo stesso update ──
    # Controllo prima di tutto il resto per massima efficienza
    if update.update_id and check_dedup_update_id(update.update_id):
        return

    req_id = str(uuid.uuid4())[:8]
    text = update.message.text
    normalized_text = markdown_to_plain_text(text).strip()
    logger.info(f"[{req_id}] msg ricevuto: {normalized_text[:80]!r}")

    # Imposta sessione corrente per undo stack e action guard L3
    chat_id = str(update.effective_chat.id) if update.effective_chat else req_id
    set_current_session(chat_id)
    # Recupera undo stack da Supabase se sessione nuova (dopo restart processo)
    load_session_from_supabase(chat_id)

    # ── Dedup secondaria su testo: stessa stringa entro 5s (fallback) ──────────
    if check_dedup(chat_id, normalized_text):
        logger.debug(f"[{req_id}] Messaggio deduplicato per chat {chat_id}, drop silenzioso")
        return

    # ── Rate limit: max 20 msg/60s ───────────────────────────────────────────
    allowed, reason = check_rate_limit(chat_id)
    if not allowed:
        await update.message.reply_text(reason)
        return

    # ── Queue leggera: se già in processing, drop + avvisa ───────────────────
    lock = _get_chat_lock(chat_id)
    if lock.locked():
        logger.debug(f"[{req_id}] Chat {chat_id} occupata — drop messaggio concorrente")
        await update.message.reply_text("Sto ancora elaborando il messaggio precedente, un momento...")
        return

    # ── Gestione conferma/annulla azioni L3 (action_guard) ──────────────────
    if has_pending_confirmation(chat_id):
        lowered = normalized_text.lower().strip()
        if lowered in ("conferma", "sì", "si", "ok", "procedi", "vai"):
            record = pop_pending_confirmation(chat_id)
            if record:
                func_name = record["func_name"]
                kwargs = record["kwargs"]
                # Importa e chiama la funzione originale
                from core import notion_tools as _nt
                func = getattr(_nt, func_name, None)
                if func is None:
                    await update.message.reply_text("Azione non disponibile in questo momento.")
                    return
                msg = await update.message.reply_text("Esecuzione in corso...")
                try:
                    result = await run_sync(func, **kwargs)
                    log_business_action(
                        action=f"Azione L3 confermata: {func_name}",
                        entity_type=kwargs.get("name_or_id", kwargs.get("task_id", "?"))[:50],
                        entity_name=str(kwargs.get("name_or_id", kwargs.get("task_id", "?"))),
                        outcome="confirmed",
                        actor="founder",
                        intent=record.get("summary", ""),
                    )
                    await msg.edit_text(result)
                except Exception as exc:
                    logger.error(f"[{req_id}] Errore esecuzione L3 confermata: {exc}")
                    await msg.edit_text(sanitize_user_error_message(exc))
                return
        elif lowered in ("annulla", "no", "stop", "lascia perdere"):
            cancelled = cancel_pending_confirmation(chat_id)
            if cancelled:
                log_business_action(
                    action="Azione L3 annullata dal fondatore",
                    entity_type="unknown",
                    entity_name="?",
                    outcome="cancelled",
                    actor="founder",
                )
                await update.message.reply_text("Operazione annullata.")
                return
        else:
            # Messaggio diverso con conferma pendente: ricorda all'utente
            await update.message.reply_text(
                "⚠️ Ho un'azione sensibile in attesa di conferma.\n\n"
                "Scrivi **conferma** per procedere oppure **annulla** per scartare.",
                parse_mode=ParseMode.MARKDOWN,
            )
            return
    # ── Fine gestione L3 ────────────────────────────────────────────────────

    if "pending_assistant_action" in context.user_data:
        if confirm_word(normalized_text):
            pending_action = context.user_data.pop("pending_assistant_action")
            response = await run_sync(execute_pending_action, pending_action)
            if response.pending_action:
                context.user_data["pending_assistant_action"] = response.pending_action
            if response.delegate:
                await _dispatch_delegate(update, context, response.delegate)
                return
            await update.message.reply_text(response.text)
            return
        if cancel_word(normalized_text):
            context.user_data.pop("pending_assistant_action", None)
            await update.message.reply_text("Operazione annullata.")
            return
        await update.message.reply_text("Ho un'operazione in attesa. Scrivi CONFERMA per procedere oppure ANNULLA.")
        return

    if "pending_reject" in context.user_data:
        approval_id = context.user_data.pop("pending_reject")
        note = None if text == "/skip" else text
        success = await run_sync(reject, approval_id, note)
        if success:
            await update.message.reply_text("Draft rifiutato.")
        else:
            await update.message.reply_text("Non sono riuscita a salvare il rifiuto. Riprova.")
        return

    if "pending_note" in context.user_data:
        approval_id = context.user_data.pop("pending_note")
        await run_sync(_save_approval_note, approval_id, text)
        await update.message.reply_text("Nota salvata.")
        return

    if "active_agent_chat" in context.user_data:
        if normalized_text.lower() in CHAT_EXIT_PHRASES:
            context.user_data.pop("active_agent_chat")
            _pop_pending_attachments(context)
            await update.message.reply_text("Ok, sono qui se hai altro.")
            return
        # Redirect: active_agent_chat non bypassa più Giuseppina
        # Cade nel blocco Giuseppina sotto

    # Shortcut operativi espliciti (approvals, logs, status, pipeline list)
    shortcut = operational_shortcut(normalized_text)
    if shortcut:
        logger.info(f"[{req_id}] → operational_shortcut: {shortcut.get('action', '?')}")
        try:
            response = await run_sync(execute_action, shortcut)
        except Exception as exc:
            logger.exception(f"[{req_id}] Errore in operational_shortcut: {exc}")
            await update.message.reply_text(sanitize_user_error_message(exc))
            return
        if response.pending_action:
            context.user_data["pending_assistant_action"] = response.pending_action
        if response.delegate:
            await _dispatch_delegate(update, context, response.delegate)
            return
        await update.message.reply_text(response.text)
        return

    # Tutti gli altri messaggi → Giuseppina
    pending_attachments = _pop_pending_attachments(context)
    task_with_attachments = _build_task_with_attachments(text, pending_attachments)

    # Contesto a Giuseppina: storico conversazione (per riferimenti impliciti) + allegati
    # build_context_for_agent carica lazy dal DB al primo accesso per continuità post-restart
    chat_ctx: dict[str, Any] = build_context_for_agent(chat_id)
    if pending_attachments:
        chat_ctx["attachments"] = [
            {"name": a["name"], "excerpt": a.get("excerpt")}
            for a in pending_attachments
        ]

    logger.info(f"[{req_id}] → Giuseppina | attachments={len(pending_attachments)} | history_turns={len(chat_ctx.get('conversation_history', []))//2}")
    msg = await update.message.reply_text("…")
    await lock.acquire()
    try:
        response_text = await chat_agent_async(AgentName.ORCHESTRATOR, task_with_attachments, chat_ctx)
    except Exception as exc:
        logger.exception(f"[{req_id}] Errore chat Giuseppina: {exc}")
        await msg.edit_text("Si è verificato un errore. Riprova tra un momento.")
        return
    finally:
        lock.release()

    # Salva il turno in sessione per il prossimo messaggio
    add_turn(chat_id, text, response_text)

    logger.info(f"[{req_id}] risposta generata: {len(response_text)} chars")
    await msg.edit_text(truncate(response_text))


async def attachment_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler per documenti e foto inviati al bot."""
    if not is_authorized(update) or not update.message:
        return

    if update.update_id and check_dedup_update_id(update.update_id):
        return

    attachments = await _collect_telegram_attachments(update)
    if not attachments:
        await update.message.reply_text("Ho ricevuto un allegato ma non sono riuscito a leggerlo.")
        return

    caption = markdown_to_plain_text(update.message.caption or "").strip()
    active_agent_name = context.user_data.get("active_agent_chat")

    if active_agent_name:
        # C'è una chat agente attiva: usa subito gli allegati con il caption (se presente)
        if caption:
            try:
                agent_name = AgentName(active_agent_name)
            except ValueError:
                context.user_data.pop("active_agent_chat", None)
                _store_pending_attachments(context, attachments)
                await update.message.reply_text("La chat agente non è più valida. Allegati salvati — scegli un agente con /agent.")
                return

            task = _build_task_with_attachments(caption, attachments)
            chat_ctx: dict[str, Any] = {
                "attachments": [{"name": a["name"], "excerpt": a.get("excerpt")} for a in attachments]
            }
            msg = await update.message.reply_text("...")
            response_text = await chat_agent_async(agent_name, task, chat_ctx)
            await msg.edit_text(truncate(response_text))
        else:
            # Nessun caption: accumula e aspetta il messaggio
            prev = _get_pending_attachments(context)
            _store_pending_attachments(context, [*prev, *attachments])
            total = len(_get_pending_attachments(context))
            agent_display = visible_agent_label(active_agent_name)
            await update.message.reply_text(
                f"{total} allegat{'o' if total == 1 else 'i'} ricevut{'o' if total == 1 else 'i'}. "
                f"Ora scrivi cosa vuoi fare — li invio a {agent_display}."
            )
    else:
        # Nessuna chat attiva: accumula allegati e guida l'utente
        prev = _get_pending_attachments(context)
        _store_pending_attachments(context, [*prev, *attachments])
        total = len(_get_pending_attachments(context))
        names = ", ".join(a["name"] for a in attachments)
        if caption:
            # Ha caption: lancia come obiettivo orchestrator
            all_attachments = _pop_pending_attachments(context)
            task = _build_task_with_attachments(caption, all_attachments)
            msg = await update.message.reply_text("Documento ricevuto. Avvio analisi...")
            result = await run_objective_async(task)
            if result["status"] == "error":
                await msg.edit_text(sanitize_user_error_message(result.get("error")))
                return
            raw_output = result.get("output", "")
            plan_text = _format_plan_for_telegram(raw_output)
            approval_id = result.get("approval_id")
            keyboard = approval_keyboard(approval_id) if approval_id else None
            await msg.edit_text(f"Piano generato\n\n{plan_text}\n\nAvvio agenti in background...", reply_markup=keyboard)
            asyncio.create_task(_dispatch_plan_tasks_background(raw_output))
        else:
            await update.message.reply_text(
                f"Allegat{'o' if total == 1 else 'i'} ricevut{'o' if total == 1 else 'i'}: {names}\n\n"
                f"Ora dimmi cosa vuoi fare, oppure usa /agent per scegliere un agente specifico."
            )


async def refresh_schema_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /refresh-schema — forza reload degli schemi Notion.
    Utile dopo aver modificato proprietà nei database Notion.
    """
    if not is_authorized(update) or not update.message:
        return

    from core import notion_board as _nb
    if not _nb.notion_enabled():
        await update.message.reply_text("Notion non abilitato — schema non disponibile.")
        return

    msg = await update.message.reply_text("Ricarico schema Notion...")
    try:
        schemas = await run_sync(_nb.refresh_all_schemas)
        db_list = "\n".join(f"• {title} ({len(props)} proprietà)" for title, props in schemas.items())
        await msg.edit_text(
            f"Schema Notion aggiornato.\n\n{db_list}" if db_list else "Schema aggiornato (nessun DB trovato)."
        )
    except Exception as exc:
        logger.error(f"[refresh_schema_handler] Errore: {exc}")
        await msg.edit_text(sanitize_user_error_message(exc))


async def undo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /undo — annulla l'ultima azione eseguita da Giuseppina su Notion.
    Funziona per: creazione task/lead/cliente, aggiornamenti stato.
    Stack undo per-sessione (persiste finché il processo è in esecuzione).
    """
    if not is_authorized(update) or not update.message:
        return

    chat_id = str(update.effective_chat.id) if update.effective_chat else None
    if not chat_id:
        await update.message.reply_text("Impossibile determinare la sessione corrente.")
        return

    if not has_undo(chat_id):
        await update.message.reply_text(
            "Nessuna azione recente da annullare.\n\n"
            "_Lo stack undo si azzera al riavvio del sistema._",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    record = pop_undo(chat_id)
    if not record:
        await update.message.reply_text("Azione scaduta o non più annullabile.")
        return

    description = describe_undo(record)
    msg = await update.message.reply_text(f"Annullo: {description}...")

    try:
        result = await run_sync(execute_undo, record)
        log_business_action(
            action=f"Undo eseguito: {description}",
            entity_type=record.get("entity_type", "unknown"),
            entity_name=record.get("entity_name", "?"),
            outcome="success",
            actor="founder",
            intent="/undo",
        )
        await msg.edit_text(f"✅ {result}")
    except Exception as exc:
        logger.error(f"[undo_handler] Errore: {exc}")
        await msg.edit_text(sanitize_user_error_message(exc))


async def _dispatch_delegate(update: Update, context: ContextTypes.DEFAULT_TYPE, delegate: str) -> None:
    routing = {
        "status": status_handler,
        "approvals": approvals_handler,
        "log": log_handler,
        "memory": memory_handler,
        "pipeline": pipeline_handler,
        "help": help_handler,
    }
    handler = routing.get(delegate)
    if not handler:
        await update.message.reply_text("Azione interna non disponibile.")
        return
    await handler(update, context)
