"""Audit trace del PoC — requisito pass/fail (deliverable venduto, contestabile).

Registra: versione skill, hash input, ogni tool chiamato (con output per i tool
quant), scelte di metodo, esito gate. Senza trace completo il run NON è
promuovibile, a prescindere dalla qualità dell'output.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

OUT_DIR = Path(__file__).parent / "out"


class AuditTrace:
    def __init__(self, skill_path: Path, inputs_path: Path, model: str):
        self.t0 = time.time()
        self.data: dict[str, Any] = {
            "poc": "k2a-8e-agent-poc / AdvisorBoost",
            "skill_version": hashlib.sha256(skill_path.read_bytes()).hexdigest()[:12],
            "skill_path": str(skill_path),
            "inputs_hash": hashlib.sha256(inputs_path.read_bytes()).hexdigest()[:12],
            "model": model,
            "tool_calls": [],          # ogni PreToolUse osservato (nome+input)
            "quant_results": [],       # output integrali dei tool quant (numeri tracciati)
            "gate_events": [],         # deny/block degli hook
            "started_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }

    def tool_call(self, name: str, tool_input: dict) -> None:
        self.data["tool_calls"].append({"t": round(time.time() - self.t0, 1), "tool": name, "input": tool_input})

    def quant_result(self, name: str, inputs: dict, outputs: dict) -> None:
        self.data["quant_results"].append({"tool": name, "inputs": inputs, "outputs": outputs})

    def gate(self, hook: str, action: str, reason: str) -> None:
        self.data["gate_events"].append({"t": round(time.time() - self.t0, 1), "hook": hook, "action": action, "reason": reason})

    def traced_numbers(self) -> set[float]:
        """Tutti i numeri prodotti dai tool quant — base per la verifica 'numeri solo da tool'."""
        nums: set[float] = set()

        def walk(v: Any) -> None:
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                nums.add(round(float(v), 2))
            elif isinstance(v, dict):
                for x in v.values():
                    walk(x)
            elif isinstance(v, list):
                for x in v:
                    walk(x)

        for r in self.data["quant_results"]:
            walk(r["outputs"])
        return nums

    def finish(self, result_meta: dict) -> Path:
        self.data["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        self.data["wall_seconds"] = round(time.time() - self.t0, 1)
        self.data["result"] = result_meta
        OUT_DIR.mkdir(exist_ok=True)
        p = OUT_DIR / "audit.json"
        p.write_text(json.dumps(self.data, indent=2, ensure_ascii=False), encoding="utf-8")
        return p


TRACE: AuditTrace | None = None  # set da run_poc all'avvio
