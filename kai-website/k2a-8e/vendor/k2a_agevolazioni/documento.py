"""Documenti di consulenza K2-AI — registro di template per tipologia.

I documenti venduti sono di DIVERSA TIPOLOGIA e DIVERSO COSTO (cfr. k2-ai.it).
Il catalogo (catalogo_documenti.json) definisce, per ogni tipologia:
  - l'indice degli argomenti (fisso per quella tipologia);
  - il 'tier' (abbonamento/Pattern in cui è incluso);
  - il 'prezzo_documento_eur' (listino a documento, da validare).

Due livelli:
  - SINGOLO: un documento per ciascun tool (indice standard a 8 sezioni);
  - COMPOSITO: check-up che aggregano più tool (indice dedicato a 9 sezioni).

Regola di prodotto: ogni tool client-facing instrada il proprio output qui;
all'interno della stessa tipologia il documento ha SEMPRE lo stesso indice.
"""
from __future__ import annotations
import json
from datetime import date
from pathlib import Path
from typing import Any, Literal
from pydantic import BaseModel, Field

from .settori import settore_label

_CATALOGO = json.loads((Path(__file__).parent / "data" / "catalogo_documenti.json").read_text())
_INDICI = _CATALOGO["indici"]
_TIPI = _CATALOGO["tipi"]

# Indice standard dei documenti SINGOLI (unica fonte di verità, retrocompatibile)
INDICE_STANDARD: list[str] = list(_INDICI["singolo_standard"])
INDICE_CHECKUP: list[str] = list(_INDICI["checkup"])

_NON_APPLICABILE = "Non applicabile."
_AUTORE = "K2-AI — Studio di ingegneria e consulenza tecnica"

_KEYS_VALUTAZIONE = [
    "classe", "giudizio", "colore", "punteggio_0_100", "esito",
    "crisi_segnalata", "ammissibile", "cumulo_ammesso", "nuovo_aiuto_capiente",
    "nuovo_aiuto_msg", "indicatori_critici", "segnali_crisi_codice_14_2019",
    "supera_intensita_massima", "indici_superati_tutti", "quadratura_ok",
]
_KEYS_META = {"avvertenze", "raccomandazioni", "riferimento_normativo", "trace"}


class SezioneDoc(BaseModel):
    numero: int
    titolo: str
    contenuto: str


# ---------------------------------------------------------------- helpers ----

def _fmt(valore: Any) -> str:
    """Rende un contenuto (str / list / dict) in testo leggibile, deterministico."""
    if valore is None or valore == "" or valore == [] or valore == {}:
        return _NON_APPLICABILE
    if isinstance(valore, str):
        return valore
    if isinstance(valore, list):
        return "\n".join(f"- {x}" for x in valore)
    if isinstance(valore, dict):
        return "\n".join(f"- **{k}**: {v}" for k, v in valore.items())
    return str(valore)


# Resa narrativa dei risultati di un tool ------------------------------------
# Strutture verbose già rese altrove o troppo dettagliate per il corpo documento.
_SKIP_VERBOSE = {
    "kpi", "controlli", "indicatori", "metriche", "dettaglio_scaglioni",
    "piano_ammortamento", "aiuti_dentro_finestra", "aiuti_fuori_finestra",
    "prossima_liberazione", "indicatori_critici", "segnali_crisi_codice_14_2019",
    "incompatibilita_rilevate", "raccomandazioni", "avvertenze",
    "riferimento_normativo", "trace", "sezioni", "markdown", "indice", "bancabilita_input",
}


def _human(k: str) -> str:
    base = k.replace("_eur", "").replace("_pct", "").replace("_", " ").strip()
    return base[:1].upper() + base[1:] if base else k


def _fmt_scalar(k: str, v: Any) -> str:
    if isinstance(v, bool):
        return "sì" if v else "no"
    if isinstance(v, (int, float)):
        if k.endswith("_eur"):
            return "€ " + f"{v:,.0f}".replace(",", ".")
        if k.endswith("_pct"):
            return f"{v} %"
        return f"{v:g}"
    return str(v)


def _fmt_risultati(p: Any) -> str:
    """Rende l'output di un tool in forma leggibile: prima gli indicatori valutati
    (lista `kpi`), poi i dati principali con chiavi umanizzate e € / % formattati."""
    if not isinstance(p, dict):
        return _fmt(p)
    righe: list[str] = []
    kpi = p.get("kpi")
    if isinstance(kpi, list) and kpi:
        righe.append("**Indicatori valutati:**")
        for k in kpi:
            if isinstance(k, dict):
                righe.append(f"- {k.get('label', '')}: **{k.get('valore')}** → _{k.get('valutazione', '')}_")
    scal = [f"- {_human(k)}: {_fmt_scalar(k, v)}"
            for k, v in p.items()
            if k not in _SKIP_VERBOSE and not isinstance(v, (list, dict)) and v not in (None, "")]
    if scal:
        if righe:
            righe.append("")
        righe.append("**Dati principali:**")
        righe.extend(scal)
    return "\n".join(righe) if righe else _NON_APPLICABILE


def _tipo_meta(tipo_documento: str | None) -> dict:
    """Recupera label/tier/prezzo/indice dal catalogo per la tipologia richiesta."""
    if tipo_documento and tipo_documento in _TIPI:
        t = _TIPI[tipo_documento]
        return {
            "tipo_documento": tipo_documento,
            "label": t["label"],
            "livello": t["livello"],
            "tier": t.get("tier", ""),
            "ambito": t.get("ambito", "trasversale"),
            "settore_default": t.get("settore", ""),
            "strato": t.get("strato", ""),
            "prodotto_commerciale": t.get("prodotto_commerciale", ""),
            "modello_prezzo": t.get("modello_prezzo", ""),
            "prezzo_documento_eur": t.get("prezzo_documento_eur"),
            "indice": list(_INDICI[t["indice"]]),
            "da_validare": bool(t.get("_da_validare") or _CATALOGO.get("_da_validare")),
        }
    return {
        "tipo_documento": tipo_documento or "",
        "label": "", "livello": "singolo", "tier": "", "ambito": "trasversale",
        "settore_default": "",
        "strato": "", "prodotto_commerciale": "", "modello_prezzo": "",
        "prezzo_documento_eur": None, "indice": list(INDICE_STANDARD),
        "da_validare": False,
    }


_SUFFISSO_PREZZO = {"progetto": "/progetto", "retainer": "/mese", "credito": " (a consumo/crediti)"}


def _intestazione(titolo, tipo_servizio, committente, d, meta) -> list[str]:
    intest = [f"**Servizio:** {tipo_servizio}"]
    if committente:
        intest.append(f"**Committente:** {committente}")
    if meta.get("settore_label"):
        intest.append(f"**Settore:** {meta['settore_label']}")
    if meta.get("prodotto_commerciale"):
        intest.append(f"**Prodotto:** {meta['prodotto_commerciale']}")
    if meta.get("tier"):
        intest.append(f"**Incluso in:** {meta['tier']}")
    if meta.get("prezzo_documento_eur") is not None:
        unita = _SUFFISSO_PREZZO.get(meta.get("modello_prezzo", ""), "")
        nota = " — listino indicativo, da validare" if meta.get("da_validare") else ""
        intest.append(f"**Listino documento:** {meta['prezzo_documento_eur']:.0f}€{unita}{nota}")
    intest.append(f"**Data:** {d.isoformat()}")
    intest.append(f"**A cura di:** {_AUTORE}")
    return intest


def _render(titolo, tipo_servizio, committente, d, meta, indice, contenuti) -> tuple[list[SezioneDoc], str]:
    """Costruisce le sezioni + il markdown a partire da un indice e dai contenuti
    (lista parallela all'indice)."""
    sezioni = [
        SezioneDoc(numero=i + 1, titolo=t, contenuto=_fmt(contenuti[i]))
        for i, t in enumerate(indice)
    ]
    righe: list[str] = [f"# {titolo}", ""]
    righe.append("  \n".join(_intestazione(titolo, tipo_servizio, committente, d, meta)))
    righe.append("")
    righe.append("## Indice degli argomenti")
    righe.extend(f"- {t}" for t in indice)
    righe.append("")
    for s in sezioni:
        righe += [f"## {s.titolo}", "", s.contenuto, ""]
    return sezioni, "\n".join(righe).rstrip() + "\n"


# ---------------------------------------------------------------- output ----

class DocumentoConsulenzaOutput(BaseModel):
    titolo: str
    tipo_servizio: str
    tipo_documento: str
    livello: str
    ambito: str
    settore: str
    tier: str
    strato: str
    prodotto_commerciale: str
    modello_prezzo: str
    prezzo_documento_eur: float | None
    committente: str
    data: date
    autore: str
    indice: list[str]
    sezioni: list[SezioneDoc]
    markdown: str
    avvertenze: list[str]
    trace: dict


# ------------------------------------------------ 1) documento da sezioni ----

class DocumentoConsulenzaInput(BaseModel):
    titolo: str = Field(..., description="Titolo del documento.")
    tipo_servizio: str = Field(..., description="Etichetta del servizio.")
    tipo_documento: str | None = Field(
        None, description=f"Tipologia dal catalogo (per indice/tier/prezzo). "
                          f"Tipi: {list(_TIPI.keys())}. Se assente usa l'indice standard.")
    committente: str = Field("", description="Nome del committente/impresa.")
    settore: str = Field("", description="Settore PMI del committente (id da settori_pmi, es. 'ristorazione_food') per contestualizzare il documento.")
    data: date | None = Field(None, description="Data del documento (default: oggi).")
    premessa: str = Field("", description="Sez.1 — premessa e finalità.")
    dati_input: dict | str = Field("", description="Sez.2 — dati e parametri di input.")
    metodologia: str = Field("", description="Sez.3 — descrizione del metodo.")
    riferimenti_normativi: list[str] = Field(default_factory=list, description="Sez.3 — norme/fonti.")
    risultati: dict | str = Field("", description="Sez.4 — risultati e quantificazione.")
    valutazioni: dict | str = Field("", description="Sez.5 — indicatori, soglie, esiti.")
    avvertenze: list[str] = Field(default_factory=list, description="Sez.6 — avvertenze e limiti.")
    raccomandazioni: list[str] = Field(default_factory=list, description="Sez.7 — raccomandazioni.")
    conclusioni: str = Field("", description="Sez.8 — conclusioni e prossimi passi.")


def genera_documento_consulenza(inp: DocumentoConsulenzaInput) -> DocumentoConsulenzaOutput:
    d = inp.data or date.today()
    meta = _tipo_meta(inp.tipo_documento)
    meta["settore_label"] = settore_label(inp.settore or meta["settore_default"])
    # I documenti singoli usano l'indice standard a 8 sezioni
    indice = INDICE_STANDARD

    sez3_parts: list[str] = []
    if inp.metodologia:
        sez3_parts.append(inp.metodologia)
    if inp.riferimenti_normativi:
        sez3_parts.append("Riferimenti normativi:\n" + _fmt(inp.riferimenti_normativi))
    sez3 = "\n\n".join(sez3_parts) if sez3_parts else _NON_APPLICABILE

    contenuti = [
        inp.premessa, inp.dati_input, sez3, inp.risultati,
        inp.valutazioni, inp.avvertenze, inp.raccomandazioni, inp.conclusioni,
    ]
    sezioni, markdown = _render(inp.titolo, inp.tipo_servizio, inp.committente, d, meta, indice, contenuti)

    return DocumentoConsulenzaOutput(
        titolo=inp.titolo, tipo_servizio=inp.tipo_servizio,
        tipo_documento=meta["tipo_documento"], livello=meta["livello"],
        ambito=meta["ambito"], settore=meta["settore_label"],
        tier=meta["tier"], strato=meta["strato"],
        prodotto_commerciale=meta["prodotto_commerciale"], modello_prezzo=meta["modello_prezzo"],
        prezzo_documento_eur=meta["prezzo_documento_eur"],
        committente=inp.committente, data=d, autore=_AUTORE,
        indice=list(indice), sezioni=sezioni, markdown=markdown,
        avvertenze=inp.avvertenze,
        trace={"formato": "documento K2-AI — singolo, indice standard 8 sezioni",
               "tipo_documento": meta["tipo_documento"], "n_sezioni": len(sezioni)},
    )


# ------------------------------------ 2) documento da output di un tool ----

class DocumentoDaRisultatoInput(BaseModel):
    tipo_servizio: str = Field(..., description="Etichetta del servizio erogato.")
    titolo: str = Field(..., description="Titolo del documento.")
    payload: dict = Field(..., description="Output JSON di un qualunque tool del motore.")
    tipo_documento: str | None = Field(
        None, description=f"Tipologia dal catalogo per indice/tier/prezzo. Tipi: {list(_TIPI.keys())}.")
    committente: str = Field("", description="Nome del committente/impresa.")
    settore: str = Field("", description="Settore PMI del committente (id da settori_pmi).")
    dati_input: dict | str = Field("", description="Parametri di input da riportare in Sez.2.")
    premessa: str = Field("", description="Premessa custom; se vuota, generata dal tipo_servizio.")
    conclusioni: str = Field("", description="Conclusioni custom; se vuote, generate dagli esiti.")


def componi_documento_da_risultato(inp: DocumentoDaRisultatoInput) -> DocumentoConsulenzaOutput:
    """Mappa l'output di un qualunque tool nel documento SINGOLO standard."""
    p = inp.payload
    valutazioni = {k: p[k] for k in _KEYS_VALUTAZIONE if k in p}
    risultati = _fmt_risultati(p)  # resa narrativa (KPI + dati principali umanizzati)

    rif = p.get("riferimento_normativo", "")
    riferimenti = [rif] if rif else []
    trace = p.get("trace", {})
    metodo = trace.get("metodo") or trace.get("metodo_punteggio") or trace.get("logica") or ""

    premessa = inp.premessa or (
        f"Il presente documento riporta l'esito del servizio «{inp.tipo_servizio}» "
        f"erogato da {_AUTORE}, con metodologia deterministica e tracciabile."
    )
    conclusioni = inp.conclusioni
    if not conclusioni:
        pezzi = [str(p[k]) for k in ("classe", "giudizio", "esito", "nuovo_aiuto_msg") if k in p]
        conclusioni = " ".join(pezzi) if pezzi else "Esito riportato nelle sezioni precedenti."

    return genera_documento_consulenza(DocumentoConsulenzaInput(
        titolo=inp.titolo, tipo_servizio=inp.tipo_servizio, tipo_documento=inp.tipo_documento,
        committente=inp.committente, settore=inp.settore, dati_input=inp.dati_input, premessa=premessa,
        metodologia=metodo, riferimenti_normativi=riferimenti, risultati=risultati,
        valutazioni=valutazioni, avvertenze=p.get("avvertenze", []),
        raccomandazioni=p.get("raccomandazioni", []), conclusioni=conclusioni,
    ))


# ----------------------------------------- 3) documento COMPOSITO (check-up) ----

_KEYS_OPPORTUNITA = [
    "plafond_residuo_eur", "credito_imposta_eur", "contributo_totale_eur",
    "importo_residuo_finanziabile_eur",
]
_KEYS_CRITICITA = [
    "segnali_crisi_codice_14_2019", "indicatori_critici",
    "incompatibilita_rilevate", "supera_intensita_massima",
]


class BloccoCheckup(BaseModel):
    area: str = Field(..., description="Etichetta dell'area di analisi (es. 'Bancabilità', 'Plafond de minimis').")
    payload: dict = Field(..., description="Output JSON del tool relativo all'area.")


class CheckupInput(BaseModel):
    tipo_checkup: Literal[
        "checkup_agevolazioni", "checkup_finanziario", "checkup_seo", "checkup_marketing",
        "checkup_hospitality", "checkup_ristorazione", "checkup_retail", "checkup_ecommerce",
        "checkup_benessere",
    ] = Field(..., description="Tipologia di check-up composito (determina label/tier/prezzo).")
    titolo: str = Field(..., description="Titolo del documento.")
    blocchi: list[BloccoCheckup] = Field(..., min_length=1, description="Aree di analisi con i rispettivi output.")
    committente: str = Field("", description="Nome del committente/impresa.")
    settore: str = Field("", description="Settore PMI del committente (id da settori_pmi).")
    profilo_impresa: dict | str = Field("", description="Sez.2 — profilo e dati di input dell'impresa.")
    conclusioni: str = Field("", description="Sez.9 — conclusioni custom; se vuote, generate.")


def _giudizio_sintetico(p: dict) -> str:
    if "classe" in p:
        return f"classe {p['classe']} — {p.get('giudizio', '')}".strip(" —")
    if "esito" in p:
        return str(p["esito"])
    kpi = p.get("kpi")
    if isinstance(kpi, list) and kpi:
        attenzione = [k for k in kpi if isinstance(k, dict) and k.get("valutazione") in ("critico", "attenzione")]
        if attenzione:
            nomi = ", ".join(k.get("label", "") for k in attenzione[:2])
            return f"{len(attenzione)} indicatori da attenzionare ({nomi})"
        return "indicatori complessivamente positivi"
    if "nuovo_aiuto_msg" in p and p["nuovo_aiuto_msg"]:
        return str(p["nuovo_aiuto_msg"])
    for k in ("credito_imposta_eur", "contributo_totale_eur", "plafond_residuo_eur",
              "importo_residuo_finanziabile_eur"):
        if k in p and p[k] is not None:
            return f"{_human(k)}: {_fmt_scalar(k, p[k])}"
    if "cumulo_ammesso" in p:
        return "cumulo ammesso" if p["cumulo_ammesso"] else "cumulo NON ammesso"
    return "esito riportato in dettaglio"


def componi_checkup(inp: CheckupInput) -> DocumentoConsulenzaOutput:
    """Aggrega più output di tool in un documento COMPOSITO con indice check-up."""
    d = date.today()
    meta = _tipo_meta(inp.tipo_checkup)
    meta["settore_label"] = settore_label(inp.settore or meta["settore_default"])
    indice = INDICE_CHECKUP

    avvertenze_all: list[str] = []
    raccomandazioni_all: list[str] = []
    riferimenti_all: list[str] = []
    sintesi: list[str] = []
    esiti_per_area: list[str] = []
    quadro: list[str] = []
    opportunita: list[str] = []
    criticita: list[str] = []

    for b in inp.blocchi:
        p = b.payload
        sintesi.append(f"**{b.area}**: {_giudizio_sintetico(p)}")
        # Esiti dettagliati (resa narrativa: KPI + dati principali umanizzati)
        esiti_per_area.append(f"### {b.area}\n" + _fmt_risultati(p))
        # Quadro indicatori (chiavi di valutazione scalari, umanizzate, niente None)
        vlines = [f"- {_human(k)}: {_fmt_scalar(k, p[k])}"
                  for k in _KEYS_VALUTAZIONE
                  if k in p and p[k] not in (None, "") and not isinstance(p[k], (list, dict))]
        if vlines:
            quadro.append(f"### {b.area}\n" + "\n".join(vlines))
        # Opportunità / criticità
        for k in _KEYS_OPPORTUNITA:
            if k in p and p[k]:
                opportunita.append(f"{b.area} — {_human(k)}: {_fmt_scalar(k, p[k])}")
        for k in _KEYS_CRITICITA:
            if k in p and p[k]:
                v = p[k]
                txt = "; ".join(map(str, v)) if isinstance(v, list) else _fmt_scalar(k, v)
                criticita.append(f"{b.area} — {_human(k)}: {txt}")
        # Accumulo trasversale
        riferimenti_all.append(p.get("riferimento_normativo", ""))
        avvertenze_all += p.get("avvertenze", [])
        raccomandazioni_all += p.get("raccomandazioni", [])

    riferimenti_all = [r for r in dict.fromkeys(riferimenti_all) if r]
    metodologia = ("Analisi deterministica e tracciabile delle aree di check-up; "
                   "ciascun esito è calcolato dai motori K2-AI dedicati.\n\n"
                   "Riferimenti normativi:\n" + _fmt(riferimenti_all))

    opp_crit = []
    if opportunita:
        opp_crit.append("**Opportunità**\n" + _fmt(opportunita))
    if criticita:
        opp_crit.append("**Criticità**\n" + _fmt(criticita))

    conclusioni = inp.conclusioni or (
        "Sintesi degli esiti: " + " · ".join(s.replace("**", "") for s in sintesi) +
        ". Si rimanda alle sezioni per il dettaglio e alle avvertenze per i limiti."
    )

    contenuti = [
        _fmt(sintesi),                         # 1. Sintesi esecutiva
        inp.profilo_impresa,                   # 2. Profilo impresa
        metodologia,                           # 3. Metodologia e riferimenti
        "\n\n".join(esiti_per_area),           # 4. Esiti per area
        "\n\n".join(quadro) if quadro else "", # 5. Quadro indicatori
        "\n\n".join(opp_crit) if opp_crit else "",  # 6. Opportunità e criticità
        avvertenze_all,                        # 7. Avvertenze
        raccomandazioni_all,                   # 8. Piano d'azione e raccomandazioni
        conclusioni,                           # 9. Conclusioni
    ]
    tipo_servizio = meta["label"] or inp.tipo_checkup
    sezioni, markdown = _render(inp.titolo, tipo_servizio, inp.committente, d, meta, indice, contenuti)

    return DocumentoConsulenzaOutput(
        titolo=inp.titolo, tipo_servizio=tipo_servizio,
        tipo_documento=meta["tipo_documento"], livello=meta["livello"],
        ambito=meta["ambito"], settore=meta["settore_label"],
        tier=meta["tier"], strato=meta["strato"],
        prodotto_commerciale=meta["prodotto_commerciale"], modello_prezzo=meta["modello_prezzo"],
        prezzo_documento_eur=meta["prezzo_documento_eur"],
        committente=inp.committente, data=d, autore=_AUTORE,
        indice=list(indice), sezioni=sezioni, markdown=markdown,
        avvertenze=avvertenze_all,
        trace={"formato": "documento K2-AI — composito, indice check-up 9 sezioni",
               "tipo_documento": meta["tipo_documento"], "n_aree": len(inp.blocchi),
               "aree": [b.area for b in inp.blocchi]},
    )
