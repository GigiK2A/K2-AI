"""Citazioni documentali verificabili.

Il modello NON inventa collegamenti: scrive `[[fonte|<id documento o nome file>|<pagina>|<testo copiato>]]` usando
gli id e le pagine degli estratti che il backend gli ha dato. Qui ogni marcatore viene:
  1. risolto su un documento davvero presente nella pratica (altrimenti si toglie);
  2. verificato: la pagina esiste e il testo copiato compare nella pagina (stato `ok`), altrimenti si degrada a
     «solo pagina» (`pag`) o si toglie — mai un'evidenziazione di un testo diverso spacciato per la fonte.
La geometria (riquadri da evidenziare) si calcola al momento dell'apertura (`localizza`), dalle parole reali del PDF.
"""
from __future__ import annotations

import hashlib
import re
import unicodedata
from typing import Dict, List, Optional, Tuple

_MARC = re.compile(r"\[\[\s*fonte\s*\|([^|\]]*)\|([^|\]]*)\|([^\]]*?)\s*\]\]", re.I)


def doc_id(file_entry: dict) -> str:
    base = str(file_entry.get("path") or file_entry.get("name") or "")
    return hashlib.sha1(base.encode("utf-8")).hexdigest()[:12]


def mappa_documenti(collected: dict) -> Dict[str, dict]:
    """id → voce di uploaded_files (l'ultima vince se un nome si ripete)."""
    return {doc_id(f): f for f in (collected or {}).get("uploaded_files") or []}


def id_per_nome(collected: dict) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for f in (collected or {}).get("uploaded_files") or []:
        out[str(f.get("name") or "").strip().casefold()] = doc_id(f)
    return out


def norm(t: str) -> str:
    t = unicodedata.normalize("NFKC", str(t or "")).casefold().replace("€", " euro ")
    t = re.sub(r"[^\w.,%/-]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def token(t: str) -> List[str]:
    """Parole normalizzate SENZA la punteggiatura ai bordi («8.850,00.» e «8.850,00» sono lo stesso token): è il confronto usato sia per
    verificare la citazione sia per evidenziarla, così i due controlli non possono più dare esiti diversi."""
    return [w for w in (x.strip(".,-/%") for x in norm(t).split()) if w]


def contiene(testo: str, quote: str) -> bool:
    q = token(quote)
    if not q:
        return False
    t = token(testo)
    return any(t[i:i + len(q)] == q for i in range(len(t) - len(q) + 1))


def trova_in_parole(parole_testo: List[str], quote: str) -> Optional[Tuple[int, int]]:
    """Primo intervallo [i, j] di PAROLE del documento (indici) che riproduce alla lettera il passaggio citato, o None.
    Una parola del PDF può valere più token («€8.850,00» → euro, 8.850,00): si appiattisce e si risale agli indici."""
    q = token(quote)
    if not q:
        return None
    piatti: List[Tuple[str, int]] = []
    for i, w in enumerate(parole_testo):
        for tk in token(w):
            piatti.append((tk, i))
    k = len(q)
    for a in range(len(piatti) - k + 1):
        if [x[0] for x in piatti[a:a + k]] == q:
            return piatti[a][1], piatti[a + k - 1][1]
    return None


def istruzioni() -> str:
    return (
        "CITAZIONI VERIFICABILI: quando riporti un dato, un importo o una clausola dal documento, chiudi la frase con\n"
        "[[fonte|ID_DOCUMENTO|PAGINA|testo copiato ALLA LETTERA dall'estratto, 3-12 parole]]\n"
        "usando l'ID e la pagina del blocco da cui lo prendi (l'intestazione di ogni estratto li riporta). Non inventare ID,\n"
        "pagine o testo: se non hai un passaggio da copiare, scrivi solo «(pag. N)». Il sistema controlla il testo copiato.\n"
    )


def _testi_pagine(collected: dict, session_id: str, chunks: Optional[List[dict]]) -> Dict[str, Dict[int, str]]:
    """doc_id → {pagina: testo}. Dai chunk se ci sono (pagine reali), altrimenti pagina 0 = testo intero."""
    nomi = id_per_nome(collected)
    out: Dict[str, Dict[int, str]] = {}
    for c in chunks or []:
        d = nomi.get(str(c.get("file_name") or "").strip().casefold())
        if not d:
            continue
        p = int(c.get("page_number") or 0)
        out.setdefault(d, {})[p] = out.get(d, {}).get(p, "") + "\n" + str(c.get("content") or "")
    for d, f in mappa_documenti(collected).items():
        if d not in out:
            pag = _pagine_da_pdf(f)
            out[d] = pag or {0: str(f.get("extractedText") or f.get("extractedSummary") or "")}
    return out


_PDF_PAGINE: Dict[str, Dict[int, str]] = {}


def _pagine_da_pdf(f: dict) -> Dict[int, str]:
    """Testo per pagina letto dal PDF originale, quando non ci sono chunk con le pagine (documento di un fascicolo, sessione vecchia).
    Così la citazione ha la pagina vera e il passaggio si può evidenziare. Vuoto se non è un PDF o il file non c'è."""
    path = str(f.get("path") or "")
    if not path or not str(f.get("name") or "").lower().endswith(".pdf"):
        return {}
    if path in _PDF_PAGINE:
        return _PDF_PAGINE[path]
    try:
        import io

        import pdfplumber

        from ..api import upload

        data = upload._bytes_documento(path)
        if not data:
            return {}
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            out = {i + 1: (pg.extract_text() or "") for i, pg in enumerate(pdf.pages[:120])}
        if len(_PDF_PAGINE) >= 20:
            _PDF_PAGINE.pop(next(iter(_PDF_PAGINE)))
        _PDF_PAGINE[path] = out
        return out
    except Exception:
        return {}


def verifica(testo: str, collected: dict, session_id: str, chunks: Optional[List[dict]] = None) -> str:
    """Riscrive i marcatori in forma normalizzata `[[fonte|doc|pag|citazione|ok|pag]]` o li toglie."""
    if not testo or not collected or not collected.get("uploaded_files"):
        return testo
    docs = mappa_documenti(collected)
    nomi = id_per_nome(collected)
    pagine = _testi_pagine(collected, session_id, chunks) if docs else {}

    def sost(m: re.Match) -> str:
        rif, pag, quote = m.group(1).strip(), m.group(2).strip(), m.group(3).strip().strip("\"«»“”'")
        d = rif if rif in docs else nomi.get(rif.casefold())
        if not d:
            return ""                                   # documento inesistente: nessun collegamento
        try:
            p = int(re.sub(r"\D", "", pag) or 0)
        except ValueError:
            p = 0
        testi = pagine.get(d, {})
        quote = re.sub(r"[|\[\]]", " ", quote)[:200]
        nq = norm(quote)
        if p in testi:
            if nq and contiene(testi[p], quote):
                return f"[[fonte|{d}|{p}|{quote}|ok]]"
            # il testo non è in quella pagina: se è in un'altra, la pagina giusta è quella; mai accettare a occhio
            if nq:
                for pp, tt in testi.items():
                    if pp and contiene(tt, quote):
                        return f"[[fonte|{d}|{pp}|{quote}|ok]]"
            return f"[[fonte|{d}|{p}||pag]]" if p else ""
        if 0 in testi and len(testi) == 1:             # formato senza pagine: si verifica sul testo intero
            if nq and contiene(testi[0], quote):
                return f"[[fonte|{d}|0|{quote}|ok]]"
            return ""
        return ""                                       # pagina inesistente nel documento

    out = _MARC.sub(sost, testo)
    return _auto_collega(out, docs, pagine)


_PAG_SEMPLICE = re.compile(r"\(?\b(?:pag\.|pagina)\s*(\d+)\)?", re.I)
_NUMERO = re.compile(r"\d[\d.]*(?:,\d+)?")


def _auto_collega(testo: str, docs: Dict[str, dict], pagine: Dict[str, Dict[int, str]]) -> str:
    """«(pag. N)» senza marcatore → citazione, SOLO se il dato è davvero in quella pagina.

    Il passaggio evidenziato è un numero/importo preso dalla frase che precede il riferimento e trovato
    alla lettera nel testo della pagina; se non c'è, la citazione resta «solo pagina». Mai testo simile.
    Con più documenti si sceglie quello la cui pagina N contiene il dato; se nessuno lo contiene e i
    documenti sono più di uno, non si collega nulla (ambiguo).
    """
    if not docs or not any(p for d in pagine.values() for p in d):
        return testo
    risultato, ultimo = [], 0
    for m in _PAG_SEMPLICE.finditer(testo):
        n = int(m.group(1))
        confini = [b.end() for b in re.finditer(r"[.!?;:](?=\s)|\n", testo[:m.start()])]
        inizio = max(confini[-1] if confini else 0, ultimo)
        clausola = testo[inizio:m.start()]
        numeri = [x for x in _NUMERO.findall(clausola) if len(x) >= 3 and "[[fonte" not in clausola]
        scelta = None
        for d, per_pag in pagine.items():
            t = per_pag.get(n)
            if t is None:
                continue
            nt = token(t)
            for num in reversed(numeri):
                if norm(num).strip(".,-/%") in nt:
                    scelta = (d, num, "ok"); break
            if scelta:
                break
        if not scelta:
            candidati = [d for d, pp in pagine.items() if n in pp]
            if len(candidati) == 1:
                scelta = (candidati[0], "", "pag")
        if scelta:
            d, q, st = scelta
            risultato.append(testo[ultimo:m.start()]); risultato.append(f"[[fonte|{d}|{n}|{q}|{st}]]"); ultimo = m.end()
    risultato.append(testo[ultimo:])
    return "".join(risultato)


import threading

_PDFIUM = threading.Lock()   # pdfium non è thread-safe: una resa alla volta (e oggetti chiusi in ordine)


def _rendi_pagina(pdf_bytes: bytes, indice: int, scala: float) -> bytes:
    import io

    import pypdfium2 as pdfium

    with _PDFIUM:
        doc = pdfium.PdfDocument(pdf_bytes)
        try:
            pag = doc[indice]
            try:
                bitmap = pag.render(scale=scala)
                img = bitmap.to_pil().convert("RGB")
            finally:
                pag.close()
        finally:
            doc.close()
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _geometria_pdfium(pdf_bytes: bytes, indice: int, quote: str) -> List[dict]:
    """Riquadri del passaggio calcolati dal motore che DISEGNA la pagina (pdfium): coincidono con l'immagine servita al visualizzatore.
    Le metriche di pdfplumber/pdfminer possono differire di qualche punto (glifi come «€» con larghezza nulla nei font standard):
    con quelle l'evidenziazione cadeva sfasata. Vuoto se il passaggio non si trova alla lettera nel testo della pagina."""
    import pypdfium2 as pdfium

    with _PDFIUM:
        doc = pdfium.PdfDocument(pdf_bytes)
        try:
            pag = doc[indice]
            try:
                tp = pag.get_textpage()
                try:
                    n = tp.count_chars()
                    testo = tp.get_text_range(0, n) if n else ""
                    if len(testo) != n:
                        return []
                    parole = [(m.start(), m.end()) for m in re.finditer(r"\S+", testo)]
                    tr = trova_in_parole([testo[a:b] for a, b in parole], quote)
                    if not tr:
                        return []
                    a, b = parole[tr[0]][0], parole[tr[1]][1]
                    W, H = float(pag.get_width()), float(pag.get_height())
                    righe: List[List[tuple]] = []
                    for k in range(a, b):
                        if testo[k].isspace():
                            continue
                        l, bo, r, t = tp.get_charbox(k, loose=False)
                        # stessa riga finché il carattere si sovrappone in verticale alla fascia della riga (punti e virgole sono bassi, «€» è alto)
                        if righe and bo <= max(x[3] for x in righe[-1]) and t >= min(x[1] for x in righe[-1]):
                            righe[-1].append((l, bo, r, t))
                        else:
                            righe.append([(l, bo, r, t)])
                    out = []
                    for box in righe:
                        l = min(x[0] for x in box); r = max(x[2] for x in box); bo = min(x[1] for x in box); t = max(x[3] for x in box)
                        out.append({"x": max(0.0, (l - 1) / W), "y": max(0.0, (H - t - 1) / H), "w": (r - l + 2) / W, "h": (t - bo + 2) / H})
                    return out
                finally:
                    tp.close()
            finally:
                pag.close()
        finally:
            doc.close()


def localizza(pdf_bytes: bytes, pagina: int, quote: str, zoom: float = 1.4) -> dict:
    """Pagina PDF resa in PNG (base64) + riquadri normalizzati (0-1) del testo citato, solo se TROVATO nelle parole reali."""
    import base64
    import io

    import pdfplumber

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        n = len(pdf.pages)
        if pagina < 1 or pagina > n:
            return {"ok": False, "motivo": "pagina inesistente", "pagine": n}
        page = pdf.pages[pagina - 1]
        W, H = float(page.width), float(page.height)
        rects: List[dict] = []
        if quote:
            try:
                rects = _geometria_pdfium(pdf_bytes, pagina - 1, quote)
            except Exception:
                rects = []
        words = page.extract_words(keep_blank_chars=False, use_text_flow=False)
        trovato = trova_in_parole([w["text"] for w in words], quote) if (quote and not rects) else None   # ripiego: geometria di pdfplumber
        if trovato:
            i0, i1 = trovato
            righe: Dict[int, List[dict]] = {}
            for w in words[i0:i1 + 1]:
                righe.setdefault(round(float(w["top"]) / 3), []).append(w)
            for ws in righe.values():
                x0 = min(float(w["x0"]) for w in ws); x1 = max(float(w["x1"]) for w in ws)
                t = min(float(w["top"]) for w in ws); b = max(float(w["bottom"]) for w in ws)
                pad = 1.5   # punti PDF: il rendering di pdfium e le metriche di pdfplumber differiscono di un soffio ai bordi
                rects.append({"x": max(0.0, (x0 - pad) / W), "y": max(0.0, (t - 1) / H), "w": (x1 - x0 + 2 * pad) / W, "h": (b - t + 2) / H})
        png = _rendi_pagina(pdf_bytes, pagina - 1, max(0.8, min(zoom, 3.0)))
        return {"ok": True, "pagina": pagina, "pagine": n, "larghezza": W, "altezza": H,
                "immagine": base64.b64encode(png).decode(), "riquadri": rects,
                "localizzato": bool(rects)}


def chunk_della_pratica(collected: dict, session_id: str, fetch) -> List[dict]:
    """Chunk con pagine di TUTTI i documenti della conversazione: quelli caricati qui e quelli aperti da un fascicolo
    (i cui chunk stanno sotto la sessione dove furono caricati). `fetch(session_id)` → lista di chunk."""
    out = list(fetch(session_id) or []) if session_id else []
    visti = {str(session_id)}
    for f in (collected or {}).get("uploaded_files") or []:
        sorg = str(f.get("sorgenteSessione") or "")
        if f.get("dalFascicolo") and sorg and sorg not in visti:
            visti.add(sorg)
            nome = str(f.get("name") or "").casefold()
            out += [c for c in (fetch(sorg) or []) if str(c.get("file_name") or "").casefold() == nome]
    return out
