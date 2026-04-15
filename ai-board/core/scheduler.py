from __future__ import annotations

import asyncio
from datetime import UTC, date, datetime, timedelta
from functools import partial
from typing import Any, Callable

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

from core.config import settings
from db.models import AgentName, TaskStatus

ROME = pytz.timezone("Europe/Rome")

scheduler = AsyncIOScheduler(
    timezone=ROME,
    job_defaults={"coalesce": True, "max_instances": 1},
)

ACTIVE_TASK_STATUSES = {
    TaskStatus.PENDING.value,
    TaskStatus.RUNNING.value,
    TaskStatus.REVIEW.value,
    TaskStatus.DRAFT.value,
}


async def _run_sync(func: Callable[..., Any], *args, **kwargs) -> Any:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, partial(func, *args, **kwargs))


def _now_rome() -> datetime:
    return datetime.now(ROME)


def _today_rome() -> date:
    return _now_rome().date()


def _parse_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        try:
            dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


def _job_context(job_id: str, content_type: str, **data: Any) -> dict[str, Any]:
    payload = {key: value for key, value in data.items() if value is not None}
    payload["__board"] = {
        "requested_by": f"scheduler:{job_id}",
        "content_type": content_type,
    }
    return payload


def _notify_scheduler_error(job_id: str, message: str) -> None:
    from interfaces.telegram.notifier import notify_error, notify_sync

    notify_sync(notify_error(f"scheduler:{job_id}", message))


def _normalize_result(job_id: str, result: dict[str, Any]) -> bool:
    status = result.get("status")
    approval_id = result.get("approval_id")
    if status == TaskStatus.DRAFT.value and approval_id:
        return True
    if status == "error":
        logger.error(f"Scheduler {job_id}: errore agente - {result.get('error', 'sconosciuto')}")
        return False

    error = result.get("error") or "job completato senza draft approvabile"
    logger.error(f"Scheduler {job_id}: esecuzione incompleta - {error}")
    _notify_scheduler_error(job_id, str(error))
    return False


def _safe_list_tasks() -> list[dict[str, Any]]:
    """Lista task da Notion se disponibile, altrimenti da Supabase."""
    from core import notion_board
    if notion_board.notion_enabled():
        return notion_board.list_tasks()
    from db.client import get_service_client
    resp = get_service_client().table("tasks").select("*").order("created_at", desc=True).limit(100).execute()
    return resp.data or []


def _safe_list_pipeline_leads() -> list[dict[str, Any]]:
    """Lista lead da Notion se disponibile, altrimenti lista vuota (pipeline Supabase non strutturata)."""
    from core import notion_board
    if notion_board.notion_enabled():
        return notion_board.list_pipeline_leads()
    return []


def _collect_daily_brief_inputs() -> dict[str, Any]:
    from core.approval import get_pending_approvals

    now_utc = datetime.now(UTC)
    today = _today_rome()

    pending = get_pending_approvals()
    old_pending: list[dict[str, Any]] = []
    for item in pending:
        created_at = _parse_datetime(item.get("created_at"))
        if created_at and created_at <= now_utc - timedelta(hours=4):
            old_pending.append(item)

    all_tasks = _safe_list_tasks()
    active_statuses = {TaskStatus.PENDING.value, TaskStatus.RUNNING.value}
    active_tasks = sorted(
        [t for t in all_tasks if t.get("status") in active_statuses],
        key=lambda t: t.get("priority") or 3,
        reverse=True,
    )[:5]
    all_leads = _safe_list_pipeline_leads()
    all_leads_sorted = sorted(all_leads, key=lambda l: l.get("score") or 0, reverse=True)

    leads = [l for l in all_leads_sorted if l.get("status") not in {"won", "lost"}]

    due_leads: list[dict[str, Any]] = []
    for lead in leads:
        due_date = _parse_datetime(lead.get("next_action_date"))
        if due_date and due_date.astimezone(ROME).date() <= today:
            due_leads.append(lead)

    return {
        "today_label": today.strftime("%d/%m/%Y"),
        "pending_count": len(pending),
        "old_pending": old_pending,
        "active_tasks": active_tasks,
        "active_leads": leads[:5],
        "due_leads": due_leads[:5],
    }


def _collect_weekly_plan_inputs() -> dict[str, Any]:
    from core import notion_board

    today = _today_rome()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=4)
    week_ago = (today - timedelta(days=7)).isoformat()

    leads = _safe_list_pipeline_leads()
    all_approvals = notion_board.list_approvals(statuses=["approved"]) if notion_board.notion_enabled() else []
    approved_assets = [
        a for a in all_approvals
        if (a.get("reviewed_at") or "") >= week_ago
    ]

    lead_counts: dict[str, int] = {}
    for lead in leads:
        status = str(lead.get("status") or "unknown")
        lead_counts[status] = lead_counts.get(status, 0) + 1

    focus_leads = [
        lead
        for lead in sorted(leads, key=lambda item: item.get("score") or 0, reverse=True)
        if lead.get("status") not in {"won", "lost"}
    ][:8]

    return {
        "week_start": week_start.strftime("%d/%m"),
        "week_end": week_end.strftime("%d/%m/%Y"),
        "lead_counts": lead_counts,
        "approved_assets_count": len(approved_assets),
        "focus_leads": focus_leads,
    }


def _collect_kpi_inputs() -> dict[str, Any]:
    from core import notion_board

    today = _today_rome()
    start_of_month = today.replace(day=1).isoformat()
    start_of_week = today - timedelta(days=today.weekday())

    leads = _safe_list_pipeline_leads()
    all_approvals = notion_board.list_approvals(statuses=["approved"]) if notion_board.notion_enabled() else []
    approvals = [a for a in all_approvals if (a.get("reviewed_at") or "") >= start_of_month]

    lead_counts: dict[str, int] = {}
    leads_this_week = 0
    for lead in leads:
        status = str(lead.get("status") or "unknown")
        lead_counts[status] = lead_counts.get(status, 0) + 1
        created_at = _parse_datetime(lead.get("created_at"))
        if created_at and created_at.astimezone(ROME).date() >= start_of_week:
            leads_this_week += 1

    active_pipeline = sum(
        count for status, count in lead_counts.items() if status not in {"won", "lost"}
    )

    active_leads = [l for l in leads if l.get("status") not in {"won", "lost"}]

    return {
        "today_label": today.strftime("%d/%m/%Y"),
        "leads_total": len(leads),
        "leads_this_week": leads_this_week,
        "active_pipeline": active_pipeline,
        "approved_this_month": len(approvals),
        "lead_counts": lead_counts,
        "active_leads": active_leads,
        "mrr_available": False,
    }


def _collect_logs_to_archive(batch_size: int = 500) -> list[dict[str, Any]]:
    from db.client import get_service_client

    client = get_service_client()
    cutoff = (datetime.now(UTC) - timedelta(days=30)).isoformat()
    response = (
        client.table("agent_logs")
        .select("*")
        .lt("created_at", cutoff)
        .order("created_at")
        .limit(batch_size)
        .execute()
    )
    return response.data or []


def _extract_task_due_date(task: dict[str, Any]) -> datetime | None:
    raw_due = task.get("due_date")
    if raw_due:
        return _parse_datetime(raw_due)

    input_data = task.get("input_data")
    if isinstance(input_data, dict):
        for key in ("due_date", "deadline", "scadenza", "expected_due_date"):
            parsed = _parse_datetime(input_data.get(key))
            if parsed:
                return parsed
    return None


def _collect_task_reminder_inputs() -> dict[str, Any]:
    today = _today_rome()
    week_limit = today + timedelta(days=7)
    active_tasks: list[dict[str, Any]] = []

    tasks = _safe_list_tasks()

    for task in tasks:
        status = str(task.get("status") or "").strip().lower()
        if status not in ACTIVE_TASK_STATUSES:
            continue

        due_dt = _extract_task_due_date(task)
        due_date = due_dt.astimezone(ROME).date() if due_dt else None
        priority = int(task.get("priority") or 3)
        active_tasks.append(
            {
                "id": task.get("id"),
                "title": str(task.get("title") or "Task senza titolo"),
                "status": status,
                "priority": priority,
                "assigned_to": str(task.get("assigned_to") or "n/d"),
                "due_date": due_date,
            }
        )

    overdue_tasks = [item for item in active_tasks if item.get("due_date") and item["due_date"] < today]
    due_week_tasks = [item for item in active_tasks if item.get("due_date") and today <= item["due_date"] <= week_limit]
    urgent_tasks = [
        item for item in active_tasks
        if item["priority"] <= 2 or (item.get("due_date") and item["due_date"] <= (today + timedelta(days=1)))
    ]
    no_due_date_tasks = [item for item in active_tasks if not item.get("due_date")]

    def sort_key(item: dict[str, Any]) -> tuple:
        due_date = item.get("due_date")
        due_sort = due_date.toordinal() if due_date else 999999
        return (item.get("priority", 3), due_sort, item.get("title", ""))

    overdue_tasks.sort(key=sort_key)
    due_week_tasks.sort(key=sort_key)
    urgent_tasks.sort(key=sort_key)

    return {
        "today_label": today.strftime("%d/%m/%Y"),
        "active_count": len(active_tasks),
        "urgent_tasks": urgent_tasks[:8],
        "due_week_tasks": due_week_tasks[:8],
        "overdue_tasks": overdue_tasks[:8],
        "no_due_date_count": len(no_due_date_tasks),
    }


def _archive_logs(rows: list[dict[str, Any]]) -> int:
    from db.client import get_service_client

    if not rows:
        return 0

    client = get_service_client()
    archive_now = datetime.now(UTC).isoformat()
    payload = [{**row, "archived_at": archive_now} for row in rows]
    ids = [row["id"] for row in rows if row.get("id")]
    if not ids:
        return 0

    client.table("agent_logs_archive").upsert(payload).execute()
    client.table("agent_logs").delete().in_("id", ids).execute()
    return len(ids)


def validate_env_on_startup() -> None:
    """
    Verifica configurazione ambiente all'avvio.
    Log warning se Notion non è configurato (scheduler usa Supabase come fallback).
    Eccezione solo se Supabase non è raggiungibile.
    """
    from core import notion_board

    if notion_board.notion_enabled():
        logger.info("Scheduler: Notion configurato e abilitato")
    else:
        logger.warning(
            "Scheduler: Notion non configurato o NOTION_PAGE_ID mancante — "
            "i job useranno Supabase come fallback per task e lead"
        )
    # Verifica Supabase
    try:
        from db.client import get_service_client
        get_service_client().table("tasks").select("id").limit(1).execute()
        logger.info("Scheduler: Supabase raggiungibile")
    except Exception as exc:
        raise RuntimeError(f"Scheduler: Supabase non raggiungibile — {exc}") from exc


def setup_scheduler() -> AsyncIOScheduler:
    """
    Configura tutti i job automatici del board.
    Tutti i contenuti generativi restano in stato draft e richiedono approvazione esplicita.
    """
    scheduler.remove_all_jobs()

    scheduler.add_job(
        job_task_deadline_reminder,
        CronTrigger.from_crontab(settings.scheduler_task_reminder_cron, timezone=ROME),
        id="task_deadline_reminder",
        name="Reminder task urgenti/scadenze",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    scheduler.add_job(
        job_daily_brief,
        CronTrigger.from_crontab(settings.scheduler_daily_brief_cron, timezone=ROME),
        id="daily_brief",
        name="Briefing giornaliero",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    scheduler.add_job(
        job_weekly_plan,
        CronTrigger.from_crontab(settings.scheduler_weekly_plan_cron, timezone=ROME),
        id="weekly_plan",
        name="Piano settimanale",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    scheduler.add_job(
        job_kpi_update,
        CronTrigger.from_crontab(settings.scheduler_kpi_update_cron, timezone=ROME),
        id="kpi_update",
        name="Aggiornamento KPI",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    scheduler.add_job(
        job_approval_reminder,
        CronTrigger(hour="12,20", minute=0, timezone=ROME),
        id="approval_reminder",
        name="Reminder approvazioni",
        replace_existing=True,
        misfire_grace_time=1800,
    )
    scheduler.add_job(
        job_market_pulse,
        CronTrigger(day_of_week="wed", hour=9, minute=0, timezone=ROME),
        id="market_pulse",
        name="Market pulse settimanale",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    scheduler.add_job(
        job_cleanup_logs,
        CronTrigger(day_of_week="sun", hour=3, minute=0, timezone=ROME),
        id="cleanup_logs",
        name="Cleanup log",
        replace_existing=True,
        misfire_grace_time=7200,
    )
    scheduler.add_job(
        job_schema_refresh,
        CronTrigger(hour="*/6", minute=0, timezone=ROME),  # ogni 6 ore
        id="schema_refresh",
        name="Refresh schema Notion",
        replace_existing=True,
        misfire_grace_time=3600,
    )

    logger.info(f"Scheduler configurato: {len(scheduler.get_jobs())} job attivi")
    return scheduler


async def job_daily_brief() -> bool:
    logger.info("Scheduler: avvio briefing giornaliero")
    try:
        inputs = await _run_sync(_collect_daily_brief_inputs)

        def _fmt_tasks(items: list[dict]) -> str:
            if not items:
                return "  Nessuna"
            return "\n".join(
                f"  - [{item.get('status','?')}] P{item.get('priority','?')} · {item.get('title','?')} (agente: {item.get('assigned_to','?')})"
                for item in items
            )

        def _fmt_leads(items: list[dict]) -> str:
            if not items:
                return "  Nessuno"
            return "\n".join(
                f"  - {l.get('name','?')} | stato: {l.get('status','?')} | score: {l.get('score','n/d')} | prossima azione: {l.get('next_action','?')} (scad. {l.get('next_action_date','?')})"
                for l in items
            )

        def _fmt_approvals(items: list[dict]) -> str:
            if not items:
                return "  Nessuna"
            return "\n".join(
                f"  - {a.get('agent','?')} · {str(a.get('content_preview') or '')[:80]}"
                for a in items
            )

        task = f"""Genera il briefing operativo del giorno per il fondatore.

Data: {inputs["today_label"]}

DRAFT IN ATTESA: {inputs["pending_count"]} totali
Fermi da oltre 4 ore ({len(inputs["old_pending"])}):
{_fmt_approvals(inputs["old_pending"])}

TASK ATTIVI ({len(inputs["active_tasks"])}):
{_fmt_tasks(inputs["active_tasks"])}

LEAD ATTIVI ({len(inputs["active_leads"])}):
{_fmt_leads(inputs["active_leads"])}

LEAD CON SCADENZA OGGI O GIÀ SCADUTA ({len(inputs["due_leads"])}):
{_fmt_leads(inputs["due_leads"])}

Il briefing deve contenere:
🎯 Le 3 priorità assolute di oggi (nomina cosa e perché)
⚠️ Alert su approvazioni ferme oltre 4 ore (quali, da chi)
🔥 Lead da sbloccare oggi: elencali per nome con l'azione specifica da fare
💡 Una raccomandazione operativa concreta per la mattinata

Tono: diretto, umano, come se lo stesse scrivendo un collega che conosce bene la situazione.
Formato: usa le emoji come intestazioni di sezione, testo denso e azionabile, massimo 300 parole."""

        from core.orchestrator import run_agent

        result = await _run_sync(
            run_agent,
            AgentName.CHIEF_OF_STAFF,
            task,
            _job_context("daily_brief", "daily_brief", **inputs),
        )
        ok = _normalize_result("daily_brief", result)
        if ok:
            logger.success("Briefing giornaliero generato")
        return ok
    except Exception as exc:
        logger.error(f"Errore job_daily_brief: {exc}")
        _notify_scheduler_error("daily_brief", f"Errore briefing giornaliero: {exc}")
        return False


async def job_task_deadline_reminder() -> bool:
    logger.info("Scheduler: avvio promemoria task")
    try:
        from interfaces.telegram.notifier import notify_sync, send_message

        inputs = await _run_sync(_collect_task_reminder_inputs)
        urgent_tasks = inputs["urgent_tasks"]
        due_week_tasks = inputs["due_week_tasks"]
        overdue_tasks = inputs["overdue_tasks"]

        lines = [
            f"Project Operations — promemoria task automatico ({inputs['today_label']})",
            f"Task attive: {inputs['active_count']}",
            "",
            f"Task urgenti: {len(urgent_tasks)}",
        ]
        if urgent_tasks:
            for item in urgent_tasks:
                due_txt = item["due_date"].strftime("%d/%m") if item.get("due_date") else "senza scadenza"
                lines.append(f"- P{item['priority']} · {item['title']} (scad. {due_txt})")
        else:
            lines.append("- Nessuna task urgente")

        lines += ["", f"Task con scadenza entro 7 giorni: {len(due_week_tasks)}"]
        if due_week_tasks:
            for item in due_week_tasks:
                lines.append(f"- {item['title']} ({item['due_date'].strftime('%d/%m')})")
        else:
            lines.append("- Nessuna task in scadenza nei prossimi 7 giorni")

        lines += ["", f"Task già scadute: {len(overdue_tasks)}"]
        if overdue_tasks:
            for item in overdue_tasks:
                lines.append(f"- {item['title']} ({item['due_date'].strftime('%d/%m')})")
        else:
            lines.append("- Nessuna task scaduta")

        if inputs["no_due_date_count"]:
            lines += [
                "",
                f"Task senza data di scadenza: {inputs['no_due_date_count']}",
                "Imposta la scadenza per includerle nei reminder.",
            ]

        notify_sync(send_message("\n".join(lines)))
        logger.success("Promemoria task inviato")
        return True
    except Exception as exc:
        logger.error(f"Errore job_task_deadline_reminder: {exc}")
        _notify_scheduler_error("task_deadline_reminder", f"Errore promemoria task: {exc}")
        return False


async def job_weekly_plan() -> bool:
    logger.info("Scheduler: avvio piano settimanale")
    try:
        inputs = await _run_sync(_collect_weekly_plan_inputs)

        def _fmt_lead_counts(counts: dict) -> str:
            if not counts:
                return "  Nessun lead in pipeline"
            return "\n".join(f"  - {status}: {n}" for status, n in sorted(counts.items()))

        def _fmt_focus_leads(items: list[dict]) -> str:
            if not items:
                return "  Nessuno"
            return "\n".join(
                f"  - {l.get('name','?')} | stato: {l.get('status','?')} | score: {l.get('score','n/d')} | prossima azione: {l.get('next_action','?')} (scad. {l.get('next_action_date','?')})"
                for l in items
            )

        task = f"""Genera il piano operativo per la settimana {inputs["week_start"]} - {inputs["week_end"]}.

PIPELINE ({sum(inputs["lead_counts"].values())} lead totali):
{_fmt_lead_counts(inputs["lead_counts"])}

OUTPUT APPROVATI NEGLI ULTIMI 7 GIORNI: {inputs["approved_assets_count"]}

LEAD IN FOCUS ({len(inputs["focus_leads"])}):
{_fmt_focus_leads(inputs["focus_leads"])}

Il piano deve contenere:
🎯 Un solo obiettivo principale misurabile per la settimana
📋 I 5 task prioritari: agente assegnato, giorno target, output atteso
✍️ Contenuti da produrre: canale, nicchia target, angolo
🔥 Lead da contattare o far avanzare: elencali per nome con l'azione specifica
📊 Un KPI unico da monitorare

Tono: come un piano che scriverebbe un chief of staff che conosce bene il business — concreto, senza fronzoli.
Formato: usa le emoji come intestazioni, lun-ven strutturato, zero testo generico. Per ogni lead citalo per nome.
IMPORTANTE: Non inventare dati. Usa esclusivamente i lead e le informazioni forniti sopra."""

        from core.orchestrator import run_agent

        result = await _run_sync(
            run_agent,
            AgentName.ORCHESTRATOR,
            task,
            _job_context("weekly_plan", "weekly_plan", **inputs),
        )
        ok = _normalize_result("weekly_plan", result)
        if ok:
            logger.success("Piano settimanale generato")
        return ok
    except Exception as exc:
        logger.error(f"Errore job_weekly_plan: {exc}")
        _notify_scheduler_error("weekly_plan", f"Errore piano settimanale: {exc}")
        return False


async def job_kpi_update() -> bool:
    logger.info("Scheduler: avvio aggiornamento KPI")
    try:
        inputs = await _run_sync(_collect_kpi_inputs)

        def _fmt_pipeline_breakdown(counts: dict) -> str:
            if not counts:
                return "  Nessun dato"
            return "\n".join(f"  - {status}: {n}" for status, n in sorted(counts.items()))

        def _fmt_active_leads(items: list[dict]) -> str:
            if not items:
                return "  Nessuno"
            return "\n".join(
                f"  - {l.get('name','?')} | stato: {l.get('status','?')} | score: {l.get('score','n/d')} | azione: {l.get('next_action','?')}"
                for l in items[:15]
            )

        task = f"""Genera il report KPI serale di oggi {inputs["today_label"]}.

DATI REALI DA NOTION:
- Lead totali in pipeline: {inputs["leads_total"]}
- Nuovi lead questa settimana: {inputs["leads_this_week"]}
- Lead attivi (esclusi won/lost): {inputs["active_pipeline"]}
- Asset approvati questo mese: {inputs["approved_this_month"]}
- Dati MRR: non disponibili

BREAKDOWN PIPELINE PER STATO:
{_fmt_pipeline_breakdown(inputs["lead_counts"])}

LEAD ATTIVI ({len(inputs["active_leads"])}):
{_fmt_active_leads(inputs["active_leads"])}

Il report deve contenere:
📊 Stato pipeline: quanti lead per stato, dove si accumula, cosa si muove
🚀 Velocità di acquisizione: lead nuovi questa settimana vs capacità attuale
✅ Produttività board: asset approvati nel mese
⚠️ Alert espliciti se qualcosa è sotto soglia o fermo
💡 Una raccomandazione concreta per domani mattina

Tono: diretto e umano, come una call di fine giornata con il fondatore — non un report formale.
Regole: cita i numeri reali forniti, non inventare dati mancanti — segnalali come "dato non disponibile". Massimo 250 parole."""

        from core.orchestrator import run_agent

        result = await _run_sync(
            run_agent,
            AgentName.FINANCE_KPI,
            task,
            _job_context("kpi_update", "kpi_update", **inputs),
        )
        ok = _normalize_result("kpi_update", result)
        if ok:
            logger.success("KPI aggiornati")
        return ok
    except Exception as exc:
        logger.error(f"Errore job_kpi_update: {exc}")
        _notify_scheduler_error("kpi_update", f"Errore aggiornamento KPI: {exc}")
        return False


async def job_approval_reminder() -> bool:
    logger.info("Scheduler: check approvazioni pendenti")
    try:
        from core.approval import expire_stale_approvals, get_pending_approvals
        from interfaces.telegram.notifier import notify_sync, send_message

        # Prima scadi i draft vecchi (>48h): non devono restare appesi per sempre
        expired = await _run_sync(expire_stale_approvals)
        if expired:
            logger.info(f"Scaduti {expired} draft stale prima del reminder")

        # Ora controlla i draft rimasti (freschi, tra 8h e 48h)
        pending = await _run_sync(get_pending_approvals)
        if not pending:
            return True

        cutoff_old = datetime.now(UTC) - timedelta(hours=8)
        old_pending = []
        for item in pending:
            created_at = _parse_datetime(item.get("created_at"))
            if created_at and created_at <= cutoff_old:
                old_pending.append(item)

        if not old_pending:
            return True

        lines = []
        for item in old_pending[:5]:
            agent = str(item.get("agent") or "?").replace("_", " ").title()
            preview = str(item.get("content_preview") or "").replace("\n", " ").strip()
            preview_short = preview[:80] + ("…" if len(preview) > 80 else "")
            created_at = _parse_datetime(item.get("created_at"))
            age_h = int((datetime.now(UTC) - created_at).total_seconds() / 3600) if created_at else "?"
            lines.append(f"- {agent} ({age_h}h fa): {preview_short}")

        text = (
            f"{len(old_pending)} draft in attesa da oltre 8 ore\n\n"
            + "\n".join(lines)
            + "\n\nUsa /approvals per gestirli."
        )
        notify_sync(send_message(text))
        logger.info(f"Reminder inviato: {len(old_pending)} draft pendenti")
        return True
    except Exception as exc:
        logger.error(f"Errore job_approval_reminder: {exc}")
        _notify_scheduler_error("approval_reminder", f"Errore reminder approvazioni: {exc}")
        return False


async def job_market_pulse() -> bool:
    logger.info("Scheduler: avvio market pulse")
    try:
        today = _today_rome()
        task = """Fai una ricerca rapida sul mercato italiano per le nostre tre nicchie.

Per ognuna cerca notizie, trend e opportunità degli ultimi 7 giorni:
1. B&B e affittacamere in Italia: cambiamenti normativi, trend occupancy, problemi comuni
2. Ristorazione locale italiana: sfide gestionali, digitalizzazione, novità di settore
3. Studi tecnici e PMI italiane: adozione AI, problemi operativi, opportunità

Output richiesto:
- 2-3 segnali concreti per nicchia
- 1 opportunità commerciale immediata per noi
- 1 argomento da usare nei contenuti LinkedIn di questa settimana
- link o fonte per ogni segnale quando disponibili

Formato: bullet list densa, italiana, nessuna statistica inventata."""

        from core.orchestrator import run_agent

        result = await _run_sync(
            run_agent,
            AgentName.MARKET_INTELLIGENCE,
            task,
            _job_context(
                "market_pulse",
                "market_pulse",
                date=today.strftime("%d/%m/%Y"),
                lookback_days=7,
                geography="Italia",
                target_verticals=["B&B", "ristoranti", "studi tecnici e PMI"],
            ),
        )
        ok = _normalize_result("market_pulse", result)
        if ok:
            logger.success("Market pulse generato")
        return ok
    except Exception as exc:
        logger.error(f"Errore job_market_pulse: {exc}")
        _notify_scheduler_error("market_pulse", f"Errore market pulse: {exc}")
        return False


async def job_cleanup_logs() -> bool:
    logger.info("Scheduler: avvio cleanup log")
    try:
        total_archived = 0
        while True:
            rows = await _run_sync(_collect_logs_to_archive)
            if not rows:
                break
            total_archived += await _run_sync(_archive_logs, rows)
            if len(rows) < 500:
                break

        if total_archived == 0:
            logger.info("Cleanup log: nessun log da archiviare")
            return True

        logger.success(f"Cleanup log: archiviati {total_archived} record")
        return True
    except Exception as exc:
        message = f"Errore cleanup log: {exc}"
        if "agent_logs_archive" in str(exc):
            message = (
                "Tabella agent_logs_archive mancante. "
                "Applica db/migrations/003_agent_logs_archive.sql su Supabase prima del prossimo cleanup."
            )
        logger.error(f"Errore job_cleanup_logs: {exc}")
        _notify_scheduler_error("cleanup_logs", message)
        return False



async def job_schema_refresh() -> bool:
    """Aggiorna cache schema Notion ogni 6 ore. Non bloccante, non critico."""
    logger.info("Scheduler: avvio refresh schema Notion")
    try:
        from core import notion_board
        if not notion_board.notion_enabled():
            logger.debug("Scheduler schema_refresh: Notion non abilitato, skip")
            return True
        schemas = await _run_sync(notion_board.refresh_all_schemas)
        logger.success(f"Schema Notion aggiornato: {len(schemas)} database")
        return True
    except Exception as exc:
        logger.warning(f"Scheduler schema_refresh fallito (non critico): {exc}")
        return True  # Non notificare — è non critico
