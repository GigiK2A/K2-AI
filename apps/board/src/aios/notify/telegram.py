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


def send_command_card(res: dict) -> None:
    """Manda l'esito di un'istruzione: valutazione + cosa è stato fatto subito +
    bottoni 'Conferma' per le azioni esterne/sensibili (callback cmdok:<id>)."""
    if not enabled():
        return
    lines = []
    if res.get("valutazione"):
        lines.append(f"_{res['valutazione']}_")
    if res.get("risposta"):
        lines.append(res["risposta"])
    for e in res.get("eseguite", []):
        lines.append(f"✅ Fatto: {e.get('descrizione','')} ({e.get('tabella','')})")
    for x in res.get("rifiutate", []):
        lines.append(f"⛔ Rifiutato: {x.get('descrizione','')} — {x.get('motivo','')}")
    rows = [[{"text": f"✅ Conferma: {c.get('descrizione','')[:40]}",
              "callback_data": f"cmdok:{c['id']}"}]
            for c in res.get("da_confermare", []) if c.get("id") is not None]
    payload = {"chat_id": os.environ["TELEGRAM_CHAT_ID"],
               "text": ("\n".join(lines) or "Nessuna azione."), "parse_mode": "Markdown"}
    if rows:
        payload["reply_markup"] = {"inline_keyboard": rows}
    try:
        _post("sendMessage", payload, timeout=15)
    except Exception:
        pass


def poll_decisions(on_approve, on_reject, *, on_text=None, on_confirm=None,
                   once: bool = False, max_loops: int | None = None) -> None:
    """Long-poll getUpdates. callback_query: approve:/reject:/cmdok:<id>. Se on_text è
    dato, ascolta anche i messaggi di testo (istruzioni in linguaggio naturale).
    once=True fa un solo giro (test). max_loops limita le iterazioni."""
    if not enabled():
        return
    allow = _allowed_chats()
    if not allow:  # fail-closed: senza chat allowlist valida NON si ascolta
        send_text("⚠️ TELEGRAM_CHAT_ID non valido (non numerico): canale disattivato.")
        return
    updates = ["callback_query"] + (["message"] if on_text else [])
    offset = 0
    loops = 0
    while True:
        try:
            data = _post("getUpdates", {"offset": offset, "timeout": 25,
                                        "allowed_updates": updates})
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
            if cq:
                chat_id = cq.get("message", {}).get("chat", {}).get("id")
                if chat_id not in allow:   # fail-closed (allow garantito non vuoto)
                    _answer(cq.get("id", ""), "Non autorizzato.")
                    continue
                cqd = cq.get("data", "")
                cqid = cq.get("id", "")
                try:
                    if cqd.startswith("approve:"):
                        on_approve(cqd.split(":", 1)[1]); _answer(cqid, "Approvato.")
                    elif cqd.startswith("reject:"):
                        on_reject(cqd.split(":", 1)[1]); _answer(cqid, "Rifiutato.")
                    elif cqd.startswith("cmdok:") and on_confirm:
                        on_confirm(cqd.split(":", 1)[1]); _answer(cqid, "Eseguito.")
                    else:
                        _answer(cqid, "Azione sconosciuta.")
                except Exception:
                    _answer(cqid, "Errore nell'azione.")
                continue
            msg = upd.get("message")
            if msg and on_text:
                chat_id = msg.get("chat", {}).get("id")
                text = (msg.get("text") or "").strip()
                if chat_id not in allow:   # fail-closed
                    continue
                if text and not text.startswith("/"):
                    try:
                        on_text(text)
                    except Exception:
                        send_text("Errore nell'elaborare l'istruzione.")
        loops += 1
        if once or (max_loops and loops >= max_loops):
            return
