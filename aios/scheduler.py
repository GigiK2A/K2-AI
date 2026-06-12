"""AIOS scheduler — run all domain agents (for cron / always-on deploy).
Each agent reads its sensors, proposes, and files proposals to the L1 approval
queue (human approves in the cockpit). Nothing is published autonomously.
Env: as serve_cockpit. Run once: cd aios && set -a && . ./.env && set +a && .venv/bin/python scheduler.py
Cron example (daily 07:00): 0 7 * * *  cd /path/aios && ./.venv/bin/python scheduler.py
"""
from aios.platform import build_platform
from aios.notify import telegram


def run_all() -> dict:
    platform = build_platform()
    results = {}
    for domain in platform.domains():
        try:
            results[domain] = platform.run(domain)
        except Exception as exc:  # one domain failing must not stop the others
            results[domain] = {"error": str(exc)}
    # Notifica Telegram delle decisioni in coda (no-op se Telegram non configurato)
    if telegram.enabled():
        try:
            for a in platform.kernel.approvals.pending():
                p = a.payload or {}
                telegram.send_approval_card(a.id, p.get("titolo") or a.action_key,
                                            p.get("contenuto") or "")
        except Exception:
            pass
    return results


if __name__ == "__main__":
    out = run_all()
    for domain, r in out.items():
        print(f"{domain}: {r}")
