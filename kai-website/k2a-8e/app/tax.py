"""Motore fiscale DETERMINISTICO (Fix #4) — alimenta FiscoBoost.

Aliquote e imposte vengono SOLO da `grounding/tax-tables-fiscale.json` (consolidato
verificato da Luca, as_of 2026-06-21: IRPEF 23/33/43 L.199/2025, IRES 24%, IRAP 3,9%+magg.
banche/assic/energia, IVA 22/4/5/10), MAI dall'LLM. Ogni risultato porta la provenance
(norma/articolo/as_of) presa dalla tabella.

Voci locality/lista-dependent (addizionali IRPEF reg./com., variazioni IRAP regionali,
ATECO Tab.1) sono PARAMETRIZZATE: se il chiamante non fornisce il valore, vengono escluse
con una nota esplicita — non inventate (decisione Luca: "parametrizzare, non hardcodare").
"""
from __future__ import annotations

import functools
import json
import pathlib
import re
from typing import Any, Optional

_TABLES_PATH = pathlib.Path(__file__).resolve().parent.parent / "grounding" / "tax-tables-fiscale.json"

# forma giuridica → soggetto IRES (società di capitali) vs IRPEF (persone fisiche/società di persone)
_SOC_CAPITALI = {"srl", "srls", "spa", "sapa", "cooperativa"}


@functools.lru_cache(maxsize=1)
def _tables() -> dict:
    return json.loads(_TABLES_PATH.read_text(encoding="utf-8"))


def _as_of() -> str:
    return _tables().get("as_of", "")


def _pct(valore: Any) -> Optional[float]:
    """'23%' → 23.0 ; '3,9%' → 3.9 ; '+2 p.p. su aliquota base' → 2.0."""
    if valore is None:
        return None
    m = re.search(r"([+-]?\d+(?:[.,]\d+)?)", str(valore))
    return float(m.group(1).replace(",", ".")) if m else None


def _eur_it(x: float) -> str:
    """72000 → '€ 72.000' (migliaia col punto, stile IT). Nessuna cifra decimale."""
    return "€ " + format(int(round(x)), ",d").replace(",", ".")


def _find(imposta: str, *substr: str) -> Optional[dict]:
    """Prima voce verified di `imposta` la cui descrizione contiene TUTTI i substring."""
    for e in _tables().get("voci_verified", []):
        if e.get("imposta") != imposta:
            continue
        d = str(e.get("descrizione", "")).lower()
        if all(s.lower() in d for s in substr):
            return e
    return None


def _prov(e: Optional[dict]) -> dict:
    f = (e or {}).get("fonte", {})
    return {"norma": f.get("norma"), "articolo": f.get("articolo"), "versione": f.get("versione")}


# ───────────────────────── IRPEF ─────────────────────────

def _irpef_brackets() -> list[dict]:
    bs = [e for e in _tables().get("voci_verified", [])
          if e.get("imposta") == "IRPEF" and "soglia_da_eur" in e and str(e.get("valore", "")).endswith("%")]
    return sorted(bs, key=lambda e: e.get("soglia_da_eur") or 0)


def irpef_lorda(reddito_imponibile_eur: float) -> dict:
    """IRPEF lorda progressiva sugli scaglioni della tabella (no addizionali, no detrazioni)."""
    reddito = max(0.0, float(reddito_imponibile_eur or 0))
    brackets = _irpef_brackets()
    imposta = 0.0
    dettaglio = []
    for b in brackets:
        da = float(b.get("soglia_da_eur") or 0)
        a = b.get("soglia_a_eur")
        a = float(a) if a is not None else float("inf")
        rate = (_pct(b.get("valore")) or 0) / 100.0
        quota = max(0.0, min(reddito, a) - da)
        if quota > 0:
            q_imp = round(quota * rate, 2)
            imposta += q_imp
            dettaglio.append({"scaglione": b.get("descrizione"), "imponibile_eur": round(quota, 2),
                              "aliquota_pct": _pct(b.get("valore")), "imposta_eur": q_imp})
    imposta = round(imposta, 2)
    media = round(imposta / reddito * 100, 2) if reddito > 0 else 0.0
    return {"imposta": "IRPEF", "imposta_eur": imposta, "aliquota_media_pct": media,
            "dettaglio_scaglioni": dettaglio, "fonte": _prov(brackets[0] if brackets else None),
            "as_of": _as_of(),
            "note": ["IRPEF lorda su imponibile dato: NON include detrazioni/deduzioni né "
                     "addizionali regionale/comunale (locality-dependent, da parametrizzare)"]}


# ───────────────────────── IRES ─────────────────────────

def ires(imponibile_eur: float) -> dict:
    e = _find("IRES", "ordinaria")
    rate = _pct(e and e.get("valore")) or 24.0
    imp = round(max(0.0, float(imponibile_eur or 0)) * rate / 100.0, 2)
    return {"imposta": "IRES", "imposta_eur": imp, "aliquota_pct": rate, "fonte": _prov(e), "as_of": _as_of()}


# ───────────────────────── IRAP ─────────────────────────

_IRAP_BASE = {
    "ordinario": ("ordinaria (base)",),
    "banche": ("banche", "aliquota base"),
    "assicurazioni": ("assicurazione", "aliquota base"),
    "concessionarie": ("concessionarie",),
    "pa": ("pubblica amministrazione",),
}
_IRAP_EFFETTIVA = {  # aliquota effettiva 2026-2028 (maggiorazione L.199/2025 c.74)
    "banche": ("banche", "effettiva"),
    "assicurazioni": ("assicurazione", "effettiva"),
}


def irap(valore_produzione_netta_eur: float, tipo: str = "ordinario", anno: int = 2026,
         aliquota_regionale_pct: Optional[float] = None) -> dict:
    """IRAP sul valore della produzione netta. tipo ∈ {ordinario,banche,assicurazioni,
    concessionarie,pa}. 2026-2028: banche/assic. usano l'aliquota EFFETTIVA con maggiorazione.
    `aliquota_regionale_pct`: variazione regionale (locality-dependent, max ±0,92); se None →
    non applicata + nota."""
    tipo = (tipo or "ordinario").lower()
    note: list[str] = []
    entry = None
    if tipo in _IRAP_EFFETTIVA and 2026 <= anno <= 2028:
        entry = _find("IRAP", *_IRAP_EFFETTIVA[tipo])
    if entry is None:
        entry = _find("IRAP", *_IRAP_BASE.get(tipo, _IRAP_BASE["ordinario"]))
    rate = _pct(entry and entry.get("valore")) or 3.9

    if aliquota_regionale_pct is not None:
        rate = round(rate + float(aliquota_regionale_pct), 4)
        note.append(f"variazione regionale {aliquota_regionale_pct:+.2f} p.p. applicata (fornita dal chiamante)")
    else:
        note.append("variazione regionale IRAP non applicata (locality-dependent, da parametrizzare: "
                    "ogni regione delibera ex art.16 c.3 D.Lgs.446/97, max ±0,92 p.p.)")
    imp = round(max(0.0, float(valore_produzione_netta_eur or 0)) * rate / 100.0, 2)
    return {"imposta": "IRAP", "imposta_eur": imp, "aliquota_pct": rate, "tipo_soggetto": tipo,
            "anno": anno, "fonte": _prov(entry), "as_of": _as_of(), "note": note}


# ───────────────────────── IVA ─────────────────────────

_IVA = {"ordinaria": ("ordinaria",), "ridotta_10": ("parte iii",),
        "ridotta_5": ("ii-bis",), "ridotta_4": ("parte ii ",)}


def iva_aliquota(tipo: str = "ordinaria") -> dict:
    e = _find("IVA", *_IVA.get((tipo or "ordinaria").lower(), _IVA["ordinaria"]))
    return {"imposta": "IVA", "aliquota_pct": _pct(e and e.get("valore")), "tipo": tipo,
            "fonte": _prov(e), "as_of": _as_of()}


# ───────────────────────── carico fiscale stimato ─────────────────────────

def carico_fiscale_stimato(forma_giuridica: str, imponibile_eur: float,
                           valore_produzione_irap_eur: float, *, anno: int = 2026,
                           tipo_irap: str = "ordinario",
                           aliquota_irap_regionale_pct: Optional[float] = None) -> dict:
    """Stima del carico fiscale di una PMI: IRES (società di capitali) o IRPEF (altre) +
    IRAP sul valore della produzione. Numeri dal motore, provenance per voce, addizionali
    locality escluse con nota."""
    fg = (forma_giuridica or "").strip().lower().replace(" ", "_")
    if fg in _SOC_CAPITALI:
        reddito = ires(imponibile_eur)
    else:
        reddito = irpef_lorda(imponibile_eur)
        reddito = {"imposta": "IRPEF", "imposta_eur": reddito["imposta_eur"],
                   "aliquota_pct": reddito["aliquota_media_pct"], "fonte": reddito["fonte"],
                   "as_of": reddito["as_of"]}
    ir = irap(valore_produzione_irap_eur, tipo=tipo_irap, anno=anno,
              aliquota_regionale_pct=aliquota_irap_regionale_pct)
    dettaglio = [
        {"imposta": reddito["imposta"], "imposta_eur": reddito["imposta_eur"],
         "aliquota_pct": reddito["aliquota_pct"], "fonte": reddito["fonte"]},
        {"imposta": "IRAP", "imposta_eur": ir["imposta_eur"], "aliquota_pct": ir["aliquota_pct"],
         "fonte": ir["fonte"]},
    ]
    totale = round(sum(d["imposta_eur"] for d in dettaglio), 2)
    note = ["Addizionali IRPEF regionale e comunale NON incluse (locality-dependent, da "
            "parametrizzare per regione/comune)"] + ir["note"]
    return {"totale_eur": totale, "dettaglio": dettaglio, "forma_giuridica": forma_giuridica,
            "anno": anno, "as_of": _as_of(), "note": note,
            "fonte_principale": _tables().get("fonte_principale")}


# ───────────────────────── binding FiscoBoost (Fix #2 parte numeri) ─────────────────────────

def _num(v: Any) -> Optional[float]:
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return float(str(v).replace("€", "").replace(".", "").replace(",", ".").strip())
    except ValueError:
        return None


# Mappa canonica DECRETO ↔ ambito d'imposta. L'LLM (specie modelli meno precisi) tende
# a etichettare TUTTO come "TUIR", anche l'IVA (che è DPR 633/1972). Iniettata nei fatti
# pre-generazione → il modello cita il decreto ESATTO invece di inventarlo a memoria.
def norme_riferimento() -> str:
    return (
        "RIFERIMENTI NORMATIVI CANONICI (cita il DECRETO ESATTO, NON 'TUIR' come default):\n"
        "- IVA (detraibilità, aliquote, esigibilità, rivalsa): DPR 633/1972 — es. art. 19 "
        "detraibilità, art. 16 aliquote, art. 6 esigibilità. NON è il TUIR.\n"
        "- Redditi d'impresa, IRES, IRPEF, ammortamenti, interessi passivi, competenza: TUIR "
        "(DPR 917/1986) — es. art. 96 ROL/interessi, art. 102-103 ammortamenti, art. 108 spese, "
        "art. 109 competenza, art. 77 IRES, art. 11 IRPEF, art. 87 PEX.\n"
        "- IRAP (valore della produzione, aliquota): D.Lgs 446/1997 — es. art. 5, art. 16.\n"
        "- Accertamento/riscossione: DPR 600/1973 e DPR 602/1973. Fatturazione elettronica: "
        "D.Lgs 127/2015.\n"
        "REGOLA: se non sei certo del decreto, NON scrivere 'TUIR' a caso — usa la mappa qui sopra."
    )


def aliquote_riepilogo() -> list[dict]:
    """Aliquote verificate (con provenance) da iniettare come riferimento — non LLM."""
    out = []
    for imp, *subs in [("IRES", "ordinaria"), ("IRAP", "ordinaria (base)"), ("IVA", "ordinaria")]:
        e = _find(imp, *subs)
        if e:
            out.append({"imposta": imp, "descrizione": e.get("descrizione"), "valore": e.get("valore"),
                        "fonte": _prov(e)})
    bs = _irpef_brackets()
    out.append({"imposta": "IRPEF", "descrizione": "scaglioni",
                "valore": "/".join(str(_pct(b.get("valore"))) for b in bs) + "%",
                "fonte": _prov(bs[0] if bs else None)})
    return out


def apply_fiscoboost(deliverable: dict, form: dict) -> tuple[dict, Optional[dict]]:
    """Sovrascrive `sintesi.carico_fiscale_stimato` col valore deterministico (imposta sul
    reddito: IRES società di capitali, IRPEF altre, su utile ante imposte o fatturato-costi).
    IRAP esclusa (manca il valore della produzione netta nel form) → nota onesta, non inventata.
    Ritorna (deliverable, meta{carico, aliquote, note, provenance})."""
    if not isinstance(deliverable, dict):
        return deliverable, None
    out = dict(deliverable)
    sintesi = dict(out.get("sintesi") or {})

    imponibile = _num(form.get("utile_ante_imposte"))
    if imponibile is None:
        fat, cos = _num(form.get("fatturato")), _num(form.get("costi_totali"))
        if fat is not None and cos is not None:
            imponibile = fat - cos
    note = ["IRAP esclusa dal carico: richiede il valore della produzione netta, non presente "
            "nel form (calcolabile con un bilancio completo via FinanceBoost).",
            "Addizionali IRPEF regionale/comunale escluse (locality-dependent).",
            "Imponibile = utile ante imposte (o fatturato−costi): proxy dell'imponibile fiscale."]

    if imponibile is None or imponibile <= 0:
        sintesi["carico_fiscale_stimato"] = None
        note.insert(0, "carico non stimabile: imponibile (utile/fatturato−costi) assente o ≤0 nel form")
        red = None
    else:
        fg = str(form.get("forma_giuridica") or "").strip().lower().replace(" ", "_")
        red = ires(imponibile) if fg in _SOC_CAPITALI else irpef_lorda(imponibile)
        sintesi["carico_fiscale_stimato"] = red["imposta_eur"]
    out["sintesi"] = sintesi

    # Il numero-cardine di una diagnosi fiscale (l'imposta sul reddito) e il PERIMETRO del
    # calcolo (IRAP/addizionali escluse, con perché) vivevano solo in `sintesi.carico_fiscale_
    # stimato` (che il render NON mostra) e in questo `meta` (interno). Risultato: il report
    # rispondeva "quante tasse?" senza mai mostrare la cifra né il caveat. Inietto una VOCE
    # deterministica (voci-shape) → il numero e le esclusioni si vedono SEMPRE, a prescindere
    # dall'LLM (che a volte tronca/parafrasa). Prepend: è la voce di testa del report.
    # IRES espone 'aliquota_pct', IRPEF (progressiva) espone 'aliquota_media_pct':
    # un unico accesso robusto evita il KeyError sui soggetti IRPEF (ditta/SNC/SAS).
    _aliq = (red or {}).get("aliquota_pct") or (red or {}).get("aliquota_media_pct") or 0
    if red is not None:
        contenuto = (
            f"Imposta sul reddito stimata — {red['imposta']} {_aliq:g}% "
            f"su {_eur_it(imponibile)} di imponibile (utile ante imposte): "
            f"**{_eur_it(red['imposta_eur'])}**.\n\n"
            "Perimetro del calcolo — voci escluse (non stimate al buio, si evita di gonfiare o "
            "sottostimare il dovuto):\n"
            "• IRAP esclusa: richiede il valore della produzione netta, non presente nel form "
            "(calcolabile con un bilancio completo via FinanceBoost). Per una PMI con costo del "
            "personale rilevante l'IRAP è un'imposta aggiuntiva NON trascurabile.\n"
            "• Addizionali IRPEF regionale/comunale escluse (dipendono dal Comune/Regione).\n"
            "• Imponibile = utile ante imposte, proxy della base fiscale: la base IRES definitiva "
            "va corretta con le variazioni fiscali (costi indeducibili, ammortamenti, ecc.)."
        )
    else:
        contenuto = (
            "Carico fiscale NON stimabile: manca l'imponibile (utile ante imposte, oppure "
            "fatturato − costi) nel form. Fornisci l'utile ante imposte per il calcolo IRES/IRPEF "
            "deterministico. IRAP e addizionali restano comunque fuori perimetro (richiedono il "
            "valore della produzione netta e i dati locality)."
        )
    tax_voce = {
        "id": "carico-fiscale-stimato",
        "titolo": "Carico fiscale stimato — imposta sul reddito e perimetro",
        "contenuto": contenuto,
        "rischi_opportunita": [],
        "azioni": [],
        "fonti": ([{"riferimento": f"{red['imposta']} {_aliq:g}% — tabelle fiscali "
                    f"K2-AI (as_of {_as_of()})", "fonte": "catalogo"}] if red is not None else []),
    }
    voci = list(out.get("voci") or [])
    if not any(isinstance(v, dict) and v.get("id") == "carico-fiscale-stimato" for v in voci):
        out["voci"] = [tax_voce, *voci]

    meta = {
        "carico_fiscale_stimato": sintesi["carico_fiscale_stimato"],
        "imposta_reddito": (red.get("imposta") if red else None),
        "provenance": (red.get("fonte") if red else None),
        "aliquote": aliquote_riepilogo(), "as_of": _as_of(), "note": note,
    }
    return out, meta
