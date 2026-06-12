"""K2-AI · canale di controllo Telegram (bidirezionale).
Manda le decisioni in coda (L1) su Telegram con bottoni Approva/Rifiuta, poi resta
in ascolto e applica la decisione al kernel (stessa azione del cockpit web).

Run: cd aios && set -a && . ./.env && set +a && .venv/bin/python telegram_bot.py
Env: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID (+ Supabase/Anthropic come il cockpit).
Senza token → esce con messaggio (graceful).
"""
from aios.platform import build_platform
from aios.notify import telegram


def main() -> None:
    if not telegram.enabled():
        print("Telegram disattivato: imposta TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID.")
        return
    platform = build_platform()
    k = platform.kernel

    pending = k.approvals.pending()
    for a in pending:
        p = a.payload or {}
        telegram.send_approval_card(a.id, p.get("titolo") or a.action_key, p.get("contenuto") or "")
    telegram.send_text(f"K2-AI: {len(pending)} decisioni in coda. Approva/rifiuta qui o dal cockpit.")

    def on_approve(aid):
        k.resolve_approval(int(aid), approve=True)

    def on_reject(aid):
        k.resolve_approval(int(aid), approve=False, reason="rifiutato via Telegram")

    print("In ascolto su Telegram (Ctrl-C per uscire)…")
    telegram.poll_decisions(on_approve, on_reject)


if __name__ == "__main__":
    main()
