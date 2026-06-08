"""Render-smoke su TUTTI i 12 output-schema: costruisce un'istanza minima
conforme da ogni schema e verifica che il render premium (copertina, indice,
header, componenti) NON crashi e produca un PDF multi-pagina.

Non serve Anthropic (usa dati mock). Garantisce che il layout regga su tutte le
forme di deliverable, non solo LegalBoost.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import assets, render  # noqa: E402


def sample(schema: dict):
    t = schema.get("type")
    if isinstance(t, list):
        t = t[0]
    if "enum" in schema:
        return schema["enum"][0]
    if t == "object":
        props = schema.get("properties", {})
        req = schema.get("required", list(props.keys()))
        return {k: sample(props[k]) for k in props if k in req or len(props) <= 8}
    if t == "array":
        it = schema.get("items", {"type": "string"})
        return [sample(it), sample(it)]
    if t in ("integer", "number"):
        return 62
    if t == "boolean":
        return True
    if t == "string":
        d = schema.get("description", "")
        return ("Esempio: " + d)[:80] if d else "Testo di esempio per la sezione."
    return "n/d"


def main() -> int:
    man = assets.manifest()
    skills = sorted({v["skill"] for v in man.values()})
    cit = [{"riferimento": "Art. 1 esempio", "fonte": "override_locale", "vigenza": "2026"}]
    ok = 0
    fail = []
    for skill in skills:
        osch = assets.load_output_schema(skill)
        bp = assets.load_blueprint(skill) or {"pacchetto": {"nome_commerciale": skill}}
        if not osch:
            fail.append((skill, "output-schema mancante"))
            continue
        inst = sample(osch)
        legal = skill == "flusso-legalboost-pmi"
        p = Path(f"/tmp/render_{skill}.pdf")
        try:
            (render.render_pdf if legal else render.render_generic_pdf)(inst, bp, cit, p)
            assert p.exists() and p.stat().st_size > 5000, "PDF troppo piccolo"
            ok += 1
            print(f"  {skill:30} OK")
        except Exception as e:
            fail.append((skill, f"{type(e).__name__}: {e}"))
            print(f"  {skill:30} FAIL {e}")

    print(f"\nRENDER PREMIUM: {ok}/{len(skills)} schemi OK")
    if fail:
        for s, e in fail:
            print("  -", s, str(e)[:120])
    return 0 if not fail else 1


if __name__ == "__main__":
    sys.exit(main())
