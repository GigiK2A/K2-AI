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


def azione_riga(azione) -> str:
    """Riga leggibile di COSA esegue l'azione su Approva (no approvazione cieca)."""
    if not isinstance(azione, dict):
        return "📋 Crea un task (nessuna scrittura specifica)"
    canale = str(azione.get("canale") or "").lower()
    if canale in {"n8n", "esterno", "external", "webhook"}:
        return f"🌐 ESTERNO via n8n · workflow «{azione.get('workflow', '?')}»"
    if azione.get("tipo") == "ddl" or azione.get("sql"):
        return "🛠 Modifica SCHEMA DB (DDL)"
    op = str(azione.get("op") or "").lower()
    tab = azione.get("tabella") or azione.get("table") or "?"
    m = f" · {azione.get('match')}" if azione.get("match") else ""
    if op == "delete":
        return f"🗑 ELIMINA da {tab}{m}"
    if op == "update":
        return f"✏️ Aggiorna {tab}{m}"
    if op == "insert":
        return f"➕ Crea in {tab}"
    return f"⚙️ {op or 'azione'} su {tab}"


def send_email_draft_card(draft_id, to: str, subject: str, body: str = "") -> None:
    """Card di una bozza email in uscita, con Invia/Scarta.

    Le bozze vivono in `email_messages`, non nella coda approvazioni: senza questa card
    non erano raggiungibili da Telegram e restavano ferme a 'bozza' per sempre (123 ad
    agosto 2026). L'invio è un'azione ESTERNA: parte solo su clic dell'owner."""
    if not enabled():
        return
    txt = (f"*Bozza email da approvare*\n\n*A:* {to or '—'}\n*Oggetto:* {subject or '—'}\n\n"
           f"{(body or '')[:600]}\n\n⚙️ *Su Invia:* 🌐 ESTERNO · parte la mail al destinatario\n"
           f"ID: `{draft_id}`")
    try:
        _post("sendMessage", {
            "chat_id": os.environ["TELEGRAM_CHAT_ID"], "text": txt, "parse_mode": "Markdown",
            "reply_markup": {"inline_keyboard": [[
                {"text": "📤 Invia", "callback_data": f"mailok:{draft_id}"},
                {"text": "🗑 Scarta", "callback_data": f"mailno:{draft_id}"}]]}}, timeout=15)
    except Exception:
        pass


def esito_riga(esito) -> str:
    """Riga leggibile di COSA è successo davvero dopo un Approva.

    `esito` è il dict prodotto da kernel.esito_effettivo (None = il tool non riporta
    un esito strutturato). Serve a non dire mai 'eseguito' quando l'attuatore ha
    fallito in silenzio, e a non spacciare per fatto un update che non ha trovato
    nessuna riga."""
    if esito is None:
        return "✅ Approvato ed eseguito."
    if not esito.get("ok"):
        return f"⚠️ Approvato ma NON eseguito — {esito.get('errore') or 'causa non riportata'}"
    canale = esito.get("canale")
    if canale == "n8n":
        return f"✅ Inviato a n8n · workflow «{esito.get('workflow', '?')}»"
    if canale == "meta":
        return "✅ Eseguito su Meta"
    tab, op = esito.get("tabella"), esito.get("op")
    righe = esito.get("righe")
    if isinstance(righe, int) and righe == 0 and op in ("update", "delete"):
        # 0 righe toccate non è un successo: l'intenzione non si è materializzata.
        return f"⚠️ Approvato ma NULLA cambiato — nessuna riga di {tab} corrisponde al match"
    if tab and op:
        n = f" ({righe} righe)" if isinstance(righe, int) else ""
        return f"✅ Eseguito: {op} su {tab}{n}"
    return "✅ Approvato ed eseguito."


def send_approval_card(approval_id, title: str, body: str = "", azione=None) -> None:
    """Manda una card con bottoni Approva/Rifiuta. callback_data = approve|reject:<id>.
    Mostra anche COSA esegue l'azione (azione) per evitare approvazioni cieche."""
    if not enabled():
        return
    riga = f"\n\n⚙️ *Su Approva:* {azione_riga(azione)}" if azione is not None else ""
    txt = f"*Approvazione richiesta*\n\n*{title}*\n{(body or '')[:400]}{riga}\n\nID: `{approval_id}`"
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
                   on_email_send=None, on_email_discard=None,
                   once: bool = False, max_loops: int | None = None) -> None:
    """Long-poll getUpdates. callback_query: approve:/reject:/cmdok:<id>. Se on_text è
    dato, ascolta anche i messaggi di testo (istruzioni in linguaggio naturale).
    once=True fa un solo giro (test). max_loops limita le iterazioni.

    I gestori possono ritornare una stringa: viene mostrata nel toast al posto di un
    esito generico, così chi clicca legge cosa è successo davvero e non un 'fatto'
    fisso. Un gestore che solleva porta l'errore nel toast, non un 'Errore' muto."""
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
                        # il toast riporta l'esito reale se il gestore lo restituisce
                        _answer(cqid, on_approve(cqd.split(":", 1)[1]) or "Approvato.")
                    elif cqd.startswith("reject:"):
                        _answer(cqid, on_reject(cqd.split(":", 1)[1]) or "Rifiutato.")
                    elif cqd.startswith("cmdok:") and on_confirm:
                        _answer(cqid, on_confirm(cqd.split(":", 1)[1]) or "Eseguito.")
                    elif cqd.startswith("mailok:") and on_email_send:
                        _answer(cqid, on_email_send(cqd.split(":", 1)[1]) or "Inviata.")
                    elif cqd.startswith("mailno:") and on_email_discard:
                        _answer(cqid, on_email_discard(cqd.split(":", 1)[1]) or "Scartata.")
                    else:
                        _answer(cqid, "Azione sconosciuta.")
                except Exception as exc:
                    _answer(cqid, f"Errore: {str(exc)[:150]}")
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
