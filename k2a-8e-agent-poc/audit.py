"""Audit trace del PoC — requisito pass/fail (deliverable venduto, contestabile).

Registra: versione skill, hash input, ogni tool chiamato, gli output INTEGRALI
dei tool quant con un call_id univoco, le scelte di gate. Il call_id è la base
della PROVENIENZA esplicita (criterio Luca #2): ogni numero dell'EV nel
deliverable deve citare la chiamata che l'ha prodotto, non solo coincidere per
valore.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any


def _walk_numbers(v: Any, acc: set[float]) -> None:
    if isinstance(v, bool):
        return
    if isinstance(v, (int, float)):
        acc.add(round(float(v), 2))
    elif isinstance(v, dict):
        for x in v.values():
            _walk_numbers(x, acc)
    elif isinstance(v, list):
        for x in v:
            _walk_numbers(x, acc)


class AuditTrace:
    def __init__(self, skill_path: Path, inputs_path: Path, model: str):
        self.t0 = time.time()
        self._n = 0
        self.data: dict[str, Any] = {
            "poc": "k2a-8e-agent-poc / AdvisorBoost",
            "skill_version": hashlib.sha256(skill_path.read_bytes()).hexdigest()[:12],
            "skill_path": str(skill_path),
            "inputs_hash": hashlib.sha256(inputs_path.read_bytes()).hexdigest()[:12],
            "inputs_path": str(inputs_path),
            "model": model,
            "tool_calls": [],
            "quant_results": [],   # {call_id, tool, inputs, outputs}
            "gate_events": [],
            "started_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }

    def tool_call(self, name: str, tool_input: dict) -> None:
        self.data["tool_calls"].append({"t": round(time.time() - self.t0, 1), "tool": name, "input": tool_input})

    def quant_result(self, full_name: str, inputs: dict, outputs: dict) -> str:
        """Registra un risultato quant e ritorna il call_id univoco da citare."""
        self._n += 1
        call_id = f"{full_name}#{self._n:03d}"
        self.data["quant_results"].append({"call_id": call_id, "tool": full_name, "inputs": inputs, "outputs": outputs})
        return call_id

    def gate(self, hook: str, action: str, reason: str) -> None:
        self.data["gate_events"].append({"t": round(time.time() - self.t0, 1), "hook": hook, "action": action, "reason": reason})

    def call_numbers(self, call_id: str) -> set[float]:
        """I numeri prodotti da UNA specifica chiamata (per la verifica di provenienza)."""
        for r in self.data["quant_results"]:
            if r["call_id"] == call_id:
                acc: set[float] = set()
                _walk_numbers(r["outputs"], acc)
                return acc
        return set()

    def finish(self, result_meta: dict, out_dir: Path) -> Path:
        self.data["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        self.data["wall_seconds"] = round(time.time() - self.t0, 1)
        self.data["result"] = result_meta
        out_dir.mkdir(parents=True, exist_ok=True)
        p = out_dir / "audit.json"
        p.write_text(json.dumps(self.data, indent=2, ensure_ascii=False), encoding="utf-8")
        return p


TRACE: AuditTrace | None = None  # set da run_poc all'avvio
