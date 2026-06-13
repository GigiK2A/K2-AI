"""Sincronizza il catalogo prodotti (spina dorsale unica) verso Supabase.

Fonte canonica: kai-website/lib/kbot/services-data.json (20 prodotti, stessa usata
da sito + K-BOT). Questo script la riversa nella tabella `suite_services` (letta
dagli agenti AIOS) e la ingesta in `aios_knowledge` (conoscenza condivisa).
Idempotente: upsert per id; knowledge aggiunta solo se mancante.

Run: cd aios && set -a && . ./.env && set +a && .venv/bin/python sync_suite.py
"""
import json
import os
import sys

from aios.supabase_rest import SupabaseREST
from aios.layers.knowledge import KnowledgeStore

DEFAULT_JSON = os.path.join(os.path.dirname(__file__), "..", "kai-website",
                            "lib", "kbot", "services-data.json")


def main(path: str = DEFAULT_JSON) -> None:
    with open(path, encoding="utf-8") as f:
        items = json.load(f)
    client = SupabaseREST(url=os.environ["AIOS_SUPABASE_URL"],
                          service_key=os.environ["AIOS_SUPABASE_SERVICE_KEY"])
    kb = KnowledgeStore(client)

    # knowledge già presenti per non duplicare
    existing = client.select("aios_knowledge", {"select": "titolo", "source": "eq.suite_services"})
    have = {r.get("titolo") for r in existing}

    n_cat, n_kb = 0, 0
    for s in items:
        client.upsert("suite_services", {
            "id": s["id"], "name": s["name"],
            "short_description": s.get("shortDescription"),
            "category": s.get("category"), "target_group": s.get("targetGroup"),
            "target": s.get("target"), "recommended_tier": s.get("recommendedTier"),
            "skills": s.get("skills") or [], "use_cases": s.get("useCases") or [],
            "tags": s.get("tags") or [], "pillar_url": s.get("pillarUrl"),
        }, on_conflict="id")
        n_cat += 1
        if s["name"] not in have:
            chunk = (f"{s['id']} · {s['name']} (tier {s.get('recommendedTier')}). "
                     f"{s.get('shortDescription','')}\nTarget: {s.get('target','')}\n"
                     f"Casi d'uso: " + "; ".join(s.get("useCases") or []))
            kb.add(source="suite_services", titolo=s["name"], chunk=chunk,
                   tags=s.get("category"))
            n_kb += 1
    print(f"suite_services upsert: {n_cat} · knowledge nuovi: {n_kb}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_JSON)
