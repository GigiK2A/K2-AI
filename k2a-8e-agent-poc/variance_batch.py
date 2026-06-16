"""Batch + varianza (AZIONE 5 di Luca).

Completa i 4 casi PMI in-target + ripete UN caso N volte per misurare la varianza
dell'orchestrazione (stesso input → struttura/provenienza/gate consistenti?).
Non dipende dallo snapshot → si fa subito con quant-lite. Un processo per run.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

POC = Path(__file__).parent
PY = POC / ".venv" / "bin" / "python"
RUN = POC / "run_poc.py"
CASES = POC / "data" / "cases"

# Re-run QUANT VERO: 4 casi in-target FRESCHI (01 = run1) + 01 ripetuto 2× → varianza n=3.
JOBS = [
    ("01-studio-ingegneria", CASES / "01-studio-ingegneria.json", POC / "out/cases/01-studio-ingegneria"),
    ("02-manifatturiero-turnaround", CASES / "02-manifatturiero-turnaround.json", POC / "out/cases/02-manifatturiero-turnaround"),
    ("03-servizi-it-acquisizione", CASES / "03-servizi-it-acquisizione.json", POC / "out/cases/03-servizi-it-acquisizione"),
    ("04-hospitality-investimento", CASES / "04-hospitality-investimento.json", POC / "out/cases/04-hospitality-investimento"),
    ("VAR-studio-run2", CASES / "01-studio-ingegneria.json", POC / "out/variance/studio-run2"),
    ("VAR-studio-run3", CASES / "01-studio-ingegneria.json", POC / "out/variance/studio-run3"),
]


def _metrics(out_dir: Path) -> dict:
    p = out_dir / "metrics.json"
    return json.loads(p.read_text()) if p.exists() else {"error": "no metrics"}


def main() -> int:
    rows = []
    for name, case, out_dir in JOBS:
        print(f"\n===== {name} =====", flush=True)
        subprocess.run([str(PY), str(RUN), str(case), str(out_dir)], cwd=POC)
        m = _metrics(out_dir)
        m["job"] = name
        rows.append(m)

    # includi il run originale di studio (out/cases/01-...) per varianza a 3
    orig = _metrics(POC / "out/cases/01-studio-ingegneria")
    orig["job"] = "VAR-studio-run1"
    studio = [orig] + [r for r in rows if r["job"].startswith("VAR-studio")]

    def spread(key):
        vals = [r.get(key) for r in studio if isinstance(r.get(key), (int, float))]
        return {"min": min(vals), "max": max(vals), "n": len(vals)} if vals else None

    summary = {
        "in_target": [
            {"job": r["job"], "delivered": r.get("delivered"), "provenance": r.get("provenance_verified"),
             "tool_calls": r.get("tool_calls"), "cost_usd": r.get("total_cost_usd"), "dur_s": r.get("duration_s")}
            for r in rows if not r["job"].startswith("VAR")
        ],
        "varianza_studio_n3": {
            "tutti_delivered": all(r.get("delivered") for r in studio),
            "tutti_provenance_ok": all(r.get("provenance_verified") for r in studio),
            "tool_calls": spread("tool_calls"),
            "cost_usd": spread("total_cost_usd"),
            "durata_s": spread("duration_s"),
        },
    }
    out = POC / "out" / "batch_variance_summary.json"
    out.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print("\n========== BATCH+VARIANZA ==========")
    print(json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
