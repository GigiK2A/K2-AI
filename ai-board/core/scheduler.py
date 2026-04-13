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


def _collect_daily_brief_inputs() -> dict[str, Any]:
    from core.approval import get_pending_approvals
    from db.client import get_service_client

    client = get_service_client()
    now_utc = datetime.now(UTC)
    today = _today_rome()

    pending = get_pending_approvals()
    old_pending: list[dict[str, Any]] = []
    for item in pending:
        created_at = _parse_datetime(item.get("created_at"))
        if created_at and created_at <= now_utc - timedelta(hours=4):
            old_pending.append(item)

    tasks_resp = (
        client.table("tasks")
        .select("title,assigned_to,priority,status,created_at")
        .in_("status", [TaskStatus.PENDING.value, TaskStatus.RUNNING.value])
        .order("priority", desc=True)
        .limit(5)
        .execute()
    )
    active_tasks = tasks_resp.data or []

    leads_resp = (
        client.table("pipeline_leads")
        .select("name,company,status,score,next_action,next_action_date")
        .order("score", desc=True)
        .limit(50)
        .execute()
    )
    leads = [
        lead
        for lead in (leads_resp.data or [])
        if lead.get("status") not in {"won", "lost"}
    ]

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
    from db.client import get_service_client

    client = get_service_client()
    today = _today_rome()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=4)
    week_ago = (today - timedelta(days=7)).isoformat()

    leads_resp = client.table("pipeline_leads").select("name,status,score,next_action,next_action_date").execute()
    leads = leads_resp.data or []
    lead_counts: dict[str, int] = {}
    for lead in leads:
        status = str(lead.get("status") or "unknown")
        lead_counts[status] = lead_counts.get(status, 0) + 1

    approved_resp = (
        client.table("approvals")
        .select("agent,content_type,reviewed_at")
        .eq("status", TaskStatus.APPROVED.value)
        .gte("reviewed_at", week_ago)
        .execute()
    )
    approved_assets = approved_resp.data or []
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
    from db.client import get_service_client

    client = get_service_client()
    today = _today_rome()
    start_of_month = today.replace(day=1).isoformat()
    start_of_week = today - timedelta(days=today.weekday())
    start_of_day = _now_rome().replace(hour=0, minute=0, second=0, microsecond=0).astimezone(UTC).isoformat()

    leads = client.table("pipeline_leads").select("status,created_at").execute().data or []
    approvals = (
        client.table("approvals")
        .select("status,reviewed_at")
        .eq("status", TaskStatus.APPROVED.value)
        .gte("reviewed_at", start_of_month)
        .execute()
        .data
        or []
    )
    runs_today = (
        client.table("agent_logs")
        .select("id")
        .gte("created_at", start_of_day)
        .execute()
        .data
        or []
    )

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

    return {
        "today_label": today.strftime("%d/%m/%Y"),
        "leads_total": len(leads),
        "leads_this_week": leads_this_week,
        "active_pipeline": active_pipeline,
        "approved_this_month": len(approvals),
        "runs_today": len(runs_today),
        "lead_counts": lead_counts,
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

    from core import notion_board

    if notion_board.notion_enabled():

        tasks = notion_board.list_tasks()
    else:
        from db.client import get_service_client

        client = get_service_client()
        tasks = (
            client.table("tasks")
            .select("id,title,assigned_to,status,priority,created_at,input_data")
            .in_("status", list(ACTIVE_TASK_STATUSES))
            .order("priority")
            .limit(400)
            .execute()
            .data
            or []
        )

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

    logger.info(f"Scheduler configurato: {len(scheduler.get_jobs())} job attivi")
    return scheduler


async def job_daily_brief() -> bool:
    logger.info("Scheduler: avvio briefing giornaliero")
    try:
        inputs = await _run_sync(_collect_daily_brief_inputs)
        task = f"""Genera il briefing operativo del giorno per il fondatore.

Data: {inputs["today_label"]}

Contesto reale:
- Draft in attesa: {inputs["pending_count"]}
- Approvazioni in attesa da oltre 4 ore: {len(inputs["old_pending"])}
- Task attivi principali: {[item.get("title") for item in inputs["active_tasks"]]}
- Lead attivi principali: {[f"{item.get('name')} ({item.get('status')})" for item in inputs["active_leads"]]}
- Lead con next_action in scadenza o scaduta: {[item.get("name") for item in inputs["due_leads"]]}

Il briefing deve contenere:
1. Le 3 priorita assolute di oggi
2. Alert su approvazioni ferme oltre 4 ore
3. Lead da sbloccare oggi con next action scaduta o in scadenza
4. Una raccomandazione operativa molto concreta per la mattinata

Formato: lista numerata, denso, zero filler, massimo 250 parole."""

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
                f"Task senza scadenza: {inputs['no_due_date_count']}",
                "Imposta la data di scadenza per includerle nei reminder settimanali.",
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
        task = f"""Genera il piano operativo per la settimana {inputs["week_start"]} - {inputs["week_end"]}.

Stato attuale:
- Pipeline lead per stato: {inputs["lead_counts"]}
- Output approvati negli ultimi 7 giorni: {inputs["approved_assets_count"]}
- Lead da tenere in focus: {[f"{item.get('name')} ({item.get('status')}, score {item.get('score') or 'n/d'})" for item in inputs["focus_leads"]]}

Il piano deve contenere:
1. Un solo obiettivo principale, misurabile
2. I 5 task prioritari con agente assegnato e giorno target
3. Contenuti da produrre con canale e nicchia target
4. Lead da contattare o far avanzare in pipeline
5. Un KPI unico da monitorare questa settimana

Formato: lun-ven, denso, operativo, senza testo generico."""

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
        task = f"""Genera il report KPI serale di oggi {inputs["today_label"]}.

Dati reali dal sistema:
- Lead totali in pipeline: {inputs["leads_total"]}
- Nuovi lead questa settimana: {inputs["leads_this_week"]}
- Lead attivi (non won/lost): {inputs["active_pipeline"]}
- Asset approvati questo mese: {inputs["approved_this_month"]}
- Run agenti oggi: {inputs["runs_today"]}
- Breakdown pipeline: {inputs["lead_counts"]}
- Dati MRR disponibili nel DB: {"si" if inputs["mrr_available"] else "no"}

Il report deve contenere:
1. Stato pipeline rispetto alla capacita commerciale attuale
2. Velocita di acquisizione lead della settimana
3. Produttivita del board oggi e nel mese
4. Alert se qualcosa e sotto soglia
5. Una raccomandazione per domani mattina

Formato: numeri in evidenza, massimo 200 parole, segnala esplicitamente i dati mancanti invece di inventarli."""

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
        from core.approval import get_pending_approvals
        from interfaces.telegram.notifier import notify_sync, send_message

        pending = await _run_sync(get_pending_approvals)
        if not pending:
            return True

        cutoff = datetime.now(UTC) - timedelta(hours=8)
        old_pending = []
        for item in pending:
            created_at = _parse_datetime(item.get("created_at"))
            if created_at and created_at <= cutoff:
                old_pending.append(item)

        if not old_pending:
            return True

        lines = []
        for item in old_pending[:5]:
            agent = str(item.get("agent") or "?").replace("_", " ")
            preview = str(item.get("content_preview") or "").replace("\n", " ").strip()
            lines.append(f"- {agent}: {preview[:80]}")

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

Per ognuna cerca notizie, trend e opportunita degli ultimi 7 giorni:
1. B&B e affittacamere in Italia: cambiamenti normativi, trend occupancy, problemi comuni
2. Ristorazione locale italiana: sfide gestionali, digitalizzazione, novita di settore
3. Studi tecnici e PMI italiane: adozione AI, problemi operativi, opportunita

Output richiesto:
- 2-3 segnali concreti per nicchia
- 1 opportunita commerciale immediata per noi
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
