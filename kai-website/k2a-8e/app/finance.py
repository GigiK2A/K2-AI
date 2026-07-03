"""Riclassificatore di bilancio DETERMINISTICO (Python puro, no LLM, no assunzioni).

Perché esiste (giu 2026): FinanceBoost dava numeri sbagliati perché un LLM provava a
DEDURRE le quantità derivate (patrimonio netto, EBITDA, debiti finanziari) da un OCR e le
sbagliava → calc.py calcolava indici fedeli su input spazzatura (D/E 6,39 su un'azienda
con cassa netta). Qui l'LLM fa solo ciò in cui è affidabile — TRASCRIVERE le voci del
bilancio (descrizione + importo + sezione) — e la riclassificazione + TUTTA l'aritmetica
le fa questo modulo. I numeri vengono SOLO da qui. Dato mancante → None + warning, mai
inventato.

Input: lista di voci ``{sezione, descrizione, importo}`` con sezione ∈
{attivo, passivo, costi, ricavi, risultato}. Gestisce il formato "4 sezioni"
(immobilizzazioni LORDE sull'attivo + fondi ammortamento nel passivo, come il bilancio
contabile italiano) e il formato CEE (immobilizzazioni nette, niente fondi nel passivo).

Output: {sp, ce, indici, quadratura, classificazione, warnings}. La quadratura
(Totale Attivo lordo == Totale Passivo + Utile) è il gate d'integrità: se non torna,
l'estrazione è incompleta/sbagliata → si SEGNALA, non si consegna come se fosse giusto.
"""
from __future__ import annotations

import json
import re
from typing import Any, Optional

# ───────────────────────── helper numerici ─────────────────────────

def _num(v: Any) -> Optional[float]:
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        s = v.strip().replace("€", "").replace("EUR", "").strip()
        if not s:
            return None
        neg = s.startswith("(") and s.endswith(")")  # contabile: (1.234) = negativo
        s = s.strip("()").strip()
        # formato IT "1.234,56" → 1234.56; decimale-punto ("6.04") non si rompe
        if "," in s:
            s = s.replace(".", "").replace(",", ".")
        try:
            x = float(s)
            return -x if neg else x
        except ValueError:
            return None
    return None


def _m(x: Optional[float]) -> Optional[float]:
    return round(x, 2) if x is not None else None


def _p(x: Optional[float]) -> Optional[float]:
    """rapporto → percentuale a 1 decimale."""
    return round(x * 100, 1) if x is not None else None


def _r(x: Optional[float]) -> Optional[float]:
    return round(x, 2) if x is not None else None


def _div(a: Optional[float], b: Optional[float]) -> Optional[float]:
    if a is None or b is None or b == 0:
        return None
    return a / b


def _has(*words: str):
    return words


# ───────────────────────── classificazione ─────────────────────────
# Per-sezione: le stesse parole (erario, banche, fornitori) cambiano significato tra
# attivo e passivo → la sezione disambigua. L'ordine è una cascata: la prima regola che
# matcha vince, dalle più specifiche alle più generiche.

def _classify_attivo(d: str) -> str:
    if "ratei" in d or "risconti" in d:
        return "ratei_attivi"
    # NB: "posta" come parola, non substring di "imposta"/"d'imposta" (che è un credito).
    if ("banc" in d or "cassa" in d or "denaro" in d or "postal" in d
            or " posta" in d or d.startswith("posta")):
        return "liquidita"
    if "client" in d and "fornit" not in d:
        return "crediti_clienti"
    # Rimanenze/magazzino: attivo corrente MA da tenere SEPARATO — il quick ratio (acid test)
    # le esclude per definizione. Prima cadevano in 'altri_crediti' (contate nel corrente ma
    # mai sottratte dal quick ratio, che restava = current ratio; e semanticamente un credito).
    # NB: match a SUBSTRING (come tutto il classificatore) → niente 'merci' ('com-merci-ali'
    # è un'ATTREZZATURA, non magazzino) né 'scorte' isolato ambiguo: solo termini inequivoci.
    if any(w in d for w in ("rimanenz", "magazzino", "materie prime", "materia prima",
                            "semilavorat", "prodotti finit", "prodotti in corso", "giacenz",
                            "scorte di magazzino", "merci in magazzino", "merce in magazzino")):
        return "rimanenze"
    if any(w in d for w in ("impiant", "macchinar", "attrezzatur", "immobilizz",
                            "immater", "software", "mobili", "macchine", "telefonia",
                            "automezz", "autovettur", "fabbricat", "terren",
                            "avviament", "brevett", "licenz", "ampliament", "hardware")):
        return "immobilizzazioni_lorde"
    if any(w in d for w in ("credit", "erario", "iva", "imposta", "ritenut",
                            "deposit", "cauzional", "fornit", "anticip", "tribut")):
        return "altri_crediti"
    return "altri_crediti"  # default attivo: credito (e si annota nei warning)


def _classify_passivo(d: str) -> str:
    if "ammort" in d and ("fond" in d or "f.do" in d or "f/do" in d):
        return "fondi_ammortamento"
    # PN dato come AGGREGATO (una riga "patrimonio netto"/"mezzi propri", non scomposto in
    # capitale/riserve/utili). Senza questa regola cadeva su debiti_vari → il PN veniva
    # contato come DEBITO, l'SP non quadrava e gli indici (leva, bancabilità) uscivano falsi.
    if "patrimonio netto" in d or "patrimonio_netto" in d or "mezzi propri" in d \
            or "capitale netto" in d or d.strip() == "equity" or d.strip() == "pn":
        return "pn_aggregato"
    if "capital" in d:
        return "pn_capitale"
    if "riserv" in d:
        return "pn_riserve"
    if ("portati a nuovo" in d or "avanzo utili" in d or "utili a nuovo"
            in d or "perdite portate" in d or "risultati portati" in d):
        return "pn_utili_a_nuovo"
    if (("utile" in d or "perdit" in d) and ("esercizio" in d or "periodo" in d
                                             or "d'esercizio" in d)):
        return "pn_utile_esercizio"
    if "tfr" in d or "fine rapporto" in d or "trattamento fine" in d:
        return "tfr"
    # "debiti finanziari" / "posizione finanziaria" come AGGREGATO: prima cadeva su
    # debiti_vari (la regola cercava 'finanziament', non 'finanziari') → PFN e bancabilità
    # sottostimate. In sezione passivo "finanziar" = debito finanziario, non oneri (CE).
    if "debiti finanziari" in d or "debito finanziario" in d or "indebitamento finanziar" in d \
            or "posizione finanziaria" in d or "pfn" in d:
        return "debiti_finanziari_ml"
    if any(w in d for w in ("mutui", "mutuo", "finanziament", "prestit", "obbligazion")):
        return "debiti_finanziari_ml"
    if "leasing" in d:
        return "debiti_finanziari_ml"
    if "factoring" in d or "banc" in d or "scoperto" in d or "anticip" in d:
        return "debiti_finanziari_correnti"
    if "ratei" in d or "risconti" in d:
        return "ratei_passivi"
    if "previdenz" in d or "inps" in d or "inail" in d:
        return "debiti_previdenziali"
    if "personale" in d or "retribuz" in d or "dipendent" in d or "stipend" in d:
        return "debiti_personale"
    if "erario" in d or "iva" in d or "imposte" in d or "tribut" in d or \
            "ires" in d or "irap" in d or "sostituto" in d or "ritenut" in d:
        return "debiti_tributari"
    if "fornit" in d or "fatture" in d or "note credito da ricevere" in d or \
            "commercial" in d:
        return "debiti_commerciali"
    if "debiti vari" in d or "carte di credito" in d or "diversi v/terzi" in d or \
            "altri debiti" in d or "debiti diversi" in d:
        return "debiti_vari"
    return "debiti_vari"  # default passivo: debito operativo (annotato nei warning)


def _classify_ce(sezione: str, d: str) -> str:
    if sezione == "ricavi":
        if "finanziar" in d or "interessi attiv" in d:
            return "proventi_finanziari"
        return "ricavi_operativi"
    # sezione == costi
    if ("ammort" in d) or ("amm.ti" in d) or ("amm.to" in d) or ("amm." in d and "amministr" not in d):
        if "amministr" not in d:
            return "ammortamenti"
    if ("oneri finanziar" in d or "interessi passiv" in d or
            ("finanziar" in d and "oneri" in d) or "commissioni e spese su factoring" in d):
        return "oneri_finanziari"
    # Imposte sul reddito (add-back per EBIT/EBITDA): "imposte esercizio/reddito", IRES,
    # IRAP, o anche solo "imposte"/"imposte correnti" (aggregato di un riclassificato).
    # Escluse le imposte INDIRETTE e l'imposta di bollo (costo operativo, non add-back).
    if (("impost" in d and "indirett" not in d and "bollo" not in d and "registro" not in d)
            or "ires" in d or "irap" in d):
        return "imposte"
    return "altri_costi_operativi"


# ───────────────────────── motore ─────────────────────────

def reclassify_bilancio(voci: list[dict], anno: Optional[int] = None,
                        clienti_giorni: int = 365) -> dict:
    """Riclassifica le voci e calcola SP/CE riclassificati + indici, deterministicamente."""
    agg: dict[str, float] = {}
    classific: dict[str, list] = {}
    warnings: list[str] = []

    def add(cat: str, voce: dict, importo: float):
        agg[cat] = agg.get(cat, 0.0) + importo
        classific.setdefault(cat, []).append(
            {"descrizione": voce.get("descrizione", ""), "importo": importo})

    has_utile_in_sp = False
    utile_esplicito: Optional[float] = None

    for v in voci:
        if not isinstance(v, dict):
            continue
        importo = _num(v.get("importo"))
        if importo is None:
            continue
        sez = str(v.get("sezione", "")).strip().lower()
        d = str(v.get("descrizione", "")).strip().lower()
        if sez == "attivo":
            add(_classify_attivo(d), v, importo)
        elif sez == "passivo":
            cat = _classify_passivo(d)
            # pn_utile_esercizio e pn_aggregato includono già l'utile del periodo → non
            # ri-sommarlo dalla sezione 'risultato' (evita doppio conteggio del PN).
            if cat in ("pn_utile_esercizio", "pn_aggregato"):
                has_utile_in_sp = True
            add(cat, v, importo)
        elif sez == "ricavi":
            add(_classify_ce(sez, d), v, importo)
        elif sez == "costi":
            add(_classify_ce(sez, d), v, importo)
        elif sez in ("risultato", "utile", "perdita"):
            utile_esplicito = -abs(importo) if "perdit" in d else importo
        else:
            warnings.append(f"voce con sezione sconosciuta ignorata: «{v.get('descrizione','')}» ({sez})")

    def g(cat: str) -> float:
        return round(agg.get(cat, 0.0), 2)

    # ── CONTO ECONOMICO ─────────────────────────────────────────────
    ricavi = g("ricavi_operativi")
    proventi_fin = g("proventi_finanziari")
    ammortamenti = g("ammortamenti")
    oneri_fin = g("oneri_finanziari")
    imposte = g("imposte")
    costi_tot = sum(round(agg.get(c, 0.0), 2) for c in
                    ("altri_costi_operativi", "ammortamenti", "oneri_finanziari", "imposte"))
    ricavi_tot = ricavi + proventi_fin

    has_ce = bool(ricavi or costi_tot)
    if utile_esplicito is not None:
        utile_netto = round(utile_esplicito, 2)
    elif has_ce and agg.get("altri_costi_operativi") is not None:
        utile_netto = round(ricavi_tot - costi_tot, 2)
        warnings.append("utile netto DERIVATO da ricavi-costi (verifica: voci di costo "
                        "potrebbero essere incomplete)")
    else:
        utile_netto = None

    # EBIT bottom-up: utile + imposte + oneri fin - proventi fin (indipendente dalla
    # completezza delle altre voci di costo). EBITDA = EBIT + ammortamenti.
    if utile_netto is not None:
        ebit = round(utile_netto + imposte + oneri_fin - proventi_fin, 2)
        ebitda = round(ebit + ammortamenti, 2)
    else:
        ebit = ebitda = None

    ce = {
        "ricavi": _m(ricavi) if has_ce else None,
        "proventi_finanziari": _m(proventi_fin),
        "ammortamenti": _m(ammortamenti),
        "oneri_finanziari": _m(oneri_fin),
        "imposte": _m(imposte),
        "utile_netto": utile_netto,
        "ebit": ebit,
        "ebitda": ebitda,
    }

    # ── STATO PATRIMONIALE ──────────────────────────────────────────
    immob_lorde = g("immobilizzazioni_lorde")
    fondi_amm = g("fondi_ammortamento")
    immob_nette = round(immob_lorde - fondi_amm, 2)
    liquidita = g("liquidita")
    crediti_clienti = g("crediti_clienti")
    altri_crediti = g("altri_crediti")
    rimanenze = g("rimanenze")
    ratei_attivi = g("ratei_attivi")
    attivo_corrente = round(liquidita + crediti_clienti + altri_crediti + rimanenze + ratei_attivi, 2)
    totale_attivo = round(immob_nette + attivo_corrente, 2)

    df_correnti = g("debiti_finanziari_correnti")
    df_ml = g("debiti_finanziari_ml")
    debiti_finanziari = round(df_correnti + df_ml, 2)
    tfr = g("tfr")
    debiti_commerciali = g("debiti_commerciali")
    debiti_tributari = g("debiti_tributari")
    debiti_previdenziali = g("debiti_previdenziali")
    debiti_personale = g("debiti_personale")
    debiti_vari = g("debiti_vari")
    ratei_passivi = g("ratei_passivi")
    passivo_corrente = round(df_correnti + debiti_commerciali + debiti_tributari +
                             debiti_previdenziali + debiti_personale + debiti_vari +
                             ratei_passivi, 2)
    debiti_terzi = round(passivo_corrente + df_ml + tfr, 2)

    # patrimonio netto: capitale + riserve + utili a nuovo (+ utile d'esercizio).
    # 4 sezioni → l'utile è una riga a sé (sezione 'risultato'); CEE → può già stare
    # dentro il PN sul passivo (pn_utile_esercizio): in tal caso NON ri-sommarlo.
    pn_da_sp = round(g("pn_capitale") + g("pn_riserve") + g("pn_utili_a_nuovo")
                     + g("pn_utile_esercizio") + g("pn_aggregato"), 2)
    pn_components = any(agg.get(c) for c in
                       ("pn_capitale", "pn_riserve", "pn_utili_a_nuovo", "pn_utile_esercizio",
                        "pn_aggregato"))
    if not pn_components and utile_netto is None:
        patrimonio_netto = None
    else:
        add_utile = utile_netto if (utile_netto is not None and not has_utile_in_sp) else 0.0
        patrimonio_netto = round(pn_da_sp + add_utile, 2)

    sp = {
        "immobilizzazioni_lorde": _m(immob_lorde),
        "fondi_ammortamento": _m(fondi_amm),
        "immobilizzazioni_nette": _m(immob_nette),
        "liquidita": _m(liquidita),
        "crediti_clienti": _m(crediti_clienti),
        "altri_crediti": _m(altri_crediti),
        "rimanenze": _m(rimanenze),
        "attivo_corrente": _m(attivo_corrente),
        "totale_attivo": _m(totale_attivo),
        "patrimonio_netto": patrimonio_netto,
        "debiti_finanziari": _m(debiti_finanziari),
        "debiti_finanziari_correnti": _m(df_correnti),
        "debiti_finanziari_ml": _m(df_ml),
        "tfr": _m(tfr),
        "passivo_corrente": _m(passivo_corrente),
        "debiti_terzi": _m(debiti_terzi),
        # componenti del PN esposte solo se una voce le ha alimentate (per il
        # cross-check della riconciliazione quality: somma componenti vs identità).
        "capitale_sociale": _m(g("pn_capitale")) if "pn_capitale" in agg else None,
        "riserve": _m(g("pn_riserve")) if "pn_riserve" in agg else None,
        "utili_portati_nuovo": _m(g("pn_utili_a_nuovo")) if "pn_utili_a_nuovo" in agg else None,
    }

    # ── QUADRATURA (gate d'integrità) ───────────────────────────────
    attivo_lordo = round(immob_lorde + attivo_corrente, 2)
    passivo_lordo = round(fondi_amm + debiti_terzi + (patrimonio_netto or 0.0), 2)
    delta = round(attivo_lordo - passivo_lordo, 2)
    tol = max(1.0, attivo_lordo * 0.005)  # 0,5% o 1€
    quad_ok = bool(attivo_lordo > 0 and patrimonio_netto is not None and abs(delta) <= tol)
    if not quad_ok and attivo_lordo > 0:
        warnings.append(f"QUADRATURA NON RISPETTATA: attivo {attivo_lordo} ≠ "
                        f"passivo+PN {passivo_lordo} (delta {delta}) — estrazione da verificare")
    quadratura = {"attivo_lordo": attivo_lordo, "passivo_lordo": passivo_lordo,
                  "delta": delta, "ok": quad_ok}

    # ── INDICI ──────────────────────────────────────────────────────
    pn = patrimonio_netto
    indici = {
        "de": _r(_div(debiti_finanziari, pn)),
        "de_totale": _r(_div(debiti_terzi, pn)),
        "roe": _p(_div(utile_netto, pn)),
        "ros": _p(_div(ebit, ricavi)) if ricavi else None,
        "roi": _p(_div(ebit, totale_attivo)) if totale_attivo else None,
        "ebitda_margin": _p(_div(ebitda, ricavi)) if ricavi else None,
        "current_ratio": _r(_div(attivo_corrente, passivo_corrente)),
        # acid test: attivo corrente MENO le rimanenze (ora classificate separatamente).
        "quick_ratio": _r(_div(round(attivo_corrente - rimanenze, 2), passivo_corrente)),
        "ccn": _m(round(attivo_corrente - passivo_corrente, 2)) if passivo_corrente else None,
        "pfn": _m(round(debiti_finanziari - liquidita, 2)),
        "interest_coverage": _r(_div(ebit, oneri_fin)) if oneri_fin else None,
        "autonomia_finanziaria": _p(_div(pn, totale_attivo)) if totale_attivo else None,
        "dso": round(_div(crediti_clienti, ricavi) * clienti_giorni, 1)
               if (ricavi and crediti_clienti) else None,
    }

    return {"anno": anno, "sp": sp, "ce": ce, "indici": indici,
            "quadratura": quadratura, "classificazione": classific, "warnings": warnings}


# ───────────────────────── bridge verso calc.py ─────────────────────────
# I form.json dei boost finanziari hanno campi-aggregato (patrimonio_netto, ebitda…)
# che l'LLM riempiva male. Se l'estrazione fornisce invece le VOCI grezze, qui le
# riclassifichiamo e SOVRASCRIVIAMO gli aggregati con i valori deterministici.

def to_bilancio_fields(reclass: dict) -> dict:
    """reclass → nomi-campo attesi da calc._compute_bilancio (solo valori non None)."""
    sp, ce = reclass.get("sp", {}), reclass.get("ce", {})
    fields = {
        "ricavi": ce.get("ricavi"),
        "ebitda": ce.get("ebitda"),
        "reddito_operativo": ce.get("ebit"),
        "utile_netto": ce.get("utile_netto"),
        "totale_attivo": sp.get("totale_attivo"),
        "attivo_corrente": sp.get("attivo_corrente"),
        "passivo_corrente": sp.get("passivo_corrente"),
        "patrimonio_netto": sp.get("patrimonio_netto"),
        "debiti_finanziari": sp.get("debiti_finanziari"),
    }
    return {k: v for k, v in fields.items() if v is not None}


def enrich_bilancio(b: dict) -> dict:
    """Se il bilancio porta le VOCI grezze, deriva gli aggregati deterministicamente e li
    SOVRASCRIVE (le voci battono gli aggregati LLM, anche sbagliati). Senza voci → invariato."""
    if not isinstance(b, dict):
        return b
    voci = b.get("voci")
    if not isinstance(voci, list) or not voci:
        return b
    reclass = reclassify_bilancio(voci, b.get("anno"))
    return {**b, **to_bilancio_fields(reclass), "_reclass": reclass}


# ───────────────────────── indici per il report (computati) ─────────────────────────
# Tabella indici DETERMINISTICA col semaforo: è ciò che popola l'output del report,
# NON la genera l'LLM. Soglie/benchmark di riferimento PMI italiane (orientative).

def _sem_high(v, good, warn):  # più alto è meglio
    if v is None:
        return "giallo"
    return "verde" if v >= good else ("giallo" if v >= warn else "rosso")


def _sem_low(v, good, warn):   # più basso è meglio
    if v is None:
        return "giallo"
    return "verde" if v <= good else ("giallo" if v <= warn else "rosso")


def build_indici(reclass: dict) -> list[dict]:
    """[{nome, valore, benchmark, semaforo, trend}] deterministico, conforme a
    output-schema FinanceBoost (valore numerico, MAI la stringa 'non disponibile')."""
    idx = (reclass or {}).get("indici", {}) or {}
    ce = (reclass or {}).get("ce", {}) or {}
    out: list[dict] = []

    def push(nome, valore, benchmark, semaforo):
        if valore is None:
            return
        out.append({"nome": nome, "valore": valore, "benchmark": benchmark, "semaforo": semaforo})

    push("D/E finanziario", idx.get("de"), 1.0, _sem_low(idx.get("de"), 1.0, 2.0))
    push("D/E totale", idx.get("de_totale"), 2.0, _sem_low(idx.get("de_totale"), 1.5, 3.0))
    push("EBITDA margin (%)", idx.get("ebitda_margin"), 10.0, _sem_high(idx.get("ebitda_margin"), 12.0, 6.0))
    push("ROE (%)", idx.get("roe"), 10.0, _sem_high(idx.get("roe"), 10.0, 3.0))
    push("ROS (%)", idx.get("ros"), 8.0, _sem_high(idx.get("ros"), 8.0, 3.0))
    push("ROI (%)", idx.get("roi"), 7.0, _sem_high(idx.get("roi"), 7.0, 2.0))
    push("Current ratio", idx.get("current_ratio"), 1.5, _sem_high(idx.get("current_ratio"), 1.5, 1.0))
    push("Interest coverage (x)", idx.get("interest_coverage"), 4.0, _sem_high(idx.get("interest_coverage"), 4.0, 2.0))
    push("Autonomia finanziaria (%)", idx.get("autonomia_finanziaria"), 33.0,
         _sem_high(idx.get("autonomia_finanziaria"), 33.0, 20.0))
    push("DSO clienti (gg)", idx.get("dso"), 60.0, _sem_low(idx.get("dso"), 60.0, 90.0))

    # PFN: < 0 = cassa netta (ottimo); altrimenti rapportata a EBITDA.
    pfn, ebitda = idx.get("pfn"), ce.get("ebitda")
    if pfn is not None:
        if pfn <= 0:
            sem = "verde"
        elif ebitda and ebitda > 0:
            ratio = pfn / ebitda
            sem = "verde" if ratio <= 2 else ("giallo" if ratio <= 3 else "rosso")
        else:
            sem = "giallo"
        out.append({"nome": "PFN (€)", "valore": pfn, "benchmark": 0.0, "semaforo": sem})

    return out


# ─── Sezioni FinanceBoost data-payload 9-voci (riclassificazione/marginalità/valutazione) ───
# Popolano DETERMINISTICAMENTE le 3 sezioni aggiunte dal contratto data-payload (vendor-sync
# §A), così non le scrive l'LLM. Riclassificazione = i nostri SP/CE; valutazione = ROI/EVA da
# bilancio + WACC dal quant; marginalità = onesta (BEP/leva non derivabili dagli aggregati).
_TAX_PROXY = 0.279  # aliquota effettiva (country snapshot italy) per il NOPAT — proxy documentato


def build_riclassificazione(reclass: dict) -> dict:
    sp, ce = reclass.get("sp", {}), reclass.get("ce", {})
    anno = reclass.get("anno")
    anni = [anno] if anno is not None else []

    def _rows(spec):
        return [{"voce": n, "valori": [v]} for n, v in spec if v is not None]

    sp_rows = _rows([
        ("Immobilizzazioni nette", sp.get("immobilizzazioni_nette")),
        ("Liquidità", sp.get("liquidita")),
        ("Attivo corrente", sp.get("attivo_corrente")),
        ("Totale attivo (netto)", sp.get("totale_attivo")),
        ("Patrimonio netto", sp.get("patrimonio_netto")),
        ("Debiti finanziari", sp.get("debiti_finanziari")),
        ("Debiti v/terzi", sp.get("debiti_terzi")),
        ("Passivo corrente", sp.get("passivo_corrente")),
    ])
    ce_rows = _rows([
        ("Ricavi", ce.get("ricavi")),
        ("EBITDA", ce.get("ebitda")),
        ("EBIT", ce.get("ebit")),
        ("Utile netto", ce.get("utile_netto")),
    ])
    return {"anni": anni, "stato_patrimoniale": sp_rows, "conto_economico": ce_rows}


def build_marginalita(reclass: dict) -> dict:
    """BEP / leva operativa richiedono la divisione costi fissi/variabili (contabilità
    analitica), NON derivabile dagli aggregati di bilancio → onestamente null + flag."""
    return {
        "margine_contribuzione": None, "costi_fissi": None, "costi_variabili": None,
        "bep_valore": None, "bep_quantita": None, "leva_operativa": None, "margine_sicurezza": None,
        "stima_da_aggregati": True,
    }


def user_wacc_from_inputs(inputs: dict) -> Optional[float]:
    """WACC/tasso di sconto FORNITO dall'utente, estratto dal testo degli input (il form non ha
    un campo WACC dedicato → l'assunzione vive nel testo libero letto anche dall'LLM). Ha la
    precedenza sul CAPM del quant, così la sezione valutazione non contraddice la prosa (che usa
    l'assunzione dell'utente). Ritorna la percentuale (es. 9.5) o None. Bound 0<w≤40 per sanità."""
    if not isinstance(inputs, dict):
        return None
    blob = json.dumps(inputs, ensure_ascii=False).lower()
    for pat in (r"wacc[^0-9%]{0,15}(\d{1,2}(?:[.,]\d+)?)\s*%",
                r"tasso di sconto[^0-9%]{0,15}(\d{1,2}(?:[.,]\d+)?)\s*%",
                r"costo del capitale[^0-9%]{0,15}(\d{1,2}(?:[.,]\d+)?)\s*%"):
        m = re.search(pat, blob)
        if m:
            v = float(m.group(1).replace(",", "."))
            if 0 < v <= 40:
                return round(v, 2)
    return None


def build_valutazione(reclass: dict, wacc_pct: Optional[float]) -> dict:
    """ROI scomposto (Du Pont) ed EVA deterministici dal bilancio + WACC (utente o quant).
    EVA solo se il WACC è disponibile (mai inventato)."""
    ce, sp = reclass.get("ce", {}), reclass.get("sp", {})
    ebit, ricavi, ta = ce.get("ebit"), ce.get("ricavi"), sp.get("totale_attivo")
    margine_operativo = _p(_div(ebit, ricavi)) if (ebit is not None and ricavi) else None
    rotazione_ci = _r(_div(ricavi, ta)) if (ricavi is not None and ta) else None
    eva = None
    if wacc_pct is not None and ebit is not None and ta is not None:
        nopat = ebit * (1 - _TAX_PROXY)
        eva = round(nopat - ta * (wacc_pct / 100.0), 2)
    return {
        "wacc": round(wacc_pct, 2) if wacc_pct is not None else None,
        "eva": eva,
        "roi_scomposto": {"margine_operativo": margine_operativo, "rotazione_ci": rotazione_ci},
        "bsc": [],
    }


def apply_financeboost_sections(deliverable: dict, reclass: dict, wacc_pct: Optional[float] = None) -> dict:
    """Sovrascrive le 3 sezioni data-payload del deliverable FinanceBoost con i valori
    deterministici (riclassificazione/marginalità/valutazione). Le altre sezioni restano."""
    if not isinstance(deliverable, dict) or not reclass:
        return deliverable
    out = dict(deliverable)
    out["riclassificazione"] = build_riclassificazione(reclass)
    out["marginalita"] = build_marginalita(reclass)
    out["valutazione_performance"] = build_valutazione(reclass, wacc_pct)
    return out


def latest_reclass_from_inputs(inputs: dict) -> Optional[dict]:
    """Trova nel form il bilancio più recente CON voci grezze e lo riclassifica.
    None se non ci sono voci (→ la pipeline lascia il path standard)."""
    if not isinstance(inputs, dict):
        return None
    bilanci = inputs.get("bilanci")
    if not isinstance(bilanci, list):
        return None
    cand = [b for b in bilanci if isinstance(b, dict)
            and isinstance(b.get("voci"), list) and b["voci"]]
    if not cand:
        return None
    with_year = [b for b in cand if _num(b.get("anno")) is not None]
    b = max(with_year, key=lambda x: _num(x.get("anno"))) if with_year else cand[-1]
    return reclassify_bilancio(b["voci"], b.get("anno"))


def periodo_from_inputs(inputs: dict) -> Optional[str]:
    """`Esercizio <anno>` dall'anno del bilancio più recente presente nel form,
    ANCHE senza voci (report PARTIAL: solo aggregati). None se nessun anno.
    Serve a togliere il controllo del campo `meta.periodo` all'LLM quando la via
    deterministica completa (apply_to_financeboost) non gira — altrimenti sulla
    cover resta il placeholder ('FinanceBoost')."""
    if not isinstance(inputs, dict):
        return None
    bilanci = inputs.get("bilanci")
    if not isinstance(bilanci, list):
        return None
    anni = [int(_num(b.get("anno"))) for b in bilanci
            if isinstance(b, dict) and _num(b.get("anno")) is not None
            and 1990 <= _num(b.get("anno")) <= 2100]
    return f"Esercizio {max(anni)}" if anni else None


def neutralize_financeboost_partial(deliverable: dict, inputs: dict) -> tuple[dict, dict]:
    """Report PARTIAL (solo aggregati, NIENTE bilancio strutturato): le sezioni
    QUANTITATIVE del FinanceBoost non sono calcolabili e la via deterministica
    completa (apply_financeboost_sections/apply_to_financeboost) NON gira. Senza
    questa pulizia restano i placeholder dell'LLM — indici 'FinanceBoost: 1',
    riclassificazione 'Voce: FinanceBoost', EVA 1 — numeri INVENTATI in un report
    pagato. Le svuotiamo a shape schema-valida (il render salta le sezioni vuote) e
    fissiamo `meta.periodo` deterministico. Restano le sezioni QUALITATIVE
    (executive_summary, piano_azione, limitazioni), oneste su dati parziali.
    Ritorna (deliverable_pulito, meta_filiera)."""
    if not isinstance(deliverable, dict):
        return deliverable, {}
    out = dict(deliverable)
    meta_f: dict = {}
    # sezioni che richiedono un bilancio riclassificato → non producibili qui
    if isinstance(out.get("indici"), list):
        out["indici"] = []
        meta_f["indici_non_calcolabili"] = "bilancio non strutturato"
    if isinstance(out.get("scenari"), list):
        # proiezioni ricavi/EBITDA/cash-flow: proiettare cifre esatte su dati parziali
        # = fabbricare. Meglio vuoto + nota nelle limitazioni.
        out["scenari"] = []
        meta_f["scenari_non_derivabili"] = "bilancio non strutturato"
    if isinstance(out.get("riclassificazione"), dict):
        # required subfields → shape valida ma vuota (il render la salta se all-empty)
        out["riclassificazione"] = {"anni": [], "stato_patrimoniale": [], "conto_economico": []}
    if isinstance(out.get("marginalita"), dict):
        out["marginalita"] = {}
    if isinstance(out.get("valutazione_performance"), dict):
        out["valutazione_performance"] = {}
    # periodo/cover: deterministico, mai 'FinanceBoost'
    periodo = periodo_from_inputs(inputs)
    meta = dict(out.get("meta") or {})
    meta["periodo"] = periodo or "Periodo non determinato (dati parziali)"
    if periodo:
        meta["data"] = periodo
    out["meta"] = meta
    return out, meta_f


def apply_to_financeboost(deliverable: dict, reclass: dict, inputs: dict) -> dict:
    """Sovrascrive nel deliverable FinanceBoost ciò che DEVE essere deterministico:
    la tabella `indici` (computata, non scritta dall'LLM), `meta.azienda`/`meta.data`,
    e annota in `limitazioni` se la quadratura non torna. Il resto (prosa, piano azione)
    resta dell'LLM."""
    if not isinstance(deliverable, dict) or not reclass:
        return deliverable
    out = dict(deliverable)
    indici = build_indici(reclass)
    if indici:
        out["indici"] = indici
    meta = dict(out.get("meta") or {})
    azienda = inputs.get("ragione_sociale") or inputs.get("azienda")
    if azienda:
        meta["azienda"] = azienda
    anno = reclass.get("anno")
    if anno:
        meta["data"] = f"Esercizio {anno}"
        meta["periodo"] = f"Esercizio {anno}"
    meta.setdefault("servizio", "FinanceBoost")
    meta.setdefault("versione", "1.0.0")
    out["meta"] = meta
    quad = reclass.get("quadratura") or {}
    if quad.get("ok") is False:
        nota = (f"Attenzione: la quadratura del bilancio non torna "
                f"(delta {quad.get('delta')}€): dati estratti da verificare.")
        # La nota si aggancia alle limitazioni ESISTENTI, ma se l'LLM ci ha messo un
        # placeholder (es. 'FinanceBoost' su dati poveri) lo strippiamo prima: niente
        # 'FinanceBoost Attenzione: …' in un report pagato. Regex ancorata all'inizio.
        _lim = re.sub(r"^\s*[A-Z][A-Za-z]{2,}Boost\b[\s:.-]*", "", str(out.get("limitazioni") or "")).strip()
        out["limitazioni"] = (_lim + " " + nota).strip() if _lim else nota
    return out


def control_table(reclass: dict) -> dict:
    """Tabella di controllo per il GATE di conferma (mostrata all'utente prima di
    generare il report). Numeri deterministici + warning + esito quadratura."""
    sp, ce = reclass.get("sp", {}), reclass.get("ce", {})
    return {
        "anno": reclass.get("anno"),
        "stato_patrimoniale": {
            "Patrimonio netto": sp.get("patrimonio_netto"),
            "Debiti finanziari": sp.get("debiti_finanziari"),
            "Debiti v/terzi (totali)": sp.get("debiti_terzi"),
            "Liquidità": sp.get("liquidita"),
            "Attivo corrente": sp.get("attivo_corrente"),
            "Passivo corrente": sp.get("passivo_corrente"),
            "Totale attivo (netto)": sp.get("totale_attivo"),
        },
        "conto_economico": {
            "Ricavi": ce.get("ricavi"),
            "EBITDA": ce.get("ebitda"),
            "EBIT": ce.get("ebit"),
            "Utile netto": ce.get("utile_netto"),
        },
        "indici": build_indici(reclass),
        "quadratura": reclass.get("quadratura"),
        "warnings": reclass.get("warnings", []),
    }
