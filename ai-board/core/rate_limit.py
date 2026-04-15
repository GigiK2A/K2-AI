"""
Rate limiting e guardrail costi per l'AI board.

Protegge da:
1. Burst di messaggi (max N richieste per finestra temporale per chat)
2. Loop automatici (stessa richiesta ripetuta troppo velocemente)
3. Retry esplosivi sulle API Notion (backoff esponenziale)
4. Costi incontrollati (token e chiamate API)

Tutto in-memory, leggero, zero dipendenze esterne.
Per un sistema single-founder questi limiti sono molto permissivi
ma proteggono dagli scenari peggiori (bug loop, retry Telegram, etc).
"""
from __future__ import annotations

import asyncio
import functools
import time
from collections import deque
from typing import Any, Callable, TypeVar

from loguru import logger

F = TypeVar("F", bound=Callable[..., Any])

# ─── Config ─────────────────────────────────────────────────────────────────
# Max messaggi per finestra
RATE_LIMIT_MAX_MESSAGES = 20       # per chat per finestra
RATE_LIMIT_WINDOW_SECONDS = 60     # finestra in secondi
RATE_LIMIT_WARN_THRESHOLD = 10     # log warning quando supera questa soglia

# Anti-loop: stessa stringa entro X secondi = sospetta duplicata
DEDUP_WINDOW_SECONDS = 5

# Retry Notion con backoff
NOTION_RETRY_MAX_ATTEMPTS = 3
NOTION_RETRY_BASE_DELAY = 1.0      # secondi
NOTION_RETRY_MAX_DELAY = 30.0

# ─── Store per-chat ──────────────────────────────────────────────────────────
# dict[chat_id, deque[timestamp]]
_message_timestamps: dict[str, deque[float]] = {}

# dict[chat_id, set[last_N_message_hashes]] per dedup
_recent_message_hashes: dict[str, deque[str]] = {}

# ─── Update-ID dedup (Telegram retry webhook) ────────────────────────────────
# Gli update_id Telegram sono globali per bot: uso dict singolo, non per-chat.
# Dopo 30s un update_id viene rimosso → nessuna perdita di memoria.
_seen_update_ids: dict[int, float] = {}
DEDUP_UPDATE_ID_TTL = 30  # secondi


def _get_timestamps(chat_id: str) -> deque[float]:
    if chat_id not in _message_timestamps:
        _message_timestamps[chat_id] = deque()
    return _message_timestamps[chat_id]


def check_rate_limit(chat_id: str) -> tuple[bool, str]:
    """
    Controlla se il chat_id ha superato il rate limit.
    Ritorna (allowed, reason).
    - allowed=True: ok, procedi
    - allowed=False: troppo veloce, blocca con reason
    """
    now = time.monotonic()
    timestamps = _get_timestamps(chat_id)

    # Rimuovi timestamp fuori finestra
    cutoff = now - RATE_LIMIT_WINDOW_SECONDS
    while timestamps and timestamps[0] < cutoff:
        timestamps.popleft()

    count = len(timestamps)

    if count >= RATE_LIMIT_MAX_MESSAGES:
        logger.warning(
            f"[rate_limit] Chat {chat_id} ha superato {RATE_LIMIT_MAX_MESSAGES} msg/{RATE_LIMIT_WINDOW_SECONDS}s"
        )
        return False, (
            f"Troppi messaggi in poco tempo ({count} negli ultimi {RATE_LIMIT_WINDOW_SECONDS}s). "
            "Aspetta un momento prima di continuare."
        )

    if count >= RATE_LIMIT_WARN_THRESHOLD:
        logger.warning(f"[rate_limit] Chat {chat_id}: alta frequenza ({count} msg nella finestra)")

    timestamps.append(now)
    return True, ""


def check_dedup(chat_id: str, message_text: str) -> bool:
    """
    Ritorna True se il messaggio è un duplicato recente (entro DEDUP_WINDOW_SECONDS).
    Telegram può fare retry su webhook → stesso testo arriva 2 volte.
    """
    msg_hash = f"{hash(message_text[:200])}"
    now = time.monotonic()

    if chat_id not in _recent_message_hashes:
        _recent_message_hashes[chat_id] = deque(maxlen=10)

    recent = _recent_message_hashes[chat_id]

    # Controlla se hash già visto di recente
    # Store: (hash, timestamp)
    for stored_hash, stored_ts in list(recent):
        if stored_hash == msg_hash and (now - stored_ts) < DEDUP_WINDOW_SECONDS:
            logger.debug(f"[rate_limit] Messaggio duplicato rilevato per chat {chat_id}")
            return True

    recent.append((msg_hash, now))
    return False


def check_dedup_update_id(update_id: int) -> bool:
    """
    Ritorna True se questo update_id è già stato processato di recente.

    Telegram può reinviare lo stesso update in caso di retry webhook o
    lentezza del bot. Questo garantisce idempotenza a livello di update.

    TTL: 30 secondi. GC automatico sopra 500 entry.
    Gli update_id Telegram sono sequenziali e globali per bot — nessuna
    collisione tra chat diverse.
    """
    now = time.monotonic()

    # GC leggero: rimuovi entry scadute quando il dict cresce
    if len(_seen_update_ids) > 500:
        cutoff = now - DEDUP_UPDATE_ID_TTL
        to_delete = [k for k, v in _seen_update_ids.items() if v < cutoff]
        for k in to_delete:
            del _seen_update_ids[k]

    if update_id in _seen_update_ids:
        if (now - _seen_update_ids[update_id]) < DEDUP_UPDATE_ID_TTL:
            logger.debug(f"[rate_limit] update_id={update_id} già processato (retry Telegram), drop")
            return True
        # Scaduto: aggiorna timestamp e riprocessa
    _seen_update_ids[update_id] = now
    return False


def reset_chat_limits(chat_id: str) -> None:
    """Reset dei limiti per un chat_id (utile per test)."""
    _message_timestamps.pop(chat_id, None)
    _recent_message_hashes.pop(chat_id, None)


# ─── Retry decorator per chiamate Notion/API esterne ────────────────────────
def retry_on_error(
    max_attempts: int = NOTION_RETRY_MAX_ATTEMPTS,
    base_delay: float = NOTION_RETRY_BASE_DELAY,
    max_delay: float = NOTION_RETRY_MAX_DELAY,
    retryable_exceptions: tuple = (Exception,),
    non_retryable_keywords: tuple = ("400", "401", "403", "404", "invalid", "not found"),
):
    """
    Decorator per retry con backoff esponenziale.
    Non fa retry su errori 4xx (client error) — solo su 5xx e network issues.

    Uso:
        @retry_on_error(max_attempts=3)
        def call_notion_api(...):
            ...
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exc: Exception | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as exc:
                    exc_str = str(exc).lower()
                    # Non riprovare su errori client
                    if any(kw in exc_str for kw in non_retryable_keywords):
                        raise

                    last_exc = exc
                    if attempt < max_attempts:
                        delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                        logger.warning(
                            f"[retry] {func.__name__} tentativo {attempt}/{max_attempts} fallito: {exc}. "
                            f"Retry tra {delay:.1f}s"
                        )
                        time.sleep(delay)
                    else:
                        logger.error(f"[retry] {func.__name__} fallito dopo {max_attempts} tentativi: {exc}")

            raise last_exc  # type: ignore[misc]
        return wrapper  # type: ignore[return-value]
    return decorator


async def retry_on_error_async(
    coro_func: Callable,
    *args,
    max_attempts: int = NOTION_RETRY_MAX_ATTEMPTS,
    base_delay: float = NOTION_RETRY_BASE_DELAY,
    max_delay: float = NOTION_RETRY_MAX_DELAY,
    **kwargs,
) -> Any:
    """
    Versione async del retry per coroutine.
    Usa asyncio.sleep (non bloccante) tra i tentativi.
    """
    last_exc: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            return await coro_func(*args, **kwargs)
        except Exception as exc:
            exc_str = str(exc).lower()
            non_retryable = ("400", "401", "403", "404", "invalid", "not found")
            if any(kw in exc_str for kw in non_retryable):
                raise

            last_exc = exc
            if attempt < max_attempts:
                delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                logger.warning(
                    f"[retry_async] {coro_func.__name__} tentativo {attempt}/{max_attempts}: {exc}. "
                    f"Retry tra {delay:.1f}s"
                )
                await asyncio.sleep(delay)

    raise last_exc  # type: ignore[misc]
