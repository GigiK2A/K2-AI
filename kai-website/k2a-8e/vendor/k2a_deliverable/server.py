"""MCP server k2a-deliverable — espone i due livelli di validazione.

Tools:
  - validate_blueprint(blueprint): livello 1 — blueprint ben formato vs meta-schema.
  - lint_deliverable(blueprint, instance): livello 2 — deliverable conforme al blueprint.

I blueprint canonici vivono in `k2a-skills/blueprints/` (override con env
K2A_BLUEPRINTS_DIR). Sia `validate_blueprint` che `lint_deliverable` accettano il
blueprint come dict inline OPPURE come stringa-riferimento (nome file o tier+skill).
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from . import adapters, linter

try:
    from fastmcp import FastMCP
except ImportError:  # pragma: no cover - permette i test senza fastmcp installato
    FastMCP = None


def lint_file_impl(blueprint: Any, path: str, twin_json_path: str | None = None) -> dict:
    """Estrae l'instance da un documento REALE (adapter) e lo passa al linter.

    dispatch per estensione: .docx -> docx_to_instance ; .html/.htm -> html_to_instance.
    Gli `_impl` esistenti restano invariati: questo è solo uno strato a monte.
    """
    bp = resolve_blueprint(blueprint)
    ext = os.path.splitext(path)[1].lower()
    if ext == ".docx":
        instance = adapters.docx_to_instance(path, twin_json_path, bp)
    elif ext in (".html", ".htm"):
        instance = adapters.html_to_instance(path)
    else:
        return {"livello": 2, "esito": "ERRORE", "errore": f"estensione non gestita: '{ext}' (atteso .docx/.html)"}
    report = lint_deliverable_impl(bp, instance)
    report["instance"] = instance  # esposto per debug/ispezione
    return report


def _blueprints_dir() -> Path:
    env = os.environ.get("K2A_BLUEPRINTS_DIR")
    if env:
        return Path(env).expanduser()
    return Path.home() / "Code" / "k2a-skills" / "blueprints"


def _meta_schema_path() -> Path:
    return _blueprints_dir() / "deliverable-blueprint.schema.json"


def load_meta_schema() -> dict:
    return json.loads(_meta_schema_path().read_text(encoding="utf-8"))


def resolve_blueprint(ref: Any) -> dict:
    """Accetta un dict (ritornato così com'è) o una stringa-riferimento.

    Stringa: nome file ('check-pmi-express.check.blueprint.json'), oppure
    'skill' o 'tier' da cercare tra i *.blueprint.json della cartella.
    """
    if isinstance(ref, dict):
        return ref
    if not isinstance(ref, str):
        raise ValueError("blueprint deve essere un dict o una stringa di riferimento")

    d = _blueprints_dir()
    # match diretto per nome file
    cand = d / ref
    if cand.is_file():
        return json.loads(cand.read_text(encoding="utf-8"))
    if not ref.endswith(".json"):
        cand = d / f"{ref}.blueprint.json"
        if cand.is_file():
            return json.loads(cand.read_text(encoding="utf-8"))

    # match per tier o skill nel contenuto
    rn = ref.strip().lower()
    for f in sorted(d.glob("*.blueprint.json")):
        bp = json.loads(f.read_text(encoding="utf-8"))
        pkg = bp.get("pacchetto", {})
        if rn in (str(pkg.get("tier", "")).lower(), str(pkg.get("skill", "")).lower()):
            return bp
    raise FileNotFoundError(f"blueprint non trovato per riferimento: '{ref}' in {d}")


# ------------------------------------------------------------------ logica pura

def _contratto_schema_path(bp: dict) -> Path | None:
    """Risolve il file `contratto_dati` (output-schema) del blueprint.

    `contratto_dati` è relativo alla cartella blueprints (es.
    'flusso-financeboost-pmi/schemas/output-schema.json'); il path reale vive nella
    root del repo skill -> fallback su base.parent (come adapters._validate_twin).
    """
    contratto = bp.get("contratto_dati")
    if not contratto:
        return None
    base = _blueprints_dir()
    cand = base / contratto
    if cand.is_file():
        return cand
    alt = base.parent / contratto
    return alt if alt.is_file() else None


def check_coverage_impl(blueprint: Any) -> dict:
    """Coverage 1:1 voce->slot vs il file contratto_dati REALE.

    Ogni voce deve dichiarare `slot` e quello slot deve esistere come proprietà
    top-level dell'output-schema. Applicabile solo ai blueprint `validazione_strict`
    (gli altri non dichiarano slot): per gli altri ritorna SKIP, non FAIL.
    """
    bp = resolve_blueprint(blueprint)
    if not bp.get("validazione_strict"):
        return {"applicabile": False, "esito": "SKIP", "motivo": "blueprint non validazione_strict"}
    sp = _contratto_schema_path(bp)
    problemi: list[dict] = []
    props: set = set()
    if sp is None:
        problemi.append({"voce": None, "slot": None,
                         "messaggio": f"contratto_dati non risolvibile: '{bp.get('contratto_dati')}'"})
    else:
        schema = json.loads(sp.read_text(encoding="utf-8"))
        props = set((schema.get("properties") or {}).keys())
    voci = bp.get("voci", []) or []
    for v in voci:
        slot = v.get("slot")
        if not slot:
            problemi.append({"voce": v.get("id"), "slot": None, "messaggio": "voce senza slot dichiarato"})
        elif sp is not None and slot not in props:
            problemi.append({"voce": v.get("id"), "slot": slot,
                             "messaggio": f"slot '{slot}' assente dalle proprietà di contratto_dati"})
    voci_scoperte = {p["voce"] for p in problemi if p["voce"] is not None}
    return {
        "applicabile": True,
        "esito": "PASS" if not problemi else "FAIL",
        "voci_totali": len(voci),
        "voci_coperte": len(voci) - len(voci_scoperte),
        "slot_contratto": sorted(props),
        "problemi": problemi,
    }


def validate_blueprint_impl(blueprint: Any) -> dict:
    bp = resolve_blueprint(blueprint)
    meta = load_meta_schema()
    Draft202012Validator.check_schema(meta)
    v = Draft202012Validator(meta)
    errs = sorted(v.iter_errors(bp), key=lambda e: list(e.path))
    errori = [{"path": list(e.path), "messaggio": e.message} for e in errs]
    # coverage 1:1 voce->slot vs contratto_dati (solo blueprint validazione_strict;
    # gli altri sono SKIP -> nessun impatto sull'esito, retrocompatibile).
    cov = check_coverage_impl(bp)
    if cov.get("applicabile") and cov.get("esito") == "FAIL":
        for p in cov["problemi"]:
            errori.append({"path": ["voci", p.get("voce"), "slot"], "messaggio": f"coverage: {p['messaggio']}"})
    return {
        "livello": 1,
        "skill": bp.get("pacchetto", {}).get("skill"),
        "tier": bp.get("pacchetto", {}).get("tier"),
        "esito": "PASS" if not errori else "FAIL",
        "errori": errori,
        "coverage": cov,
    }


def lint_deliverable_impl(blueprint: Any, instance: dict) -> dict:
    bp = resolve_blueprint(blueprint)
    report = linter.lint(bp, instance or {})
    report["livello"] = 2
    return report


# ------------------------------------------------------------------ MCP wiring

if FastMCP is not None:
    mcp = FastMCP("k2a-deliverable")

    @mcp.tool()
    def validate_blueprint(blueprint: Any) -> dict:
        """Livello 1: verifica che un blueprint sia ben formato rispetto al meta-schema.

        `blueprint`: dict inline oppure riferimento (nome file, tier o skill).
        """
        return validate_blueprint_impl(blueprint)

    @mcp.tool()
    def lint_deliverable(blueprint: Any, instance: dict) -> dict:
        """Livello 2: verifica che un deliverable prodotto sia conforme al suo blueprint.

        `blueprint`: dict inline o riferimento. `instance`: descrizione strutturata
        del deliverable (voci, pagine, artefatti, elementi_grafici, tabelle, flag).
        Ritorna esito PASS/FAIL con conteggio errori/warning e findings dettagliati.
        """
        return lint_deliverable_impl(blueprint, instance)

    @mcp.tool()
    def validate_coverage(blueprint: Any) -> dict:
        """Coverage 1:1 voce->slot del blueprint vs il file contratto_dati (output-schema).

        Applicabile solo ai blueprint `validazione_strict` (es. FinanceBoost). Verifica
        che ogni voce dichiari uno `slot` esistente tra le proprietà top-level dell'output-schema.
        """
        return check_coverage_impl(blueprint)

    @mcp.tool()
    def lint_file(blueprint: Any, path: str, twin_json_path: str | None = None) -> dict:
        """Livello 2 su FILE reale: estrae l'instance da un documento (.docx/.html) via
        adapter di formato e lo valida contro il blueprint.

        `blueprint`: dict o riferimento. `path`: percorso del deliverable prodotto.
        `twin_json_path`: opzionale, JSON gemello da validare vs `contratto_dati` (attiva R11).
        Ritorna l'esito del lint + l'instance estratto (campo `instance`) per debug.
        """
        return lint_file_impl(blueprint, path, twin_json_path)


def main() -> None:  # pragma: no cover
    if FastMCP is None:
        raise SystemExit("fastmcp non installato: pip install fastmcp")
    mcp.run()


if __name__ == "__main__":  # pragma: no cover
    main()
