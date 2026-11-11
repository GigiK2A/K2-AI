#!/usr/bin/env python3
"""Prova di accesso ai bucket kbot-uploads e kbot-reports PRIMA e DOPO la privatizzazione, con file FITTIZI.

Cosa fa (solo con --esegui; senza, stampa il piano e non scrive nulla):
  1. carica in ogni bucket un PDF finto `test31/<uuid>/fittizio.pdf` (nessun dato reale, un solo percorso, ripulito alla fine);
  2. legge il file SENZA credenziali dall'URL pubblico (`/object/public/…`)           → prima: 200 (esposto) · dopo: 400/404 (chiuso)
  2b. legge il file con la chiave di servizio (percorso del backend per visualizzatore, citazioni, allegati) → sempre identico
  3. genera un URL firmato e lo legge SENZA credenziali                                 → sempre 200 e contenuto identico
  4. passa l'URL pubblico «vecchio» da `rinfresca_url` e legge il risultato            → dopo: 200 (i vecchi link salvati nelle sessioni continuano a funzionare)
  5. (se c'è SUPABASE_ANON_KEY) prova l'elenco del bucket con la chiave anon            → 0 voci visibili (file non enumerabili; 200 con elenco vuoto va bene)
  6. cancella gli oggetti creati (solo quelli sotto `test31/<uuid>/`).

Uso:   SUPABASE_URL=… SUPABASE_SERVICE_ROLE_KEY=… python scripts/verifica_bucket.py --fase prima --progetto uiuvwzrmrdqbfajguuab --esegui
Esito: tabella PASS/FAIL e codice di uscita 0 solo se tutto è come atteso per la fase. Le chiavi non vengono mai stampate.
"""
from __future__ import annotations

import argparse
import os
import sys
import uuid
from typing import Callable, Dict, List, Optional, Tuple

BUCKET = ("kbot-uploads", "kbot-reports")
PREFISSO = "test31"


def _pdf(token: str) -> bytes:
    return f"%PDF-1.4\n% FITTIZIO {token}\n%%EOF\n".encode()


def raccogli(client, base_url: str, http_get: Callable[[str], Tuple[int, bytes]], rinfresca: Callable[[Optional[str]], Optional[str]],
             anon_key: Optional[str] = None, http_list: Optional[Callable[[str, str], int]] = None, buckets=BUCKET) -> Dict[str, dict]:
    # `http_list(bucket, chiave)` restituisce QUANTE voci vede la chiave anon (0 se rifiutato o se la RLS restituisce un elenco vuoto: 200 con 0 voci = chiuso)
    """Esegue le letture e le restituisce (senza giudicarle). Pulisce sempre ciò che ha creato."""
    out: Dict[str, dict] = {}
    creati: List[Tuple[str, str]] = []
    try:
        for b in buckets:
            token = uuid.uuid4().hex
            path = f"{PREFISSO}/{token}/fittizio.pdf"
            contenuto = _pdf(token)
            client.storage.from_(b).upload(path, contenuto, {"content-type": "application/pdf", "upsert": "true"})
            creati.append((b, path))
            pubblico = f"{base_url.rstrip('/')}/storage/v1/object/public/{b}/{path}"
            r: dict = {}
            r["pubblico_anonimo"] = http_get(pubblico)[0]
            firmato = client.storage.from_(b).create_signed_url(path, 120)
            url = firmato.get("signedURL") or firmato.get("signedUrl") or firmato.get("signed_url") if isinstance(firmato, dict) else getattr(firmato, "signed_url", None)
            if url and url.startswith("/"):
                url = base_url.rstrip("/") + ("/storage/v1" if not url.startswith("/storage/") else "") + url
            codice, corpo = http_get(url) if url else (0, b"")
            r["firmato_anonimo"] = codice
            r["firmato_contenuto_ok"] = corpo == contenuto
            try:                                   # il percorso del backend per visualizzatore, citazioni e allegati: chiave di servizio, indipendente dalla visibilità del bucket
                r["servizio_contenuto_ok"] = client.storage.from_(b).download(path) == contenuto
            except Exception:
                r["servizio_contenuto_ok"] = False
            nuovo = rinfresca(pubblico)
            codice2, corpo2 = http_get(nuovo) if nuovo and nuovo != pubblico else (0, b"")
            r["vecchio_link_rinfrescato"] = codice2
            r["vecchio_link_contenuto_ok"] = corpo2 == contenuto
            r["vecchio_link_e_cambiato"] = bool(nuovo and nuovo != pubblico and "/sign/" in nuovo)
            if anon_key and http_list:
                r["elenco_con_anon"] = http_list(b, anon_key)
            out[b] = r
    finally:
        for b, path in creati:
            try:
                client.storage.from_(b).remove([path])
            except Exception:
                print(f"ATTENZIONE: non sono riuscito a cancellare {b}/{path}: ripulire a mano (solo test31/…)", file=sys.stderr)
    return out


def prepara_cache(client, base_url: str, http_get: Callable[[str], Tuple[int, bytes]], buckets=BUCKET) -> List[str]:
    """Per il controllo della cache di rete DOPO la privatizzazione: carica un file fittizio, lo legge dal link pubblico (così finisce nella cache),
    lo CANCELLA e restituisce l'URL pubblico. Dopo il passaggio a privato (e dopo la scadenza della cache) quell'URL non deve più rispondere 200."""
    urls: List[str] = []
    for b in buckets:
        path = f"{PREFISSO}/cache-{uuid.uuid4().hex}/fittizio.pdf"
        client.storage.from_(b).upload(path, _pdf("cache"), {"content-type": "application/pdf", "upsert": "true"})
        try:
            url = f"{base_url.rstrip('/')}/storage/v1/object/public/{b}/{path}"
            if http_get(url)[0] == 200:
                urls.append(url)
        finally:
            client.storage.from_(b).remove([path])
    return urls


def controlla_cache(urls: List[str], http_get: Callable[[str], Tuple[int, bytes]]) -> List[Tuple[str, int, bool]]:
    return [(u, http_get(u)[0], http_get(u)[0] != 200) for u in urls]


def valuta(fase: str, risultati: Dict[str, dict]) -> List[Tuple[str, str, object, object, bool]]:
    """(bucket, controllo, atteso, ottenuto, ok)."""
    righe = []
    for b, r in risultati.items():
        if fase == "prima":
            righe.append((b, "lettura anonima del link PUBBLICO", "200 (stato attuale: esposto)", r["pubblico_anonimo"], r["pubblico_anonimo"] == 200))
        else:
            righe.append((b, "lettura anonima del link PUBBLICO", "400/404 (chiuso)", r["pubblico_anonimo"], r["pubblico_anonimo"] in (400, 401, 403, 404)))
        righe.append((b, "lettura anonima dell'URL FIRMATO", 200, r["firmato_anonimo"], r["firmato_anonimo"] == 200 and r["firmato_contenuto_ok"]))
        righe.append((b, "lettura con la chiave di servizio (visualizzatore, citazioni)", "contenuto identico", "identico" if r.get("servizio_contenuto_ok") else "DIVERSO/errore", bool(r.get("servizio_contenuto_ok"))))
        righe.append((b, "vecchio link pubblico → rinfresca_url", "URL firmato nuovo", "cambiato" if r["vecchio_link_e_cambiato"] else "invariato", r["vecchio_link_e_cambiato"]))
        righe.append((b, "lettura del vecchio link rinfrescato", 200, r["vecchio_link_rinfrescato"], r["vecchio_link_rinfrescato"] == 200 and r["vecchio_link_contenuto_ok"]))
        if "elenco_con_anon" in r:
            righe.append((b, "elenco del bucket con la chiave anon (voci visibili)", "0 (non enumerabile)", r["elenco_con_anon"], r["elenco_con_anon"] == 0))
    return righe


def stampa(fase: str, righe) -> bool:
    print(f"\nFASE: {fase.upper()}")
    ok_tutti = True
    for b, controllo, atteso, ottenuto, ok in righe:
        ok_tutti &= bool(ok)
        print(f"  {'PASS' if ok else 'FAIL'}  {b:13} {controllo:42} atteso={atteso!s:28} ottenuto={ottenuto}")
    print("ESITO:", "tutto come atteso" if ok_tutti else "CI SONO DIFFERENZE")
    return ok_tutti


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fase", choices=("prima", "dopo"))
    ap.add_argument("--bucket", action="append", choices=BUCKET, help="limita la prova a un bucket (ripetibile); senza: entrambi")
    ap.add_argument("--prepara-cache", metavar="FILE", help="crea e cancella file fittizi dopo averli letti dal link pubblico; salva gli URL (da ricontrollare dopo la privatizzazione)")
    ap.add_argument("--controlla-cache", metavar="FILE", help="rilegge gli URL salvati: nessuno deve rispondere 200 (senza scrivere nulla)")
    ap.add_argument("--progetto", required=False, help="riferimento del progetto Supabase atteso nell'URL (evita di girare sull'ambiente sbagliato)")
    ap.add_argument("--esegui", action="store_true", help="senza questa opzione non scrive nulla")
    a = ap.parse_args(argv)
    if not (a.fase or a.prepara_cache or a.controlla_cache):
        ap.error("indica --fase, --prepara-cache o --controlla-cache")
    buckets = tuple(a.bucket) if a.bucket else BUCKET
    url, chiave = os.environ.get("SUPABASE_URL", ""), os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    if a.controlla_cache:                                            # sola lettura: nessuna credenziale necessaria
        import httpx
        righe = controlla_cache([x.strip() for x in open(a.controlla_cache, encoding="utf-8") if x.strip()], lambda u: (httpx.get(u, timeout=30).status_code, b""))
        for u, codice, ok in righe:
            print(f"  {'PASS' if ok else 'FAIL'}  cache: {u.split('/object/')[1][:40]}…  HTTP {codice} (atteso: non 200)")
        print("ESITO:", "nessun URL pubblico risponde più" if all(ok for *_, ok in righe) else "ALCUNI URL RISPONDONO ANCORA 200 (cache di rete o bucket ancora pubblico)")
        return 0 if all(ok for *_, ok in righe) else 1
    if not a.progetto or a.progetto not in url:
        print(f"RIFIUTO: SUPABASE_URL non contiene «{a.progetto}»: ambiente sbagliato.", file=sys.stderr)
        return 2
    if not a.esegui:
        print(f"PIANO (nessuna scrittura): fase={a.fase or 'cache'}, progetto={a.progetto}; creerebbe {PREFISSO}/<uuid>/fittizio.pdf in {', '.join(BUCKET)}, "
              "leggerebbe i link senza credenziali, e cancellerebbe i file creati. Aggiungi --esegui per procedere.")
        return 0
    if not chiave:
        print("RIFIUTO: manca SUPABASE_SERVICE_ROLE_KEY.", file=sys.stderr)
        return 2
    import httpx
    from supabase import create_client
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    from app.lib import storage

    client = create_client(url, chiave)

    def http_get(u: str) -> Tuple[int, bytes]:
        r = httpx.get(u, timeout=30, follow_redirects=True)
        return r.status_code, r.content

    anon = os.environ.get("SUPABASE_ANON_KEY")

    def http_list(bucket: str, k: str) -> int:
        r = httpx.post(f"{url.rstrip('/')}/storage/v1/object/list/{bucket}", headers={"apikey": k, "Authorization": f"Bearer {k}"}, json={"prefix": PREFISSO, "limit": 1000}, timeout=30)
        try:
            d = r.json()
            return len(d) if r.status_code == 200 and isinstance(d, list) else 0
        except Exception:
            return 0
    # rinfresca_url usa il client admin dell'app: con l'ambiente di questo script punta allo stesso progetto
    if a.prepara_cache:
        urls = prepara_cache(client, url, http_get, buckets)
        open(a.prepara_cache, "w", encoding="utf-8").write("\n".join(urls) + "\n")
        print(f"preparati {len(urls)} URL pubblici fittizi (file già cancellati) in {a.prepara_cache}")
        return 0
    ris = raccogli(client, url, http_get, storage.rinfresca_url, anon, http_list if anon else None, buckets)
    return 0 if stampa(a.fase, valuta(a.fase, ris)) else 1


if __name__ == "__main__":
    sys.exit(main())
