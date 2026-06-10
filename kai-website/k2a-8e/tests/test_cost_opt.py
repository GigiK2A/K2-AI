"""Verifica le ottimizzazioni di costo del deep (client Anthropic FINTO, zero crediti):
1. FAIL-FAST REPAIR: una sezione invalida alla prima chiamata viene RIPARATA da una
   mini-chiamata invece di far rifiutare l'intero documento.
2. TIERING: le sezioni 'meccaniche' usano il modello light; le sezioni-analisi no.
3. Il meta riporta repairs / cache_read / input.
"""
from __future__ import annotations

import json
import re
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import assets, llm  # noqa: E402


def sample(schema, root):
    if isinstance(schema, dict) and "$ref" in schema:
        ref = schema["$ref"]
        if ref.startswith("#/$defs/"):
            schema = root.get("$defs", {}).get(ref.split("/")[-1], {})
    if "const" in schema:
        return schema["const"]
    if "enum" in schema:
        return schema["enum"][0]
    t = schema.get("type")
    if isinstance(t, list):
        t = t[0]
    if t == "object":
        return {k: sample(v, root) for k, v in schema.get("properties", {}).items()}
    if t == "array":
        it = schema.get("items", {"type": "string"})
        n = max(1, schema.get("minItems", 1))
        return [sample(it, root) for _ in range(n)]
    if t in ("integer", "number"):
        return 12
    if t == "boolean":
        return True
    return "Analisi di esempio densa e conforme allo schema."


class _Usage:
    input_tokens = 100
    output_tokens = 200
    cache_read_input_tokens = 90


class _Block:
    def __init__(self, text):
        self.type = "text"; self.text = text


class _Resp:
    def __init__(self, text):
        self.content = [_Block(text)]; self.usage = _Usage(); self.stop_reason = "end_turn"


def _install(schema, break_section, calls):
    fake = types.ModuleType("anthropic")

    class _Stream:
        def __init__(self, r): self._r = r
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def get_final_message(self): return self._r

    class _Messages:
        def stream(self, **kw):
            model = kw.get("model")
            user = kw["messages"][0]["content"]
            is_repair = "Correggi" in user or "NON è conforme" in user
            m = re.search(r"sezione «([^»]+)»", user)
            name = m.group(1) if m else ""
            calls.append({"model": model, "repair": is_repair, "name": name})
            sub = schema["properties"].get(name, {})
            # la sezione 'break_section' è spazzatura alla PRIMA chiamata, valida in repair
            if name == break_section and not is_repair:
                return _Stream(_Resp("non e json {{{"))
            return _Stream(_Resp(json.dumps(sample(sub, schema), ensure_ascii=False)))

    class _Anthropic:
        def __init__(self, api_key=None): self.messages = _Messages()

    fake.Anthropic = _Anthropic
    sys.modules["anthropic"] = fake
    return fake


def main() -> int:
    llm.ANTHROPIC_API_KEY = "test-fake"
    bp = {"pacchetto": {"nome_commerciale": "Test"}}
    facts = {"f": {"tipo": "normativo", "valore": "Art. X", "fonte": "normattiva", "vigenza": "2026"}}
    inputs = {"ragione_sociale": "Acme"}

    # schema con una sezione-lista (light) e sezioni oggetto (analisi)
    schema = assets.load_output_schema("flusso-fiscoboost-pmi")
    # scegli una sezione required non strutturale da "rompere"
    req = [r for r in schema.get("required", []) if r not in ("meta", "metadata", "input", "files")]
    break_section = req[0] if req else list(schema["properties"])[0]

    # --- 1) REPAIR: la sezione rotta viene riparata, il doc NON rifiuta ---
    calls = []
    _install(schema, break_section, calls)
    res, meta = llm.generate_deliverable_deep(schema, bp, facts, inputs)
    repair_calls = [c for c in calls if c["repair"]]
    ok_repair = res is not None and meta.get("repairs", 0) >= 1 and len(repair_calls) >= 1
    print(f"REPAIR: doc {'OK' if res else 'REFUSED'} · repairs={meta.get('repairs')} · "
          f"chiamate_repair={len(repair_calls)} · break='{break_section}' → {'PASS' if ok_repair else 'FAIL'}")

    # --- 2) TIERING: se MODEL_LIGHT differisce, le sezioni meccaniche lo usano ---
    llm.ANTHROPIC_MODEL_LIGHT = "MODEL-LIGHT-SENTINEL"
    llm.ANTHROPIC_MODEL = "MODEL-FULL"
    calls2 = []
    _install(schema, None, calls2)
    llm.generate_deliverable_deep(schema, bp, facts, inputs)
    # almeno una sezione light deve esistere e usare il sentinel; l'analisi core usa FULL
    light_names = [n for n, s in schema["properties"].items()
                   if n not in ("meta", "metadata", "input", "files") and llm._is_light_section(s)]
    used_light = any(c["model"] == "MODEL-LIGHT-SENTINEL" for c in calls2)
    used_full = any(c["model"] == "MODEL-FULL" for c in calls2)
    ok_tier = (used_full and (used_light if light_names else True))
    print(f"TIERING: sezioni_light={light_names} · usato_light={used_light} · usato_full={used_full} "
          f"→ {'PASS' if ok_tier else 'FAIL'}")

    # --- 3) cache/meta presenti ---
    ok_meta = "cache_read_tokens" in meta and "input_tokens" in meta
    print(f"META: cache_read/input presenti → {'PASS' if ok_meta else 'FAIL'}")

    allok = ok_repair and ok_tier and ok_meta
    print("\n" + ("COST-OPT TEST PASS" if allok else "COST-OPT TEST FAIL"))
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
