"""Batch robustezza — esegue il PoC su tutti i casi PMI in-target (un processo per
caso = stato pulito, come in prod) e aggrega le misure.

NB: con quant-lite (snapshot placeholder + assunzioni scelte dal modello), questo
misura la ROBUSTEZZA DELL'ORCHESTRAZIONE (completa? passa i gate? provenienza
verificata? varianza tra run?), NON la correttezza dei numeri — quella aspetta il
k2a-mcp-quant vero + le assunzioni nei tool (criterio Luca #1).

Uso: set -a; . ../kai-website/kbot/backend/.env.local; set +a
     .venv/bin/python run_batch.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

POC_DIR = Path(__file__).parent
PY = POC_DIR / ".venv" / "bin" / "python"
CASES = sorted((POC_DIR / "data" / "cases").glob("*.json"))


def main() -> int:
    if not CASES:
        print("nessun caso in data/cases/", file=sys.stderr)
        return 2
    rows = []
    for case in CASES:
        name = case.stem
        out_dir = POC_DIR / "out" / "cases" / name
        print(f"\n===== CASO: {name} =====")
        r = subprocess.run([str(PY), str(POC_DIR / "run_poc.py"), str(case), str(out_dir)],
                           cwd=POC_DIR, capture_output=False)
        m = json.loads((out_dir / "metrics.json").read_text()) if (out_dir / "metrics.json").exists() else {"case": name, "error": f"exit {r.returncode}"}
        rows.append(m)

    delivered = [r for r in rows if r.get("delivered")]
    summary = {
        "n_casi": len(rows),
        "consegnati": len(delivered),
        "falliti": len(rows) - len(delivered),
        "provenienza_verificata_su_consegnati": sum(1 for r in delivered if r.get("provenance_verified")),
        "costo_medio_usd": round(sum(r.get("total_cost_usd") or 0 for r in delivered) / len(delivered), 3) if delivered else None,
        "durata_media_s": round(sum(r.get("duration_s") or 0 for r in delivered) / len(delivered), 1) if delivered else None,
        "tool_calls_min_max": [min((r.get("tool_calls") or 0 for r in delivered), default=0), max((r.get("tool_calls") or 0 for r in delivered), default=0)],
        "gate_blocks_totali": sum(r.get("gate_blocks_stop") or 0 for r in rows),
        "per_caso": rows,
    }
    out = POC_DIR / "out" / "batch_summary.json"
    out.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    print("\n========== BATCH SUMMARY ==========")
    print(json.dumps({k: v for k, v in summary.items() if k != "per_caso"}, indent=2))
    print(f"dettaglio: {out}")
    return 0 if summary["falliti"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
