"""Re-extraction best-effort di sezioni critiche dai PDF originali (NT-2).

CONTESTO TECNICO (verificato in NT-2 Stage 0):
I PDF NTC2018 / Circolare 7/2019 incorporano i simboli matematici in font subset
(KMFNLF+Symbol, ...) PRIVI di mappa ToUnicode: pdfplumber li restituisce come token
`(cid:NNN)` dove NNN è un indice di glifo del subset (NON un codepoint standard).
Inoltre i titoli/heading in grassetto sono disegnati due volte con offset minimo →
`extract_text()` raddoppia il primo carattere ("44.1.12" per "4.1.12").

STRATEGIA (best-effort, decisa con il committente):
1. `dedupe_chars(tolerance=1)` rimuove il raddoppio dei glifi sovrapposti.
2. `CID_MAP` mappa i glifi matematici Symbol più frequenti, identificati per
   contesto (≤ ≥ = · √ γ σ δ Δ λ ...). I CID residui non mappati vengono rimossi
   (stripping) → l'output NON contiene mai `(cid:NNN)` né replacement char `�`.
3. NB: la prosa risulta pulita e i simboli leggibili, ma il LAYOUT di frazioni/
   apici/pedici NON viene ricostruito (limite intrinseco dell'estrazione testuale).
   Le formule restano quindi linearizzate e imperfette: vedi REPORT_NT_2.md.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Iterator

import pdfplumber
from pdfplumber.utils import extract_text as _pp_extract_text

# --- Recupero simboli matematici dal font Symbol subset (cid -> unicode) ------
# CID = indice di glifo del subset, NON un codepoint standard ⇒ è VALIDO SOLO per
# la famiglia di font su cui è stato calibrato (Symbol di QUESTI PDF). Lo stesso
# numero di CID in un font di testo (TimesNewRoman/Palatino) è una LETTERA diversa:
# applicare la mappa a quei font inietterebbe simboli sbagliati (verificato in
# Stage 0: cid:16 in TimesNewRoman è una lettera, non "−"). Per questo la mappa è
# applicata SOLO ai glifi la cui fontname contiene "Symbol" (vedi _map_chars).
# I CID identificati per contesto sulle sezioni critiche:
SYMBOL_CID_MAP: dict[int, str] = {
    32: "=",     # uguale
    100: "≤",    # minore-uguale
    450: "≤",    # minore-uguale (variante subset)
    151: "√",    # radice
    152: "·",    # punto di moltiplicazione
    74: "γ",     # gamma minuscola (γ_M0 ...)
    86: "σ",     # sigma
    71: "δ",     # delta minuscola
    39: "Δ",     # Delta maiuscola (range tensione Δσ)
    79: "λ",     # lambda (snellezza normalizzata)
}

_CID_RE = re.compile(r"\(cid:(\d+)\)")
_CID_CHAR_RE = re.compile(r"^\(cid:(\d+)\)$")


def _map_chars(chars: list[dict]) -> tuple[list[dict], int]:
    """Mappa i glifi (cid:N) a livello di carattere, in modo FONT-AWARE.

    - font Symbol + cid noto  -> simbolo Unicode.
    - tutti gli altri (cid:N) -> rimossi (strip), per non iniettare simboli errati.

    Returns: (chars_modificati, n_glifi_rimossi).
    """
    out: list[dict] = []
    dropped = 0
    for ch in chars:
        m = _CID_CHAR_RE.match(ch.get("text", ""))
        if not m:
            out.append(ch)
            continue
        cid = int(m.group(1))
        if "Symbol" in ch.get("fontname", "") and cid in SYMBOL_CID_MAP:
            nch = dict(ch)
            nch["text"] = SYMBOL_CID_MAP[cid]
            out.append(nch)
        else:
            dropped += 1  # glifo non recuperabile: rimosso
    return out, dropped


def clean_cid(text: str) -> tuple[str, int]:
    """Variante string-based (font-agnostica) — usata solo nei test/utility.

    Sostituisce i (cid:N) di SYMBOL_CID_MAP; rimuove i residui. NB: priva di
    awareness del font, quindi NON usata nel percorso di estrazione principale.
    """
    dropped = 0

    def _repl(m: re.Match) -> str:
        nonlocal dropped
        cid = int(m.group(1))
        if cid in SYMBOL_CID_MAP:
            return SYMBOL_CID_MAP[cid]
        dropped += 1
        return ""

    return _CID_RE.sub(_repl, text), dropped


def normalize_whitespace(text: str) -> str:
    """Compatta spazi multipli e righe vuote ridondanti, preservando i ritorni a capo."""
    lines = [re.sub(r"[ \t]+", " ", ln).rstrip() for ln in text.split("\n")]
    out: list[str] = []
    blank = False
    for ln in lines:
        if not ln.strip():
            if not blank:
                out.append("")
            blank = True
        else:
            out.append(ln)
            blank = False
    return "\n".join(out).strip()


def extract_pages_range(pdf_path: Path, page_start: int, page_end: int) -> tuple[str, int]:
    """Estrae testo pulito da un range di pagine (1-indexed, inclusi).

    Applica dedupe_chars (anti-raddoppio) + clean_cid (recupero simboli).

    Returns:
        (testo, n_cid_droppati_totale)
    """
    texts: list[str] = []
    total_dropped = 0
    with pdfplumber.open(pdf_path) as pdf:
        last = len(pdf.pages)
        for p in range(page_start - 1, min(page_end, last)):
            page = pdf.pages[p].dedupe_chars(tolerance=1)
            chars, dropped = _map_chars(page.chars)
            total_dropped += dropped
            txt = _pp_extract_text(chars) if chars else ""
            if txt and txt.strip():
                texts.append(txt)
    return normalize_whitespace("\n\n".join(texts)), total_dropped


# --- Riconoscimento heading di paragrafo -------------------------------------
# Es. "4.2.4.1.2.1 Trazione", "C4.2.4.1.3.4.9 ...". Almeno 3 livelli (X.Y.Z),
# titolo che inizia con maiuscola e NON è tutto numerico.
# Es. "4.2.4.1.2.1 Trazione" (no dot) e "3.3.1. VELOCITÀ BASE" (trailing dot).
PARAGRAPH_HEADING_RE = re.compile(
    r"^(C?\d+(?:\.\d+){2,})\.?\s+([A-ZÀ-Ù][^\n]{2,80})$",
    re.MULTILINE,
)


def split_into_paragraphs(text: str) -> Iterator[dict]:
    """Splitta il testo in paragrafi sui heading riconoscibili.

    Yields dict: {paragrafo, section_code, titolo, contenuto}.
    """
    matches = list(PARAGRAPH_HEADING_RE.finditer(text))
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        paragrafo = m.group(1)
        titolo_short = m.group(2).strip()
        contenuto = text[m.end():end].strip()
        yield {
            "paragrafo": paragrafo,
            "section_code": paragrafo,
            "titolo": f"{paragrafo} {titolo_short}",
            "contenuto": contenuto,
        }


# --- Tag euristici -----------------------------------------------------------
_MACRO_TAG = {"3": "azioni", "4": "verifica", "5": "ponti", "6": "geotecnica",
              "7": "sisma", "8": "esistenti", "11": "materiali"}
_SEC_TAG = {
    "3.2": "sisma", "3.3": "vento", "4.1": "calcestruzzo", "4.2": "acciaio",
    "4.4": "legno", "4.5": "muratura", "6.4": "fondazioni", "7.2": "sisma",
}
_KW_TAG = {
    "trazione": "trazione", "compression": "compressione", "flession": "flessione",
    "taglio": "taglio", "instabilità": "instabilita", "saldatura": "saldatura",
    "bullon": "bullone", "flangia": "flangia", "snervamento": "snervamento",
    "fatica": "fatica", "fessurazione": "fessurazione", "deformazione": "deformazione",
    "ancoraggio": "ancoraggio", "vento": "vento", "sismic": "sisma", "neve": "neve",
    "portanza": "fondazioni", "cedimento": "fondazioni",
}


def heuristic_tags(paragrafo: str, contenuto: str) -> list[str]:
    """Deriva tag da section_code (macro+secondario) e parole chiave nel contenuto."""
    tags: set[str] = set()
    code = paragrafo.lstrip("C")
    parts = code.split(".")
    if parts[0] in _MACRO_TAG:
        tags.add(_MACRO_TAG[parts[0]])
    if len(parts) >= 2:
        sec = f"{parts[0]}.{parts[1]}"
        if sec in _SEC_TAG:
            tags.add(_SEC_TAG[sec])
    cl = contenuto.lower()
    for kw, tag in _KW_TAG.items():
        if kw in cl:
            tags.add(tag)
    return sorted(tags)


def has_corruption(text: str) -> bool:
    """True se restano replacement char o token CID (qualità post-pulizia)."""
    return "�" in text or bool(_CID_RE.search(text))


def compute_sha1(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()
