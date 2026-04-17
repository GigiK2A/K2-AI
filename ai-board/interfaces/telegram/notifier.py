import asyncio
from typing import Optional

from loguru import logger
from telegram import Bot, InlineKeyboardMarkup

from core.config import settings
from interfaces.telegram.presentation import (
    clean_preview,
    sanitize_user_error_message,
    visible_agent_label,
)

_bot: Optional[Bot] = None


def get_bot() -> Bot:
    global _bot
    if _bot is None:
        _bot = Bot(token=settings.telegram_bot_token)
    return _bot


_TG_MAX = 4096  # Limite Telegram per messaggio singolo


def _split_text(text: str, max_len: int = _TG_MAX) -> list[str]:
    """Divide il testo in chunk ≤ max_len, spezzando su paragrafi o newline.

    Non tronca mai: garantisce che tutto il contenuto venga inviato.
    """
    if len(text) <= max_len:
        return [text]
    chunks: list[str] = []
    while text:
        if len(text) <= max_len:
            chunks.append(text)
            break
        # Prova a spezzare sull'ultimo doppio newline (paragrafo)
        split_at = text.rfind("\n\n", 0, max_len)
        if split_at <= 0:
            # Fallback: ultimo newline
            split_at = text.rfind("\n", 0, max_len)
        if split_at <= 0:
            # Fallback: ultima parola
            split_at = text.rfind(" ", 0, max_len)
        if split_at <= 0:
            split_at = max_len
        chunks.append(text[:split_at].rstrip())
        text = text[split_at:].lstrip("\n")
    return chunks


async def send_message(
    text: str,
    keyboard: InlineKeyboardMarkup | None = None,
    parse_mode: str | None = None,
) -> bool:
    """Invia messaggio al fondatore. Se supera il limite Telegram lo spezza."""
    try:
        bot = get_bot()
        chunks = _split_text(text)
        for i, chunk in enumerate(chunks):
            # La keyboard va solo sull'ultimo chunk
            kb = keyboard if i == len(chunks) - 1 else None
            await bot.send_message(
                chat_id=settings.telegram_chat_id,
                text=chunk,
                reply_markup=kb,
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


async def notify_informational(agent_name: str, content_type: str, text: str) -> bool:
    """Invia un messaggio informativo direttamente, senza draft né bottoni di approvazione."""
    label = visible_agent_label(f"scheduler:{content_type}") or visible_agent_label(agent_name)
    return await send_message(f"{label}\n\n{text}")


async def notify_draft_ready(agent_name: str, approval_id: str, preview: str) -> bool:
    """Notifica che un draft è pronto per revisione."""
    from interfaces.telegram.keyboards import approval_keyboard

    readable_agent = visible_agent_label(agent_name)
    plain = clean_preview(preview, max_len=520)
    text = (
        f"Draft pronto\n\n"
        f"Area: {readable_agent}\n"
        f"Anteprima:\n{plain}"
    )
    return await send_message(text, keyboard=approval_keyboard(approval_id))


async def notify_error(agent_name: str, error: str) -> bool:
    """Notifica errore operativo con messaggio utente non tecnico."""
    logger.warning(f"Errore interno da notificare (agent={agent_name}): {error}")
    text = (
        f"{visible_agent_label(agent_name)}\n\n"
        f"{sanitize_user_error_message(error)}"
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
