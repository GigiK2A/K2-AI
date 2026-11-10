"""Memoria aziendale: fascicoli persistenti (commesse, clienti, contratti…) con voci tracciate e documenti.

Principi (audit 7):
  * ISOLAMENTO NEL CODICE: ogni lettura/scrittura passa da `_q(user_id)`; senza utente nessuno strumento è offerto. Un id di un altro
    utente risponde «non trovato», mai «non autorizzato» (non si rivela l'esistenza).
  * SCRITTURE SOLO CON CONFERMA DELL'UTENTE, verificata dal codice sul messaggio dell'utente (non sulla parola del modello):
    un documento o una pagina web che dicono «salva questo» non possono scrivere nulla.
  * OGNI VOCE HA FONTE, DATA E STATO DI VERIFICA; un valore diverso per la stessa chiave segna entrambe «contraddittorio».
  * Nel contesto del modello entra solo un sommario limitato (non l'intero archivio).
"""
from __future__ import annotations

import contextvars
import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from . import fascicoli_versioni as V
from .supabase_admin import get_admin_client

log = logging.getLogger(__name__)

T_FASC, T_VOCI, T_DOC = "kbot_fascicoli", "kbot_fascicolo_voci", "kbot_fascicolo_documenti"
TIPI_FASCICOLO = {"commessa", "cliente", "fornitore", "contratto", "controversia", "consulenza", "progetto", "investimento"}
TIPI_VOCE = {"dato", "decisione", "scadenza", "analisi", "anomalia", "nota", "attivita"}
MAX_VOCI_PER_SALVATAGGIO = 12
MAX_BLOCCO = 2600


@dataclass
class Contesto:
    user_id: Optional[str]
    session_id: str = ""
    ultimo_utente: str = ""
    ultimo_assistente: str = ""
    collected: Dict[str, Any] = field(default_factory=dict)
    salvataggi: int = 0


_CTX: contextvars.ContextVar[Optional[Contesto]] = contextvars.ContextVar("kbot_fascicoli_ctx", default=None)


def inizia_turno(user_id: Optional[str], session_id: str, ultimo_utente: str, ultimo_assistente: str, collected: dict) -> None:
    _CTX.set(Contesto(user_id=user_id or None, session_id=str(session_id or ""), ultimo_utente=ultimo_utente or "",
                      ultimo_assistente=ultimo_assistente or "", collected=collected))


def contesto() -> Optional[Contesto]:
    return _CTX.get()


def disponibile() -> bool:
    c = _CTX.get()
    return bool(c and c.user_id) and os.environ.get("KBOT_FASCICOLI", "1") != "0"


_SCHEMA_OK: Dict[str, Any] = {}


def schema_versioni_ok() -> Optional[bool]:
    """True se la migrazione 008 è applicata (colonne `stato_record`, tabella eventi). Cache 60 s. None se non verificabile."""
    import time
    t = _SCHEMA_OK.get("t", 0)
    if time.monotonic() - t < 60 and "v" in _SCHEMA_OK:
        return _SCHEMA_OK["v"]
    try:
        _db().table(T_VOCI).select("stato_record,revisione").limit(1).execute()
        _db().table("kbot_fascicolo_eventi").select("id").limit(1).execute()
        v: Optional[bool] = True
    except Exception as e:
        v = False if "stato_record" in str(e) or "revisione" in str(e) or "kbot_fascicolo_eventi" in str(e) or "does not exist" in str(e) else None
    _SCHEMA_OK.update({"t": time.monotonic(), "v": v})
    return v


def _db():
    return get_admin_client()


def _ora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _righe(tabella: str, user_id: str, **eq: Any) -> List[dict]:
    q = _db().table(tabella).select("*").eq("user_id", user_id)
    for k, v in eq.items():
        q = q.eq(k, v)
    return [r for r in (q.execute().data or []) if not r.get("deleted_at")]


# ── lettura ────────────────────────────────────────────────────────────────────────────────────────────
def elenco(user_id: str, limite: int = 200) -> List[dict]:
    r = _righe(T_FASC, user_id)
    r.sort(key=lambda x: str(x.get("updated_at") or ""), reverse=True)
    return r[:limite]


def trova(user_id: str, rif: str) -> Optional[dict]:
    """Per id o per codice (senza distinguere maiuscole). Solo fascicoli dell'utente."""
    rif = (rif or "").strip()
    if not rif:
        return None
    for f in elenco(user_id):
        if str(f.get("id")) == rif or str(f.get("codice") or "").casefold() == rif.casefold():
            return f
    return None


def voci(user_id: str, fascicolo_id: str) -> List[dict]:
    v = _righe(T_VOCI, user_id, fascicolo_id=fascicolo_id)
    v.sort(key=lambda x: str(x.get("created_at") or ""))
    return v


def documenti(user_id: str, fascicolo_id: str) -> List[dict]:
    return _righe(T_DOC, user_id, fascicolo_id=fascicolo_id)


def cerca(user_id: str, query: str) -> List[dict]:
    q = [t for t in re.findall(r"\w{2,}", (query or "").casefold())]
    out = []
    for f in elenco(user_id):
        testo = " ".join([str(f.get("codice") or ""), str(f.get("titolo") or ""), str(f.get("tipo") or "")])
        if q:
            vv = voci(user_id, str(f["id"]))
            testo += " " + " ".join(f"{v.get('testo', '')} {v.get('valore') or ''}" for v in vv)
            punti = sum(1 for t in q if t in testo.casefold())
            if not punti:
                continue
        else:
            punti = 0
        out.append((punti, f))
    out.sort(key=lambda x: -x[0])
    return [f for _p, f in out[:8]]


# ── scrittura ──────────────────────────────────────────────────────────────────────────────────────────
_VERBI_SALVA = re.compile(r"\b(salva\w*|registra\w*|memorizza\w*|aggiung\w*|inserisc\w*|tieni\s+traccia|archivia\w*|crea\w*\s+(?:il\s+|un\s+)?fascicolo|apri\w*\s+(?:il\s+|un\s+)?fascicolo"
                          r"|consolid\w*|sostitu\w*|aggiorn\w*|contest\w*|conferm\w*|approv\w*|segn\w*|imposta\w*|scart\w*|procedi|fai\s+pure)\b", re.I)
_SI = re.compile(r"^\s*(?:s[ìi]|ok|okay|va\s+bene|certo|confermo|conferma|procedi|d['’]accordo|perfetto|fallo|esatto)\b", re.I)
_NO = re.compile(r"\b(?:non\s+(?:salvare|registrare|memorizzare|aggiungere|archiviare)|no\b|niente)\b", re.I)


def conferma_utente(ctx: Optional[Contesto]) -> bool:
    """True solo se il MESSAGGIO DELL'UTENTE chiede di salvare, o conferma una proposta di salvataggio fatta nel turno precedente."""
    if not ctx:
        return False
    u = ctx.ultimo_utente or ""
    if _NO.search(u):
        return False
    if _VERBI_SALVA.search(u):
        return True
    a = (ctx.ultimo_assistente or "").casefold()
    return bool(_SI.match(u) and "fascicolo" in a and re.search(r"salv|registr|aggiung|memoriz|archivi|aprire|creare|consolid|sostitu|aggiorn|contest|approv|segnar", a))


def _num(x: Any) -> str:
    return re.sub(r"[^\d,.\-]", "", str(x or "")).replace(".", "").replace(",", ".")


def salva(ctx: Contesto, *, fascicolo: str = "", tipo: str = "commessa", codice: str = "", titolo: str = "", stato: str = "",
          voci_in: Optional[List[dict]] = None, allega_documenti: bool = False) -> dict:
    """Crea/aggiorna un fascicolo e aggiunge voci. Chiamare solo dopo `conferma_utente`."""
    uid = ctx.user_id
    assert uid
    f = trova(uid, fascicolo or codice) if (fascicolo or codice) else None
    nuovo = False
    if not f:
        if not (titolo or codice):
            return {"ok": False, "errore": "fascicolo inesistente: indica codice e titolo per crearlo"}
        t = tipo if tipo in TIPI_FASCICOLO else "commessa"
        riga = {"user_id": uid, "tipo": t, "codice": (codice or "").strip() or None, "titolo": (titolo or codice).strip()[:200], "stato": "aperto"}
        f = _db().table(T_FASC).insert(riga).execute().data[0]
        nuovo = True
    elif stato in ("aperto", "in_corso", "chiuso") and stato != f.get("stato"):
        _db().table(T_FASC).update({"stato": stato, "updated_at": _ora()}).eq("id", f["id"]).eq("user_id", uid).execute()
        f = {**f, "stato": stato}
    fid = str(f["id"])
    esistenti = voci(uid, fid)
    salvate, avvisi = [], []
    esiti = {"creata": 0, "duplicato": 0, "fonte_aggiunta": 0, "proposta": 0}
    for v in (voci_in or [])[:MAX_VOCI_PER_SALVATAGGIO]:
        r = V.inserisci(ctx, fid, v, esistenti, attore="modello")
        if r["esito"] in esiti:
            esiti[r["esito"]] += 1
        if r["esito"] in ("creata", "proposta"):
            salvate.append(r["id"])
        if r.get("dettaglio") and r["esito"] in ("proposta", "fonte_aggiunta"):
            avvisi.append(r["dettaglio"])
    n_doc, note_doc = 0, []
    if allega_documenti:
        n_doc, note_doc = _allega_documenti(ctx, fid)
        avvisi += note_doc
    _db().table(T_FASC).update({"updated_at": _ora()}).eq("id", fid).eq("user_id", uid).execute()
    return {"ok": True, "fascicolo": fid, "codice": f.get("codice"), "titolo": f.get("titolo"), "nuovo": nuovo,
            "voci_salvate": len(salvate), "documenti_allegati": n_doc, "avvisi": avvisi, "esiti": esiti, "id_salvati": [str(i) for i in salvate]}


def _serie(nome: str) -> str:
    """Nome senza estensione, numero di versione, data e suffissi «rev/final»: stessa serie = versioni dello stesso documento."""
    n = re.sub(r"\.[A-Za-z0-9]{2,4}$", "", str(nome or "")).casefold()
    n = re.sub(r"[-_ .]*(?:v|ver|versione|rev|revisione)[-_ .]?\d+\b", " ", n)
    n = re.sub(r"\b(?:final[ei]?|definitiv[oa]|nuov[oa]|aggiornat[oa]|copia)\b", " ", n)
    n = re.sub(r"\d{1,4}[-_./]\d{1,2}[-_./]\d{1,4}", " ", n)
    return re.sub(r"[^a-z0-9]+", "-", n).strip("-") or "documento"


def _sha(t: str) -> str:
    import hashlib
    return hashlib.sha256(re.sub(r"\s+", " ", t or "").strip().encode("utf-8")).hexdigest()


def _allega_documenti(ctx: Contesto, fid: str) -> Tuple[int, List[str]]:
    """Conserva i documenti della conversazione nel fascicolo. Stesso testo già presente → non si duplica; stessa serie → nuova versione."""
    uid = ctx.user_id
    assert uid
    esistenti = documenti(uid, fid)
    gia = {d.get("path") for d in esistenti}
    n, note = 0, []
    for f in (ctx.collected or {}).get("uploaded_files") or []:
        if f.get("dalFascicolo") or not f.get("path") or f["path"] in gia:
            continue
        testo = f.get("extractedText") or f.get("extractedSummary") or ""
        sha, serie = _sha(testo), _serie(f.get("name"))
        if testo and any(d.get("sha256") == sha for d in esistenti):
            note.append(f"«{f.get('name')}» ha lo stesso contenuto di un documento già in fascicolo: non duplicato")
            continue
        prec = sorted([d for d in esistenti if (d.get("serie") or _serie(d.get("name"))) == serie], key=lambda d: int(d.get("versione") or 1))
        ver = int(prec[-1].get("versione") or 1) + 1 if prec else 1
        r = _db().table(T_DOC).insert({"fascicolo_id": fid, "user_id": uid, "name": f.get("name") or "documento", "type": f.get("type"),
                                       "size": f.get("size"), "path": f["path"], "extracted_text": testo, "extraction_method": f.get("extractionMethod"),
                                       "source_session": ctx.session_id or None, "versione": ver, "serie": serie, "sha256": sha, "stato": "caricato",
                                       "sostituisce_doc": prec[-1]["id"] if prec else None}).execute().data[0]
        esistenti.append(r)
        V.evento(uid, fid, None, "documento", None, {"doc": doc_id_di(r), "versione": ver, "nome": f.get("name")}, "documento conservato", "modello")
        if prec:
            note.append(f"«{f.get('name')}» è la versione {ver} di «{prec[-1].get('name')}» (la v{prec[-1].get('versione') or 1} resta conservata)")
        n += 1
    return n, note


def doc_id_di(d: dict) -> str:
    import hashlib
    return hashlib.sha1(str(d.get("path") or d.get("name") or "").encode("utf-8")).hexdigest()[:12]


def trova_documento(uid: str, fid: str, rif: str) -> Optional[dict]:
    rif = (rif or "").strip().casefold()
    dd = documenti(uid, fid)
    for d in dd:
        if rif and (doc_id_di(d) == rif or str(d.get("id")) == rif):
            return d
    c = [d for d in dd if rif and rif in str(d.get("name") or "").casefold()]
    return sorted(c, key=lambda d: int(d.get("versione") or 1))[-1] if c else None


def documento_dell_utente(user_id: str, doc_id: str) -> Optional[dict]:
    """Un documento di un fascicolo DELL'UTENTE per id (`doc_id_di`); altrimenti None. Mai documenti di altri utenti."""
    for d in _righe(T_DOC, user_id):
        if doc_id_di(d) == doc_id:
            return d
    return None


def collega_documento(ctx: Contesto, d: dict) -> None:
    """Rende UN documento del fascicolo disponibile nella conversazione (testo, citazioni, visualizzatore) senza ricaricarlo."""
    col = ctx.collected
    if any(x.get("path") == d.get("path") for x in col.get("uploaded_files") or []):
        return
    col.setdefault("uploaded_files", []).append({"name": d.get("name"), "type": d.get("type") or "", "size": d.get("size") or 0, "path": d["path"],
                                                 "publicUrl": "", "extractedText": d.get("extracted_text") or "", "extractedSummary": "",
                                                 "extractionMethod": d.get("extraction_method") or "", "dalFascicolo": str(d.get("fascicolo_id") or "1"),
                                                 "sorgenteSessione": str(d.get("source_session") or "")})


def passaggi_documento(ctx: Contesto, d: dict, query: str, k: int = 5) -> List[dict]:
    """Passaggi pertinenti di un documento del fascicolo: con le pagine se i chunk della sessione di origine esistono, altrimenti a «parti»."""
    from . import rag
    chunks: List[dict] = []
    if d.get("source_session"):
        chunks = [c for c in rag.fetch_chunks(str(d["source_session"])) if str(c.get("file_name") or "").casefold() == str(d.get("name") or "").casefold()]
    if not chunks:
        chunks = rag.chunk_da_file(str(d.get("source_session") or ""), [{"name": d.get("name"), "extractedText": d.get("extracted_text")}])
    return rag.bm25_top_k(query or "", chunks, k=k) if query else chunks[:k]


def collega(ctx: Contesto, f: dict) -> int:
    """Collega la conversazione al fascicolo. I documenti NON si caricano tutti: restano nel fascicolo e si aprono a richiesta
    (`fascicolo_documento`), così il contesto e collected_data non crescono con ogni file. Ritorna il numero di documenti disponibili."""
    uid = ctx.user_id
    assert uid
    ctx.collected["fascicolo_id"] = str(f["id"])
    return len(documenti(uid, str(f["id"])))


def elimina_voce(user_id: str, fascicolo_id: str, voce_id: str) -> bool:
    if not any(str(v.get("id")) == voce_id for v in voci(user_id, fascicolo_id)):
        return False
    _db().table(T_VOCI).update({"deleted_at": _ora()}).eq("id", voce_id).eq("user_id", user_id).execute()
    return True


def correggi_voce(user_id: str, fascicolo_id: str, voce_id: str, patch: dict) -> bool:
    if not any(str(v.get("id")) == voce_id for v in voci(user_id, fascicolo_id)):
        return False
    ok = {k: patch[k] for k in ("testo", "valore", "verifica") if k in patch}
    if ok.get("verifica") and ok["verifica"] not in ("confermato", "non_verificato", "contraddittorio"):
        return False
    ok["data_verifica"] = _ora()
    _db().table(T_VOCI).update(ok).eq("id", voce_id).eq("user_id", user_id).execute()
    return True


def elimina_fascicolo(user_id: str, fascicolo_id: str) -> bool:
    if not trova(user_id, fascicolo_id):
        return False
    _db().table(T_FASC).update({"deleted_at": _ora()}).eq("id", fascicolo_id).eq("user_id", user_id).execute()
    return True


# ── presentazione al modello ───────────────────────────────────────────────────────────────────────────
def _riga_voce(v: dict) -> str:
    return V.riga(v)


def _riga_doc(d: dict) -> str:
    return f"{d.get('name')} [doc:{doc_id_di(d)}] v{d.get('versione') or 1} ({d.get('stato') or 'caricato'})"


MAX_CARATTERI_APRI = 12000
PER_PAGINA = 40


def formatta_fascicolo(user_id: str, f: dict, max_voci: int = PER_PAGINA, con_superate: bool = False, da: int = 0,
                       tipo: str = "", cerca_testo: str = "") -> str:
    """Il fascicolo per il modello. MAI troncato in silenzio: se non entra tutto dice «mostrati N–M di T» e come chiedere il resto (`da`)."""
    vv = voci(user_id, str(f["id"]))
    dd = documenti(user_id, str(f["id"]))
    n_sup = sum(1 for v in vv if V.stato_di(v) in ("superata", "archiviata"))
    mostra = vv if con_superate else [v for v in vv if V.stato_di(v) in V.ATTIVI]
    if tipo:
        mostra = [v for v in mostra if v.get("tipo") == tipo]
    if cerca_testo:
        q = cerca_testo.casefold()
        mostra = [v for v in mostra if q in f"{v.get('chiave') or ''} {v.get('testo') or ''} {v.get('valore') or ''}".casefold() or str(v["id"]).startswith(q)]
    totale = len(mostra)
    da = max(0, int(da or 0))
    righe = [f"FASCICOLO {f.get('codice') or '(senza codice)'} — {f.get('titolo')} [{f.get('tipo')}, {f.get('stato')}] id={f['id']}"]
    corpo, usati = [], 0
    budget = MAX_CARATTERI_APRI - 1500
    for v in mostra[da:da + max(1, max_voci)]:
        r = _riga_voce(v)
        if usati + len(r) > budget and corpo:
            break
        corpo.append(r)
        usati += len(r) + 1
    righe += corpo or ["(nessun record attuale)"]
    if corpo and da + len(corpo) < totale:
        righe.append(f"[PARZIALE: mostrati i record {da + 1}–{da + len(corpo)} di {totale}. Per il resto richiama fascicolo_apri con da={da + len(corpo)} (o filtra con tipo/cerca_testo).]")
    elif corpo:
        righe.append(f"[COMPLETO: {da + 1}–{da + len(corpo)} di {totale} record.]")
    if n_sup and not con_superate:
        righe.append(f"({n_sup} record superati/archiviati nello storico: usa fascicolo_voce con azione «storico» o con_superate=true)")
    if dd:
        per_serie: Dict[str, List[dict]] = {}
        for d in dd:
            per_serie.setdefault(d.get("serie") or _serie(d.get("name")), []).append(d)
        for serie, lst in per_serie.items():
            lst.sort(key=lambda d: int(d.get("versione") or 1))
            ult = lst[-1]
            verif = [d for d in lst if d.get("stato") in ("verificato", "approvato")]
            appr = [d for d in lst if d.get("stato") == "approvato"]
            righe.append(f"Documento {serie}: ultima ricevuta {_riga_doc(ult)}"
                         + (f"; ultima verificata v{verif[-1].get('versione') or 1}" if verif else "; nessuna versione verificata")
                         + (f"; approvata v{appr[-1].get('versione') or 1}" if appr else "; nessuna approvata")
                         + " — apribile con fascicolo_documento; i valori «attuali» sono quelli in uso nei calcoli")
    contest = [v for v in vv if V.stato_di(v) == "contestata"]
    prop = [v for v in vv if V.stato_di(v) == "da_verificare" and v.get("sostituisce")]
    if contest:
        righe.append(f"ATTENZIONE: {len(contest)} record contestati — segnalalo e chiedi quale è corretto.")
    if prop:
        righe.append(f"{len(prop)} proposte di aggiornamento in attesa di conferma dell'utente.")
    return "\n".join(righe)


def blocco_prompt() -> str:
    """Sommario per il prompt: fascicolo collegato (breve) oppure l'elenco dei fascicoli dell'utente. Fail-open."""
    c = _CTX.get()
    if not (c and c.user_id) or os.environ.get("KBOT_FASCICOLI", "1") == "0":
        return ""
    try:
        fid = (c.collected or {}).get("fascicolo_id")
        f = trova(c.user_id, str(fid)) if fid else None
        if f:
            return ("\n\nFASCICOLO COLLEGATO A QUESTA CONVERSAZIONE (memoria aziendale dell'utente):\n"
                    + formatta_fascicolo(c.user_id, f, 10) + "\nI documenti non sono nel contesto: aprili con `fascicolo_documento`. Per salvare o aggiornare usa gli strumenti `fascicolo_*` SOLO dopo che l'utente ha chiesto o confermato.\n")[:MAX_BLOCCO]
        lista = elenco(c.user_id, 8)
        if not lista:
            return "\n\nMEMORIA AZIENDALE: l'utente non ha ancora fascicoli. Se emerge una commessa/cliente/contratto da seguire nel tempo, proponi di aprirne uno (e salva solo dopo il sì).\n"
        elenco_txt = "; ".join(f"{x.get('codice') or x.get('titolo')} ({x.get('tipo')}, {x.get('stato')})" for x in lista)
        return f"\n\nMEMORIA AZIENDALE — fascicoli dell'utente: {elenco_txt}. Se l'utente cita una di queste pratiche, usa `fascicolo_cerca`/`fascicolo_apri` e `fascicolo_collega` invece di chiedergli di nuovo i dati; non sono nel contesto finché non li apri.\n"[:MAX_BLOCCO]
    except Exception:
        log.warning("blocco fascicoli non disponibile (fail-open)", exc_info=True)
        return ""


# ── strumenti del modello ──────────────────────────────────────────────────────────────────────────────
NOMI = ("fascicolo_cerca", "fascicolo_apri", "fascicolo_collega", "fascicolo_salva", "fascicolo_aggiorna", "fascicolo_voce", "fascicolo_confronta", "fascicolo_duplicati", "fascicolo_documento")
_NUOVO = {"tipo": {"type": "string", "enum": sorted(TIPI_VOCE)}, "testo": {"type": "string", "description": "Cosa si registra, in una frase."},
          "chiave": {"type": "string", "description": "Nome STABILE del dato (es. imponibile_dichiarato, pratiche_protocollate): serve a riconoscere duplicati e cambi di valore."},
          "valore": {"type": "string"}, "unita": {"type": "string", "description": "es. EUR, pratiche"}, "periodo": {"type": "string"},
          "contesto": {"type": "string", "description": "SOLO un'etichetta breve (max 40 caratteri) della prestazione/voce di contratto. Non scriverci note o provenienza."},
          "origine": {"type": "string", "enum": ["letto_da_documento", "dichiarato_utente", "calcolato"]},
          "stato": {"type": "string", "enum": ["attuale", "da_verificare"], "description": "da_verificare per revisioni solo dichiarate"},
          "doc": {"type": "string", "description": "ID documento dell'estratto da cui viene il dato."}, "pag": {"type": "integer"},
          "quote": {"type": "string", "description": "Testo copiato dal documento."}}


def definizioni() -> List[dict]:
    voce = {"type": "object", "properties": _NUOVO, "required": ["testo"]}
    voce_c = {"type": "object", "properties": {k: _NUOVO[k] for k in ("tipo", "testo", "chiave", "valore", "unita", "periodo", "contesto")}}
    return [
        {"name": "fascicolo_cerca", "description": "Cerca fra i fascicoli dell'utente (commesse, clienti, contratti…) per codice, titolo o contenuto.",
         "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}}},
        {"name": "fascicolo_apri", "description": "Apre un fascicolo (id o codice): record ATTUALI con stato, verifica, origine e fonti; documenti con versione. `alla_data` (AAAA-MM-GG) mostra cosa era valido allora.",
         "input_schema": {"type": "object", "properties": {"fascicolo": {"type": "string"}, "alla_data": {"type": "string"}, "con_superate": {"type": "boolean"},
                                                           "da": {"type": "integer", "description": "indice del primo record (paginazione: l'output dice se è PARZIALE)"},
                                                           "tipo": {"type": "string", "enum": sorted(TIPI_VOCE)}, "cerca_testo": {"type": "string"}}, "required": ["fascicolo"]}},
        {"name": "fascicolo_collega", "description": "Collega QUESTA conversazione a un fascicolo (non carica i documenti: si aprono con fascicolo_documento).",
         "input_schema": {"type": "object", "properties": {"fascicolo": {"type": "string"}}, "required": ["fascicolo"]}},
        {"name": "fascicolo_salva", "description": (
            "Crea un fascicolo o vi aggiunge informazioni NUOVE (per cambiare un record esistente usa fascicolo_aggiorna). Il sistema evita i duplicati (stesso valore: aggiunge solo la fonte) e, se il valore è DIVERSO da quello corrente, "
            "crea una PROPOSTA «da_verificare» senza sostituire nulla. Funziona SOLO se l'utente lo ha chiesto o confermato nel suo ultimo messaggio."),
         "input_schema": {"type": "object", "properties": {
             "fascicolo": {"type": "string"}, "tipo": {"type": "string", "enum": sorted(TIPI_FASCICOLO)}, "codice": {"type": "string"}, "titolo": {"type": "string"},
             "stato": {"type": "string", "enum": ["aperto", "in_corso", "chiuso"]}, "voci": {"type": "array", "items": voce}, "allega_documenti": {"type": "boolean"}}}},
        {"name": "fascicolo_aggiorna", "description": (
            "CAMBIA il valore di un record GIÀ ESISTENTE (id a 6+ caratteri, da fascicolo_apri) mantenendone l'ID: il valore precedente resta nello storico. NON crea mai record. "
            "Usalo per ogni «aggiorna/modifica/correggi l'importo di…»: fascicolo_salva serve solo per informazioni NUOVE. Idempotente (stesso valore = nessuna modifica). "
            "`revisione_attesa` (la rev mostrata da fascicolo_apri) protegge da modifiche concorrenti. Richiede la conferma dell'utente."),
         "input_schema": {"type": "object", "properties": {"fascicolo": {"type": "string"}, "record": {"type": "string", "description": "id del record da aggiornare"},
                                                           "valore": {"type": "string", "description": "nuovo valore"}, "testo": {"type": "string"}, "unita": {"type": "string"},
                                                           "motivo": {"type": "string", "description": "perché cambia (obbligatorio)"}, "revisione_attesa": {"type": "integer"},
                                                           "doc": {"type": "string"}, "pag": {"type": "integer"}, "quote": {"type": "string"}},
                          "required": ["fascicolo", "record", "motivo"]}},
        {"name": "fascicolo_voce", "description": (
            "Operazioni su un record (id a 6+ caratteri). `storico`: tutte le versioni e la cronologia (anche solo `alla_data`). Le altre MODIFICANO e richiedono la conferma "
            "dell'utente: `sostituisci` (conferma una proposta: il vecchio valore diventa superato, resta nello storico), `contesta`, `archivia`/`scarta`, `conferma` (soggetto autorizzato), `verifica_esterna`."),
         "input_schema": {"type": "object", "properties": {"fascicolo": {"type": "string"}, "azione": {"type": "string", "enum": ["storico", "sostituisci", "contesta", "archivia", "scarta", "conferma", "verifica_esterna"]},
                                                           "record": {"type": "string", "description": "id (o parte del testo, solo per storico)"}, "motivo": {"type": "string"}, "alla_data": {"type": "string"}},
                          "required": ["fascicolo", "azione"]}},
        {"name": "fascicolo_confronta", "description": "Confronta i valori di una NUOVA versione/revisione con quelli del fascicolo (sola lettura): invariati, diversi, nuovi, assenti. Non modifica nulla.",
         "input_schema": {"type": "object", "properties": {"fascicolo": {"type": "string"}, "valori": {"type": "array", "items": voce_c}, "documento_caricato": {"type": "boolean", "description": "true solo se il nuovo documento è davvero stato caricato"}},
                          "required": ["fascicolo", "valori"]}},
        {"name": "fascicolo_duplicati", "description": "`elenca`: gruppi di record duplicati con fonti e differenze, e quale tenere. `consolida`: archivia i duplicati unendone le fonti (nulla si cancella; annullabile) — richiede conferma dell'utente.",
         "input_schema": {"type": "object", "properties": {"fascicolo": {"type": "string"}, "azione": {"type": "string", "enum": ["elenca", "consolida"]}}, "required": ["fascicolo", "azione"]}},
        {"name": "fascicolo_documento", "description": (
            "Recupera un documento conservato nel fascicolo (id `doc:…` o nome; l'ultima versione se ce ne sono più): metadati, versioni e i passaggi pertinenti a `query`, "
            "con id e pagina per citarli [[fonte|…]]; l'utente potrà aprirlo nel visualizzatore. `imposta_stato` (verificato/approvato) richiede la conferma dell'utente."),
         "input_schema": {"type": "object", "properties": {"fascicolo": {"type": "string"}, "documento": {"type": "string"}, "query": {"type": "string"}, "imposta_stato": {"type": "string", "enum": ["caricato", "verificato", "approvato"]}},
                          "required": ["fascicolo", "documento"]}},
    ]


SYSTEM_HINT = (
    "\n\nSTRUMENTI MEMORIA AZIENDALE (`fascicolo_*`): i fascicoli persistono fra le conversazioni. Leggi con cerca/apri; apri i documenti con `fascicolo_documento` (recupero mirato). "
    "SCRIVI solo dopo che l'utente ha chiesto o confermato: prima mostra il riepilogo di cosa salveresti/cambieresti (valori, fonti) e aspetta il sì; se il sistema risponde «NON SALVATO/NON ESEGUITO», "
    "chiedi conferma, non ritentare. PER CAMBIARE un record esistente: `fascicolo_apri` (id e rev) poi `fascicolo_aggiorna` — mai `fascicolo_salva`, che serve solo per informazioni nuove; se l'aggiornamento "
    "fallisce, riferisci l'errore: NON creare un record nuovo come ripiego. Un valore DIVERSO salvato con fascicolo_salva non sovrascrive: diventa proposta, e si sostituisce solo con la conferma (`fascicolo_voce` «sostituisci»). Una revisione solo dichiarata "
    "(senza nuovo documento) resta «da_verificare». Non scegliere da solo il valore più recente: distingui ultimo documento ricevuto, verificato, approvato e valore in uso. "
    "Riporta sempre stato, origine e fonte dei dati; non dire di aver salvato o modificato se lo strumento non lo conferma.\n")


def _fascicolo(c: Contesto, a: dict) -> Optional[dict]:
    return trova(c.user_id, str(a.get("fascicolo") or ""))


def _senza_conferma(cosa: str) -> str:
    return (f"NON ESEGUITO: manca la conferma esplicita dell'utente nel suo ultimo messaggio. Mostragli il riepilogo ({cosa}) e chiedigli se procedere.")


def esegui(nome: str, args: dict) -> str:
    c = _CTX.get()
    if not (c and c.user_id):
        return "[memoria aziendale non disponibile: serve un utente autenticato]"
    a = args if isinstance(args, dict) else {}
    try:
        if nome == "fascicolo_cerca":
            r = cerca(c.user_id, str(a.get("query") or ""))
            return "Nessun fascicolo trovato." if not r else "\n".join(f"- {f.get('codice') or '—'} | {f.get('titolo')} | {f.get('tipo')} | {f.get('stato')} | id={f['id']}" for f in r)
        if nome == "fascicolo_salva":
            if not conferma_utente(c):
                return ("NON SALVATO: manca la conferma esplicita dell'utente nel suo ultimo messaggio. Di' all'utente cosa salveresti "
                        "(fascicolo, dati con fonte) e chiedigli se vuole che lo registri.")
            if c.salvataggi >= 3:
                return "NON SALVATO: limite di salvataggi per turno raggiunto."
            c.salvataggi += 1
            r = salva(c, fascicolo=str(a.get("fascicolo") or ""), tipo=str(a.get("tipo") or "commessa"), codice=str(a.get("codice") or ""),
                      titolo=str(a.get("titolo") or ""), stato=str(a.get("stato") or ""), voci_in=a.get("voci") if isinstance(a.get("voci"), list) else [],
                      allega_documenti=bool(a.get("allega_documenti")))
            if not r.get("ok"):
                return "NON SALVATO: " + str(r.get("errore"))
            e = r["esiti"]
            return (f"ESITO: ok. Salvato nel fascicolo {r.get('codice') or r.get('titolo')}{' (nuovo)' if r['nuovo'] else ''}: {e['creata']} record nuovi, {e['duplicato']} già presenti (non duplicati), "
                    f"{e['fonte_aggiunta']} con fonte aggiunta, {e['proposta']} proposte di aggiornamento in attesa di conferma, {r['documenti_allegati']} documenti."
                    + (f"\nId creati/proposti: {', '.join(i[:8] for i in r['id_salvati'])}." if r.get("id_salvati") else "")
                    + ("\n" + "\n".join(r["avvisi"]) if r["avvisi"] else ""))
        f = _fascicolo(c, a)
        if not f:
            return "Fascicolo non trovato."
        fid = str(f["id"])
        if nome == "fascicolo_apri":
            if a.get("alla_data"):
                return f"FASCICOLO {f.get('codice') or f.get('titolo')}\n" + V.storico(c.user_id, fid, "", str(a["alla_data"]))
            return formatta_fascicolo(c.user_id, f, con_superate=bool(a.get("con_superate")), da=int(a.get("da") or 0),
                                      tipo=str(a.get("tipo") or ""), cerca_testo=str(a.get("cerca_testo") or ""))
        if nome == "fascicolo_collega":
            n = collega(c, f)
            return f"Conversazione collegata al fascicolo {f.get('codice') or f.get('titolo')} ({n} documenti conservati, apribili con fascicolo_documento).\n" + formatta_fascicolo(c.user_id, f, 12)
        if nome == "fascicolo_confronta":
            return V.confronta(c.user_id, fid, [x for x in (a.get("valori") or []) if isinstance(x, dict)], bool(a.get("documento_caricato")))
        if nome == "fascicolo_aggiorna":
            if not conferma_utente(c):
                return "ESITO: errore NON_ESEGUITO — " + _senza_conferma(f"aggiornare il record {a.get('record')} a {a.get('valore')}")
            if not str(a.get("motivo") or "").strip():
                return "ESITO: errore MOTIVO_MANCANTE — indica il motivo dell'aggiornamento."
            fo = {k: a.get(k) for k in ("doc", "pag", "quote") if a.get(k) not in (None, "")}
            r = V.aggiorna(c, fid, str(a.get("record") or ""), a.get("valore"), a.get("testo"), a.get("unita"), str(a.get("motivo") or ""),
                           a.get("revisione_attesa"), fo or None, "utente")
            return (("ESITO: ok" + (" (idempotente)" if r.get("idempotente") else "") if r["ok"] else f"ESITO: errore {r['codice']}") + f" — {r['dettaglio']}"
                    + (f"\n{{\"ok\": true, \"id\": \"{r['id']}\", \"revisione\": {r['revisione']}, \"valore\": \"{r.get('valore')}\"}}" if r["ok"] else ""))
        if nome == "fascicolo_voce":
            act = str(a.get("azione") or "")
            if act == "storico":
                return V.storico(c.user_id, fid, str(a.get("record") or ""), str(a.get("alla_data") or ""))
            if not conferma_utente(c):
                return _senza_conferma(f"{act} sul record {a.get('record')}")
            r = V.azione(c, fid, str(a.get("record") or ""), act, str(a.get("motivo") or ""), "utente")
            return ("ESITO: ok — ESEGUITO: " + r["dettaglio"]) if r.get("ok") else "ESITO: errore — NON ESEGUITO: " + str(r.get("errore"))
        if nome == "fascicolo_duplicati":
            gr = V.duplicati(c.user_id, fid)
            if a.get("azione") != "consolida":
                return V.descrivi_duplicati(gr)
            if not conferma_utente(c):
                return _senza_conferma("consolidamento dei duplicati: " + V.descrivi_duplicati(gr)[:400])
            r = V.consolida(c, fid, None, "utente")
            return f"ESEGUITO: consolidati {len(r['gruppi'])} gruppi (duplicati archiviati, non cancellati; annullabili dall'utente)."
        if nome == "fascicolo_documento":
            d = trova_documento(c.user_id, fid, str(a.get("documento") or ""))
            if not d:
                return "Documento non trovato nel fascicolo."
            if a.get("imposta_stato"):
                if not conferma_utente(c):
                    return _senza_conferma(f"stato del documento → {a['imposta_stato']}")
                _db().table(T_DOC).update({"stato": a["imposta_stato"]}).eq("id", d["id"]).eq("user_id", c.user_id).execute()
                V.evento(c.user_id, fid, None, "documento", {"stato": d.get("stato")}, {"stato": a["imposta_stato"], "doc": doc_id_di(d)}, "stato del documento", "utente")
                return f"ESEGUITO: documento {d.get('name')} v{d.get('versione') or 1} → {a['imposta_stato']}."
            collega_documento(c, {**d, "fascicolo_id": fid})
            ps = passaggi_documento(c, d, str(a.get("query") or ""))
            ver = sorted(documenti(c.user_id, fid), key=lambda x: int(x.get("versione") or 1))
            ver = [x for x in ver if (x.get("serie") or _serie(x.get("name"))) == (d.get("serie") or _serie(d.get("name")))]
            testa = (f"DOCUMENTO {_riga_doc(d)} — versioni: " + ", ".join(f"v{x.get('versione') or 1} {x.get('stato') or 'caricato'}" for x in ver)
                     + f"\nPer citare scrivi [[fonte|{doc_id_di(d)}|PAGINA|testo copiato]]; l'utente può aprirlo nel visualizzatore.")
            corpo = "\n\n".join(f"--- pag.{p.get('page_number') or '?'} ---\n{str(p.get('content') or '')[:1200]}" for p in ps) or "(nessun testo estratto)"
            return testa + "\n" + corpo
    except Exception:
        log.warning("strumento %s fallito (fail-open)", nome, exc_info=True)
        return "[strumento memoria non riuscito: non dichiarare di aver letto o salvato nulla]"
    return "[strumento sconosciuto]"
