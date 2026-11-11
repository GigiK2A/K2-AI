#!/usr/bin/env python3
"""Prova di accesso ai bucket kbot-uploads e kbot-reports PRIMA e DOPO la privatizzazione, con file FITTIZI.

Cosa fa (solo con --esegui; senza, stampa il piano e non scrive nulla):
  1. carica in ogni bucket un PDF finto `test31/<uuid>/fittizio.pdf` (nessun dato reale, un solo percorso, ripulito alla fine);
  2. legge il file SENZA credenziali dall'URL pubblico (`/object/public/…`)           → prima: 200 (esposto) · dopo: 400/404 (chiuso)
  3. genera un URL firmato e lo legge SENZA credenziali                                 → sempre 200 e contenuto identico
  4. passa l'URL pubblico «vecchio» da `rinfresca_url` e legge il risultato            → dopo: 200 (i vecchi link salvati nelle sessioni continuano a funzionare)
  5. (se c'è SUPABASE_ANON_KEY) prova l'elenco del bucket con la chiave anon            → sempre rifiutato
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
             anon_key: Optional[str] = None, http_list: Optional[Callable[[str, str], int]] = None) -> Dict[str, dict]:
    """Esegue le letture e le restituisce (senza giudicarle). Pulisce sempre ciò che ha creato."""
    out: Dict[str, dict] = {}
    creati: List[Tuple[str, str]] = []
    try:
        for b in BUCKET:
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


def valuta(fase: str, risultati: Dict[str, dict]) -> List[Tuple[str, str, object, object, bool]]:
    """(bucket, controllo, atteso, ottenuto, ok)."""
    righe = []
    for b, r in risultati.items():
        if fase == "prima":
            righe.append((b, "lettura anonima del link PUBBLICO", "200 (stato attuale: esposto)", r["pubblico_anonimo"], r["pubblico_anonimo"] == 200))
        else:
            righe.append((b, "lettura anonima del link PUBBLICO", "400/404 (chiuso)", r["pubblico_anonimo"], r["pubblico_anonimo"] in (400, 401, 403, 404)))
        righe.append((b, "lettura anonima dell'URL FIRMATO", 200, r["firmato_anonimo"], r["firmato_anonimo"] == 200 and r["firmato_contenuto_ok"]))
        righe.append((b, "vecchio link pubblico → rinfresca_url", "URL firmato nuovo", "cambiato" if r["vecchio_link_e_cambiato"] else "invariato", r["vecchio_link_e_cambiato"]))
        righe.append((b, "lettura del vecchio link rinfrescato", 200, r["vecchio_link_rinfrescato"], r["vecchio_link_rinfrescato"] == 200 and r["vecchio_link_contenuto_ok"]))
        if "elenco_con_anon" in r:
            righe.append((b, "elenco del bucket con la chiave anon", "rifiutato", r["elenco_con_anon"], r["elenco_con_anon"] not in (200,)))
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
    ap.add_argument("--fase", choices=("prima", "dopo"), required=True)
    ap.add_argument("--progetto", required=True, help="riferimento del progetto Supabase atteso nell'URL (evita di girare sull'ambiente sbagliato)")
    ap.add_argument("--esegui", action="store_true", help="senza questa opzione non scrive nulla")
    a = ap.parse_args(argv)
    url, chiave = os.environ.get("SUPABASE_URL", ""), os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    if a.progetto not in url:
        print(f"RIFIUTO: SUPABASE_URL non contiene «{a.progetto}»: ambiente sbagliato.", file=sys.stderr)
        return 2
    if not a.esegui:
        print(f"PIANO (nessuna scrittura): fase={a.fase}, progetto={a.progetto}; creerebbe {PREFISSO}/<uuid>/fittizio.pdf in {', '.join(BUCKET)}, "
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
        return httpx.post(f"{url.rstrip('/')}/storage/v1/object/list/{bucket}", headers={"apikey": k, "Authorization": f"Bearer {k}"}, json={"prefix": PREFISSO}, timeout=30).status_code
    # rinfresca_url usa il client admin dell'app: con l'ambiente di questo script punta allo stesso progetto
    ris = raccogli(client, url, http_get, storage.rinfresca_url, anon, http_list if anon else None)
    return 0 if stampa(a.fase, valuta(a.fase, ris)) else 1


if __name__ == "__main__":
    sys.exit(main())
