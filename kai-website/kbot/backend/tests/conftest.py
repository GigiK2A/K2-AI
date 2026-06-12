"""Env di test coerenti per TUTTA la suite, settate prima di qualsiasi import di app.
Evita la contaminazione da ordine-di-import (es. STRIPE_WEBHOOK_SECRET assente al
primo import → webhook 503 invece di 400). NB: INTERNAL_API_KEY volutamente NON
settata, così l'endpoint /diagnostics resta accessibile nei test."""
import os

for _k, _v in {
    "NEXT_PUBLIC_SUPABASE_URL": "https://x.supabase.co",
    "SUPABASE_SERVICE_ROLE_KEY": "x",
    "ANTHROPIC_API_KEY": "x",
    "STRIPE_SECRET_KEY": "sk_test_dummy",
    "STRIPE_WEBHOOK_SECRET": "whsec_test_dummy",
    "K2A_ENTITLEMENT_SECRET": "ci-secret-32bytes-minimum-length!",
}.items():
    os.environ.setdefault(_k, _v)
