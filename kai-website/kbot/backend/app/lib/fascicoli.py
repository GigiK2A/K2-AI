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
from typing import Any, Dict, List, Optional

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
_VERBI_SALVA = re.compile(r"\b(salva\w*|registra\w*|memorizza\w*|aggiung\w*|inserisc\w*|tieni\s+traccia|archivia\w*|crea\w*\s+(?:il\s+|un\s+)?fascicolo|apri\w*\s+(?:il\s+|un\s+)?fascicolo)\b", re.I)
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
    return bool(_SI.match(u) and "fascicolo" in a and re.search(r"salv|registr|aggiung|memoriz|archivi|aprire|creare", a))


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
    for v in (voci_in or [])[:MAX_VOCI_PER_SALVATAGGIO]:
        testo = str(v.get("testo") or "").strip()[:600]
        if not testo:
            continue
        chiave = (str(v.get("chiave") or "").strip().casefold() or None)
        valore = str(v.get("valore") or "").strip()[:120] or None
        fonte = {"origine": "documento" if v.get("doc") else "utente", "session_id": ctx.session_id}
        for k_in, k_out in (("doc", "doc"), ("pag", "pag"), ("quote", "quote")):
            if v.get(k_in) not in (None, ""):
                fonte[k_out] = v[k_in]
        verifica = "confermato" if fonte["origine"] == "utente" else "non_verificato"
        if chiave and valore:
            for e in esistenti:
                if e.get("chiave") == chiave and e.get("valore") and _num(e["valore"]) != _num(valore):
                    verifica = "contraddittorio"
                    _db().table(T_VOCI).update({"verifica": "contraddittorio"}).eq("id", e["id"]).eq("user_id", uid).execute()
                    avvisi.append(f"«{chiave}»: valore già in fascicolo {e['valore']} (fonte {((e.get('fonte') or {}).get('origine') or '?')}), nuovo {valore}: entrambi segnati «contraddittorio»")
        riga = {"fascicolo_id": fid, "user_id": uid, "tipo": v.get("tipo") if v.get("tipo") in TIPI_VOCE else "dato", "chiave": chiave,
                "testo": testo, "valore": valore, "fonte": fonte, "verifica": verifica, "data_verifica": _ora()}
        salvate.append(_db().table(T_VOCI).insert(riga).execute().data[0]["id"])
    n_doc = 0
    if allega_documenti:
        n_doc = _allega_documenti(ctx, fid)
    _db().table(T_FASC).update({"updated_at": _ora()}).eq("id", fid).eq("user_id", uid).execute()
    return {"ok": True, "fascicolo": fid, "codice": f.get("codice"), "titolo": f.get("titolo"), "nuovo": nuovo,
            "voci_salvate": len(salvate), "documenti_allegati": n_doc, "avvisi": avvisi}


def _allega_documenti(ctx: Contesto, fid: str) -> int:
    uid = ctx.user_id
    assert uid
    gia = {d.get("path") for d in documenti(uid, fid)}
    n = 0
    for f in (ctx.collected or {}).get("uploaded_files") or []:
        if f.get("dalFascicolo") or not f.get("path") or f["path"] in gia:
            continue
        _db().table(T_DOC).insert({"fascicolo_id": fid, "user_id": uid, "name": f.get("name") or "documento", "type": f.get("type"),
                                   "size": f.get("size"), "path": f["path"], "extracted_text": f.get("extractedText") or f.get("extractedSummary") or "",
                                   "extraction_method": f.get("extractionMethod"), "source_session": ctx.session_id or None}).execute()
        n += 1
    return n


def collega(ctx: Contesto, f: dict) -> int:
    """Collega la conversazione al fascicolo: i suoi documenti diventano disponibili (testo, citazioni, visualizzatore) senza ricaricarli."""
    uid = ctx.user_id
    assert uid
    col = ctx.collected
    col["fascicolo_id"] = str(f["id"])
    presenti = {x.get("path") for x in col.get("uploaded_files") or []}
    aggiunti = 0
    for d in documenti(uid, str(f["id"])):
        if d.get("path") in presenti:
            continue
        col.setdefault("uploaded_files", []).append({"name": d.get("name"), "type": d.get("type") or "", "size": d.get("size") or 0, "path": d["path"],
                                                     "publicUrl": "", "extractedText": d.get("extracted_text") or "", "extractedSummary": "",
                                                     "extractionMethod": d.get("extraction_method") or "", "dalFascicolo": str(f["id"])})
        aggiunti += 1
    return aggiunti


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
    fo = v.get("fonte") or {}
    fonte = fo.get("origine", "?") + (f", doc {fo['doc']} pag. {fo.get('pag')}" if fo.get("doc") else "")
    return f"- [{v.get('tipo')}] {v.get('testo')}" + (f" = {v['valore']}" if v.get("valore") else "") + f" ({v.get('verifica')}; fonte: {fonte}; {str(v.get('data_verifica') or v.get('created_at') or '')[:10]})"


def formatta_fascicolo(user_id: str, f: dict, max_voci: int = 30) -> str:
    vv = voci(user_id, str(f["id"]))
    dd = documenti(user_id, str(f["id"]))
    righe = [f"FASCICOLO {f.get('codice') or '(senza codice)'} — {f.get('titolo')} [{f.get('tipo')}, {f.get('stato')}] id={f['id']}"]
    righe += [_riga_voce(v) for v in vv[-max_voci:]] or ["(nessuna voce salvata)"]
    if dd:
        righe.append("Documenti conservati: " + "; ".join(str(d.get("name")) for d in dd))
    contr = [v for v in vv if v.get("verifica") == "contraddittorio"]
    if contr:
        righe.append(f"ATTENZIONE: {len(contr)} voci contraddittorie — segnalalo all'utente e chiedi quale è corretta.")
    return "\n".join(righe)[:6000]


def blocco_prompt() -> str:
    """Sommario per il prompt: fascicolo collegato (breve) oppure l'elenco dei fascicoli dell'utente. Fail-open."""
    c = _CTX.get()
    if not (c and c.user_id) or os.environ.get("KBOT_FASCICOLI", "1") == "0":
        return ""
    try:
        fid = (c.collected or {}).get("fascicolo_id")
        f = trova(c.user_id, str(fid)) if fid else None
        if f:
            return ("\n\nFASCICOLO COLLEGATO A QUESTA CONVERSAZIONE (memoria aziendale dell'utente, già verificata dal sistema):\n"
                    + formatta_fascicolo(c.user_id, f, 12) + "\nPer salvare novità nel fascicolo usa `fascicolo_salva` SOLO dopo che l'utente ha chiesto o confermato.\n")[:MAX_BLOCCO]
        lista = elenco(c.user_id, 8)
        if not lista:
            return "\n\nMEMORIA AZIENDALE: l'utente non ha ancora fascicoli. Se emerge una commessa/cliente/contratto da seguire nel tempo, proponi di aprirne uno (e salva solo dopo il sì).\n"
        elenco_txt = "; ".join(f"{x.get('codice') or x.get('titolo')} ({x.get('tipo')}, {x.get('stato')})" for x in lista)
        return f"\n\nMEMORIA AZIENDALE — fascicoli dell'utente: {elenco_txt}. Se l'utente cita una di queste pratiche, usa `fascicolo_cerca`/`fascicolo_apri` e `fascicolo_collega` invece di chiedergli di nuovo i dati; non sono nel contesto finché non li apri.\n"[:MAX_BLOCCO]
    except Exception:
        log.warning("blocco fascicoli non disponibile (fail-open)", exc_info=True)
        return ""


# ── strumenti del modello ──────────────────────────────────────────────────────────────────────────────
NOMI = ("fascicolo_cerca", "fascicolo_apri", "fascicolo_collega", "fascicolo_salva")


def definizioni() -> List[dict]:
    voce = {"type": "object", "properties": {
        "tipo": {"type": "string", "enum": sorted(TIPI_VOCE)}, "testo": {"type": "string", "description": "Cosa si registra, in una frase."},
        "chiave": {"type": "string", "description": "Nome del dato (es. imponibile_dichiarato) per riconoscere contraddizioni."},
        "valore": {"type": "string"}, "doc": {"type": "string", "description": "ID documento dell'estratto da cui viene il dato."},
        "pag": {"type": "integer"}, "quote": {"type": "string", "description": "Testo copiato dal documento."}}, "required": ["testo"]}
    return [
        {"name": "fascicolo_cerca", "description": "Cerca fra i fascicoli dell'utente (commesse, clienti, contratti…) per codice, titolo o contenuto.",
         "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}}},
        {"name": "fascicolo_apri", "description": "Apre un fascicolo dell'utente (id o codice): voci con fonte, data e stato di verifica, documenti conservati.",
         "input_schema": {"type": "object", "properties": {"fascicolo": {"type": "string"}}, "required": ["fascicolo"]}},
        {"name": "fascicolo_collega", "description": "Collega QUESTA conversazione a un fascicolo: i suoi documenti diventano subito leggibili e citabili, senza ricaricarli.",
         "input_schema": {"type": "object", "properties": {"fascicolo": {"type": "string"}}, "required": ["fascicolo"]}},
        {"name": "fascicolo_salva", "description": (
            "Crea un fascicolo o vi aggiunge voci (dati, decisioni, scadenze, anomalie) e, se richiesto, i documenti della conversazione. "
            "Funziona SOLO se l'utente lo ha chiesto o confermato nel suo ultimo messaggio: prima proponi cosa salveresti e attendi il sì."),
         "input_schema": {"type": "object", "properties": {
             "fascicolo": {"type": "string", "description": "id o codice di un fascicolo esistente"}, "tipo": {"type": "string", "enum": sorted(TIPI_FASCICOLO)},
             "codice": {"type": "string"}, "titolo": {"type": "string"}, "stato": {"type": "string", "enum": ["aperto", "in_corso", "chiuso"]},
             "voci": {"type": "array", "items": voce}, "allega_documenti": {"type": "boolean"}}}},
    ]


SYSTEM_HINT = (
    "\n\nSTRUMENTI MEMORIA AZIENDALE (`fascicolo_*`): i fascicoli dell'utente persistono fra le conversazioni. Leggi con cerca/apri, collega la "
    "conversazione con `fascicolo_collega`. SCRIVI solo dopo che l'utente ha chiesto o confermato: prima di `fascicolo_salva` di' cosa "
    "salveresti (dati, fonte) e aspetta il sì; se il sistema risponde «NON SALVATO», chiedi conferma, non ritentare. Riporta sempre la fonte "
    "e lo stato di verifica dei dati del fascicolo; se ci sono voci contraddittorie, segnalalo. Non dire di aver salvato se lo strumento non lo conferma.\n")


def esegui(nome: str, args: dict) -> str:
    c = _CTX.get()
    if not (c and c.user_id):
        return "[memoria aziendale non disponibile: serve un utente autenticato]"
    a = args if isinstance(args, dict) else {}
    try:
        if nome == "fascicolo_cerca":
            r = cerca(c.user_id, str(a.get("query") or ""))
            return "Nessun fascicolo trovato." if not r else "\n".join(f"- {f.get('codice') or '—'} | {f.get('titolo')} | {f.get('tipo')} | {f.get('stato')} | id={f['id']}" for f in r)
        if nome == "fascicolo_apri":
            f = trova(c.user_id, str(a.get("fascicolo") or ""))
            return formatta_fascicolo(c.user_id, f) if f else "Fascicolo non trovato."
        if nome == "fascicolo_collega":
            f = trova(c.user_id, str(a.get("fascicolo") or ""))
            if not f:
                return "Fascicolo non trovato."
            n = collega(c, f)
            return f"Conversazione collegata al fascicolo {f.get('codice') or f.get('titolo')}: {n} documenti resi disponibili.\n" + formatta_fascicolo(c.user_id, f, 12)
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
            return (f"Salvato nel fascicolo {r.get('codice') or r.get('titolo')}{' (nuovo)' if r['nuovo'] else ''}: {r['voci_salvate']} voci, "
                    f"{r['documenti_allegati']} documenti." + ("\nATTENZIONE contraddizioni: " + " | ".join(r["avvisi"]) if r["avvisi"] else ""))
    except Exception:
        log.warning("strumento %s fallito (fail-open)", nome, exc_info=True)
        return "[strumento memoria non riuscito: non dichiarare di aver letto o salvato nulla]"
    return "[strumento sconosciuto]"
