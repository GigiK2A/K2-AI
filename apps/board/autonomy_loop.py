"""AIOS autonomy loop — un solo processo always-on (worker per deploy).

Cosa fa, in continuo e da solo:
- thread Telegram bidirezionale: ricevi le decisioni (Approva/Rifiuta) e puoi
  scrivere istruzioni in linguaggio naturale (stesso CommandRouter del cockpit);
- ad ogni tick (default 30 min) prepara le BOZZE di risposta alle mail nuove (L1);
- una volta al giorno fa girare i 6 agenti di dominio (propongono in coda L1);
- notifica su Telegram ogni nuova decisione in attesa.

Niente viene pubblicato/inviato senza la tua approvazione: il loop PROPONE, tu approvi.

Run locale:  cd aios && set -a && . ./.env && set +a && .venv/bin/python autonomy_loop.py
Env extra:   AIOS_TICK_SECONDS (default 1800), AIOS_AGENTS_HOUR (default 7 = ora UTC
             in cui far gartire gli agenti di dominio una volta al giorno).
"""
from __future__ import annotations

import os
import threading
import time

from aios.platform import build_platform
from aios.notify import telegram


def _draft_emails(platform) -> dict:
    conv = getattr(platform, "conversations", None)
    if conv is None:
        return {}
    try:
        return conv.draft_replies(limit=5)
    except Exception as exc:
        return {"error": str(exc)[:120]}


def _run_agents(platform) -> dict:
    out = {}
    for d in platform.domains():
        try:
            out[d] = platform.run(d)
        except Exception as exc:   # un dominio che fallisce non ferma gli altri
            out[d] = {"error": str(exc)[:120]}
    return out


# Massimo di card per tick. `seen` vive in memoria: dopo un riavvio l'intero
# arretrato risulterebbe "nuovo" e partirebbero centinaia di messaggi in pochi
# secondi (oltre i limiti Telegram). Con il cap l'arretrato viene smaltito poco
# per volta invece che tutto insieme.
MAX_CARD_PER_TICK = int(os.environ.get("AIOS_MAX_CARD_PER_TICK", "8"))


def _notify_new_pending(kernel, seen: set) -> int:
    """Manda su Telegram solo le decisioni in coda non ancora notificate."""
    n = 0
    try:
        for a in kernel.approvals.pending():
            if a.id in seen:
                continue
            if n >= MAX_CARD_PER_TICK:
                break
            seen.add(a.id)
            p = a.payload or {}
            telegram.send_approval_card(a.id, p.get("titolo") or a.action_key,
                                        p.get("contenuto") or "", p.get("azione"))
            n += 1
    except Exception:
        pass
    return n


def _notify_new_email_drafts(platform, seen_mail: set) -> int:
    """Propone su Telegram le bozze email mai inviate.

    Le bozze stanno in `email_messages`, non nella coda approvazioni: prima di questa
    funzione erano raggiungibili solo dal cockpit web ed è per questo che restavano
    ferme a 'bozza' a tempo indefinito."""
    conv = getattr(platform, "conversations", None)
    if conv is None:
        return 0
    n = 0
    try:
        for d in conv.bozze_in_attesa():
            did = d.get("id")
            if did is None or did in seen_mail:
                continue
            if n >= MAX_CARD_PER_TICK:
                break
            seen_mail.add(did)
            telegram.send_email_draft_card(did, str(d.get("to_email") or ""),
                                           str(d.get("subject") or ""),
                                           str(d.get("body") or ""))
            n += 1
    except Exception:
        pass
    return n


def _start_telegram(platform) -> None:
    """Canale di controllo Telegram in un thread daemon (se configurato)."""
    if not telegram.enabled():
        return
    k = platform.kernel

    def _bot():
        def on_approve(aid):
            # L'esito va LETTO: resolve_approval ritorna EXECUTED anche quando
            # l'attuatore ha fallito in silenzio (l'errore è dentro il risultato).
            res = k.resolve_approval(int(aid), approve=True)
            riga = telegram.esito_riga(res.esito)
            telegram.send_text(riga)
            return riga[:190]

        def on_reject(aid):
            k.resolve_approval(int(aid), approve=False, reason="rifiutato via Telegram")
            telegram.send_text("🚫 Rifiutato.")
            return "Rifiutato."

        def on_email_send(draft_id):
            conv = getattr(platform, "conversations", None)
            if conv is None:
                return "Email non disponibili."
            out = conv.send(str(draft_id), actor="telegram")
            if out.get("ok"):
                msg = "📤 Email inviata."
            else:
                err = out.get("errore") or (out.get("esito") or {}).get("errore") or "causa non riportata"
                msg = f"⚠️ NON inviata — {err}"
            telegram.send_text(msg)
            return msg[:190]

        def on_email_discard(draft_id):
            conv = getattr(platform, "conversations", None)
            if conv is None:
                return "Email non disponibili."
            out = conv.discard(str(draft_id))
            msg = "🗑 Bozza scartata." if out.get("ok") else f"⚠️ {out.get('errore', 'errore')}"
            telegram.send_text(msg)
            return msg[:190]

        def on_text(text):
            if platform.commands is None:
                telegram.send_text("Comandi non disponibili.")
                return
            res = platform.commands.handle(text, actor="telegram")
            telegram.send_command_card(res.to_dict())

        def on_confirm(token):
            out = platform.commands.confirm(int(token), actor="telegram")
            msg = ("✅ Eseguito." if out.get("ok") else
                   f"⚠️ Non eseguito: {out.get('errore') or ''}")
            telegram.send_text(msg)
            return msg[:190]

        telegram.poll_decisions(on_approve, on_reject, on_text=on_text, on_confirm=on_confirm,
                                on_email_send=on_email_send, on_email_discard=on_email_discard)

    threading.Thread(target=_bot, daemon=True, name="telegram-poll").start()


def main() -> None:
    platform = build_platform()
    k = platform.kernel
    tick = int(os.environ.get("AIOS_TICK_SECONDS", "1800"))
    agents_hour = int(os.environ.get("AIOS_AGENTS_HOUR", "7"))
    seen: set = set()
    seen_mail: set = set()
    last_agents_day = None

    _start_telegram(platform)
    if telegram.enabled():
        telegram.send_text("🟢 *K2-AI* è attivo. Preparo bozze e proposte, ti avviso qui. "
                           "Scrivimi un'istruzione quando vuoi.")

    print(f"AIOS autonomy loop avviato (tick {tick}s, agenti alle {agents_hour:02d}:00 UTC).")
    while True:
        now = time.gmtime()
        # bozze email ad ogni tick (economiche: scrivono solo se c'è mail nuova senza bozza)
        em = _draft_emails(platform)
        if em.get("bozze_create"):
            print(f"[{time.strftime('%H:%M', now)}] bozze email: {em['bozze_create']}")

        # agenti di dominio + follow-up lead 1 volta al giorno, all'ora prevista
        if now.tm_hour == agents_hour and last_agents_day != now.tm_yday:
            last_agents_day = now.tm_yday
            res = _run_agents(platform)
            print(f"[{time.strftime('%H:%M', now)}] agenti: {res}")
            conv = getattr(platform, "conversations", None)
            if conv is not None:
                try:
                    fu = conv.draft_lead_followups(limit=5)
                    print(f"[{time.strftime('%H:%M', now)}] follow-up lead: {fu}")
                except Exception as exc:
                    print(f"follow-up lead error: {exc}")

        nuovi = _notify_new_pending(k, seen)
        if nuovi:
            print(f"[{time.strftime('%H:%M', now)}] notificate {nuovi} nuove decisioni")
        # le bozze email vanno proposte esplicitamente: non passano dalla coda approvazioni
        nuove_mail = _notify_new_email_drafts(platform, seen_mail)
        if nuove_mail:
            print(f"[{time.strftime('%H:%M', now)}] proposte {nuove_mail} bozze email")
        time.sleep(tick)


if __name__ == "__main__":
    main()
