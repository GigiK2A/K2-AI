#!/usr/bin/env python3
"""Avvia il backend K-BOT IN LOCALE per misurare una modifica senza pubblicarla.

Supabase è finto (in memoria: le sessioni non toccano nessun database vero), l'LLM è quello vero dello
shim e il corpus Normattiva è quello vero. Serve a confrontare due configurazioni dello STESSO codice
(es. KBOT_NORME_EVIDENCE=0 contro 1) con il banco di prova, nello stesso momento e sullo stesso modello:

    # due istanze identiche tranne il flag
    python3 evals/server_locale.py --porta 8123 --evidenza 0 &
    python3 evals/server_locale.py --porta 8124 --evidenza 1 &
    python3 evals/run_eval.py --base-url http://127.0.0.1:8123/api/kbot --etichetta locale-senza
    python3 evals/run_eval.py --base-url http://127.0.0.1:8124/api/kbot --etichetta locale-con

Cosa NON è uguale alla produzione: niente ricerca web (nessuna chiave OpenAI), niente PostHog, niente
Stripe. Il confronto fra le due istanze è alla pari; il confronto con i risultati della produzione no.

Richiede le dipendenze di requirements.txt (uvicorn compreso) e, per i test e il Supabase finto, la
cartella tests/ del repo. La chiave dello shim si legge da un file e non viene mai stampata.
"""
from __future__ import annotations

import argparse
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(AQUI)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--porta", type=int, required=True)
    ap.add_argument("--evidenza", choices=("0", "1"), default="1", help="KBOT_NORME_EVIDENCE (default 1)")
    ap.add_argument("--corpus", default=os.path.expanduser("~/normattiva_ai/normattiva.db"),
                    help="normattiva.db (default ~/normattiva_ai/normattiva.db)")
    ap.add_argument("--shim-url", default="http://127.0.0.1:4000")
    ap.add_argument("--shim-chiave-file", default=os.path.expanduser("~/.k2a-local/shim_master_key.txt"))
    ap.add_argument("--modello", default="k2a-kbot", help="nome della rotta sullo shim")
    ap.add_argument("--extra-env", action="append", default=[], metavar="CHIAVE=VALORE",
                    help="altre variabili d'ambiente (ripetibile), es. KBOT_NORME_MAX_RIF=3")
    a = ap.parse_args()

    # ambiente PRIMA di qualsiasi import dell'app (come tests/conftest.py)
    for k, v in {"NEXT_PUBLIC_SUPABASE_URL": "https://locale.invalid", "SUPABASE_SERVICE_ROLE_KEY": "locale",
                 "STRIPE_SECRET_KEY": "sk_test_locale", "STRIPE_WEBHOOK_SECRET": "whsec_locale",
                 "K2A_ENTITLEMENT_SECRET": "locale-secret-32bytes-minimum-length!"}.items():
        os.environ.setdefault(k, v)
    for k in ("OPENAI_API_KEY", "INTERNAL_API_KEY"):
        os.environ.pop(k, None)                       # niente ricerca web, nessuna chiave interna
    chiave = open(a.shim_chiave_file, encoding="utf-8").read().strip()
    os.environ["ANTHROPIC_BASE_URL"] = a.shim_url
    os.environ["ANTHROPIC_API_KEY"] = chiave
    os.environ["ANTHROPIC_MODEL"] = a.modello
    os.environ["NORMATTIVA_DB_PATH"] = a.corpus
    os.environ["KBOT_NORME_EVIDENCE"] = a.evidenza
    os.environ["KBOT_FREE_MODE"] = "1"
    for kv in a.extra_env:
        k, _, v = kv.partition("=")
        os.environ[k] = v

    sys.path.insert(0, BACKEND)
    sys.path.insert(0, os.path.join(BACKEND, "tests"))
    from test_e2e_scenarios import FakeSupabase                 # noqa: E402  (Supabase in memoria)

    fake = FakeSupabase()
    import app.lib.supabase_admin as sa                          # noqa: E402
    import app.lib.sessions as sess                              # noqa: E402
    sa.get_admin_client = lambda: fake
    sess.get_admin_client = lambda: fake
    try:
        import app.api.upload as up                              # noqa: E402
        up.get_admin_client = lambda: fake
    except Exception:
        pass

    import uvicorn                                               # noqa: E402
    from app.main import app                                     # noqa: E402
    print(f"K-BOT locale su :{a.porta} | evidenza={a.evidenza} | modello={a.modello} | corpus={a.corpus}", flush=True)
    uvicorn.run(app, host="127.0.0.1", port=a.porta, log_level="warning")


if __name__ == "__main__":
    main()
