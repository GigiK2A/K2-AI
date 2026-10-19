#!/usr/bin/env python3
"""Aggiunge una norma (testo VIGENTE, articolo per articolo) al supplemento `data/normattiva_supplement.db`.

Perché esiste: il corpus canonico ha dei buchi (19/10/2026: dello Statuto dei lavoratori, L. 300/1970, c'è solo
l'art. 1; la L. 604/1966 non c'è). Il testo di legge NON si scrive a mano né si cita a memoria: si scarica
dall'API ufficiale Normattiva (OpenData, endpoint `dettaglio-atto-urn`, senza autenticazione), che restituisce
l'articolo VIGENTE con le note di aggiornamento (sentenze della Corte costituzionale comprese). Il titolo
dell'atto restituito dall'API viene stampato e va confrontato con la norma voluta: l'URN sbagliato darebbe
un'altra legge.

Uso:
  python3 scripts/aggiungi_norma_al_supplemento.py \\
      --urn "urn:nir:stato:legge:1970-05-20;300" --tipo legge --anno 1970 --numero 300
  (--dry-run: scarica e mostra senza scrivere; --max N: ultimo numero d'articolo da provare, default 60)

Idempotente: le righe dello stesso articolo già presenti nel supplemento vengono sostituite; gli articoli già
presenti nel corpus principale (se indicato con --corpus) vengono saltati. Formato del testo = quello del corpus
canonico (frontmatter YAML + «# Art. N — …» + rubrica + commi + blocchi «AGGIORNAMENTO (n)»).
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

API = "https://api.normattiva.it/t/normattiva.api/bff-opendata/v1/api/v1/atto/dettaglio-atto-urn"
SUFFISSI = ("bis", "ter", "quater", "quinquies", "sexies")
LABEL_TIPO = {"legge": "Legge", "decreto_legislativo": "Decreto Legislativo", "decreto_legge": "Decreto-legge"}


def scarica(urn: str, pausa: float = 0.25) -> dict | None:
    """L'oggetto `atto` dell'API per l'URN, None se l'articolo non esiste (HTTP 404)."""
    time.sleep(pausa)
    req = urllib.request.Request(API, data=json.dumps({"urn": urn}).encode(),
                                 headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
    for tentativo in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return (json.loads(r.read()).get("data") or {}).get("atto")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if tentativo == 2:
                raise
        except urllib.error.URLError:
            if tentativo == 2:
                raise
        time.sleep(2 * (tentativo + 1))
    return None


def _testo(frag: str) -> str:
    frag = re.sub(r"(?i)<br\s*/?>", "\n", frag)
    frag = re.sub(r"(?i)</(div|p|li|h\d)>", "\n", frag)
    frag = re.sub(r"<[^>]+>", "", frag)
    righe = [re.sub(r"[ \t ]+", " ", l).strip() for l in html.unescape(frag).split("\n")]
    out, vuota = [], False
    for l in righe:
        if l:
            out.append(l)
            vuota = False
        elif not vuota and out:
            vuota = True
    return "\n".join(out).strip()


def converti(atto: dict, tipo: str, anno: int, numero: str, art: str) -> tuple[str, str] | None:
    """(file, testo) nel formato del corpus, oppure None se l'HTML non è l'articolo richiesto."""
    h = atto.get("articoloHtml") or ""
    m = re.search(r'<h2 class="article-num-akn" id="art_([^"]+)">\s*([^<]*)</h2>', h)
    if not m or re.sub(r"[^0-9a-z]", "", m.group(1).lower()) != re.sub(r"[^0-9a-z]", "", art.lower()):
        return None
    rub = re.search(r'<div class="article-heading-akn">(.*?)</div>', h, re.S)
    corpo = re.search(r'<span class="art-just-text-akn">(.*?)</span>\s*(?=<div class="art_aggiornamento-akn">|</div>\s*$|$)', h, re.S)
    if corpo:
        testo_art = _testo(corpo.group(1))
    else:                                           # articoli con commi numerati (art-commi-div-akn)
        resto = h[m.end():]
        resto = re.sub(r'<div class="article-heading-akn">.*?</div>', "", resto, count=1, flags=re.S)
        resto = resto.split('<div class="art_aggiornamento-akn">')[0]
        testo_art = _testo(resto)
    note = []
    for blocco in re.findall(r'<div class="art_aggiornamento-akn">(.*?)</div>\s*</div>\s*(?=<div class="art_aggiornamento-akn">|</div>\s*$|$)', h, re.S):
        t = re.search(r'art_aggiornamento_title-akn">(.*?)</div>', blocco, re.S)
        b = re.search(r'art_aggiornamento_testo-akn">(.*)', blocco, re.S)
        if t and b:
            note.append(f"-------------\n{_testo(t.group(1))}\n{_testo(b.group(1))}")
    inizio = str(atto.get("articoloDataInizioVigenza") or "")
    inizio_iso = f"{inizio[:4]}-{inizio[4:6]}-{inizio[6:8]}" if len(inizio) == 8 and inizio.isdigit() else ""
    nome_art = m.group(1).replace("_", "-")
    front = ("---\n" f"tipo: {tipo}\nanno: {anno}\nnumero: '{numero}'\n"
             f"titolo_norma: {LABEL_TIPO.get(tipo, tipo)}\nsource: api_dettaglio_atto_urn\nformato_richiesta: V\n"
             f"file_prefix: {tipo}_{anno}_{numero}\narticolo: '{nome_art}'\ndata_vigenza: '{date.today().isoformat()}'\n"
             f"inizio_vigenza_articolo: '{inizio_iso}'\nfonte: Normattiva OpenData — API dettaglio-atto-urn (testo vigente)\n---\n\n")
    intest = f"# {m.group(2).strip()} — {LABEL_TIPO.get(tipo, tipo)}\n\n"
    rubrica = (_testo(rub.group(1)) + "\n\n") if rub else ""
    testo = front + intest + rubrica + testo_art + ("\n" + "\n".join(note) if note else "") + "\n"
    return f"chunks/{tipo}_{anno}_{numero}_art_{nome_art}.md", testo


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--urn", required=True)
    ap.add_argument("--tipo", required=True)
    ap.add_argument("--anno", type=int, required=True)
    ap.add_argument("--numero", required=True)
    ap.add_argument("--max", type=int, default=60)
    ap.add_argument("--db", default=str(Path(__file__).resolve().parent.parent / "data" / "normattiva_supplement.db"))
    ap.add_argument("--corpus", default="", help="corpus principale: gli articoli che ha già si saltano")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    primo = scarica(f"{a.urn}~art1")
    if not primo:
        print("ERRORE: l'API non conosce questo URN", file=sys.stderr)
        return 2
    print(f"Atto restituito dall'API: {primo.get('titolo')} — {(primo.get('sottoTitolo') or '').strip().splitlines()[0][:100]}")
    righe, trovati, assenti = [], [], 0
    for n in range(1, a.max + 1):
        for suf in ("",) + SUFFISSI:
            art = f"{n}{suf}"
            atto = primo if (n == 1 and not suf) else scarica(f"{a.urn}~art{art}")
            if not atto:
                if suf == "":
                    assenti += 1
                if suf:                              # i suffissi sono consecutivi: il primo mancante chiude la serie
                    break
                continue
            r = converti(atto, a.tipo, a.anno, a.numero, art)
            if r:
                righe.append(r)
                trovati.append(art)
            elif suf:
                break
    print(f"Articoli trovati: {len(trovati)} → {', '.join(trovati)}")
    if not righe:
        return 3
    saltati = []
    if a.corpus:
        con = sqlite3.connect(f"file:{a.corpus}?mode=ro", uri=True)
        presenti = {f for (f,) in con.execute("SELECT file FROM chunks WHERE file LIKE ?", (f"%{a.tipo}_{a.anno}_{a.numero}_art_%",))}
        con.close()
        base = {Path(p).name for p in presenti}
        saltati = [f for f, _ in righe if Path(f).name in base]
        righe = [(f, t) for f, t in righe if Path(f).name not in base]
        print(f"Già nel corpus principale (saltati): {[Path(s).name for s in saltati]}")
    if a.dry_run:
        for f, t in righe[:2]:
            print(f"\n=== {f}\n{t[:900]}")
        return 0
    con = sqlite3.connect(a.db)
    for f, t in righe:
        for (i,) in con.execute("SELECT id FROM chunks WHERE file LIKE ?", (f"%{Path(f).name}",)).fetchall():
            con.execute("DELETE FROM chunks WHERE id=?", (i,))
        con.execute("DELETE FROM chunks_fts WHERE file LIKE ?", (f"%{Path(f).name}",))
        cur = con.execute("INSERT INTO chunks(file, testo, source) VALUES (?,?,?)", (f, t, "supplement"))
        con.execute("INSERT INTO chunks_fts(rowid, file, testo) VALUES (?,?,?)", (cur.lastrowid, f, t))
    con.commit()
    con.close()
    print(f"Scritti nel supplemento: {len(righe)} articoli ({a.db})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
