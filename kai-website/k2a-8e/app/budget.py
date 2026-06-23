"""Binder §E — `piano_economico_finanziario` di AdvisorBoost dal MCP k2a_budget (vendorizzato).

`budget_36m` + `budget_scenari` + `budget_sensitivity` (envelope CalcResult, deterministico) →
`piano_economico_finanziario.{budget_mensile_36m, scenari, sensitivity, ipotesi_base}`.
Sostituisce i ~30 slot di proiezione che prima erano scritti dall'LLM.

- `bilancio_base` dal bilancio reale dell'azienda (convenzione PMI servizi documentata:
  CV=0, CF = ricavi − EBITDA; ammortamenti/oneri se presenti).
- EV degli scenari = EBITDA_anno3 × multiplo (dal quant in `enterprise_value.multipli_ebitda`;
  fallback: implied = `valore_raccomandato / EBITDA_base`). Senza multiplo → scenari NON
  sovrascritti (resta l'LLM: `enterprise_value_eur` è required) + flag onesto.
- warning del motore propagati (aliquota approssimata, no loss carryforward, default usati).

Da chiamare DOPO advisor.apply_advisor (che popola enterprise_value).
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "vendor"))

_MESE_KEYS = ("mese", "ricavi", "costi_variabili", "costi_fissi", "ebitda",
              "ammortamenti", "oneri_finanziari", "imposte", "utile_netto", "fcf")
_DELTA_PCT = 10.0


def _num(v: Any) -> Optional[float]:
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return float(str(v).replace("€", "").replace(" ", "").replace(".", "").replace(",", "."))
    except ValueError:
        return None


def _latest_bilancio(inputs: dict) -> Optional[dict]:
    bs = [b for b in ((inputs or {}).get("bilanci") or []) if isinstance(b, dict)]
    if not bs:
        return None
    wy = [b for b in bs if _num(b.get("anno")) is not None]
    b = max(wy, key=lambda b: _num(b.get("anno"))) if wy else bs[-1]
    # In produzione l'intake trascrive le VOCI grezze (non gli aggregati): riclassifico
    # con finance.py per ottenere ricavi/ebitda/D&A/oneri/PFN deterministici (allega _reclass).
    try:
        from . import finance
        return finance.enrich_bilancio(b)
    except Exception:
        return b


def _from_reclass(b: dict, dove: str, chiave: str) -> Optional[float]:
    rc = b.get("_reclass") if isinstance(b.get("_reclass"), dict) else {}
    return _num((rc.get(dove) or {}).get(chiave))


def _bilancio_base(b: dict) -> Optional[dict]:
    ricavi = _num(b.get("ricavi")) or _from_reclass(b, "ce", "ricavi")
    ebitda = _num(b.get("ebitda")) or _from_reclass(b, "ce", "ebitda")
    if ricavi is None or ebitda is None or ricavi <= 0:
        return None
    cv = _num(b.get("costi_variabili")) or 0.0
    # D&A e oneri finanziari: dagli aggregati o, se assenti, dalla riclassificazione delle voci
    amm = _num(b.get("ammortamenti")) or _from_reclass(b, "ce", "ammortamenti") or 0.0
    oneri = _num(b.get("oneri_finanziari")) or _from_reclass(b, "ce", "oneri_finanziari") or 0.0
    return {
        "ricavi_eur_anno_base": ricavi,
        "costi_variabili_eur_anno_base": cv,
        "costi_fissi_eur_anno_base": max(ricavi - ebitda - cv, 0.0),
        "ammortamenti_eur_anno_base": amm,
        "oneri_finanziari_eur_anno_base": oneri,
    }


def _pfn_iniziale(b: dict) -> Optional[float]:
    pfn = _num(b.get("pfn")) or _num(b.get("posizione_finanziaria_netta")) or _from_reclass(b, "indici", "pfn")
    if pfn is not None:
        return pfn
    df = _num(b.get("debiti_finanziari")) or _from_reclass(b, "sp", "debiti_finanziari")
    if df is not None:
        liq = _num(b.get("liquidita")) or _num(b.get("disponibilita_liquide")) or 0.0
        return df - liq
    return None


def _multiplo(deliverable: dict, ebitda_base: Optional[float]) -> Optional[float]:
    ev = deliverable.get("enterprise_value") if isinstance(deliverable.get("enterprise_value"), dict) else {}
    m = _num((ev.get("multipli_ebitda") or {}).get("multiplo_mediano"))
    if m and m > 0:
        return m
    vr = _num(ev.get("valore_raccomandato_eur"))
    if vr and ebitda_base and ebitda_base > 0:
        return vr / ebitda_base
    return None


def _map_sensitivity(matrice: dict, base_ebitda: Optional[float]) -> list[dict]:
    out: list[dict] = []
    for leva, righe in (matrice or {}).items():
        for r in righe:
            if r.get("variazione") == "base":
                continue
            imp = _num(r.get("delta_eur"))
            if imp is None:           # schema vuole number: salta righe senza impatto (no PEF invalido)
                continue
            segno = 1 if r.get("variazione") == "plus" else -1
            row = {"variabile": leva, "delta_percentuale": segno * _DELTA_PCT,
                   "impatto_ebitda_eur": imp}
            if base_ebitda:
                row["impatto_ebitda_perc"] = round(imp / base_ebitda * 100, 2)
            out.append(row)
    return out


def bind_pef(deliverable: dict, inputs: dict) -> dict:
    b = _latest_bilancio(inputs)
    if b is None:
        return {"disponibile": False, "note": "nessun bilancio: §E (budget) saltato"}
    base = _bilancio_base(b)
    if base is None:
        return {"disponibile": False, "note": "ricavi/EBITDA assenti dal bilancio: budget non calcolabile"}

    from k2a_budget.engine import budget_36m
    from k2a_budget.scenari import budget_scenari
    from k2a_budget.sensitivity import budget_sensitivity
    try:
        from k2a_budget.snapshot import get_aliquota_default
        aliquota_pct = get_aliquota_default()
    except Exception:
        aliquota_pct = None

    pfn0 = _pfn_iniziale(b)
    env = budget_36m(base, pfn_iniziale_eur=pfn0)
    if "outputs" not in env:
        return {"disponibile": False, "note": f"budget_36m errore: {env.get('errore')}"}
    o = env["outputs"]
    pef = deliverable.setdefault("piano_economico_finanziario", {})

    # 1) 36 mesi — copia diretta (solo le chiavi a schema)
    pef["budget_mensile_36m"] = [{k: m[k] for k in _MESE_KEYS if k in m} for m in o["budget_mensile_36m"]]

    # 2) scenari (ricavi/EBITDA dal motore; EV = EBITDA_anno3 × multiplo)
    ebitda_base = base["ricavi_eur_anno_base"] - base["costi_fissi_eur_anno_base"] - base["costi_variabili_eur_anno_base"]
    mult = _multiplo(deliverable, ebitda_base)
    sc_env = budget_scenari(base, pfn_iniziale_eur=pfn0)
    scen_out = sc_env.get("outputs", {}).get("scenari", {}) if "outputs" in sc_env else {}
    scen_map: dict[str, dict] = {}
    ev_base: Optional[float] = None
    for nome in ("base", "ottimistico", "pessimistico"):
        s = scen_out.get(nome)
        if not s or not s.get("totali_annui"):
            continue
        ta = s["totali_annui"]
        a1, a3 = ta[0], ta[2]
        ev = round(a3["ebitda"] * mult, 2) if mult else None
        if nome == "base":
            ev_base = ev
        entry = {
            "nome": nome,
            "ricavi_anno1_eur": round(a1["ricavi"], 2),
            "ricavi_anno2_eur": round(ta[1]["ricavi"], 2),
            "ricavi_anno3_eur": round(a3["ricavi"], 2),
            "ebitda_anno3_eur": round(a3["ebitda"], 2),
            "ebitda_margin_anno3": round(a3["ebitda"] / a3["ricavi"] * 100, 2) if a3.get("ricavi") else None,
            "condizioni": f"crescita ricavi {s.get('crescita_ricavi_pct_anno')}%/anno",
        }
        if ev is not None:
            entry["enterprise_value_eur"] = ev
        scen_map[nome] = entry
    for nome, s in scen_map.items():
        if ev_base is not None and "enterprise_value_eur" in s:
            s["delta_ev_vs_base_eur"] = round(s["enterprise_value_eur"] - ev_base, 2)
    # sovrascrivo gli scenari SOLO se ho l'EV per tutti (enterprise_value_eur è required a schema)
    scenari_bound = bool(scen_map) and all("enterprise_value_eur" in s for s in scen_map.values())
    if scenari_bound:
        pef["scenari"] = {k: scen_map[k] for k in ("base", "ottimistico", "pessimistico") if k in scen_map}

    # 3) sensitivity
    se_env = budget_sensitivity(base, delta_pct=_DELTA_PCT)
    if "outputs" in se_env:
        base_eb = _num(se_env["outputs"].get("base_ebitda_cumulato_36m_eur"))
        pef["sensitivity"] = _map_sensitivity(se_env["outputs"].get("matrice", {}), base_eb)

    # 4) ipotesi_base (narrativa deterministica e ONESTA su default/assenze)
    cv0 = base["costi_variabili_eur_anno_base"]
    da_of_assenti = base["ammortamenti_eur_anno_base"] == 0 and base["oneri_finanziari_eur_anno_base"] == 0
    aliq_txt = f"{aliquota_pct}%" if aliquota_pct is not None else "default motore"
    ipotesi = [
        f"Ricavi base {round(base['ricavi_eur_anno_base'])}€ · EBITDA base {round(ebitda_base)}€",
        (f"Costi variabili {round(cv0)}€" if cv0 else "Costi variabili = 0 (convenzione PMI servizi: nessun COGS proporzionale)"),
        f"Aliquota imposte {aliq_txt} (IRES+IRAP semplificata; vedi warning motore)",
        "Crescita ricavi/costi fissi: default 2%/anno (assunzioni custom dal form NON ancora passate al motore)",
        (f"PFN iniziale: {round(pfn0)}€ (negativo = cassa netta)" if pfn0 is not None else "PFN iniziale non nota → rollforward da 0"),
    ]
    if da_of_assenti:
        ipotesi.append("⚠ Ammortamenti e oneri finanziari assenti dal bilancio (=0): utile netto e FCF potenzialmente sovrastimati")
    pef["ipotesi_base"] = ipotesi

    return {
        "disponibile": True, "scenari_bound": scenari_bound,
        "mesi": len(pef["budget_mensile_36m"]), "multiplo_ev_usato": mult,
        "pfn_iniziale": pfn0, "da_of_assenti": da_of_assenti,
        "warnings_motore": [w.get("codice") for w in env.get("warnings", [])],
        "note": (None if scenari_bound else "scenari NON sovrascritti: manca il multiplo EV (lascio l'LLM, enterprise_value_eur è required)"),
        "provenance": "k2a_budget.budget_36m/scenari/sensitivity (vendorizzato @5c54105)",
    }


def apply_budget(deliverable: dict, inputs: dict) -> tuple[dict, Optional[dict]]:
    if not isinstance(deliverable, dict):
        return deliverable, None
    return deliverable, bind_pef(deliverable, inputs)
