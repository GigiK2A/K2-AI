"""Test AVVERSARIALE del clamp su TUTTI i 12 output-schema.

Costruisce per ogni schema un'istanza che VIOLA deliberatamente i vincoli formali
(pattern, minItems, maxLength, maximum/minimum, enum), poi applica
`llm._clamp_to_schema` e verifica che il risultato diventi CONFORME. Prova, senza
crediti, che la generazione reale non fallirà la validazione per uno scostamento
formale del modello.

Nota: NON copre violazioni semantiche irreparabili (campo required mancante,
tipo completamente sbagliato) — quelle restano un refuse legittimo gestito a monte.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from jsonschema import Draft202012Validator  # noqa: E402

from app import assets, llm  # noqa: E402


def bad(schema: dict, root: dict):
    """Istanza tipata ma che viola i vincoli formali dove possibile."""
    if isinstance(schema, dict) and "$ref" in schema:
        ref = schema["$ref"]
        if ref.startswith("#/$defs/"):
            schema = root.get("$defs", {}).get(ref.split("/")[-1], {})
    if "enum" in schema:
        return "VALORE_FUORI_ENUM_!!!"        # viola enum
    t = schema.get("type")
    if isinstance(t, list):
        t = t[0]
    if t == "object":
        props = schema.get("properties", {})
        # includo TUTTE le proprietà required (altrimenti refuse legittimo, non clamp)
        req = set(schema.get("required", list(props)))
        return {k: bad(v, root) for k, v in props.items() if k in req or len(props) <= 10}
    if t == "array":
        # array VUOTO → viola minItems (deve essere paddato dal clamp)
        return []
    if t in ("integer", "number"):
        return 10 ** 9                         # viola maximum quasi sempre
    if t == "boolean":
        return True
    if t == "string":
        # lunga + maiuscole + simboli: viola maxLength e pattern tipici
        return "QUESTA STRINGA È VOLUTAMENTE TROPPO LUNGA E CON MAIUSCOLE/Simboli!!! " * 6
    return "X"


def main() -> int:
    man = assets.manifest()
    skills = sorted({v["skill"] for v in man.values()})
    ok, fail = 0, []
    for skill in skills:
        s = assets.load_output_schema(skill)
        inst = bad(s, s)
        clamped = llm._clamp_to_schema(inst, s, s)
        errs = sorted(Draft202012Validator(s).iter_errors(clamped), key=lambda e: list(e.path))
        # ignoro SOLO gli errori di 'required' (violazione semantica, non formale)
        formal = [e for e in errs if e.validator not in ("required", "type")]
        if formal:
            fail.append((skill, [f"{list(e.path)}: {e.validator} {str(e.message)[:60]}" for e in formal[:4]]))
            print(f"  {skill:34} FAIL  {len(formal)} residui")
        else:
            ok += 1
            print(f"  {skill:34} OK (clamp ripara pattern/minItems/maxLen/num/enum)")

    print(f"\nCLAMP AVVERSARIALE: {ok}/{len(skills)} schemi resi conformi")
    if fail:
        for s, errs in fail:
            print(f"\n{s}:")
            for e in errs:
                print("   -", e)
    print("\n" + ("CLAMP-ADVERSARIAL TEST PASS" if not fail else "CLAMP-ADVERSARIAL TEST FAIL"))
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
