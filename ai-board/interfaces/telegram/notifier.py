import asyncio
import hashlib
import json
import re
import time
from datetime import UTC, datetime
from typing import Optional

from loguru import logger
from telegram import Bot, InlineKeyboardMarkup

from core.config import settings
from core.text import markdown_to_telegram_html
from db.client import get_service_client
from interfaces.telegram.presentation import (
    clean_preview,
    sanitize_user_error_message,
    visible_agent_label,
)

_bot: Optional[Bot] = None
_INFORMATIONAL_DEDUP_TTL_SECONDS = 180
_recent_informational_hashes: dict[str, float] = {}
_JSON_FENCE_RE = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL | re.IGNORECASE)


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


def _claim_dedup_key(dedup_key: str, ttl_seconds: int) -> bool:
    now_monotonic = time.monotonic()

    # Dedup locale in-process
    for key, ts in list(_recent_informational_hashes.items()):
        if (now_monotonic - ts) > ttl_seconds:
            _recent_informational_hashes.pop(key, None)
    if dedup_key in _recent_informational_hashes:
        return False

    # Dedup distribuita best-effort (via shared_memory su Supabase)
    try:
        client = get_service_client()
        rows = (
            client.table("shared_memory")
            .select("key,updated_at")
            .eq("key", dedup_key)
            .limit(1)
            .execute()
            .data
            or []
        )
        if rows:
            updated_at = str(rows[0].get("updated_at") or "").replace("Z", "+00:00")
            if updated_at:
                updated_dt = datetime.fromisoformat(updated_at)
                if updated_dt.tzinfo is None:
                    updated_dt = updated_dt.replace(tzinfo=UTC)
                age_s = (datetime.now(UTC) - updated_dt).total_seconds()
                if age_s < ttl_seconds:
                    _recent_informational_hashes[dedup_key] = now_monotonic
                    return False

        client.table("shared_memory").upsert(
            {
                "key": dedup_key,
                "value": {"type": "scheduler_dedup", "claimed_at": datetime.now(UTC).isoformat()},
                "category": "scheduler",
                "updated_by": "telegram_notifier",
                "updated_at": datetime.now(UTC).isoformat(),
            }
        ).execute()
    except Exception as exc:
        logger.warning(f"Dedup distribuita non disponibile ({dedup_key}): {exc}")

    _recent_informational_hashes[dedup_key] = now_monotonic
    return True


async def notify_informational(
    agent_name: str,
    content_type: str,
    text: str,
    dedup_key: str | None = None,
    dedup_ttl_seconds: int = _INFORMATIONAL_DEDUP_TTL_SECONDS,
) -> bool:
    """Invia un messaggio informativo con deduplica opzionale per evento."""
    label = visible_agent_label(f"scheduler:{content_type}") or visible_agent_label(agent_name)
    body = _normalize_informational_body(str(text or "").strip(), content_type=content_type)
    if body.lower().startswith(label.lower()):
        body = body[len(label):].lstrip("\n ")

    payload = f"{label}\n\n{body}".strip()

    # Idempotenza: per dedup_key usa chiave evento, altrimenti hash payload.
    digest = dedup_key or hashlib.sha256(payload.encode("utf-8", errors="ignore")).hexdigest()
    if not _claim_dedup_key(digest, max(30, int(dedup_ttl_seconds))):
        logger.info("Notifica informativa duplicata rilevata: invio saltato")
        return True

    return await send_message(markdown_to_telegram_html(payload), parse_mode="HTML")


def _normalize_informational_body(text: str, content_type: str) -> str:
    """Pulisce output grezzi (es. JSON/codefence) per i messaggi Telegram."""
    raw = (text or "").strip()
    if not raw:
        return "Aggiornamento non disponibile."

    # Rimuovi fence markdown se presenti.
    fence_match = _JSON_FENCE_RE.match(raw)
    if fence_match:
        raw = fence_match.group(1).strip()

    # weekly_plan può accidentalmente uscire come JSON dell'orchestrator.
    if content_type == "weekly_plan":
        parsed = _try_parse_json(raw)
        if isinstance(parsed, dict) and isinstance(parsed.get("tasks"), list):
            tasks = parsed.get("tasks") or []
            lines = []
            plan_title = str(parsed.get("plan_title") or "").strip()
            objective = str(parsed.get("objective") or "").strip()
            if plan_title:
                lines.append(f"🎯 **{plan_title}**")
            if objective:
                lines.append(objective)
            if tasks:
                lines.append("")
                lines.append("📋 **Task prioritari**")
                for idx, item in enumerate(tasks[:5], start=1):
                    title = str(item.get("title") or "Task")
                    owner = str(item.get("agent") or "").strip()
                    owner_txt = f" ({owner})" if owner else ""
                    lines.append(f"{idx}. {title}{owner_txt}")
            formatted = "\n".join(lines).strip()
            if formatted:
                return formatted

    # Fallback: messaggio originale.
    return raw


def _try_parse_json(raw: str) -> dict | list | None:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None


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
