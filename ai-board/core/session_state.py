"""
Stato conversazionale per-sessione Telegram.

Tiene in memoria un buffer rolling delle ultime N interazioni per chat_id.
Al primo accesso per un chat_id carica lo storico persistito (DB) per
garantire continuità anche dopo restart del processo.

Scopo: dare a Giuseppina la memoria a breve termine necessaria per
risolvere riferimenti impliciti ("aggiungila", "fallo", "quello di prima")
senza richiedere all'utente di ripetere il contesto.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from loguru import logger

_MAX_TURNS = 8            # turni mantenuti in memoria per sessione
_MAX_CHARS_PER_TURN = 1200  # tronca per non far esplodere il context del LLM


@dataclass
class ConversationTurn:
    user: str
    assistant: str
    ts: str = ""  # ISO timestamp


@dataclass
class TelegramSession:
    chat_id: str
    turns: deque[ConversationTurn] = field(default_factory=lambda: deque(maxlen=_MAX_TURNS))
    loaded_from_db: bool = False


# dict[chat_id, TelegramSession]
_sessions: dict[str, TelegramSession] = {}


def get_session(chat_id: str) -> TelegramSession:
    if chat_id not in _sessions:
        _sessions[chat_id] = TelegramSession(chat_id=chat_id)
    return _sessions[chat_id]


def _load_from_db(session: TelegramSession) -> None:
    """Carica gli ultimi turni dal DB al primo accesso (lazy, una volta per sessione).

    Non solleva eccezioni: se il DB non è disponibile continua in-memory.
    """
    if session.loaded_from_db:
        return
    session.loaded_from_db = True
    try:
        from core.conversation import load_agent_conversation_turns
        from db.models import AgentName

        turns = load_agent_conversation_turns(AgentName.ORCHESTRATOR, limit=5)
        loaded = 0
        for t in turns:
            user_msg = str(t.get("user_message") or "").strip()
            assistant_msg = str(t.get("assistant_message") or "").strip()
            if not user_msg and not assistant_msg:
                continue
            ts = str(t.get("created_at") or "")
            session.turns.append(ConversationTurn(
                user=user_msg[:_MAX_CHARS_PER_TURN],
                assistant=assistant_msg[:_MAX_CHARS_PER_TURN],
                ts=ts,
            ))
            loaded += 1
        if loaded:
            logger.debug(f"[session] {loaded} turni storici caricati per chat {session.chat_id}")
    except Exception as exc:
        logger.warning(f"[session] Impossibile caricare storico per chat {session.chat_id}: {exc}")


def add_turn(chat_id: str, user_message: str, assistant_message: str) -> None:
    """Aggiunge un nuovo turno alla sessione dopo ogni scambio completato."""
    session = get_session(chat_id)
    session.turns.append(ConversationTurn(
        user=user_message[:_MAX_CHARS_PER_TURN],
        assistant=assistant_message[:_MAX_CHARS_PER_TURN],
        ts=datetime.now(UTC).isoformat(),
    ))


def build_context_for_agent(chat_id: str) -> dict[str, Any]:
    """
    Costruisce il context dict da passare a Giuseppina.

    Include la conversation_history come lista di turni {role, content}.
    Carica lo storico dal DB al primo accesso (lazy).

    Se la sessione è vuota (prima volta assoluta), ritorna {} senza overhead.
    """
    session = get_session(chat_id)
    if not session.loaded_from_db:
        _load_from_db(session)

    if not session.turns:
        return {}

    history: list[dict[str, str]] = []
    for turn in session.turns:
        if turn.user:
            history.append({"role": "user", "content": turn.user})
        if turn.assistant:
            history.append({"role": "assistant", "content": turn.assistant})

    return {"conversation_history": history} if history else {}


def clear_session(chat_id: str) -> None:
    """Reset completo della sessione (es. dopo un logout o comando /start)."""
    _sessions.pop(chat_id, None)
