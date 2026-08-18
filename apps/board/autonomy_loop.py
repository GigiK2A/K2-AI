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
# secondi (oltre i limiti Telegram, che li scarta in silenzio). Con il cap
# l'arretrato viene smaltito poco per volta invece che perso tutto insieme.
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

        telegram.poll_decisions(on_approve, on_reject, on_text=on_text, on_confirm=on_confirm)

    threading.Thread(target=_bot, daemon=True, name="telegram-poll").start()


def _run_one_agent(platform, domain: str) -> dict:
    try:
        return platform.run(domain)
    except Exception as exc:
        return {"error": str(exc)[:120]}


def main() -> None:
    from aios.heartbeat import HeartbeatScheduler

    platform = build_platform()
    k = platform.kernel
    tick = int(os.environ.get("AIOS_TICK_SECONDS", "1800"))
    agents_hour = int(os.environ.get("AIOS_AGENTS_HOUR", "7"))
    seen: set = set()
    last_agents_day = None

    # Heartbeat per-agente (Paperclip #4), opt-in: se AIOS_HEARTBEATS è impostato
    # ogni dominio si sveglia col suo intervallo; altrimenti resta il batch giornaliero.
    hb = (HeartbeatScheduler.from_env(client=getattr(k, "_supabase", None))
          if HeartbeatScheduler.enabled() else None)

    _start_telegram(platform)
    if telegram.enabled():
        telegram.send_text("🟢 *K2-AI* è attivo. Preparo bozze e proposte, ti avviso qui. "
                           "Scrivimi un'istruzione quando vuoi.")

    mode = "heartbeat per-agente" if hb else f"batch alle {agents_hour:02d}:00 UTC"
    print(f"AIOS autonomy loop avviato (tick {tick}s, agenti: {mode}).")
    while True:
        now = time.gmtime()
        # bozze email ad ogni tick (economiche: scrivono solo se c'è mail nuova senza bozza)
        em = _draft_emails(platform)
        if em.get("bozze_create"):
            print(f"[{time.strftime('%H:%M', now)}] bozze email: {em['bozze_create']}")

        if hb is not None:
            # ── Ritmo per-agente: fa partire solo i domini "dovuti" a questo tick. ──
            now_epoch = time.time()
            due = hb.due(platform.domains(), now_epoch)
            for d in due:
                res = _run_one_agent(platform, d)
                hb.mark_ran(d, now_epoch)
                print(f"[{time.strftime('%H:%M', now)}] heartbeat {d}: {res}")
        elif now.tm_hour == agents_hour and last_agents_day != now.tm_yday:
            # ── Batch storico: tutti gli agenti una volta al giorno all'ora prevista. ──
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
        time.sleep(tick)


if __name__ == "__main__":
    main()
