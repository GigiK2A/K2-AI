"""APScheduler wiring — daily brief + email triage cron jobs.

The scheduler is started during FastAPI lifespan if at least one job is
enabled. If apscheduler is not installed (e.g. running tests without the
full requirements), we degrade to a no-op so imports never fail.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from app.settings import get_settings

log = logging.getLogger(__name__)

_scheduler: Optional[Any] = None


def _build_scheduler() -> Optional[Any]:
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type: ignore
        from apscheduler.triggers.cron import CronTrigger  # type: ignore
    except ImportError:
        log.warning("scheduler.apscheduler_missing")
        return None

    settings = get_settings()
    sched = AsyncIOScheduler(timezone=settings.daily_brief_tz)

    if settings.daily_brief_enabled:
        try:
            from app.agent.daily_brief import deliver_daily_brief

            sched.add_job(
                deliver_daily_brief,
                CronTrigger.from_crontab(
                    settings.daily_brief_cron, timezone=settings.daily_brief_tz
                ),
                id="daily_brief",
                replace_existing=True,
            )
            log.info(
                "scheduler.daily_brief_registered",
                extra={"cron": settings.daily_brief_cron, "tz": settings.daily_brief_tz},
            )
        except Exception:  # noqa: BLE001
            log.exception("scheduler.daily_brief_register_failed")

    if settings.email_triage_enabled:
        try:
            from app.agent.email_triage import build_default_provider, triage_inbox

            async def _run_triage() -> None:
                provider, _ = build_default_provider()
                await triage_inbox(provider)

            sched.add_job(
                _run_triage,
                CronTrigger.from_crontab(
                    settings.email_triage_cron, timezone=settings.daily_brief_tz
                ),
                id="email_triage",
                replace_existing=True,
            )
            log.info(
                "scheduler.email_triage_registered",
                extra={"cron": settings.email_triage_cron},
            )
        except Exception:  # noqa: BLE001
            log.exception("scheduler.email_triage_register_failed")

    return sched


def start_scheduler() -> None:
    """Start the global scheduler if any job is enabled."""
    global _scheduler
    settings = get_settings()
    if not (settings.daily_brief_enabled or settings.email_triage_enabled):
        log.info("scheduler.disabled — no jobs requested")
        return
    if _scheduler is not None:
        return
    sched = _build_scheduler()
    if sched is None:
        return
    try:
        sched.start()
        _scheduler = sched
        log.info("scheduler.started")
    except Exception:  # noqa: BLE001
        log.exception("scheduler.start_failed")


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler is None:
        return
    try:
        _scheduler.shutdown(wait=False)
    except Exception:  # noqa: BLE001
        log.exception("scheduler.shutdown_failed")
    _scheduler = None
