from typing import Optional

from loguru import logger
from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from core.config import settings
from interfaces.telegram.handlers import (
    agent_handler,
    approvals_handler,
    attachment_message_handler,
    board_handler,
    callback_handler,
    consiglio_handler,
    help_handler,
    log_handler,
    memory_handler,
    message_handler,
    pipeline_handler,
    refresh_schema_handler,
    schedule_handler,
    skip_handler,
    start_handler,
    status_handler,
    task_handler,
    undo_handler,
)

_current_app: Optional[Application] = None


async def _global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Cattura tutte le eccezioni non gestite dagli handler e notifica l'utente."""
    logger.error(f"Eccezione non gestita nel bot Telegram: {context.error}", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                f"Errore durante l'elaborazione.\n\nDettaglio: {str(context.error)[:200]}"
            )
        except Exception as notify_exc:
            logger.warning(f"Impossibile notificare l'errore all'utente: {notify_exc}")


def build_application() -> Application:
    """Costruisce l'Application con tutti i handler registrati."""
    app = Application.builder().token(settings.telegram_bot_token).build()

    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CommandHandler("task", task_handler))
    app.add_handler(CommandHandler("agent", agent_handler))
    app.add_handler(CommandHandler("board", board_handler))
    app.add_handler(CommandHandler("consiglio", consiglio_handler))
    app.add_handler(CommandHandler("approvals", approvals_handler))
    app.add_handler(CommandHandler("schedule", schedule_handler))
    app.add_handler(CommandHandler("status", status_handler))
    app.add_handler(CommandHandler("memory", memory_handler))
    app.add_handler(CommandHandler("log", log_handler))
    app.add_handler(CommandHandler("pipeline", pipeline_handler))
    app.add_handler(CommandHandler("skip", skip_handler))
    app.add_handler(CommandHandler("undo", undo_handler))
    app.add_handler(CommandHandler("refresh_schema", refresh_schema_handler))

    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler((filters.Document.ALL | filters.PHOTO) & ~filters.COMMAND, attachment_message_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    app.add_error_handler(_global_error_handler)

    return app


def get_running_application() -> Optional[Application]:
    return _current_app


async def start_polling() -> Application:
    """Avvia il bot in modalità polling (sviluppo locale)."""
    logger.info("Bot Telegram: avvio in modalità polling")
    global _current_app
    app = build_application()
    await app.initialize()
    await app.start()
    if app.updater is None:
        raise RuntimeError("Updater non disponibile per la modalità polling")
    await app.updater.start_polling(drop_pending_updates=True)
    _current_app = app
    logger.success("Bot Telegram attivo — polling avviato")
    return app


async def start_webhook(url: str) -> Application:
    """Avvia il bot in modalità webhook (produzione)."""
    logger.info(f"Bot Telegram: avvio webhook su {url}")
    if not settings.telegram_webhook_secret:
        raise RuntimeError(
            "TELEGRAM_WEBHOOK_SECRET non impostato. Obbligatorio in modalità webhook "
            "per validare l'header X-Telegram-Bot-Api-Secret-Token (audit H-1)."
        )
    global _current_app
    app = build_application()
    await app.initialize()
    await app.start()
    webhook_url = f"{url.rstrip('/')}/webhook"
    await app.bot.set_webhook(
        url=webhook_url,
        drop_pending_updates=True,
        secret_token=settings.telegram_webhook_secret,
    )
    _current_app = app
    logger.success("Bot Telegram attivo — webhook configurato (secret_token attivo)")
    return app


async def process_webhook_payload(payload: dict) -> None:
    """Processa un update Telegram ricevuto via webhook FastAPI."""
    app = get_running_application()
    if app is None:
        raise RuntimeError("Application Telegram non inizializzata")
    update = Update.de_json(payload, app.bot)
    await app.process_update(update)


async def stop(app: Application):
    """Ferma il bot in modo pulito."""
    global _current_app
    if settings.telegram_mode == "webhook" and settings.telegram_webhook_url:
        try:
            await app.bot.delete_webhook()
        except Exception as exc:
            logger.warning(f"Errore rimozione webhook Telegram: {exc}")
    if app.updater and app.updater.running:
        await app.updater.stop()
    await app.stop()
    await app.shutdown()
    _current_app = None
    logger.info("Bot Telegram fermato")
