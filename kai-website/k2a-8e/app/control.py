"""ControlBoost (cruscotto-direzionale) — KPI Balanced Scorecard DETERMINISTICI.

Il flagship (1499€) NON aveva binder: le 4 prospettive BSC (finanziaria/cliente/processi/
crescita), gli alert e il trend li scriveva l'LLM → su Gemma uscivano vuoti/placeholder e
il gate rifiutava ('[] should be non-empty'), su Claude erano numeri INVENTATI in un cruscotto
di supporto decisionale. Qui i KPI si calcolano dai dati operativi del mese (fatturato, costi,
incassi/pagamenti, clienti, ore, cassa, crediti). Modellato su finance/host/tax.
"""
from __future__ import annotations

from typing import Any, Optional


def _num(v: Any) -> Optional[float]:
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        s = v.strip().replace("€", "").replace("%", "").replace(" ", "")
        if "," in s and "." in s:
            s = s.replace(".", "").replace(",", ".")
        elif "," in s:
            s = s.replace(",", ".")
        try:
            return float(s)
        except ValueError:
            return None
    return None


def _sem(valore: Optional[float], target: Optional[float], higher_better: bool = True,
         tol: float = 0.05) -> str:
    """verde/giallo/rosso confrontando valore e target. tol = banda gialla (±5% default)."""
    if valore is None or target is None:
        return "giallo"
    if target == 0:  # target 'almeno 0' (es. cash flow): positivo=verde, zero=giallo, negativo=rosso
        return "verde" if valore > 0 else ("giallo" if valore == 0 else "rosso")
    ratio = valore / target
    if not higher_better:
        ratio = 2 - ratio  # inverti: sotto-target è bene
    if ratio >= 1 - tol:
        return "verde"
    if ratio >= 1 - 3 * tol:
        return "giallo"
    return "rosso"


def _kpi(nome, valore, target, unita, higher_better=True, formula="", nota=""):
    if valore is None:
        return None
    sem = _sem(valore, target, higher_better)
    # scostamento % vs target; con target 0 (es. cash flow ≥0) lo scostamento non è definito → 0.0
    scost = round((valore / target - 1) * 100, 1) if target not in (None, 0) else 0.0
    return {"nome": nome, "valore": round(valore, 2), "target": round(target, 2) if target is not None else 0.0,
            "unita": unita, "semaforo": sem, "scostamento_percentuale": scost,
            "formula": formula, "fonte_dati": "dati operativi del mese (K2-AI)", "nota": nota}


def apply_controlboost(deliverable: dict, form: dict) -> tuple[dict, Optional[dict]]:
    """Sovrascrive le 4 prospettive KPI + alert + trend coi numeri DETERMINISTICI dai dati
    operativi. Se mancano i dati minimi (fatturato/costi) lascia stare (il gate deciderà)."""
    if not isinstance(deliverable, dict) or not isinstance(form, dict):
        return deliverable, None
    fatt = _num(form.get("fatturato"))
    costi = _num(form.get("costi_operativi"))
    if fatt is None or costi is None:
        return deliverable, None
    incassi, pagamenti = _num(form.get("incassi")), _num(form.get("pagamenti"))
    nuovi, persi = _num(form.get("nuovi_clienti")), _num(form.get("clienti_persi"))
    attivi = _num(form.get("clienti_attivi"))
    ore_lav, ore_fat = _num(form.get("ore_lavorate")), _num(form.get("ore_fatturabili"))
    cassa = _num(form.get("posizione_cassa"))
    crediti = _num(form.get("crediti"))
    conc = _num(form.get("concentrazione_top5_pct"))
    budget = _num(form.get("target_budget")) or fatt
    margine = fatt - costi
    margine_pct = margine / fatt * 100 if fatt else None

    fin = [
        _kpi("Fatturato del mese", fatt, budget, "EUR", True, "fatturato vs target budget"),
        _kpi("Margine operativo", margine, fatt * 0.15, "EUR", True, "fatturato − costi operativi"),
        _kpi("Margine operativo %", margine_pct, 15, "%", True, "margine / fatturato"),
    ]
    if incassi is not None and pagamenti is not None:
        fin.append(_kpi("Cash flow del mese", incassi - pagamenti, 0, "EUR", True, "incassi − pagamenti"))
    if cassa is not None:
        fin.append(_kpi("Posizione di cassa", cassa, max(pagamenti or 0, fatt * 0.5), "EUR", True,
                        "saldo cassa a fine mese", "target orientativo: ~1 mese di uscite"))

    cli = []
    if attivi is not None:
        cli.append(_kpi("Clienti attivi", attivi, attivi, "n.", True, "clienti con fatturato nel mese"))
    if nuovi is not None:
        cli.append(_kpi("Nuovi clienti", nuovi, max(1, (persi or 0) + 1), "n.", True, "acquisiti nel mese"))
    if persi is not None and attivi:
        cli.append(_kpi("Churn rate", persi / attivi * 100, 5, "%", False, "clienti persi / attivi",
                        "soglia di attenzione ~5%/mese"))
    if conc is not None:
        cli.append(_kpi("Concentrazione top-5", conc, 30, "%", False, "quota fatturato dei primi 5 clienti",
                        "sopra il 40% = rischio dipendenza"))

    proc = []
    if ore_lav and ore_fat is not None:
        proc.append(_kpi("Utilizzo (billability)", ore_fat / ore_lav * 100, 80, "%", True,
                         "ore fatturabili / ore lavorate"))
    if crediti is not None and fatt:
        proc.append(_kpi("DSO (giorni incasso)", crediti / fatt * 30, 60, "gg", False,
                         "crediti / fatturato × 30", "giorni medi di incasso"))

    cresc = [_kpi("Raggiungimento budget", fatt / budget * 100, 100, "%", True, "fatturato / target budget")]
    if nuovi is not None and persi is not None:
        cresc.append(_kpi("Crescita netta clienti", nuovi - persi, 0, "n.", True, "nuovi − persi"))

    fin = [k for k in fin if k]; cli = [k for k in cli if k]
    proc = [k for k in proc if k]; cresc = [k for k in cresc if k]

    # ALERT: ogni KPI rosso/giallo → alert (livello, deviazione, causa, azione).
    alert = []
    for persp, kpis in (("finanziaria", fin), ("cliente", cli), ("processi", proc), ("crescita", cresc)):
        for k in kpis:
            if k["semaforo"] in ("rosso", "giallo"):
                tipo = "concentrazione" if "oncentraz" in k["nome"] else "scostamento_target"
                alert.append({
                    "kpi": k["nome"], "livello": k["semaforo"], "tipo": tipo,
                    "priorita": 1 if k["semaforo"] == "rosso" else 2,
                    "deviazione": f"{k['scostamento_percentuale']}% vs target",
                    "valore_attuale": k["valore"], "valore_target": k["target"],
                    "scostamento_percentuale": k.get("scostamento_percentuale") or 0.0,
                    "cause": ["Da approfondire con la direzione: il valore è calcolato dai dati "
                              "operativi del mese, la causa va letta nel contesto gestionale."],
                    "azione": f"Verificare «{k['nome']}» e definire un'azione correttiva prima del prossimo mese.",
                })

    # TREND: senza storico, un solo punto (il mese corrente) — soddisfa minItems=1 senza inventare.
    mese = str(form.get("mese") or form.get("anno") or "mese corrente")
    trend = {"mesi": [mese], "fatturato": [round(fatt, 2)], "budget": [round(budget, 2)],
             "ebitda": [round(margine, 2)],
             "cashflow": [round((incassi - pagamenti), 2)] if (incassi is not None and pagamenti is not None) else [],
             "clienti_attivi": [attivi] if attivi is not None else [],
             "nuovi_clienti": [nuovi] if nuovi is not None else [],
             "clienti_persi": [persi] if persi is not None else [],
             "dso": [round(crediti / fatt * 30, 1)] if (crediti is not None and fatt) else [],
             "posizione_cassa": [cassa] if cassa is not None else []}

    out = dict(deliverable)
    out["kpi_finanziaria"] = fin
    if cli:
        out["kpi_cliente"] = cli
    if proc:
        out["kpi_processi"] = proc
    if cresc:
        out["kpi_crescita"] = cresc
    out["alert"] = alert
    out["trend_12_mesi"] = trend
    return out, {"controlboost_kpi_deterministici": True,
                 "n_kpi": len(fin) + len(cli) + len(proc) + len(cresc), "n_alert": len(alert)}
