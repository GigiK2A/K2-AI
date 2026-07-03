"""Binder agevolazioni DETERMINISTICO (Fix #3).

I benefici (Nuova Sabatini, Transizione 5.0, de minimis) vengono dai tool del package
`k2a_agevolazioni` vendorizzato (`vendor/k2a_agevolazioni/`), importato come libreria —
non scritti dall'LLM. Calcola ciò che il form consente; dichiara onesto il resto.

Cumulabilità: NON sommata alla cieca — gli scenari sono derivati da una regola dichiarata
(base = miglior singolo strumento, no cumulo; massimo = somma con caveat di verifica).
De minimis: massimale dal tool; il plafond residuo È calcolato dagli aiuti pregressi del
form (`agevolazioni_gia_fruite`, testo libero → importi estratti con parser robusto) e
SOVRASCRIVE `profilo_aziendale.de_minimis_residuo_eur` (numero deterministico, non dall'LLM).
"""
from __future__ import annotations

import pathlib
import re
import sys
from datetime import date
from typing import Any, Optional

_VENDOR = pathlib.Path(__file__).resolve().parent.parent / "vendor"

try:
    if str(_VENDOR) not in sys.path:
        sys.path.insert(0, str(_VENDOR))
    from k2a_agevolazioni.nuova_sabatini import NuovaSabatiniInput, nuova_sabatini
    from k2a_agevolazioni.transizione_5_0 import Transizione50Input, transizione_5_0
    from k2a_agevolazioni.de_minimis import (
        AiutoDeMinimis, DeMinimisPlafondInput, de_minimis_plafond)
    _AVAILABLE = True
    _IMPORT_ERR = None
except Exception as exc:  # pragma: no cover
    _AVAILABLE = False
    _IMPORT_ERR = str(exc)

# Eleggibilità per strumento (tipo investimento del form → strumento)
_TIPO_SABATINI = {"macchinari", "software"}                       # beni strumentali
_TIPO_T50 = {"macchinari", "software", "efficienza_energetica"}   # beni 4.0 / Allegato IV-V


def _num(v: Any) -> Optional[float]:
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        s = v.strip().replace("€", "").replace(" ", "")
        if "," in s:
            s = s.replace(".", "").replace(",", ".")
        try:
            return float(s)
        except ValueError:
            return None
    return None


# L'autofill/LLM etichetta gli investimenti con parole libere ('server GPU', 'hardware',
# 'sviluppo software', 'R&S'…). I tool riconoscono solo i tipi canonici (macchinari/software/
# efficienza_energetica/rd). Normalizziamo i sinonimi → altrimenti un 'server GPU' non attiva
# né Sabatini né Transizione 5.0 e il beneficio esce 0 pur essendo un bene agevolabile.
# Ordine INTENZIONALE: le categorie specifiche (green/R&S/formazione) prima delle generiche
# (software/macchinari), così 'impianto fotovoltaico' → efficienza (non macchinari) e 'sviluppo
# software' → R&S (development, non un acquisto software agevolabile → conservativo, niente
# beneficio inventato). 'impiant' generico NON è in macchinari: troppo ambiguo.
_TIPO_SYNONYMS = (
    ("efficienza_energetica", ("efficienza energ", "fotovoltaic", "rinnovabil", "risparmio energetic",
                               "coibent", "pompa di calore", "colonnine")),
    ("rd", ("ricerca e sviluppo", "r&d", "r&s", "r & d", "r & s", "prototip", "brevett")),
    ("formazione", ("formazion", "corsi", "upskill", "addestrament del personale")),
    ("software", ("software", "licenz", "applicativ", "gestionale", "cloud", "saas")),
    ("macchinari", ("macchinar", "server", "gpu", "hardware", "attrezzatur", "computer", "workstation",
                    "bene strumentale", "beni strumentali", "impianto di produzione")),
)


def _canon_tipo(raw: Any) -> Optional[str]:
    """Mappa un'etichetta libera al tipo canonico del form. Se è già canonico, lo tiene."""
    t = str(raw or "").strip().lower()
    if not t:
        return None
    if t in ("macchinari", "software", "brevetti", "formazione", "efficienza_energetica",
             "rd", "assunzioni", "export", "edilizia"):
        return t
    for canon, keys in _TIPO_SYNONYMS:
        if any(k in t for k in keys):
            return canon
    return None


def _investment_sums(form: dict) -> dict:
    sums: dict[str, float] = {}
    for it in (form.get("investimenti_pianificati") or []):
        if not isinstance(it, dict):
            continue
        imp, tipo = _num(it.get("importo_stimato")), _canon_tipo(it.get("tipo"))
        if imp and imp > 0 and tipo:
            sums[tipo] = sums.get(tipo, 0.0) + imp
    return sums


def _settore_deminimis(form: dict) -> str:
    digits = "".join(ch for ch in str(form.get("settore_ateco") or "") if ch.isdigit())
    if digits[:2] in ("01", "02", "03"):  # agricoltura/pesca
        return "pesca_acquacoltura" if digits[:2] == "03" else "agricoltura_primaria"
    return "generale"


# Aiuti de minimis pregressi: il form li porta come testo libero (`agevolazioni_gia_fruite`).
# Estraiamo gli importi con un parser robusto (k/mila/mln, separatori IT/EN) per calcolare il
# plafond residuo in modo deterministico. Soglia 1.000€: scarta i falsi positivi tipo
# "Industria 5.0"/"Transizione 4.0" (i "4.0"/"5.0" NON sono importi).
_MULT_EUR = {"k": 1e3, "mila": 1e3, "mln": 1e6, "mio": 1e6, "milione": 1e6, "milioni": 1e6, "m": 1e6}


def _parse_eur_amount(text: Any) -> Optional[float]:
    if not isinstance(text, str) or not text.strip():
        return None
    s = text.lower().replace("€", " ").replace("euro", " ")
    for m in re.finditer(r"(\d{1,3}(?:[.,]\d{3})+|\d+(?:[.,]\d+)?)\s*(mln|mila|mio|milioni|milione|k|m)?\b", s):
        num_s, mult = m.group(1), m.group(2)
        if re.fullmatch(r"\d{1,3}(?:[.,]\d{3})+", num_s):     # separatori delle migliaia
            num = float(re.sub(r"[.,]", "", num_s))
        else:
            num = float(num_s.replace(",", "."))              # separatore decimale (o intero)
        if mult:
            num *= _MULT_EUR.get(mult, 1.0)
        if num >= 1000:                                       # scarta "4.0"/"5.0" e spiccioli
            return round(num, 2)
    return None


def _de_minimis_usato(form: dict) -> tuple[float, int]:
    """Somma gli aiuti de minimis pregressi (`agevolazioni_gia_fruite`) → (usato_eur, n_rilevati)."""
    tot, n = 0.0, 0
    for item in (form.get("agevolazioni_gia_fruite") or []):
        amt = _parse_eur_amount(item if isinstance(item, str) else str(item))
        if amt:
            tot += amt
            n += 1
    return round(tot, 2), n


def de_minimis_facts(form: dict) -> Optional[dict]:
    """Plafond de minimis DETERMINISTICO da iniettare nei `facts` PRE-generazione (pipeline.resolve),
    così la PROSA dell'LLM usa il residuo giusto e non lo ricalcola col vecchio massimale 200k.
    None se il package non è disponibile."""
    if not _AVAILABLE:
        return None
    usato, _ = _de_minimis_usato(form)
    settore = _settore_deminimis(form)
    if usato > 0:
        aiuti = [AiutoDeMinimis(importo_eur=usato, data_concessione=date.today(),
                                descrizione="aiuti pregressi (aggregato dal form)")]
        dm = de_minimis_plafond(DeMinimisPlafondInput(settore=settore, aiuti_ricevuti=aiuti))
    else:
        dm = de_minimis_plafond(DeMinimisPlafondInput(settore=settore))
    residuo = round(dm.plafond_residuo_eur, 2)
    _it = lambda x: f"{x:,.0f}".replace(",", ".")  # 300000 → "300.000"
    return {
        "massimale_eur": dm.massimale_eur, "usato_eur": usato, "residuo_eur": residuo,
        "riferimento": dm.riferimento_normativo,
        "nota": (f"Plafond de minimis: massimale {_it(dm.massimale_eur)}€ (Reg. UE 2023/2831, dal "
                 f"01/01/2024 — NON i vecchi 200.000€), aiuti pregressi {_it(usato)}€, residuo "
                 f"{_it(residuo)}€. Usa SEMPRE questi valori nel testo, non ricalcolarli."),
    }


def compute_benefici(form: dict) -> Optional[dict]:
    """Ritorna {benefici:{scenari + dettaglio_per_strumento}, note, provenance} o None se il
    package non è disponibile."""
    if not _AVAILABLE:
        return None
    sums = _investment_sums(form)
    dettaglio: list[dict] = []
    provenance: list[dict] = []

    fin_sab = round(sum(v for t, v in sums.items() if t in _TIPO_SABATINI), 2)
    if fin_sab > 0:
        s = nuova_sabatini(NuovaSabatiniInput(finanziamento_eur=fin_sab, tipologia="industria_4_0"))
        dettaglio.append({
            "strumento_id": "nuova_sabatini", "spesa_agevolabile_eur": fin_sab,
            "beneficio_lordo_eur": s.contributo_totale_eur, "beneficio_netto_eur": s.contributo_totale_eur,
            "aliquota_pct": s.contributo_su_finanziamento_pct,
        })
        provenance.append({"strumento": "nuova_sabatini", "fonte": "k2a_agevolazioni",
                           "riferimento": s.riferimento_normativo, "avvertenze": list(s.avvertenze)})

    inv_t50 = round(sum(v for t, v in sums.items() if t in _TIPO_T50), 2)
    if inv_t50 > 0:
        t = transizione_5_0(Transizione50Input(investimento_eur=inv_t50, anno_investimento=2026))
        if t.risparmio_imposta_stimato_eur is not None:
            dettaglio.append({
                "strumento_id": "transizione_5_0",
                "spesa_agevolabile_eur": t.investimento_agevolabile_eur,
                "beneficio_lordo_eur": t.risparmio_imposta_stimato_eur,
                "beneficio_netto_eur": t.risparmio_imposta_stimato_eur,
                "aliquota_pct": t.aliquota_imposta_pct,
            })
            provenance.append({"strumento": "transizione_5_0", "fonte": "k2a_agevolazioni",
                               "riferimento": t.riferimento_normativo, "avvertenze": list(t.avvertenze)})

    # de minimis: massimale + plafond residuo DETERMINISTICI. Gli aiuti pregressi arrivano come
    # testo libero (`agevolazioni_gia_fruite`): ne estraiamo gli importi e li passiamo al tool come
    # aiuti strutturati (data odierna → dentro la finestra mobile 3 anni, ipotesi prudente che
    # minimizza il residuo). Il residuo sovrascrive il campo LLM (che altrimenti resta a 0).
    usato_dm, n_dm = _de_minimis_usato(form)
    settore_dm = _settore_deminimis(form)
    if usato_dm > 0:
        aiuti = [AiutoDeMinimis(importo_eur=usato_dm, data_concessione=date.today(),
                                descrizione="aiuti pregressi (aggregato dal form)")]
        dm = de_minimis_plafond(DeMinimisPlafondInput(settore=settore_dm, aiuti_ricevuti=aiuti))
        dm_nota = (f"plafond residuo {dm.plafond_residuo_eur:.0f}€ = massimale {dm.massimale_eur:.0f}€ − "
                   f"pregressi {usato_dm:.0f}€ (finestra mobile 3 anni; ipotesi prudente: pregressi "
                   f"tutti entro finestra. Verificare date esatte e impresa unica su visura RNA).")
    else:
        dm = de_minimis_plafond(DeMinimisPlafondInput(settore=settore_dm))
        dm_nota = ("nessun aiuto de minimis pregresso rilevato nel form → plafond residuo = massimale "
                   "(verificare saldo effettivo su visura RNA).")
    residuo_dm = round(dm.plafond_residuo_eur, 2)
    provenance.append({"strumento": "de_minimis", "fonte": "k2a_agevolazioni",
                       "massimale_eur": dm.massimale_eur, "usato_eur": usato_dm,
                       "residuo_eur": residuo_dm, "riferimento": dm.riferimento_normativo,
                       "nota": dm_nota})

    benefits = [d["beneficio_lordo_eur"] for d in dettaglio
                if isinstance(d.get("beneficio_lordo_eur"), (int, float))]
    if benefits:
        base = round(max(benefits), 2)
        massimo = round(sum(benefits), 2)
        ottimistico = round((base + massimo) / 2, 2)
        note = (f"Scenari: base = miglior singolo strumento (nessun cumulo); massimo = somma "
                f"(CUMULABILITÀ DA VERIFICARE — Sabatini e Transizione 5.0 sullo stesso bene non "
                f"sempre cumulabili). De minimis massimale {dm.massimale_eur:.0f}€, "
                f"residuo {residuo_dm:.0f}€ (usato {usato_dm:.0f}€).")
    else:
        base = ottimistico = massimo = 0.0
        note = (f"Nessun investimento pianificato con importo nel form → benefici non stimabili. "
                f"De minimis massimale {dm.massimale_eur:.0f}€, residuo {residuo_dm:.0f}€.")

    return {
        "benefici": {
            "scenario_base_eur": base, "scenario_ottimistico_eur": ottimistico,
            "scenario_massimo_eur": massimo, "dettaglio_per_strumento": dettaglio,
        },
        "de_minimis": {"massimale_eur": dm.massimale_eur, "usato_eur": usato_dm,
                       "residuo_eur": residuo_dm, "n_aiuti_rilevati": n_dm},
        "note": note, "provenance": provenance,
    }


def apply_agevolazioni(deliverable: dict, form: dict) -> tuple[dict, Optional[dict]]:
    """Sovrascrive `benefici_stimati` + `profilo_aziendale.de_minimis_residuo_eur` del deliverable
    coi numeri deterministici dei tool. Ritorna (deliverable, meta{note,provenance}) o
    (deliverable, None) se il package non è disponibile."""
    if not isinstance(deliverable, dict):
        return deliverable, None
    c = compute_benefici(form)
    if not c:
        return deliverable, None
    out = dict(deliverable)
    ben = dict(c["benefici"])
    # Se NESSUNO strumento è calcolabile (nessun investimento per tipologia nel form) NON
    # mostrare '0.0' negli scenari — su un report pagato "Scenario massimo: 0,00€" legge come
    # "non hai diritto a niente", falso: manca solo l'input. Sostituiamo con uno stato onesto
    # (niente scenari fittizi) + nota che dice COME ottenere il calcolo. Vedi il pattern
    # FinanceBoost PARTIAL: niente numeri fuorvianti su dati mancanti.
    if not ben.get("dettaglio_per_strumento"):
        ben = {
            "dettaglio_per_strumento": [],
            "nota": ("Benefici non stimabili: nel form non risultano investimenti pianificati per "
                     "tipologia. Indica gli importi per tipo (macchinari, software, ricerca e "
                     "sviluppo, efficienza energetica) e il calcolo dei contributi — Nuova Sabatini, "
                     "Transizione 5.0, credito R&S — parte in automatico. "
                     f"Plafond de minimis residuo: {c['de_minimis']['residuo_eur']:.0f}€."),
        }
    out["benefici_stimati"] = ben
    # Plafond residuo de minimis: numero deterministico → sovrascrive il valore LLM (spesso 0).
    dm = c.get("de_minimis")
    if dm and isinstance(out.get("profilo_aziendale"), dict):
        prof = dict(out["profilo_aziendale"])
        prof["de_minimis_residuo_eur"] = dm["residuo_eur"]
        out["profilo_aziendale"] = prof
    return out, {"note": c["note"], "provenance": c["provenance"]}
