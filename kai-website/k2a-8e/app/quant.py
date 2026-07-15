"""Resolver dei fact di VALUTAZIONE dal quant deterministico di Luca (Fix #0 Fase 1).

I numeri di valutazione (WACC, EV da multipli, DCF) NON devono uscire dall'LLM: vengono
dal package `k2a_quant` vendorizzato (`vendor/k2a_quant/`, pin 1d7d9c2), importato come
LIBRERIA Python pura (no HTTP, no MCP stdio). Innestato in `pipeline.resolve` PRIMA del
fallback formula-stringa: per le chiavi quant (`dcf`, `wacc`, `multipli_ev`) si tenta il
calcolo; per ogni altra chiave ritorna None → il chiamante usa calc.py / il fallback.

Guard onesti (CALLER-SIDE handoff §1): settore finanziario, settore non coperto, dati
mancanti → fact `non_disponibile` con motivo + provenance, MAI un numero inventato.
"""
from __future__ import annotations

import functools
import json
import pathlib
import sys
from typing import Any, Optional

QUANT_KEYS = {"dcf", "wacc", "multipli_ev"}
_VENDOR = pathlib.Path(__file__).resolve().parent.parent / "vendor"
_KD_SPREAD = 0.025  # spread di default sul costo del debito (Kd pre-tax = rf + spread): assunzione documentata

# Import del package vendorizzato come libreria. Se mancano le dep (pydantic/numpy) →
# _AVAILABLE False: le chiavi quant tornano non_disponibile (onesto), non un numero LLM.
try:
    if str(_VENDOR) not in sys.path:
        sys.path.insert(0, str(_VENDOR))
    from k2a_quant import capm as _capm
    from k2a_quant import ev_multiples as _evm
    from k2a_quant import snapshot as _snapmod
    from k2a_quant.wacc import WaccInput, compute_wacc  # noqa: F401  (compute_wacc riservato a estensioni)
    _AVAILABLE = True
    _IMPORT_ERR = None
except Exception as exc:  # pragma: no cover
    _AVAILABLE = False
    _IMPORT_ERR = str(exc)


@functools.lru_cache(maxsize=1)
def _snapshot() -> dict:
    return json.loads((_VENDOR / "k2a_quant" / "data" / "industry_multiples.json").read_text(encoding="utf-8"))


def _num(v: Any) -> Optional[float]:
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        s = v.strip().replace("€", "").replace(" ", "")
        if not s:
            return None
        if "," in s:
            s = s.replace(".", "").replace(",", ".")
        try:
            return float(s)
        except ValueError:
            return None
    return None


def _latest_bilancio(form: dict) -> Optional[dict]:
    bilanci = form.get("bilanci")
    if not isinstance(bilanci, list):
        return None
    rows = [b for b in bilanci if isinstance(b, dict)]
    if not rows:
        return None
    with_year = [b for b in rows if _num(b.get("anno")) is not None]
    return max(with_year, key=lambda b: _num(b.get("anno"))) if with_year else rows[-1]


def _sector_from_ateco(ateco: Any, snapshot: dict) -> Optional[str]:
    """ATECO (prime 2 cifre) → settore via mappa snapshot; accetta anche un nome-settore diretto."""
    a2s = snapshot.get("ateco_to_sector", {})
    s = str(ateco or "").strip().lower()
    if s in snapshot.get("sectors", {}):
        return s
    digits = "".join(ch for ch in str(ateco or "") if ch.isdigit())
    if len(digits) >= 2 and digits[:2] in a2s:
        return a2s[digits[:2]]
    return None


def _nd(formula: str, motivo: str, *, call_id=None, as_of=None) -> dict:
    f = {"tipo": "non_disponibile", "valore": None, "formula": formula, "motivo": motivo, "fonte": "k2a-quant"}
    if call_id:
        f["call_id"] = call_id
    if as_of:
        f["snapshot_as_of"] = as_of
    return f


def _ok(valore, formula, outputs, env: dict) -> dict:
    return {
        "tipo": "valore_calcolato", "valore": valore, "formula": formula, "fonte": "k2a-quant",
        "call_id": env.get("call_id"), "snapshot_as_of": env.get("snapshot_as_of"),
        "outputs": outputs, "warnings": env.get("warnings") or [],
    }


_FORMULA = {
    "wacc": "WACC = Ke·E/(E+D) + Kd·(1-t)·D/(E+D); Ke=CAPM(beta settore, rf, erp)",
    "multipli_ev": "EV = multiplo settore × EBITDA (o × Ricavi se EBITDA≤0)",
    "dcf": "EV(DCF) = Σ FCF_t/(1+WACC)^t + TV; richiede FCF previsti",
}


def resolve_quant_fact(key: str, form: dict) -> Optional[dict]:
    """Chiave di valutazione → fact calcolato dal quant, o `non_disponibile`. None se la
    chiave non è di competenza del quant (il chiamante usa calc.py / fallback)."""
    if key not in QUANT_KEYS:
        return None
    formula = _FORMULA[key]
    if not _AVAILABLE:
        return _nd(formula, f"quant non disponibile nell'engine ({_IMPORT_ERR})")

    snap = _snapshot()
    as_of = _snapmod.snapshot_as_of(snap)

    # dcf: gli FCF previsti non sono nel form advisor → onesto non_disponibile (Fix #5).
    if key == "dcf":
        return _nd(formula, "FCF previsti non presenti nel form (servono fcff_anni) — DCF non calcolabile", as_of=as_of)

    b = _latest_bilancio(form)
    if b is None:
        return _nd(formula, "nessun bilancio strutturato nel form", as_of=as_of)
    settore = _sector_from_ateco(form.get("settore_ateco"), snap)
    if settore is None:
        return _nd(formula, f"settore non identificato da ATECO «{form.get('settore_ateco')}»", as_of=as_of)

    ricavi = _num(b.get("ricavi")) or _num(form.get("fatturato"))
    ebitda = _num(b.get("ebitda"))
    pn = _num(b.get("patrimonio_netto"))
    # mancante ≠ zero (audit 1e): se i debiti finanziari non sono nel form, il calcolo
    # procede con 0 ma l'assunzione va DICHIARATA nel risultato (mai nascosta).
    df_dichiarato = _num(b.get("debiti_finanziari"))
    df = df_dichiarato if df_dichiarato is not None else 0.0

    if key == "multipli_ev":
        if ricavi is None and (ebitda is None or ebitda <= 0):
            return _nd(formula, "EBITDA e ricavi assenti dal bilancio", as_of=as_of)
        env = _evm.ev_from_multiples(settore, ebitda or 0.0, ricavi or 0.0, snap)
        if env.get("errore"):
            err = env["errore"]
            return _nd(formula, err.get("messaggio") or err.get("code") or "rifiuto quant",
                       call_id=env.get("call_id"), as_of=as_of)
        out = env.get("outputs") or {}
        return _ok(out.get("ev_eur"), formula, out, env)

    if key == "wacc":
        if pn is None or pn <= 0:
            return _nd(formula, "patrimonio netto assente o ≤0: WACC non determinabile", as_of=as_of)
        # Ke dal CAPM guarded (gestisce il guard finanziario, settore non trovato, ecc.)
        env = _capm.capm_cost_of_equity(settore, df, pn, ricavi or _num(form.get("fatturato")) or 0.0, snap)
        if env.get("errore"):
            err = env["errore"]
            return _nd(formula, err.get("messaggio") or err.get("code") or "rifiuto quant",
                       call_id=env.get("call_id"), as_of=as_of)
        out = dict(env.get("outputs") or {})
        ke = _num(out.get("ke_pct"))
        if ke is None:
            return _nd(formula, "CAPM non ha prodotto Ke", call_id=env.get("call_id"), as_of=as_of)
        country = _snapmod.country(snap, "italy")
        rf = _num(country.get("rf_10y")) or 0.0
        tax = _num(country.get("tax_rate")) or 0.279
        kd_pretax = rf + _KD_SPREAD
        e, d = pn, df
        we = e / (e + d) if (e + d) > 0 else 1.0
        wd = 1.0 - we
        wacc = ke / 100.0 * we + kd_pretax * (1 - tax) * wd
        wacc_pct = round(wacc * 100, 2)
        out.update({
            "wacc_pct": wacc_pct, "weight_equity": round(we, 4), "weight_debt": round(wd, 4),
            "kd_pretax_pct": round(kd_pretax * 100, 2), "tax_rate_pct": round(tax * 100, 1),
            **({"df_assunzione": "debiti_finanziari non forniti: assunti 0 (pesi WACC solo "
                                 "equity) — ipotesi da confermare"}
               if df_dichiarato is None else {}),
            "kd_assunzione": f"Kd pre-tax = rf {round(rf*100,2)}% + spread {round(_KD_SPREAD*100,1)}% (default, non dal form)",
        })
        return _ok(wacc_pct, formula, out, env)

    return None  # pragma: no cover


# ───────────────────────── binding strutturale (Fix #0 Fase 2) ─────────────────────────
# Dopo la generazione LLM, gli slot numerici del deliverable vengono SOVRASCRITTI col
# valore del tool (CalcResult). Chiude INV1/P0-1/P0-2: il numero nel PDF è derivato dal
# tool, non ri-emesso dal modello. La provenance (call_id/as_of) è registrata e si annota
# il valore LLM scartato (evidenza della divergenza).
_BIND_MAP: dict[str, list[tuple]] = {
    "flusso-advisorboost-pmi": [
        ("multipli_ev", "ev_eur", ("enterprise_value", "multipli_ebitda", "ev_mediano_eur")),
        ("multipli_ev", "multiplo_usato", ("enterprise_value", "multipli_ebitda", "multiplo_mediano")),
        ("wacc", "wacc_pct", ("enterprise_value", "dcf", "wacc")),
    ],
}


def _set_slot(d: dict, path: tuple, value) -> Any:
    cur = d
    for p in path[:-1]:
        if not isinstance(cur.get(p), dict):
            cur[p] = {}
        cur = cur[p]
    prev = cur.get(path[-1])
    cur[path[-1]] = value
    return prev


def bind_quant_slots(skill: str, deliverable: dict, facts: dict) -> tuple[dict, list[dict]]:
    """Sovrascrive gli slot numerici del deliverable col valore deterministico del quant.
    Ritorna (deliverable, provenance[]). No-op per skill non mappate o fact non calcolati."""
    prov: list[dict] = []
    if not isinstance(deliverable, dict):
        return deliverable, prov
    for fact_key, out_field, path in _BIND_MAP.get(skill, []):
        f = facts.get(fact_key)
        if not isinstance(f, dict) or f.get("tipo") != "valore_calcolato":
            continue
        val = (f.get("outputs") or {}).get(out_field)
        if val is None:
            val = f.get("valore")
        if val is None:
            continue
        prev = _set_slot(deliverable, path, val)
        prov.append({
            "slot": ".".join(path), "valore": val, "fonte": "k2a-quant",
            "call_id": f.get("call_id"), "snapshot_as_of": f.get("snapshot_as_of"),
            "valore_llm_sovrascritto": prev,
        })
    return deliverable, prov
