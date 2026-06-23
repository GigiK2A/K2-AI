"""Audit SEO on-page — screening tecnico deterministico.

Verifica gli elementi on-page oggettivamente misurabili: lunghezza di title e
meta description, presenza della keyword target, densità della keyword,
leggibilità del testo (indice Gulpease per l'italiano), unicità dell'H1 e
copertura degli attributi alt. Produce un punteggio 0-100 e una classe A/B/C/D.

NB: soglie orientative di prassi SEO, non regole ufficiali di ranking.
"""
from __future__ import annotations
import json
import re
from pathlib import Path
from pydantic import BaseModel, Field

_DATA = json.loads((Path(__file__).parent / "data" / "seo_soglie.json").read_text())


class SeoOnPageInput(BaseModel):
    keyword: str = Field(..., min_length=1, description="Keyword/frase target da ottimizzare.")
    title: str = Field("", description="Tag <title> della pagina.")
    meta_description: str = Field("", description="Meta description della pagina.")
    testo: str = Field("", description="Testo del corpo pagina (per densità e leggibilità).")
    h1: list[str] = Field(default_factory=list, description="Elenco dei testi degli H1 presenti.")
    n_immagini: int = Field(0, ge=0, description="Numero di immagini nella pagina.")
    n_immagini_con_alt: int = Field(0, ge=0, description="Numero di immagini con attributo alt valorizzato.")
    url: str = Field("", description="URL della pagina (informativo).")


class CheckSeo(BaseModel):
    id: str
    label: str
    valore: float | int | bool | str | None
    valutazione: str
    score: int
    peso: int


class SeoOnPageOutput(BaseModel):
    keyword: str
    punteggio_0_100: float
    classe: str
    giudizio: str
    colore: str
    gulpease: float | None
    densita_keyword_pct: float | None
    controlli: list[CheckSeo]
    criticita: list[str]
    raccomandazioni: list[str]
    avvertenze: list[str]
    riferimento_normativo: str
    trace: dict


_BANDA = {2: "ottimo", 1: "buono", 0: "critico"}


def _conta_parole(testo: str) -> int:
    return len(re.findall(r"\b\w+\b", testo, flags=re.UNICODE))


def _gulpease(testo: str) -> float | None:
    """Indice Gulpease = 89 + (300*frasi - 10*lettere) / parole. Clampa 0-100."""
    parole = _conta_parole(testo)
    if parole == 0:
        return None
    lettere = len(re.findall(r"[A-Za-zÀ-ÿ]", testo))
    frasi = max(1, len(re.findall(r"[.!?]+", testo)))
    g = 89 + (300 * frasi - 10 * lettere) / parole
    return round(max(0.0, min(100.0, g)), 1)


def _densita(testo: str, keyword: str) -> float | None:
    parole = _conta_parole(testo)
    if parole == 0:
        return None
    occ = len(re.findall(re.escape(keyword.lower()), testo.lower()))
    n_kw_parole = max(1, _conta_parole(keyword))
    return round(occ * n_kw_parole / parole * 100, 2)


def _score_range(valore: float, ottimo: list, buono: list) -> int:
    if ottimo[0] <= valore <= ottimo[1]:
        return 2
    if buono[0] <= valore <= buono[1]:
        return 1
    return 0


def _score_alto(valore: float, s: dict) -> int:
    if valore >= s["ottimo"]:
        return 2
    if valore >= s["buono"]:
        return 1
    return 0


def audit_seo_onpage(inp: SeoOnPageInput) -> SeoOnPageOutput:
    avvertenze = [_DATA["_disclaimer"]]
    controlli: list[CheckSeo] = []
    somma = 0.0
    peso_tot = 0
    criticita: list[str] = []
    raccomandazioni: list[str] = []

    kw = inp.keyword.lower()
    s = _DATA["soglie"]

    def _add(cid, valore, score, peso, label):
        nonlocal somma, peso_tot
        somma += score * peso
        peso_tot += peso
        controlli.append(CheckSeo(id=cid, label=label, valore=valore,
                                  valutazione=_BANDA[score], score=score, peso=peso))
        if score == 0:
            criticita.append(label)

    # Title length
    tl = len(inp.title)
    _add("title_len", tl, _score_range(tl, s["title_len"]["ottimo"], s["title_len"]["buono"]),
         s["title_len"]["peso"], s["title_len"]["label"])
    if tl < s["title_len"]["ottimo"][0] or tl > s["title_len"]["ottimo"][1]:
        raccomandazioni.append(f"Porta il title a {s['title_len']['ottimo'][0]}-{s['title_len']['ottimo'][1]} caratteri (attuale {tl}).")

    # Meta length
    ml = len(inp.meta_description)
    _add("meta_len", ml, _score_range(ml, s["meta_len"]["ottimo"], s["meta_len"]["buono"]), s["meta_len"]["peso"], s["meta_len"]["label"])
    if ml < s["meta_len"]["ottimo"][0] or ml > s["meta_len"]["ottimo"][1]:
        raccomandazioni.append(f"Porta la meta description a {s['meta_len']['ottimo'][0]}-{s['meta_len']['ottimo'][1]} caratteri (attuale {ml}).")

    # Densità keyword
    dens = _densita(inp.testo, inp.keyword)
    if dens is not None:
        _add("densita_keyword_pct", dens, _score_range(dens, s["densita_keyword_pct"]["ottimo"], s["densita_keyword_pct"]["buono"]), s["densita_keyword_pct"]["peso"], s["densita_keyword_pct"]["label"])
        if dens > s["densita_keyword_pct"]["buono"][1]:
            raccomandazioni.append(f"Densità keyword {dens}% troppo alta: rischio keyword stuffing, ridurre.")
        elif dens < s["densita_keyword_pct"]["ottimo"][0]:
            raccomandazioni.append(f"Densità keyword {dens}% bassa: inserire la keyword in modo naturale nel testo.")

    # Gulpease
    g = _gulpease(inp.testo)
    if g is not None:
        _add("gulpease", g, _score_alto(g, s["gulpease"]), s["gulpease"]["peso"], s["gulpease"]["label"])
        if g < s["gulpease"]["buono"]:
            raccomandazioni.append(f"Leggibilità Gulpease {g} bassa: frasi più corte e parole più semplici.")

    # Booleani
    b = _DATA["booleani"]
    kw_title = kw in inp.title.lower()
    _add("keyword_nel_title", kw_title, 2 if kw_title else 0, b["keyword_nel_title"]["peso"], b["keyword_nel_title"]["label"])
    if not kw_title:
        raccomandazioni.append("Inserisci la keyword target nel title.")

    kw_meta = kw in inp.meta_description.lower()
    _add("keyword_nel_meta", kw_meta, 2 if kw_meta else 0, b["keyword_nel_meta"]["peso"], b["keyword_nel_meta"]["label"])
    if not kw_meta:
        raccomandazioni.append("Inserisci la keyword nella meta description.")

    kw_h1 = any(kw in h.lower() for h in inp.h1)
    _add("keyword_in_h1", kw_h1, 2 if kw_h1 else 0, b["keyword_in_h1"]["peso"], b["keyword_in_h1"]["label"])
    if not kw_h1:
        raccomandazioni.append("Includi la keyword in un H1.")

    un_h1 = len(inp.h1) == 1
    _add("un_solo_h1", len(inp.h1), 2 if un_h1 else 0, b["un_solo_h1"]["peso"], b["un_solo_h1"]["label"])
    if not un_h1:
        raccomandazioni.append(f"Usa esattamente un H1 (attuali {len(inp.h1)}).")

    if inp.n_immagini > 0:
        cov = inp.n_immagini_con_alt / inp.n_immagini
        alt_ok = cov >= 0.9
        _add("copertura_alt_ok", round(cov, 2), 2 if alt_ok else (1 if cov >= 0.5 else 0), b["copertura_alt_ok"]["peso"], b["copertura_alt_ok"]["label"])
        if not alt_ok:
            raccomandazioni.append(f"Copertura alt immagini {cov:.0%}: aggiungi attributi alt descrittivi.")

    punteggio = round(somma / (peso_tot * 2) * 100, 1) if peso_tot else 0.0
    banda = next(x for x in _DATA["rating_bande"] if punteggio >= x["min_score"])

    return SeoOnPageOutput(
        keyword=inp.keyword,
        punteggio_0_100=punteggio,
        classe=banda["classe"], giudizio=banda["giudizio"], colore=banda["colore"],
        gulpease=g, densita_keyword_pct=dens,
        controlli=controlli, criticita=criticita, raccomandazioni=raccomandazioni,
        avvertenze=avvertenze,
        riferimento_normativo=_DATA["_fonte"],
        trace={"fonte_dati": _DATA["_fonte"], "data_validita_dati": _DATA["_data_validita"],
               "metodo": "media pesata dei controlli on-page (0-2) normalizzata 0-100",
               "peso_totale": peso_tot, "parole_testo": _conta_parole(inp.testo)},
    )
