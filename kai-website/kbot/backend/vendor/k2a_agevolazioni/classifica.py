"""Classificazione del prodotto erogato — singolo Check express vs Boost composito.

Risolve l'errore tipico dell'agente: vendere un deliverable multi-misura
(es. AdvisorBoost 1.999€) al prezzo di un singolo Check express (49 crediti).

Dato l'insieme dei tool/aree effettivamente usati, il tool determina IN MODO
DETERMINISTICO il prodotto corretto (id di catalogo) e ne allega il prezzo da
scheda_listino. Regola: ≥2 componenti della stessa famiglia → Boost (Servizio);
un solo componente isolato → Check express (Consumo).

v2 (MASTERPLAN-K2AI v2.1 §3.6) — leve di fidelizzazione:
  - L3: sconto Boost per abbonati (Pro -10%, Business -20%), moltiplicativo con
    eventuali promo, con floor di sicurezza al 40% (D-L3-A, D-L3-B).
  - L4: retainer suggerito post-Boost (solo retainer realmente presenti a
    catalogo; oggi solo Hospitality) (D-L4-A, D-L4-B).
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, Field

from .listino import scheda_listino, SchedaListinoInput

_CATALOGO = json.loads((Path(__file__).parent / "data" / "catalogo_documenti.json").read_text())
_TIPI = _CATALOGO["tipi"]
# composito_id -> set(componenti) dal catalogo (unica fonte di verità)
_COMPOSITI = {k: set(v.get("componenti", [])) for k, v in _TIPI.items() if v.get("livello") == "composito"}

# ===== Costanti L3 e L4 (MASTERPLAN v2.1 §3.6) =====
# Sconti per piano sul prezzo Boost
_SCONTO_PIANO: dict[str, float] = {
    "free": 0.0,
    "pro": 0.10,
    "business": 0.20,
}
# Floor di sicurezza sullo sconto totale aggregato (D-L3-B)
_SCONTO_MAX_AGGREGATO: float = 0.40
# Mapping Boost → Retainer (L4). Solo Hospitality oggi (D-L4-B).
# Estensione futura: D-007 MASTERPLAN (task #15 backlog).
_RETAINER_PER_BOOST: dict[str, str] = {
    "checkup_hospitality": "revenue_management_hospitality",
    # I seguenti retainer non esistono ancora nel catalogo (D-007 aperta):
    # "checkup_agevolazioni": "advisor_retainer",  # da creare task #15
    # "checkup_marketing": "strategy_retainer",    # da creare task #15
    # "checkup_finanziario": "advisor_retainer",   # da creare task #15
    # "checkup_seo": "content_factory",            # da creare task #15
}


class ClassificaProdottoInput(BaseModel):
    componenti: list[str] = Field(
        ..., min_length=1,
        description="Id dei tool/aree (singoli) effettivamente usati per il deliverable, "
                    "es. ['de_minimis','transizione_5_0','cumulabilita'] o ['hospitality_kpi'].")
    composito: bool | None = Field(
        default=None,
        description="Override esplicito: True forza il Boost composito, False forza il singolo. "
                    "Se assente, la classificazione è automatica (≥2 componenti → Boost).")
    piano: Literal["free", "pro", "business"] = Field(
        default="free",
        description="Piano abbonamento del cliente. Determina lo sconto applicabile sui Boost "
                    "(L3, MASTERPLAN §3.6). Default 'free' = nessuno sconto (backward compatible).")
    sconto_promo_eur_frazione: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="Eventuale sconto promozionale frazionario (0.0-1.0). Si combina moltiplicativo "
                    "con lo sconto piano. Floor aggregato 40% (D-L3-B). Oggi sempre 0.0.")


class RetainerSuggerito(BaseModel):
    id: str
    prodotto: str
    prezzo_mensile_eur: float
    note: str | None = None


class ClassificaProdottoOutput(BaseModel):
    # ===== Campi esistenti (semantica invariata) =====
    prodotto_consigliato: str
    livello: str            # singolo | composito (tassonomia commerciale del catalogo)
    strato: str             # consumo | servizio | retainer
    prezzo_listino_eur: float | None
    costo_crediti: int | None
    prezzo_per_piano: dict[str, float]   # dict con i 3 piani (free/pro/business) — forma naturale per la vetrina
    motivazione: str
    avvertenze: list[str]
    riferimento: str
    trace: dict
    # ===== Nuovi campi v2 (additivi) =====
    prezzo_per_piano_richiesto: float | None = None   # prezzo scontato per il `piano` passato in input
    livello_documentale: str | None = None   # D1-D5 dal catalogo (campo aggiunto in task #2)
    sconto_piano_perc: float = 0.0           # 0.0 / 0.10 / 0.20 in base al piano
    sconto_promo_perc: float = 0.0           # 0.0 oggi, gancio per future promo
    sconto_aggregato_perc: float = 0.0       # totale dopo combinazione + floor 40%
    retainer_suggerito: RetainerSuggerito | None = None
    retainer_disponibile: bool = False


def _applica_sconto_abbonati(
    prezzo_listino: float,
    piano: str,
    sconto_promo_frazione: float,
) -> tuple[float, float, float, float]:
    """Applica sconto piano e promo in modo MOLTIPLICATIVO (D-L3-A), troncando al
    floor di sicurezza _SCONTO_MAX_AGGREGATO (D-L3-B).

    Returns: (prezzo_finale, sconto_piano_perc, sconto_promo_perc, sconto_aggregato_perc)
    """
    sp = round(_SCONTO_PIANO.get(piano, 0.0), 4)
    sm = round(max(0.0, min(1.0, sconto_promo_frazione)), 4)
    aggregato = 1.0 - (1.0 - sp) * (1.0 - sm)
    # round a 4 decimali per evitare artefatti float (es. 0.09999999999999998)
    aggregato_finale = round(min(aggregato, _SCONTO_MAX_AGGREGATO), 4)
    prezzo_finale = round(prezzo_listino * (1.0 - aggregato_finale), 2)
    return prezzo_finale, sp, sm, aggregato_finale


def _suggerisci_retainer_post_boost(boost_id: str) -> RetainerSuggerito | None:
    """Restituisce il retainer naturale del Boost se esiste a catalogo (L4).
    None se il Boost non è mappato o il retainer non è presente (D-L4-B).
    """
    retainer_id = _RETAINER_PER_BOOST.get(boost_id)
    if retainer_id is None:
        return None
    retainer_data = _TIPI.get(retainer_id)
    if retainer_data is None:
        # Non inventare: D-007 e D-L4-B
        return None
    # Per revenue_management_hospitality il canone mensile è in prezzo_documento_eur
    # (catalogo: modello_prezzo="retainer", prezzo_documento_eur=399, success_fee_pct=15).
    note = retainer_data.get("_nota")
    fee = retainer_data.get("success_fee_pct")
    if fee and not note:
        note = f"Canone mensile + {fee:g}% success fee."
    return RetainerSuggerito(
        id=retainer_id,
        prodotto=retainer_data.get("prodotto_commerciale", retainer_id),
        prezzo_mensile_eur=float(retainer_data.get("prezzo_documento_eur", 0)),
        note=note,
    )


def classifica_prodotto(inp: ClassificaProdottoInput) -> ClassificaProdottoOutput:
    avvertenze: list[str] = []
    used = [c for c in inp.componenti]
    used_set = set(used)

    # componenti non riconosciuti a catalogo
    noti = {c for comps in _COMPOSITI.values() for c in comps}
    sconosciuti = [c for c in used if c not in _TIPI and c not in noti]
    if sconosciuti:
        avvertenze.append(f"Componenti non riconosciuti a catalogo: {sconosciuti} (ignorati).")

    # famiglia: composito con la maggiore sovrapposizione coi componenti usati
    # (LOGICA ESISTENTE — non modificata)
    best = None
    best_overlap: set = set()
    for cid, comps in _COMPOSITI.items():
        ov = comps & used_set
        if len(ov) > len(best_overlap):
            best, best_overlap = cid, ov

    n_overlap = len(best_overlap)
    # decisione singolo/composito (LOGICA ESISTENTE — non modificata)
    if inp.composito is not None:
        is_comp = inp.composito
    else:
        is_comp = n_overlap >= 2

    if best is None:
        single = used[0]
        prodotto = single if single in _TIPI else used[0]
        motivazione = "Nessuna famiglia di Boost corrispondente: trattato come singolo."
        avvertenze.append("Impossibile mappare i componenti a un Boost: verificare gli id.")
    elif is_comp:
        prodotto = best
        motivazione = (f"{n_overlap} componenti della famiglia '{best}' usati "
                       f"({sorted(best_overlap)}): è un Boost composito (strato Servizio), "
                       f"NON un singolo Check express.")
        if inp.composito is True and n_overlap < 2:
            avvertenze.append("Composito forzato con <2 componenti: verificare la coerenza.")
    else:
        prodotto = (sorted(best_overlap)[0] if best_overlap else used[0])
        motivazione = (f"Un solo componente isolato ('{prodotto}'): è un Check express "
                       f"(strato Consumo). Per un advisory multi-area userebbe '{best}'.")

    sl = scheda_listino(SchedaListinoInput(prodotto=prodotto))
    avvertenze.extend(sl.avvertenze)

    # ===== v2: livello documentale (task #2) =====
    livello_documentale = _TIPI.get(prodotto, {}).get("livello_documentale")

    # ===== v2: L3 sconto abbonati (solo sui Boost, strato 'servizio') =====
    sconto_piano_perc = 0.0
    sconto_promo_perc = 0.0
    sconto_aggregato_perc = 0.0
    if sl.strato == "servizio" and sl.prezzo_listino_eur is not None:
        # dict con i 3 piani (forma naturale per la vetrina prezzi)
        prezzo_per_piano = {
            p: _applica_sconto_abbonati(sl.prezzo_listino_eur, p, inp.sconto_promo_eur_frazione)[0]
            for p in ("free", "pro", "business")
        }
        # prezzo per il piano richiesto in input (+ percentuali di sconto applicate)
        prezzo_per_piano_richiesto, sconto_piano_perc, sconto_promo_perc, sconto_aggregato_perc = \
            _applica_sconto_abbonati(sl.prezzo_listino_eur, inp.piano, inp.sconto_promo_eur_frazione)
    else:
        # Check express (consumo) / retainer / prodotto sconosciuto: nessuno sconto piano.
        # I 3 piani hanno lo stesso prezzo di listino (0.0 se prezzo None, es. prodotto sconosciuto).
        base = sl.prezzo_listino_eur if sl.prezzo_listino_eur is not None else 0.0
        prezzo_per_piano = {"free": base, "pro": base, "business": base}
        prezzo_per_piano_richiesto = sl.prezzo_listino_eur

    # ===== v2: L4 retainer suggerito (solo Boost composito mappato) =====
    retainer_suggerito = None
    if is_comp and sl.strato == "servizio":
        retainer_suggerito = _suggerisci_retainer_post_boost(prodotto)
    retainer_disponibile = retainer_suggerito is not None

    return ClassificaProdottoOutput(
        prodotto_consigliato=prodotto,
        livello=_TIPI.get(prodotto, {}).get("livello", ""),
        strato=sl.strato,
        prezzo_listino_eur=sl.prezzo_listino_eur,
        costo_crediti=sl.costo_crediti,
        prezzo_per_piano=prezzo_per_piano,
        prezzo_per_piano_richiesto=prezzo_per_piano_richiesto,
        motivazione=motivazione,
        avvertenze=avvertenze,
        riferimento="catalogo_documenti.json (componenti dei Boost) + scheda_listino",
        livello_documentale=livello_documentale,
        sconto_piano_perc=sconto_piano_perc,
        sconto_promo_perc=sconto_promo_perc,
        sconto_aggregato_perc=sconto_aggregato_perc,
        retainer_suggerito=retainer_suggerito,
        retainer_disponibile=retainer_disponibile,
        trace={"componenti_usati": used, "famiglia": best,
               "overlap": sorted(best_overlap), "is_composito": is_comp,
               "piano": inp.piano, "retainer_mappato": _RETAINER_PER_BOOST.get(prodotto),
               "floor_sconto_applicato": sconto_aggregato_perc >= _SCONTO_MAX_AGGREGATO},
    )
