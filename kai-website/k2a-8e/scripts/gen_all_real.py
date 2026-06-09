"""Genera TUTTI i boost reali (un servizio per tipo di skill) in un colpo solo.

Uso (serve ANTHROPIC_API_KEY con credito):
    export ANTHROPIC_API_KEY="$(grep '^ANTHROPIC_API_KEY=' \
        ../kbot/backend/.env.local | head -1 | sed 's/^ANTHROPIC_API_KEY=//' | tr -d '\"')"
    .venv/bin/python scripts/gen_all_real.py

Output: per ogni boost, status + assembly + token + path PDF. I file finiscono in
_out/all-<skill>/. Niente scrittura su stato prod. Pensato per la verifica finale
dell'intero catalogo dopo una ricarica crediti.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import assets, jobs, pipeline  # noqa: E402
from app.settings import OUT_DIR  # noqa: E402

# input plausibile e generico (il motore ancora i fatti dallo snapshot, non da qui)
INPUTS = {
    "ragione_sociale": "Acme Manifatturiera SRL",
    "settore": "manifatturiero",
    "dipendenti": 18,
    "fatturato": 2400000,
    "regime": "ordinario",
    "tipo_contratto": "fornitura",
    "sito": "acme.it",
    "ecommerce": True,
}


def main() -> int:
    man = assets.manifest()
    # un service_id per ogni skill distinta (evita doppioni dello stesso boost)
    seen: dict[str, str] = {}
    for sid, entry in man.items():
        seen.setdefault(entry["skill"], sid)

    rows = []
    for skill, sid in seen.items():
        jid = f"all-{skill}"
        jobs._JOBS[jid] = {"job_id": jid, "status": "routed"}
        t = time.time()
        try:
            pipeline.run(jid, sid, INPUTS, "FULL")
        except Exception as e:
            rows.append((skill, sid, f"EXC {type(e).__name__}", 0, "-"))
            print(f"### {skill:30} EXC {e}")
            continue
        j = jobs.get(jid) or {}
        st = j.get("status")
        fil = (j.get("meta") or {}).get("filiera") or {}
        d = OUT_DIR / jid
        pdf = d / "deliverable.pdf"
        js = d / "deliverable.json"
        chars = len(js.read_text(encoding="utf-8")) if js.exists() else 0
        kb = pdf.stat().st_size // 1024 if pdf.exists() else 0
        rows.append((skill, sid, st, chars, f"{kb}KB" if kb else "no-pdf"))
        print(f"### {skill:30} {st:9} {time.time()-t:5.0f}s "
              f"assembly={fil.get('assembly')} chars={chars} pdf={kb}KB")
        if st not in ("rendered", "done", "completed"):
            print("    validation:", json.dumps(j.get("validation"), ensure_ascii=False)[:300])

    ok = sum(1 for r in rows if r[2] in ("rendered", "done", "completed"))
    print(f"\n=== {ok}/{len(rows)} boost generati ===")
    return 0 if ok == len(rows) else 1


if __name__ == "__main__":
    sys.exit(main())
