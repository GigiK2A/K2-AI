import asyncio
from typing import Optional

from loguru import logger
from telegram import Bot, InlineKeyboardMarkup

from core.config import settings
from core.text import markdown_to_plain_text, truncate_text

_bot: Optional[Bot] = None


def get_bot() -> Bot:
    global _bot
    if _bot is None:
        _bot = Bot(token=settings.telegram_bot_token)
    return _bot


def _split_text(text: str, max_len: int = 4000) -> list[str]:
    """Divide il testo in chunk da max_len caratteri, spezzando sui newline."""
    if len(text) <= max_len:
        return [text]
    chunks: list[str] = []
    while text:
        if len(text) <= max_len:
            chunks.append(text)
            break
        split_at = text.rfind("\n", 0, max_len)
        if split_at <= 0:
            split_at = max_len
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip("\n")
    return chunks


async def send_message(
    text: str,
    keyboard: InlineKeyboardMarkup | None = None,
    parse_mode: str | None = None,
) -> bool:
    """Invia messaggio al fondatore."""
    try:
        bot = get_bot()
        await bot.send_message(
            chat_id=settings.telegram_chat_id,
            text=text[:4096],
            reply_markup=keyboard,
            parse_mode=parse_mode,
        )
        return True
    except Exception as exc:
        logger.error(f"Errore invio notifica Telegram: {exc}")
        return False


async def send_long_message(text: str, parse_mode: str | None = None) -> bool:
    """Invia un messaggio lungo suddividendolo in più parti se supera il limite Telegram."""
    chunks = _split_text(text)
    for chunk in chunks:
        ok = await send_message(chunk, parse_mode=parse_mode)
        if not ok:
            return False
    return True


async def notify_draft_ready(agent_name: str, approval_id: str, preview: str) -> bool:
    """Notifica che un draft è pronto per revisione."""
    from interfaces.telegram.keyboards import approval_keyboard

    readable_agent = agent_name.replace("_", " ").title()
    cleaned_preview = truncate_text(markdown_to_plain_text(preview), 500, suffix="\n…")
    text = (
        f"Draft pronto\n\n"
        f"Agente: {readable_agent}\n"
        f"Anteprima:\n{cleaned_preview}\n\n"
        f"ID: {approval_id[:8]}..."
    )
    return await send_message(text, keyboard=approval_keyboard(approval_id))


async def notify_error(agent_name: str, error: str) -> bool:
    """Notifica errore di un agente."""
    text = (
        f"Errore agente\n\n"
        f"Agente: {agent_name}\n"
        f"Errore: {error[:300]}"
    )
    return await send_message(text)


async def notify_system(message: str) -> bool:
    """Notifica di sistema generica."""
    return await send_message(f"Sistema\n\n{message}")


def notify_sync(coro) -> bool:
    """
    Helper per chiamare notifiche async da contesto sync
    (es: da un agente o dallo scheduler).
    """
    try:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coro)

        loop.create_task(coro)
        return True
    except Exception as exc:
        logger.warning(f"Errore notify_sync: {exc}")
        return False
