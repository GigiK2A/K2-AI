"""Canale di controllo Telegram (bidirezionale), stdlib urllib only.
- invia "card" di approvazione con bottoni Approva/Rifiuta
- riceve le decisioni via long-polling (getUpdates) e le mappa ad azioni
Graceful: se TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID non sono settati → no-op.
Sicurezza: accetta callback solo da chat id in allowlist; callback_data porta solo
un id opaco (l'approval id), nessun segreto.
"""
from __future__ import annotations

import json
import os
import urllib.request


def enabled() -> bool:
    return bool(os.environ.get("TELEGRAM_BOT_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID"))


def _base() -> str:
    return f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_TOKEN']}"


def _allowed_chats() -> set[int]:
    ids = {os.environ.get("TELEGRAM_CHAT_ID", "")}
    ids |= set((os.environ.get("TELEGRAM_ALLOWED_CHAT_IDS", "") or "").split(","))
    out = set()
    for x in ids:
        x = x.strip()
        if x:
            try:
                out.add(int(x))
            except ValueError:
                pass
    return out


def _post(method: str, payload: dict, timeout: int = 35) -> dict:
    body = json.dumps(payload).encode()
    req = urllib.request.Request(f"{_base()}/{method}", data=body,
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310
        raw = r.read().decode("utf-8")
    return json.loads(raw) if raw else {}


def send_text(text: str) -> None:
    if not enabled():
        return
    try:
        _post("sendMessage", {"chat_id": os.environ["TELEGRAM_CHAT_ID"],
                              "text": text, "parse_mode": "Markdown"}, timeout=15)
    except Exception:
        pass


def send_approval_card(approval_id, title: str, body: str = "") -> None:
    """Manda una card con bottoni Approva/Rifiuta. callback_data = approve|reject:<id>."""
    if not enabled():
        return
    txt = f"*Approvazione richiesta*\n\n*{title}*\n{(body or '')[:400]}\n\nID: `{approval_id}`"
    try:
        _post("sendMessage", {
            "chat_id": os.environ["TELEGRAM_CHAT_ID"], "text": txt, "parse_mode": "Markdown",
            "reply_markup": {"inline_keyboard": [[
                {"text": "✅ Approva", "callback_data": f"approve:{approval_id}"},
                {"text": "❌ Rifiuta", "callback_data": f"reject:{approval_id}"}]]}}, timeout=15)
    except Exception:
        pass


def _answer(cq_id: str, text: str) -> None:
    try:
        _post("answerCallbackQuery", {"callback_query_id": cq_id, "text": text}, timeout=10)
    except Exception:
        pass


def poll_decisions(on_approve, on_reject, *, once: bool = False, max_loops: int | None = None) -> None:
    """Long-poll getUpdates; per ogni callback_query valida chiama on_approve/on_reject(id).
    once=True fa un solo giro (utile nei test). max_loops limita le iterazioni."""
    if not enabled():
        return
    allow = _allowed_chats()
    if not allow:  # fail-closed: senza chat allowlist valida NON si ascolta
        send_text("⚠️ TELEGRAM_CHAT_ID non valido (non numerico): canale decisioni disattivato.")
        return
    offset = 0
    loops = 0
    while True:
        try:
            data = _post("getUpdates", {"offset": offset, "timeout": 25,
                                        "allowed_updates": ["callback_query"]})
        except Exception:
            if once:
                return
            loops += 1
            if max_loops and loops >= max_loops:
                return
            continue
        for upd in data.get("result", []):
            offset = upd["update_id"] + 1
            cq = upd.get("callback_query")
            if not cq:
                continue
            chat_id = cq.get("message", {}).get("chat", {}).get("id")
            if chat_id not in allow:   # fail-closed (allow è garantito non vuoto)
                _answer(cq.get("id", ""), "Non autorizzato.")
                continue
            cqd = cq.get("data", "")
            cqid = cq.get("id", "")
            try:
                if cqd.startswith("approve:"):
                    on_approve(cqd.split(":", 1)[1]); _answer(cqid, "Approvato.")
                elif cqd.startswith("reject:"):
                    on_reject(cqd.split(":", 1)[1]); _answer(cqid, "Rifiutato.")
                else:
                    _answer(cqid, "Azione sconosciuta.")
            except Exception:
                _answer(cqid, "Errore nell'azione.")
        loops += 1
        if once or (max_loops and loops >= max_loops):
            return
