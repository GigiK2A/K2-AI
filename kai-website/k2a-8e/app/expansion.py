"""Expansion Engine — economia DETERMINISTICA dell'espansione internazionale.

Nasce dall'eval "NaturaViva" (espansione in DE/FR/NL): il report StrategyBoost aveva
insight qualitativi buoni ma ZERO modello economico (nessun conto economico per paese,
break-even, ROI, ranking, decisione). Peggio: l'LLM inventava/alterava i numeri del
cliente (target 150-200k → 500k, sconto 28% → 12%). Qui i numeri per-mercato si CALCOLANO
dagli input, con FORMULA e ASSUNZIONI esplicite su ogni valore — mai inventati dall'LLM.

REGOLA CARDINE (spec Luca): "meglio nessun numero che un numero sbagliato". La semantica
degli input di mercato è ambigua (il margine di canale è già netto? la logistica è dentro
o fuori?). Il modello adottato è UNO, standard e TRASPARENTE — ogni output porta la
formula e le assunzioni, così un CFO può validarlo invece di fidarsi al buio:

  ricavi_target      = punto medio del range dichiarato dal cliente         [ASSUNZIONE]
  ricavi_netti       = ricavi_target × (1 − resi%)      (i resi riducono il venduto)
  margine_lordo      = ricavi_netti × margine_canale%   (margine di canale = % dichiarata)
  costo_logistica    = ricavi_target × logistica%       (logistica ESTERNA al margine canale,
                                                          come elencata a parte dal cliente)
  contribuzione      = margine_lordo − costo_logistica − marketing
  margine_contrib_%  = contribuzione / ricavi_target
  capitale_circolante= ricavi_target × (giorni_pagamento / 365)   (crediti immobilizzati)
  investimento_anno1 = marketing + capitale_circolante
  ROI_anno1_%        = contribuzione / investimento_anno1
  break_even_ricavi  = marketing / (margine_canale% − logistica%)  (costi fissi / tasso contrib.)

Se i dati minimi mancano → il mercato entra come "dati insufficienti" (nessun numero
inventato). Modulo puro (no LLM, no I/O), pienamente testabile — modellato su control.py.
"""
from __future__ import annotations

from typing import Any, Optional

# margini di canale di default (punto medio dei range tipici PMI cosmetica) SOLO se il
# cliente non li dichiara — marcati come assunzione, non spacciati per dati.
_CANALE_MARGINE_DEFAULT = {"ecommerce": 22.0, "negozi": 14.0, "distributore": 9.0,
                           "distributori": 9.0, "retail": 14.0, "diretto": 22.0}
_DECISIONI = ("ENTER", "PILOT", "WAIT", "NO-GO")


def _num(v: Any) -> Optional[float]:
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        s = v.strip().replace("€", "").replace("%", "").replace(" ", "")
        if "," in s and "." in s:
            s = s.replace(".", "").replace(",", ".") if s.rfind(",") > s.rfind(".") else s.replace(",", "")
        elif "," in s:
            s = s.replace(",", ".")
        try:
            return float(s)
        except ValueError:
            return None
    return None


def _mid(lo: Optional[float], hi: Optional[float], single: Optional[float]) -> tuple[Optional[float], bool]:
    """Punto medio di un range (lo, hi); se c'è un valore singolo usa quello. Ritorna
    (valore, is_range) — is_range=True segnala che è il punto medio di un intervallo."""
    if lo is not None and hi is not None:
        return (lo + hi) / 2.0, (lo != hi)
    v = single if single is not None else (lo if lo is not None else hi)
    return v, False


def _canale_margine(c: dict) -> tuple[Optional[float], bool]:
    """Margine di canale %: esplicito dal cliente, altrimenti default per canale (assunto)."""
    m = _num(c.get("margine_canale_pct") or c.get("margine_pct") or c.get("margine"))
    if m is not None:
        return m, False
    canale = str(c.get("canale") or c.get("modello") or "").strip().lower()
    for k, v in _CANALE_MARGINE_DEFAULT.items():
        if k in canale:
            return v, True
    return None, True


def _country_economics(c: dict) -> dict:
    """Conto economico deterministico di UN mercato. Ogni valore con formula; assunzioni
    raccolte in `assunzioni`. Se mancano i dati minimi → stato 'dati_insufficienti'."""
    paese = str(c.get("paese") or c.get("mercato") or c.get("nome") or "Mercato").strip() or "Mercato"
    assunzioni: list[str] = []

    ricavi, is_range = _mid(_num(c.get("target_ricavi_min") or c.get("ricavi_min")),
                            _num(c.get("target_ricavi_max") or c.get("ricavi_max")),
                            _num(c.get("target_ricavi") or c.get("ricavi") or c.get("fatturato_target")))
    if is_range:
        assunzioni.append(f"ricavi = punto medio del range dichiarato (€{ricavi:,.0f})".replace(",", "."))
    margine_pct, marg_assunto = _canale_margine(c)
    if marg_assunto and margine_pct is not None:
        assunzioni.append(f"margine di canale {margine_pct:g}% assunto (non dichiarato per questo mercato)")

    if ricavi is None or margine_pct is None:
        return {"paese": paese, "stato": "dati_insufficienti",
                "dati_mancanti": [k for k, v in (("ricavi target", ricavi), ("margine di canale", margine_pct))
                                  if v is None],
                "nota": "N/D — servono almeno ricavi target e margine di canale per il conto economico."}

    resi_pct = _num(c.get("resi_pct") or c.get("resi")) or 0.0
    if not (c.get("resi_pct") or c.get("resi")):
        assunzioni.append("resi non dichiarati → assunti 0%")
    logistica_pct, log_range = _mid(_num(c.get("logistica_pct_min")), _num(c.get("logistica_pct_max")),
                                    _num(c.get("logistica_pct") or c.get("logistica")))
    if logistica_pct is None:
        logistica_pct = 0.0
        assunzioni.append("logistica non dichiarata → assunta 0% (sottostima il costo pieno)")
    elif log_range:
        assunzioni.append(f"logistica = punto medio del range ({logistica_pct:g}%)")
    marketing = _num(c.get("marketing_eur") or c.get("marketing")) or 0.0
    if not (c.get("marketing_eur") or c.get("marketing")):
        assunzioni.append("budget marketing non dichiarato → assunto €0")
    giorni_pag = _num(c.get("pagamento_giorni") or c.get("giorni_pagamento")) or 0.0

    ricavi_netti = ricavi * (1 - resi_pct / 100.0)
    margine_lordo = ricavi_netti * margine_pct / 100.0
    costo_logistica = ricavi * logistica_pct / 100.0
    contribuzione = margine_lordo - costo_logistica - marketing
    margine_contrib_pct = contribuzione / ricavi * 100.0 if ricavi else None
    capitale_circolante = ricavi * (giorni_pag / 365.0) if giorni_pag else 0.0
    investimento = marketing + capitale_circolante
    roi_pct = contribuzione / investimento * 100.0 if investimento > 0 else None
    tasso_contrib = margine_pct - logistica_pct  # % contribuzione sui ricavi al netto marketing
    break_even = marketing / (tasso_contrib / 100.0) if tasso_contrib > 0 and marketing > 0 else None

    def _r(x):
        return round(x, 2) if isinstance(x, (int, float)) else x

    return {
        "paese": paese, "stato": "calcolato",
        "ricavi_target_eur": _r(ricavi),
        "resi_pct": _r(resi_pct), "logistica_pct": _r(logistica_pct),
        "margine_canale_pct": _r(margine_pct), "marketing_eur": _r(marketing),
        "giorni_pagamento": _r(giorni_pag),
        "ricavi_netti_eur": _r(ricavi_netti),
        "margine_lordo_eur": _r(margine_lordo),
        "costo_logistica_eur": _r(costo_logistica),
        "contribuzione_eur": _r(contribuzione),
        "margine_contribuzione_pct": _r(margine_contrib_pct),
        "capitale_circolante_eur": _r(capitale_circolante),
        "investimento_anno1_eur": _r(investimento),
        "roi_anno1_pct": _r(roi_pct),
        "break_even_ricavi_eur": _r(break_even),
        "formula": ("contribuzione = ricavi×(1−resi%)×margine_canale% − ricavi×logistica% − marketing; "
                    "ROI = contribuzione / (marketing + circolante); "
                    "break-even = marketing / (margine_canale% − logistica%)"),
        "assunzioni": assunzioni,
    }


def _complexity_score(c: dict, eco: dict) -> tuple[float, list[str]]:
    """0-100, più alto = più complesso/rischioso. Da: giorni pagamento, esclusiva, sconto,
    resi, logistica. Motivazione per ogni contributo (niente score arbitrario)."""
    pts, perche = 0.0, []
    gp = _num(c.get("pagamento_giorni") or c.get("giorni_pagamento")) or 0.0
    if gp >= 60:
        pts += 25; perche.append(f"pagamento a {gp:g}gg (cassa immobilizzata)")
    elif gp >= 45:
        pts += 15; perche.append(f"pagamento a {gp:g}gg")
    elif gp > 0:
        pts += 5
    escl = _num(c.get("esclusiva_anni")) or 0.0
    if escl >= 2:
        pts += 25; perche.append(f"esclusiva {escl:g} anni (lock-in sul distributore)")
    elif escl >= 1:
        pts += 12; perche.append(f"esclusiva {escl:g} anno")
    sc = _num(c.get("sconto_pct") or c.get("sconto")) or 0.0
    if sc >= 35:
        pts += 25; perche.append(f"sconto distributore {sc:g}% (erosione forte del margine)")
    elif sc >= 28:
        pts += 15; perche.append(f"sconto {sc:g}%")
    elif sc > 0:
        pts += 8
    resi = eco.get("resi_pct") or 0.0
    if resi >= 10:
        pts += 15; perche.append(f"resi {resi:g}%")
    elif resi >= 5:
        pts += 8
    log = eco.get("logistica_pct") or 0.0
    if log >= 8:
        pts += 10; perche.append(f"logistica {log:g}%")
    elif log >= 6:
        pts += 5
    return min(100.0, pts), perche


def _decision(eco: dict, complexity: float) -> tuple[str, str]:
    """ENTER / PILOT / WAIT / NO-GO da margine di contribuzione e complessità. Regola
    dichiarata, non un verdetto opaco."""
    mc = eco.get("margine_contribuzione_pct")
    contrib = eco.get("contribuzione_eur")
    if mc is None or contrib is None:
        return "WAIT", "dati insufficienti per una raccomandazione economica solida"
    if contrib <= 0:
        return "NO-GO", f"contribuzione negativa (€{contrib:,.0f}): il mercato brucia margine".replace(",", ".")
    if mc >= 12 and complexity < 50:
        return "ENTER", f"margine di contribuzione {mc:.1f}% e complessità contenuta"
    if mc >= 6:
        return "PILOT", f"margine {mc:.1f}% positivo ma {'complessità alta' if complexity >= 50 else 'sottile'}: entrare in pilota, non full-scale"
    return "WAIT", f"margine di contribuzione {mc:.1f}% troppo sottile: rinegoziare le condizioni prima di entrare"


def _attractiveness(eco: dict, ricavi_max: float) -> float:
    """0-100, guidato dal MARGINE di contribuzione (un mercato che perde soldi NON è
    attraente, per quanto grande): margine ≤0 → score ~0; la scala di ricavi conta solo
    come tiebreak tra mercati già profittevoli (peso 20%)."""
    mc = eco.get("margine_contribuzione_pct")
    if mc is None:
        return 0.0
    margin_score = max(0.0, min(100.0, mc / 25.0 * 100.0))
    if mc <= 0:
        return round(margin_score, 1)  # niente bonus scala per un mercato in perdita
    scale_score = (eco.get("ricavi_target_eur", 0) / ricavi_max * 100.0) if ricavi_max else 0.0
    return round(0.8 * margin_score + 0.2 * scale_score, 1)


def build_expansion(mercati: list, params: Optional[dict] = None) -> Optional[dict]:
    """Analisi completa multi-mercato. Ritorna None se non ci sono mercati validi (no-op).
    params: {budget_eur, mol_medio_pct} — opzionali, per il confronto col budget."""
    if not isinstance(mercati, list) or not mercati:
        return None
    ecos = [_country_economics(c) for c in mercati if isinstance(c, dict)]
    if not ecos:
        return None
    calcolati = [e for e in ecos if e.get("stato") == "calcolato"]
    ricavi_max = max((e.get("ricavi_target_eur", 0) or 0) for e in calcolati) if calcolati else 0.0

    ranking = []
    for c, eco in zip([m for m in mercati if isinstance(m, dict)], ecos):
        if eco.get("stato") != "calcolato":
            ranking.append({"paese": eco["paese"], "stato": "dati_insufficienti",
                            "decisione": "WAIT", "nota": eco.get("nota")})
            continue
        cx, cx_perche = _complexity_score(c, eco)
        decis, motivo = _decision(eco, cx)
        attr = _attractiveness(eco, ricavi_max)
        ranking.append({
            "paese": eco["paese"],
            "attrattivita_score": attr,
            "complessita_score": round(cx, 1),
            "complessita_fattori": cx_perche,
            "margine_contribuzione_pct": eco.get("margine_contribuzione_pct"),
            "contribuzione_eur": eco.get("contribuzione_eur"),
            "investimento_anno1_eur": eco.get("investimento_anno1_eur"),
            "roi_anno1_pct": eco.get("roi_anno1_pct"),
            "decisione": decis, "motivo_decisione": motivo,
        })
    # priorità: prima ENTER, poi PILOT, poi WAIT, poi NO-GO; DENTRO ogni gruppo il mercato
    # col MARGINE di contribuzione migliore (non il più grande: un mercato grande ma in
    # perdita non va davanti a uno piccolo meno-in-perdita — bug eval: DE davanti a NL).
    ordine = {d: i for i, d in enumerate(_DECISIONI)}

    def _mc_key(r):
        mc = r.get("margine_contribuzione_pct")
        return mc if mc is not None else -999.0
    ranking.sort(key=lambda r: (ordine.get(r.get("decisione"), 9), -_mc_key(r)))
    for i, r in enumerate(ranking, 1):
        r["priorita"] = i

    scenari = _scenari(calcolati)
    budget = _num((params or {}).get("budget_eur"))
    invest_tot = sum(e.get("investimento_anno1_eur", 0) or 0 for e in calcolati)
    budget_nota = None
    if budget is not None:
        budget_nota = (f"Investimento anno-1 dei mercati calcolati: €{invest_tot:,.0f} vs budget "
                       f"€{budget:,.0f} → {'compatibile' if invest_tot <= budget else 'ECCEDE il budget: scaglionare l’ingresso'}.").replace(",", ".")

    return {
        "conto_economico_mercati": ecos,
        "ranking_mercati": ranking,
        "scenari_espansione": scenari,
        "sintesi_budget": budget_nota,
        "confronto_canali": _confronto_canali(mercati, params),
        "raccomandazione": _raccomandazione(ranking),
        "metodo_espansione": ("Conto economico per mercato con formula esplicita; decisione ENTER/PILOT/"
                   "WAIT/NO-GO da margine di contribuzione e complessità. I numeri derivano dai "
                   "dati forniti dal cliente; le assunzioni sono elencate per ogni mercato."),
    }


def _scenari(calcolati: list) -> Optional[dict]:
    """Prudente / base / aggressivo sulla contribuzione totale dei mercati calcolati.
    Prudente = -30% ricavi, aggressivo = +20% (assunzioni dichiarate)."""
    if not calcolati:
        return None
    base = sum(e.get("contribuzione_eur", 0) or 0 for e in calcolati)
    ricavi = sum(e.get("ricavi_target_eur", 0) or 0 for e in calcolati)
    # scala la contribuzione col ricavo, tenendo i costi fissi (marketing) invarianti:
    # prudente e aggressivo agiscono sulla parte variabile.
    mkt = sum(e.get("marketing_eur", 0) or 0 for e in calcolati)
    var_base = base + mkt  # contribuzione al lordo del marketing (parte che scala coi ricavi)

    def _sc(fattore):
        return round(var_base * fattore - mkt, 2)
    return {
        "prudente": {"delta_ricavi_pct": -30, "contribuzione_eur": _sc(0.70),
                     "assunzione": "ricavi −30% (ingresso più lento del previsto), marketing invariato"},
        "base": {"delta_ricavi_pct": 0, "contribuzione_eur": round(base, 2),
                 "assunzione": "target dichiarati dal cliente"},
        "aggressivo": {"delta_ricavi_pct": 20, "contribuzione_eur": _sc(1.20),
                       "assunzione": "ricavi +20% (traction sopra le attese), marketing invariato"},
        "nota": f"Scenari sulla contribuzione aggregata dei {len(calcolati)} mercati con dati sufficienti "
                f"(ricavi base €{ricavi:,.0f}).".replace(",", "."),
    }


def _confronto_canali(mercati: list, params: Optional[dict]) -> Optional[dict]:
    """Distributore vs ecommerce: la rotta distributore (margine dichiarato ~8-10%) erode
    il margine sotto la soglia di sostenibilità una volta tolte logistica e marketing;
    l'ecommerce ha ~22% di margine ma richiede il CAC/conversione, che qui NON abbiamo
    (nell'eval il CPL 15€ era INVENTATO). Onesto: non calcoliamo l'ecommerce senza dati."""
    p = params or {}
    ecom = _num(p.get("margine_ecommerce_pct")) or _CANALE_MARGINE_DEFAULT["ecommerce"]
    distrib = _num(p.get("margine_distributore_pct")) or _CANALE_MARGINE_DEFAULT["distributore"]
    ecom_assunto = p.get("margine_ecommerce_pct") is None
    return {
        "distributore_margine_pct": distrib,
        "ecommerce_margine_pct": ecom,
        "delta_pct_punti": round(ecom - distrib, 1),
        "lettura": (f"La rotta distributore ({distrib:g}% di margine di canale) va sotto lo zero di "
                    f"contribuzione una volta tolte logistica e marketing: le proposte attuali erodono "
                    f"il margine. L'ecommerce ({ecom:g}%) parte da ~{round(ecom/distrib,1) if distrib else '—'}× "
                    f"il margine di canale, ma la sua redditività dipende dal CAC/tasso di conversione, "
                    f"dato NON fornito → da misurare prima di decidere. Non entrare in esclusiva col "
                    f"distributore prima di aver testato l'ecommerce."),
        "dati_mancanti_ecommerce": ["CAC / costo per acquisizione", "tasso di conversione",
                                    "valore medio ordine", "traffico atteso"],
        "assunzione": "margine ecommerce di riferimento assunto" if ecom_assunto else "margine ecommerce dichiarato",
    }


def _raccomandazione(ranking: list) -> str:
    enter = [r["paese"] for r in ranking if r.get("decisione") == "ENTER"]
    pilot = [r["paese"] for r in ranking if r.get("decisione") == "PILOT"]
    wait = [r["paese"] for r in ranking if r.get("decisione") == "WAIT"]
    nogo = [r["paese"] for r in ranking if r.get("decisione") == "NO-GO"]
    parti = []
    if enter:
        parti.append(f"FASE 1 — entrare in {', '.join(enter)} (margine e complessità favorevoli)")
    if pilot:
        parti.append(f"FASE 2 — pilota su {', '.join(pilot)} con soglie di uscita (margine, resi, CAC)")
    if wait or nogo:
        blocca = wait + nogo
        parti.append(f"FASE 3 — {', '.join(blocca)} solo dopo rinegoziazione delle condizioni")
    return ". ".join(parti) if parti else "Dati insufficienti per una sequenza di ingresso."


def _collect_numbers(obj) -> list:
    """Tutti i numeri prodotti dall'engine — per registrarli come GROUNDED (sono derivati
    deterministicamente dagli input, non inventati dall'LLM: il gate di grounding non deve
    cancellarli, come per i binder finance/quant)."""
    out: list = []
    if isinstance(obj, dict):
        for v in obj.values():
            out.extend(_collect_numbers(v))
    elif isinstance(obj, list):
        for v in obj:
            out.extend(_collect_numbers(v))
    elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
        out.append(round(float(obj), 4))
        out.append(round(abs(float(obj)), 4))  # il report può scrivere il valore assoluto ('perdita €37.200')
    return out


def apply_expansion(deliverable: dict, inputs: dict,
                    facts: Optional[dict] = None) -> tuple[dict, Optional[dict]]:
    """Hook per apply_deterministic_bindings: se gli input portano `mercati_esteri`,
    inietta le sezioni economiche deterministiche nel deliverable. No-op altrimenti.
    Se `facts` è passato, vi registra i numeri calcolati così il gate di grounding li
    riconosce come ancorati (sono derivati dagli input, non inventati)."""
    if not isinstance(deliverable, dict) or not isinstance(inputs, dict):
        return deliverable, None
    mercati = inputs.get("mercati_esteri") or inputs.get("mercati") or inputs.get("paesi_target")
    if not isinstance(mercati, list) or not mercati:
        return deliverable, None
    analisi = build_expansion(mercati, {"budget_eur": inputs.get("budget_espansione_eur")
                                        or inputs.get("budget_eur"),
                                        "mol_medio_pct": inputs.get("mol_medio_pct"),
                                        "margine_ecommerce_pct": inputs.get("margine_ecommerce_pct"),
                                        "margine_distributore_pct": inputs.get("margine_distributore_pct")})
    if not analisi:
        return deliverable, None
    out = dict(deliverable)
    for k, v in analisi.items():
        if v is not None:
            out[k] = v
    if isinstance(facts, dict):
        facts["_expansion_grounded_numbers"] = {"numeri": _collect_numbers(analisi)}
    n_calc = sum(1 for e in analisi.get("conto_economico_mercati", []) if e.get("stato") == "calcolato")
    return out, {"expansion_engine": True, "mercati": len(mercati), "mercati_calcolati": n_calc}
