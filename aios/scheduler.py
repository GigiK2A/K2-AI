"""AIOS scheduler — run all domain agents (for cron / always-on deploy).
Each agent reads its sensors, proposes, and files proposals to the L1 approval
queue (human approves in the cockpit). Nothing is published autonomously.
Env: as serve_cockpit. Run once: cd aios && set -a && . ./.env && set +a && .venv/bin/python scheduler.py
Cron example (daily 07:00): 0 7 * * *  cd /path/aios && ./.venv/bin/python scheduler.py
"""
from aios.platform import build_platform


def run_all() -> dict:
    platform = build_platform()
    results = {}
    for domain in platform.domains():
        try:
            results[domain] = platform.run(domain)
        except Exception as exc:  # one domain failing must not stop the others
            results[domain] = {"error": str(exc)}
    return results


if __name__ == "__main__":
    out = run_all()
    for domain, r in out.items():
        print(f"{domain}: {r}")
