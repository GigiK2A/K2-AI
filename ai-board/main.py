import asyncio
import os
import signal
import sys

from loguru import logger
from rich.console import Console
from rich.panel import Panel

from core.config import settings, supabase_configured
from core.memory import load_memory
from db.client import get_client

console = Console()


async def startup_checks() -> None:
    logger.remove()
    logger.add(sys.stderr, level=settings.log_level.upper())

    console.print(Panel.fit("[bold]AI Board[/bold] — avvio sistema", border_style="dim"))

    if supabase_configured():
        logger.info("Verifica connessione Supabase...")
        try:
            client = get_client()
            client.table("shared_memory").select("key").limit(1).execute()
            logger.success("Supabase: connesso")
        except Exception as exc:
            logger.error(f"Supabase: errore connessione — {exc}")
            raise SystemExit(1) from exc
    else:
        logger.warning("Supabase non configurato — avvio in modalità Notion-only.")

    logger.info("Caricamento memoria condivisa...")
    memory = load_memory()
    logger.success(f"Memoria condivisa: {len(memory)} chiavi")

    logger.info("Verifica agenti...")
    from core.orchestrator import AGENT_REGISTRY

    logger.success(f"Agenti unificati: {len(AGENT_REGISTRY)} caricati")

    if settings.anthropic_api_key:
        if not settings.anthropic_api_key.startswith("sk-ant"):
            logger.warning("ANTHROPIC_API_KEY non sembra valida — il failover verso Anthropic non sarà disponibile.")
    else:
        logger.warning("ANTHROPIC_API_KEY non impostata — Anthropic non sarà disponibile.")

    if settings.openai_api_key:
        if not settings.openai_api_key.startswith("sk-"):
            logger.warning("OPENAI_API_KEY non sembra valida — il failover verso OpenAI non sarà disponibile.")
    else:
        logger.warning("OPENAI_API_KEY non impostata — OpenAI non sarà disponibile.")

    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        logger.warning("Telegram non configurato: bot Telegram non verrà avviato.")

    console.print("[green]Sistema pronto[/green]")
    console.print(f"  Supabase: {'connesso' if supabase_configured() else 'disattivo (Notion-only)'}")
    console.print(f"  Memoria: {len(memory)} chiavi")
    console.print(f"  Agenti unificati: {len(AGENT_REGISTRY)}")
    console.print(f"  Telegram mode: {settings.telegram_mode}")


async def _wait_for_signal(stop_event: asyncio.Event) -> None:
    loop = asyncio.get_running_loop()

    def handle_signal() -> None:
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, handle_signal)
        except NotImplementedError:
            pass

    await stop_event.wait()


async def main():
    await startup_checks()

    from core.scheduler import setup_scheduler
    from interfaces.dashboard.app import create_dashboard_app
    from interfaces.telegram.bot import start_polling, start_webhook, stop as stop_bot
    import uvicorn

    sched = setup_scheduler()
    sched.start()
    logger.success(f"Scheduler avviato: {len(sched.get_jobs())} job attivi")

    port = int(os.getenv("PORT") or settings.app_port)
    # Bind: default localhost-only. Set APP_BIND_HOST=0.0.0.0 explicitly to expose.
    # Railway/Render/etc. require 0.0.0.0 to receive traffic from their proxy.
    bind_host = os.getenv("APP_BIND_HOST", "127.0.0.1")
    dashboard = create_dashboard_app()
    config = uvicorn.Config(
        dashboard,
        host=bind_host,
        port=port,
        log_level="warning",
        server_header=False,
    )
    server = uvicorn.Server(config)

    tg_app = None
    if settings.telegram_bot_token and settings.telegram_chat_id:
        if settings.telegram_mode == "webhook" and settings.telegram_webhook_url:
            tg_app = await start_webhook(settings.telegram_webhook_url)
        else:
            tg_app = await start_polling()
    else:
        logger.warning("Bot Telegram non avviato: mancano TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID.")

    stop_event = asyncio.Event()
    signal_task = asyncio.create_task(_wait_for_signal(stop_event))
    server_task = asyncio.create_task(server.serve())

    console.print(f"[green]Dashboard:[/green] http://localhost:{port}")
    console.print("[green]Telegram:[/green] bot attivo")
    console.print(f"[green]Scheduler:[/green] {len(sched.get_jobs())} job programmati")
    console.print("[dim]Premi Ctrl+C per fermare.[/dim]\n")

    try:
        await stop_event.wait()
    except KeyboardInterrupt:
        pass
    finally:
        logger.info("Arresto in corso...")
        stop_event.set()
        try:
            sched.shutdown(wait=False)
        except Exception as exc:
            logger.warning(f"Errore arresto scheduler: {exc}")
        server.should_exit = True
        try:
            await server_task
        except Exception as exc:
            logger.warning(f"Dashboard terminata con errore: {exc}")
        signal_task.cancel()
        if tg_app is not None:
            await stop_bot(tg_app)
        logger.success("Sistema fermato.")


def _free_port(port: int) -> None:
    """Termina il processo che occupa la porta, se presente."""
    import signal as _signal
    try:
        import subprocess
        result = subprocess.run(
            ["lsof", "-ti", f":{port}"],
            capture_output=True, text=True
        )
        pids = result.stdout.strip().split()
        for pid_str in pids:
            try:
                os.kill(int(pid_str), _signal.SIGTERM)
                logger.info(f"Liberata porta {port} (PID {pid_str})")
            except (ProcessLookupError, ValueError):
                pass
    except Exception as exc:
        logger.warning(f"Impossibile liberare porta {port}: {exc}")


if __name__ == "__main__":
    if settings.app_env == "development":
        _free_port(int(os.getenv("PORT") or settings.app_port))
    asyncio.run(main())
