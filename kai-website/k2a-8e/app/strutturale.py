"""Cabla vs_strutturale (vendorizzato) — 52 verifiche NTC 2018 (check_*).

STATO ONESTO: vendorizzato + resolver pronto, ma NON operativo end-to-end per 2 blocchi su Luca:
  1. il pacchetto pubblicato NON include `data/sanity_rules.json` (`_sanity.py` lo cerca a
     parent.parent.parent/data) → i `check_*` crashano con sanity ON (default). Qui NON
     disabilitiamo la sanity: l'output strutturale è safety-critical, girare senza i controlli
     di sanità sarebbe peggio del non-disponibile.
  2. nessun boost del catalogo (11 schemi verificati) consuma un risultato di verifica
     strutturale → serve uno StructBoost instradato (decisione prodotto).

`resolve_check()` è già pronto per quando Luca sblocca; `apply_strutturale()` degrada onesto.
Per questo NON è agganciato a un hook nella pipeline (nessun consumer) — vedi VENDORED_FROM.
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "vendor"))

# nome-verifica → (modulo, funzione, classe Input). Estendibile on-demand sui 52 check_*.
_CHECKS = {
    "resistenza_tubolare": ("vs_strutturale.check_resistance", "check_tubular_resistance", "CheckResistanceInput"),
}


def resolve_check(tipo: str, params: dict) -> dict:
    spec = _CHECKS.get(tipo)
    if not spec:
        return {"ok": False, "note": f"verifica '{tipo}' non mappata (dei 52 check_*: aggiungere a _CHECKS)"}
    mod_name, fn_name, in_name = spec
    mod = importlib.import_module(mod_name)
    fn = getattr(mod, fn_name)
    in_cls = getattr(mod, in_name)
    out = fn(in_cls(**(params or {})))
    return {"ok": True, "risultato": out.model_dump() if hasattr(out, "model_dump") else dict(out)}


def apply_strutturale(deliverable: dict, inputs: dict) -> tuple[dict, Optional[dict]]:
    if not isinstance(deliverable, dict):
        return deliverable, None
    vs = (inputs or {}).get("verifica_strutturale")
    if not isinstance(vs, dict) or not vs.get("tipo"):
        return deliverable, {"disponibile": False,
                             "note": "verifica strutturale non eseguita: nessun input verifica_strutturale + nessuno slot deliverable nel catalogo (serve StructBoost)"}
    try:
        res = resolve_check(vs["tipo"], vs.get("parametri") or {})
    except Exception as e:
        return deliverable, {"disponibile": False, "tipo": vs.get("tipo"),
                             "note": f"check non eseguibile (bug upstream: manca data/sanity_rules.json nel pacchetto): {type(e).__name__}"}
    return deliverable, {"disponibile": res.get("ok", False), "tipo": vs.get("tipo"),
                         "risultato": res.get("risultato"),
                         "note": res.get("note", "risultato in meta (nessuno slot deliverable: surfacing = StructBoost)"),
                         "provenance": "vs_strutturale (vendorizzato)"}
