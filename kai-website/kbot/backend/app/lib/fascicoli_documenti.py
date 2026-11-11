"""Versioni dei documenti di un fascicolo (test 30B).

Tre cose DISTINTE, mai confuse:
  * il DOCUMENTO LOGICO — identificativo stabile `documento_id` (uguale in tutte le sue versioni), sigla `L-xxxxxxxx`;
  * la VERSIONE — una riga della tabella (`id`), con il suo file, il suo `doc:ID` per le citazioni (= sha1 del percorso: cambia a ogni file),
    numero progressivo, data, fonte, autore, motivo e stato (`caricato` → `verificato` → `approvato`);
  * i RECORD del fascicolo (importi, scadenze…): registrare una versione NON li tocca e NON approva i contenuti del documento.

Le versioni si conservano per intero: non si sovrascrive né si cancella nulla. Registrare lo stesso contenuto due volte non crea righe.
I documenti salvati prima della migrazione 010 hanno `documento_id` vuoto: il loro documento logico è la radice della catena `sostituisce_doc`.
"""
from __future__ import annotations

import difflib
import logging
import re
import uuid
from typing import Dict, List, Optional

from . import fascicoli as F
from . import fascicoli_versioni as V

log = logging.getLogger(__name__)

MAX_VERSIONI = 50
_NUM = re.compile(r"\d[\d.]*(?:,\d+)?")


# ── identità: documento logico e versione ─────────────────────────────────────────────────────────────
def sha(d: dict) -> Optional[str]:
    """Impronta del contenuto: quella salvata o, per i documenti vecchi, ricalcolata dal testo estratto (mai quella del testo vuoto)."""
    if d.get("sha256"):
        return str(d["sha256"])
    t = str(d.get("extracted_text") or "").strip()
    return F._sha(t) if t else None


def radice(d: dict, per_id: Dict[str, dict]) -> str:
    """Id del documento logico: `documento_id`, oppure la radice della catena `sostituisce_doc` (documenti anteriori alla 010)."""
    cur, visti = d, set()
    while not cur.get("documento_id") and cur.get("sostituisce_doc") and str(cur["sostituisce_doc"]) in per_id and str(cur["id"]) not in visti:
        visti.add(str(cur["id"]))
        cur = per_id[str(cur["sostituisce_doc"])]
    return str(cur.get("documento_id") or cur["id"])


def sigla(logico: str) -> str:
    return "L-" + str(logico).replace("-", "")[:8]


def gruppi(dd: List[dict]) -> Dict[str, List[dict]]:
    """documento logico → versioni in ordine (la v1 per prima). Le versioni sono SEMPRE tutte conservate."""
    per_id = {str(d["id"]): d for d in dd}
    g: Dict[str, List[dict]] = {}
    for d in dd:
        g.setdefault(radice(d, per_id), []).append(d)
    for lst in g.values():
        lst.sort(key=lambda x: (int(x.get("versione") or 1), str(x.get("created_at") or "")))
    return g


def gruppo_di(dd: List[dict], d: dict) -> List[dict]:
    g = gruppi(dd)
    return g.get(radice(d, {str(x["id"]): x for x in dd}), [d])


def _nome(lst: List[dict]) -> str:
    return str(lst[-1].get("name") or "documento")


def risolvi(dd: List[dict], rif: str) -> Optional[dict]:
    """Un riferimento → {"logico", "versioni", "versione"|None} oppure {"ambiguo": [...]} oppure None.
    Accetta: id di UNA versione (`doc:…`, 12 caratteri, o uuid), sigla/uuid del documento logico (`L-…`), nome del file."""
    r = (rif or "").strip().casefold()
    if r.startswith("doc:"):
        r = r[4:]
    if not r:
        return None
    g = gruppi(dd)
    for logico, lst in g.items():
        for d in lst:
            if r in (F.doc_id_di(d), str(d.get("id")).casefold()) or (len(r) >= 8 and str(d.get("id")).casefold().startswith(r)):
                return {"logico": logico, "versioni": lst, "versione": d}
    for logico, lst in g.items():
        if r in (sigla(logico).casefold(), logico.casefold()) or (r.startswith("l-") and len(r) >= 6 and sigla(logico).casefold().startswith(r)):
            return {"logico": logico, "versioni": lst, "versione": None}
    trovati = [(lg, lst) for lg, lst in g.items() if any(r in str(d.get("name") or "").casefold() for d in lst)]
    if len(trovati) == 1:
        return {"logico": trovati[0][0], "versioni": trovati[0][1], "versione": None}
    if len(trovati) > 1:
        return {"ambiguo": [f"{sigla(lg)} «{_nome(lst)}»" for lg, lst in trovati]}
    return None


def elenco_versioni(lst: List[dict]) -> str:
    """Una riga per versione: id per citare, numero, stato, data, autore, fonte, motivo. È il «recupera tutte le versioni»."""
    righe = []
    for d in lst:
        extra = []
        if d.get("created_at"):
            extra.append(f"registrata il {str(d['created_at'])[:10]}")
        if d.get("autore"):
            extra.append(f"da {d['autore']}")
        if d.get("fonte"):
            extra.append(f"fonte {str(d['fonte'])[:80]}")
        if d.get("motivo"):
            extra.append(f"motivo: {str(d['motivo'])[:120]}")
        righe.append(f"  v{d.get('versione') or 1} — {d.get('name')} [doc:{F.doc_id_di(d)}] stato={d.get('stato') or 'caricato'}" + (" — " + "; ".join(extra) if extra else ""))
    return "\n".join(righe)


def info_versione(user_id: str, path: str) -> Optional[dict]:
    """Per il visualizzatore: di quale documento logico e versione è il file `path` (solo documenti DELL'UTENTE)."""
    rows = F._righe(F.T_DOC, user_id, path=path)
    if not rows:
        return None
    d = rows[0]
    lst = gruppo_di(F.documenti(user_id, str(d["fascicolo_id"])), d)
    return {"versione": int(d.get("versione") or 1), "versioni_totali": len(lst), "documento_logico": sigla(radice(d, {str(x["id"]): x for x in lst})),
            "stato_documento": d.get("stato") or "caricato", "ultima": int(lst[-1].get("versione") or 1),
            "versioni": [{"doc": F.doc_id_di(x), "versione": int(x.get("versione") or 1), "stato": x.get("stato") or "caricato"} for x in lst]}


# ── schema ────────────────────────────────────────────────────────────────────────────────────────────
_SCHEMA: Dict[str, object] = {}


def schema_ok() -> Optional[bool]:
    """True se la migrazione 010 è applicata. Cache 60 s. None se non verificabile."""
    import time
    if time.monotonic() - float(_SCHEMA.get("t", 0)) < 60 and "v" in _SCHEMA:
        return _SCHEMA["v"]  # type: ignore[return-value]
    try:
        F._db().table(F.T_DOC).select("documento_id,motivo,autore,fonte").limit(1).execute()
        v: Optional[bool] = True
    except Exception as e:
        s = str(e)
        v = False if any(k in s for k in ("documento_id", "autore", "does not exist", "42703")) else None
    _SCHEMA.update({"t": time.monotonic(), "v": v})
    return v


def campi_nuovi(logico: str, motivo: str, autore: str, fonte: str) -> dict:
    """Le colonne della 010 solo se esistono: prima dell'applicazione della migrazione il resto continua a funzionare."""
    return {"documento_id": logico, "motivo": motivo or None, "autore": autore, "fonte": fonte or None} if schema_ok() is not False else {}


# ── allegato della conversazione ─────────────────────────────────────────────────────────────────────
def _allegati(c: "F.Contesto") -> List[dict]:
    return list((c.collected or {}).get("uploaded_files") or [])


def _id_allegato(f: dict) -> str:
    from .fonti_documenti import doc_id
    return doc_id(f)


def _scegli_allegato(c: "F.Contesto", rif: str) -> Optional[dict]:
    files = _allegati(c)
    r = (rif or "").strip().casefold()
    if r.startswith("doc:"):
        r = r[4:]
    if r:
        for f in files:
            if r == _id_allegato(f):
                return f
        nomi = [f for f in files if r == str(f.get("name") or "").casefold()] or [f for f in files if r in str(f.get("name") or "").casefold()]
        return nomi[-1] if len(nomi) >= 1 and len({x.get("path") for x in nomi}) == 1 else None
    liberi = [f for f in files if not f.get("dalFascicolo")]
    return liberi[0] if len(liberi) == 1 else None


def _elenco_allegati(c: "F.Contesto") -> str:
    files = _allegati(c)
    return "; ".join(f"«{f.get('name')}» [doc:{_id_allegato(f)}]" for f in files) or "nessuno"


def _esito_ok(d: dict, lst: List[dict], extra: str, logico: str, idem: bool = False) -> dict:
    return {"ok": True, "idempotente": idem, "id": str(d["id"]), "doc": F.doc_id_di(d), "versione": int(d.get("versione") or 1), "logico": logico,
            "dettaglio": extra + "\nVersioni conservate del documento:\n" + elenco_versioni(lst)}


def registra(c: "F.Contesto", fid: str, allegato: str, documento: str, motivo: str, nuovo_documento: bool = False) -> dict:
    """Registra un allegato della conversazione come NUOVA VERSIONE di un documento esistente (o come nuovo documento).
    Chiamare solo dopo `conferma_utente`. Non modifica record, non verifica né approva i contenuti, non cancella versioni."""
    uid = c.user_id
    assert uid
    if schema_ok() is False:
        return {"ok": False, "codice": "MIGRAZIONE_MANCANTE", "dettaglio": "il versionamento dei documenti richiede la migrazione 010 sul database: non ancora applicata. Nulla è stato scritto."}
    f = _scegli_allegato(c, allegato)
    if not f:
        return {"ok": False, "codice": "ALLEGATO_NON_TROVATO",
                "dettaglio": f"indica `allegato` con l'id (doc:…) o il nome di un file allegato in QUESTA conversazione. Allegati disponibili: {_elenco_allegati(c)}."}
    if not f.get("path"):
        return {"ok": False, "codice": "ALLEGATO_NON_SALVATO", "dettaglio": f"«{f.get('name')}» non risulta caricato nell'archivio: non si può registrare."}
    dd = F.documenti(uid, fid)
    testo = str(f.get("extractedText") or f.get("extractedSummary") or "")
    h = F._sha(testo) if testo.strip() else None
    gia = next((d for d in dd if d.get("path") == f["path"]), None) or (next((d for d in dd if sha(d) == h), None) if h else None)
    if gia:                                                         # stesso file o stesso contenuto: NON si crea nulla (idempotenza)
        lst = gruppo_di(dd, gia)
        lg = radice(gia, {str(x["id"]): x for x in dd})
        return _esito_ok(gia, lst, f"GIÀ REGISTRATO: «{f.get('name')}» coincide con la v{gia.get('versione') or 1} del documento {sigla(lg)} «{_nome(lst)}» "
                                   f"(stesso {'file' if gia.get('path') == f['path'] else 'contenuto'}). Non è stata creata nessuna nuova versione.", lg, idem=True)
    bersaglio = None
    if documento:
        bersaglio = risolvi(dd, documento)
        if not bersaglio:
            return {"ok": False, "codice": "DOCUMENTO_NON_TROVATO", "dettaglio": "nessun documento del fascicolo corrisponde a «%s». Documenti: %s." % (documento, "; ".join(
                f"{sigla(lg)} «{_nome(l)}»" for lg, l in gruppi(dd).items()) or "nessuno")}
        if "ambiguo" in bersaglio:
            return {"ok": False, "codice": "AMBIGUO", "dettaglio": "il riferimento è ambiguo: " + "; ".join(bersaglio["ambiguo"]) + ". Ripeti con la sigla L-… o l'id doc:…"}
    elif not nuovo_documento:
        serie = F._serie(f.get("name"))
        simili = [(lg, l) for lg, l in gruppi(dd).items() if (l[0].get("serie") or F._serie(l[0].get("name"))) == serie]
        if simili:
            return {"ok": False, "codice": "AMBIGUO", "dettaglio": f"«{f.get('name')}» sembra una nuova versione di " + "; ".join(f"{sigla(lg)} «{_nome(l)}»" for lg, l in simili)
                    + ". Ripeti con `documento` = la sigla L-… (o l'id doc:…) per aggiungerla come versione, oppure `nuovo_documento`=true se è un documento diverso. Nulla è stato scritto."}
    if bersaglio:
        lst, logico = bersaglio["versioni"], bersaglio["logico"]
        if len(lst) >= MAX_VERSIONI:
            return {"ok": False, "codice": "LIMITE", "dettaglio": f"il documento ha già {MAX_VERSIONI} versioni."}
        ver = max(int(d.get("versione") or 1) for d in lst) + 1
        serie, prec = lst[0].get("serie") or F._serie(lst[0].get("name")), lst[-1]
    else:
        logico, ver, serie, prec, lst = str(uuid.uuid4()), 1, F._serie(f.get("name")), None, []
    fonte = f"chat:{c.session_id or '-'}:{f.get('name')}"
    riga = {"fascicolo_id": fid, "user_id": uid, "name": f.get("name") or "documento", "type": f.get("type"), "size": f.get("size"), "path": f["path"],
            "extracted_text": testo, "extraction_method": f.get("extractionMethod"), "source_session": c.session_id or None, "versione": ver, "serie": serie,
            "sha256": h, "stato": "caricato", "sostituisce_doc": prec["id"] if prec else None, **campi_nuovi(logico, motivo, "utente", fonte)}
    try:
        nuova = F._db().table(F.T_DOC).insert(riga).execute().data[0]
    except Exception as e:                                           # due richieste insieme: il vincolo univoco ne lascia passare una sola
        if "duplicate" in str(e).lower() or "23505" in str(e) or "unique" in str(e).lower():
            dd2 = F.documenti(uid, fid)
            gia = next((d for d in dd2 if d.get("path") == f["path"] or (h and sha(d) == h)), None)
            if gia:
                l2 = gruppo_di(dd2, gia)
                return _esito_ok(gia, l2, f"GIÀ REGISTRATO (richiesta concorrente): v{gia.get('versione') or 1} del documento {sigla(radice(gia, {str(x['id']): x for x in dd2}))}.",
                                 radice(gia, {str(x["id"]): x for x in dd2}), idem=True)
        raise
    V.evento(uid, fid, None, "documento", None, {"doc": F.doc_id_di(nuova), "documento_logico": logico, "versione": ver, "nome": f.get("name"),
                                                  "sostituisce": str(prec["id"]) if prec else None, "sha": (h or "")[:12]}, motivo or "versione registrata", "utente")
    # la conversazione ora sa che quell'allegato è una versione del fascicolo (citazioni e visualizzatore leggono dallo stesso file)
    f["dalFascicolo"], f["versione"], f["documentoLogico"] = fid, ver, sigla(logico)
    dd3 = F.documenti(uid, fid)                                     # rilegge dal database: l'esito riporta ciò che c'è davvero
    l3 = gruppo_di(dd3, nuova)
    quando = f"v{ver} del documento {sigla(logico)} «{_nome(l3)}»" if prec else f"NUOVO documento {sigla(logico)} «{f.get('name')}» (v1)"
    return _esito_ok(nuova, l3, f"Registrata come {quando}. Stato: caricato — i CONTENUTI non sono verificati né approvati, e NESSUN record del fascicolo (importi, scadenze…) è stato modificato. "
                                f"{'La v%s resta conservata. ' % (ver - 1) if prec else ''}Per vedere le differenze usa fascicolo_documento con confronta_con; per aggiornare i record usa fascicolo_aggiorna dopo la conferma dell'utente.", logico)


# ── recupero e confronto ─────────────────────────────────────────────────────────────────────────────
def _righe_testo(d: dict) -> List[str]:
    return [re.sub(r"\s+", " ", r).strip() for r in str(d.get("extracted_text") or "").splitlines() if r.strip()]


def confronta(a: dict, b: dict, max_coppie: int = 30) -> str:
    """Differenze fra due versioni: righe cambiate (prima → dopo), righe solo in una, numeri che compaiono/spariscono."""
    ra, rb = _righe_testo(a), _righe_testo(b)
    intest = f"CONFRONTO v{a.get('versione') or 1} [doc:{F.doc_id_di(a)}] → v{b.get('versione') or 1} [doc:{F.doc_id_di(b)}]"
    if ra == rb:
        return intest + ": i testi estratti sono IDENTICI."
    sm = difflib.SequenceMatcher(None, ra, rb, autojunk=False)
    cambi, solo_a, solo_b = [], [], []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "replace":
            for x, y in zip(ra[i1:i2], rb[j1:j2]):
                cambi.append(f"  «{x[:160]}» → «{y[:160]}»")
            solo_a += ra[i1 + (j2 - j1):i2] if i2 - i1 > j2 - j1 else []
            solo_b += rb[j1 + (i2 - i1):j2] if j2 - j1 > i2 - i1 else []
        elif tag == "delete":
            solo_a += ra[i1:i2]
        elif tag == "insert":
            solo_b += rb[j1:j2]
    na, nb = {x for x in _NUM.findall(" ".join(ra)) if len(x) >= 3}, {x for x in _NUM.findall(" ".join(rb)) if len(x) >= 3}
    out = [intest + f": {len(cambi)} righe modificate, {len(solo_a)} presenti solo nella prima, {len(solo_b)} solo nella seconda."]
    if cambi:
        out += ["Righe modificate (prima → dopo):"] + cambi[:max_coppie]
    if solo_a:
        out += ["Solo nella prima:"] + [f"  - {x[:160]}" for x in solo_a[:12]]
    if solo_b:
        out += ["Solo nella seconda:"] + [f"  + {x[:160]}" for x in solo_b[:12]]
    if na - nb or nb - na:
        out.append("Numeri spariti: " + (", ".join(sorted(na - nb)[:15]) or "—") + " | numeri nuovi: " + (", ".join(sorted(nb - na)[:15]) or "—"))
    out.append("Il confronto è sul testo estratto e NON modifica nulla: i record del fascicolo restano invariati finché l'utente non conferma un aggiornamento.")
    return "\n".join(out)
