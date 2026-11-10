"""Memoria-profilo cross-sessione del cliente ("prima consulente, poi report", 17 lug).

K-BOT costruisce progressivamente il profilo dell'azienda per gli utenti AUTENTICATI:
anagrafica, contesto operativo, storico consulenziale. Il profilo viene iniettato nel
prompt di ogni turno (il bot non richiede mai dati già noti, dà consulenza continuativa)
e aggiornato in modo DETERMINISTICO dai dati già estratti in sessione (summary, autofill,
deliverable) — nessuna chiamata LLM aggiuntiva. Fail-open ovunque: un problema di profilo
non deve MAI rompere la chat. KBOT_PROFILE_MEMORY=0 disattiva.

Tabella: kbot_client_memory (user_id uuid PK → auth.users, profile jsonb, updated_at).
NB: NON kbot_profiles — quella è la tabella consensi/anagrafica dell'auth, altro scopo.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Optional

from .supabase_admin import get_admin_client

log = logging.getLogger(__name__)

TABLE = "kbot_client_memory"
_MAX_LIST = 10  # cap per liste (storico, problemi): il prompt deve restare compatto

# Campi anagrafici che l'utente può impostare ESPLICITAMENTE (dashboard / signup), così non
# vanno reinseriti in ogni chat: vengono presi dall'account e iniettati nel prompt.
ANAGRAFICA_FIELDS = ("ragione_sociale", "partita_iva", "codice_ateco", "forma_giuridica",
                     "settore", "dipendenti", "fatturato", "citta")
_ANAGRAFICA_LABELS = {
    "ragione_sociale": "Ragione sociale", "partita_iva": "Partita IVA",
    "codice_ateco": "Codice ATECO", "forma_giuridica": "Forma giuridica",
    "settore": "Settore", "dipendenti": "Dipendenti", "fatturato": "Fatturato",
    "citta": "Città / sede",
}


def _enabled() -> bool:
    return os.getenv("KBOT_PROFILE_MEMORY", "1") != "0"


def load(user_id: Optional[str]) -> Optional[dict]:
    """Profilo dell'utente, o None (anonimo / assente / errore)."""
    if not user_id or not _enabled():
        return None
    try:
        res = (get_admin_client().table(TABLE).select("profile")
               .eq("user_id", user_id).limit(1).execute())
        rows = getattr(res, "data", None) or []
        return rows[0].get("profile") if rows else None
    except Exception:
        log.warning("profilo: load fallita (fail-open)", exc_info=True)
        return None


def _save(user_id: str, profile: dict) -> None:
    get_admin_client().table(TABLE).upsert({
        "user_id": user_id, "profile": profile,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).execute()


def _clean(v: Any) -> Optional[str]:
    s = str(v or "").strip()
    return s if s and s.lower() not in ("null", "none", "n/d", "-") else None


def _push_unique(lst: list, item: str) -> bool:
    """Append dedupe (case-insensitive, contains-aware). True se aggiunto."""
    low = item.lower()
    for x in lst:
        xl = str(x).lower()
        if low == xl or low in xl or xl in low:
            return False
    lst.append(item)
    del lst[:-_MAX_LIST]
    return True


def merge_from_session(profile: Optional[dict], session: dict) -> tuple[dict, bool]:
    """Merge DETERMINISTICO dei dati di sessione nel profilo. Ritorna (profilo, changed).
    Regola: ciò che l'utente dice ORA vince sul profilo (i campi anagrafici si
    sovrascrivono se la sessione ne porta di nuovi)."""
    p = dict(profile or {})
    ana = dict(p.get("anagrafica") or {})
    ctx = dict(p.get("contesto") or {})
    storico = list(p.get("storico") or [])
    confermati = set(p.get("confermati") or [])      # campi impostati ESPLICITAMENTE dall'utente: le conversazioni non li toccano
    prov = dict(p.get("prov") or {})                 # per voce appresa: conversazione (8 car.) e data. Niente valori, niente testi
    _origine = {"sid": str(session.get("id") or "")[:8], "data": datetime.now(timezone.utc).date().isoformat()}
    changed = False

    coll = session.get("collected_data") or session.get("collected") or {}
    extracted = coll.get("extractedData") or {}
    # fatti detti in chat (scheda del cliente): senza questo il profilo si riempiva solo da summary/report
    from .scheda_cliente import piatta as _piatta
    scheda_flat = _piatta(coll.get("scheda_cliente"))

    # ── anagrafica: dai campi già estratti (summary + autofill), l'ultimo vince ──
    for pkey, sources in (
        ("ragione_sociale", ("ragione_sociale", "companyName", "azienda")),
        ("settore", ("businessType", "settore", "settore_ateco")),
        ("forma_giuridica", ("forma_giuridica",)),
        ("dipendenti", ("n_dipendenti", "dipendenti")),
        ("fatturato", ("fatturato", "fatturato_ultimo_anno")),
        ("clienti_principali", ("clienti_principali",)),
        ("citta", ("citta",)),
    ):
        if pkey in confermati:
            continue
        for src in (coll, extracted, coll.get("deliverable_inputs") or {}, scheda_flat):
            for k in sources:
                v = _clean(src.get(k)) if isinstance(src, dict) else None
                if v and ana.get(pkey) != v:
                    ana[pkey] = v
                    prov[pkey] = dict(_origine)
                    changed = True
                    break
            else:
                continue
            break

    # ── altri fatti stabili detti in chat (soci, quote, clienti, date…): l'ultimo valore vince ──
    fatti = dict(p.get("fatti") or {})
    _gia = {"ragione_sociale", "settore", "forma_giuridica", "dipendenti", "fatturato", "citta"}
    for k, v in scheda_flat.items():
        if k in _gia or not _clean(v):
            continue
        if fatti.get(k) != v:
            fatti[k] = v
            prov[k] = dict(_origine)
            changed = True
    while len(fatti) > 25:
        fatti.pop(next(iter(fatti)))

    # ── contesto operativo: problemi/obiettivi dalle sintesi (dedupe) ──
    problemi = list(ctx.get("problemi") or [])
    obiettivi = list(ctx.get("obiettivi") or [])
    for v, dest in ((extracted.get("summary"), problemi), (extracted.get("objective"), obiettivi)):
        s = _clean(v)
        if s and _push_unique(dest, s[:220]):
            prov["_contesto"] = dict(_origine)
            changed = True
    ctx["problemi"], ctx["obiettivi"] = problemi[-_MAX_LIST:], obiettivi[-_MAX_LIST:]

    # ── storico consulenziale: report generati in questa sessione ──
    label = _clean(coll.get("deliverable_label")) or _clean(coll.get("deliverable_service"))
    job = _clean(coll.get("deliverable_job_id"))
    if label and job and not any(e.get("job") == job for e in storico):
        storico.append({"data": datetime.now(timezone.utc).date().isoformat(),
                        "tipo": "report", "tema": label, "job": job})
        del storico[:-_MAX_LIST]
        changed = True

    if ana:
        p["anagrafica"] = ana
    if fatti:
        p["fatti"] = fatti
    if ctx.get("problemi") or ctx.get("obiettivi"):
        p["contesto"] = ctx
    if storico:
        p["storico"] = storico
    if prov:
        p["prov"] = {k: v for k, v in prov.items() if k in ana or k in fatti or k == "_contesto"}
    return p, changed


def load_anagrafica(user_id: Optional[str]) -> dict:
    """Dati azienda impostati sull'account (per il form dashboard/signup). {} se assente."""
    prof = load(user_id) or {}
    ana = prof.get("anagrafica") if isinstance(prof, dict) else None
    conf = set(prof.get("confermati") or []) if isinstance(prof, dict) else set()
    # Solo i dati CONFERMATI: il modulo dashboard non deve precompilare (e far «confermare» senza accorgersene) valori appresi da altre
    # conversazioni; quelli si vedono e si correggono da /profile/memoria.
    return {k: v for k, v in (ana or {}).items() if k in ANAGRAFICA_FIELDS and k in conf and _clean(v)}


def seed_from_metadata(user_id: Optional[str], user_metadata: Optional[dict]) -> dict:
    """Al primo accesso, se l'anagrafica è vuota, la inizializza dai metadati raccolti al
    signup (company_name → ragione sociale, work_sector → settore) così il nuovo utente
    trova già precompilato ciò che ha inserito. Best-effort. Ritorna l'anagrafica corrente."""
    try:
        current = load_anagrafica(user_id)
        if current or not user_id or not _enabled():
            return current
        meta = user_metadata or {}
        seed = {}
        rs = _clean(meta.get("company_name") or meta.get("companyName"))
        st = _clean(meta.get("work_sector") or meta.get("workSector"))
        if rs:
            seed["ragione_sociale"] = rs
        if st:
            seed["settore"] = st
        if not seed:
            return {}
        return save_anagrafica(user_id, seed)
    except Exception:
        log.warning("profilo: seed da metadati fallito (fail-open)", exc_info=True)
        return {}


def save_anagrafica(user_id: str, data: dict) -> dict:
    """Salva/aggiorna i dati azienda dell'account (merge sui campi noti). I campi vuoti
    RIMUOVONO il valore. Ritorna l'anagrafica risultante. Solleva su errore (l'endpoint
    lo traduce): a differenza dell'auto-merge best-effort, questo è un salvataggio esplicito."""
    if not _enabled():
        raise RuntimeError("profile memory disabled")
    prof = dict(load(user_id) or {})
    ana = dict(prof.get("anagrafica") or {})
    conf = set(prof.get("confermati") or [])
    for k in ANAGRAFICA_FIELDS:
        if k in data:
            v = _clean(data.get(k))
            if v:
                ana[k] = v[:120]
                conf.add(k)                              # impostato dall'utente: confermato
            else:
                ana.pop(k, None)
                conf.discard(k)
    ana = {k: v for k, v in ana.items() if k in ANAGRAFICA_FIELDS or _clean(v)}
    prof["anagrafica"] = ana
    prof["confermati"] = sorted(conf)
    _save(user_id, prof)
    return {k: v for k, v in ana.items() if k in ANAGRAFICA_FIELDS and k in conf}


def update_after_turn(session: dict) -> None:
    """Aggiorna il profilo dell'owner della sessione (best-effort, mai bloccante)."""
    if not _enabled():
        return
    user_id = session.get("user_id")
    if not user_id:
        return
    try:
        current = load(user_id)
        merged, changed = merge_from_session(current, session)
        if changed:
            _save(user_id, merged)
    except Exception:
        log.warning("profilo: update fallita (fail-open)", exc_info=True)


def _data_it(prov: Optional[dict]) -> str:
    d = str((prov or {}).get("data") or "")
    if len(d) == 10 and d[4] == "-" and d[7] == "-":
        return f"{d[8:10]}/{d[5:7]}/{d[:4]}"
    return ""


def _voci(profile: dict, scheda: Optional[dict]) -> tuple[list[str], list[str]]:
    """(confermate, apprese) come righe di testo. Le voci apprese portano conversazione/data; quelle che l'utente sta dicendo
    NELLA conversazione in corso (scheda) non si ripetono: vince ciò che dice ora."""
    from .scheda_cliente import piatta as _piatta
    ora = set(_piatta(scheda))
    prov = profile.get("prov") or {}
    confermati = set(profile.get("confermati") or [])
    conf, app = [], []

    def _fonte(k: str) -> str:
        d = _data_it(prov.get(k))
        return f" (da una conversazione del {d})" if d else " (da una conversazione precedente, data non nota)"

    for k, v in (profile.get("anagrafica") or {}).items():
        if k in ora:
            continue
        etichetta = _ANAGRAFICA_LABELS.get(k, k.replace("_", " "))
        if k in confermati:
            conf.append(f"{etichetta}: {v}")
        else:
            app.append(f"{etichetta}: {v}{_fonte(k)}")
    for k, v in list((profile.get("fatti") or {}).items())[-12:]:
        if k not in ora and k not in (profile.get("anagrafica") or {}):
            app.append(f"{k.replace('_', ' ')}: {v}{_fonte(k)}")
    ctx = profile.get("contesto") or {}
    for chiave, titolo in (("problemi", "Tema trattato"), ("obiettivi", "Obiettivo espresso")):
        for v in (ctx.get(chiave) or [])[-3:]:
            app.append(f"{titolo}: {v}{_fonte('_contesto')}")
    for e in (profile.get("storico") or [])[-3:]:
        app.append(f"Report prodotto il {e.get('data')}: {e.get('tema')}")
    return conf, app


def statistiche(profile: Optional[dict], scheda: Optional[dict] = None) -> dict:
    """Quante voci confermate/apprese entrano nel prompt: numeri, mai valori (tracciabilità senza dati aziendali nei log)."""
    if not isinstance(profile, dict) or not profile:
        return {"confermati": 0, "appresi": 0}
    conf, app = _voci(profile, scheda)
    return {"confermati": len(conf), "appresi": len(app)}


def memoria_appresa(user_id: Optional[str]) -> list[dict]:
    """Elenco delle voci apprese dell'utente (per mostrarle e farle correggere): chiave, valore, conversazione, data."""
    prof = load(user_id) or {}
    prov, confermati = prof.get("prov") or {}, set(prof.get("confermati") or [])
    out = []
    for k, v in (prof.get("anagrafica") or {}).items():
        if k not in confermati:
            out.append({"chiave": k, "valore": v, "conversazione": (prov.get(k) or {}).get("sid", ""), "data": (prov.get(k) or {}).get("data", "")})
    for k, v in (prof.get("fatti") or {}).items():
        out.append({"chiave": k, "valore": v, "conversazione": (prov.get(k) or {}).get("sid", ""), "data": (prov.get(k) or {}).get("data", "")})
    return out


def dimentica(user_id: Optional[str], chiave: Optional[str] = None) -> int:
    """Cancella una voce appresa (o tutte). I dati CONFERMATI dall'utente nell'account non si toccano. Ritorna quante ne ha tolte."""
    if not user_id or not _enabled():
        return 0
    prof = dict(load(user_id) or {})
    confermati = set(prof.get("confermati") or [])
    ana, fatti, prov = dict(prof.get("anagrafica") or {}), dict(prof.get("fatti") or {}), dict(prof.get("prov") or {})
    tolte = 0
    for k in [k for k in ana if k not in confermati and (chiave is None or k == chiave)]:
        ana.pop(k); prov.pop(k, None); tolte += 1
    for k in [k for k in fatti if chiave is None or k == chiave]:
        fatti.pop(k); prov.pop(k, None); tolte += 1
    if chiave is None and prof.get("contesto"):
        prof.pop("contesto"); prov.pop("_contesto", None)
    if tolte or chiave is None:
        prof["anagrafica"], prof["fatti"], prof["prov"] = ana, fatti, prov
        _save(user_id, prof)
    return tolte


def render_block(profile: Optional[dict], scheda: Optional[dict] = None) -> str:
    """Blocchi del system prompt: DATI CONFERMATI dall'utente (fatti utilizzabili) e MEMORIA APPRESA (non verificata, con provenienza).
    `scheda` = fatti detti nella conversazione in corso: prevalgono sulla memoria e non si ripetono."""
    if not isinstance(profile, dict) or not profile:
        return ""
    conf, app = _voci(profile, scheda)
    out = ""
    if conf:
        out += ("\nPROFILO CLIENTE — DATI CONFERMATI DALL'UTENTE (impostati nel suo account: puoi usarli come fatti e non "
                "richiederli; se ciò che dice ORA li contraddice, vale ciò che dice ora):\n- " + "\n- ".join(conf) + "\n")
    if app:
        out += ("\nMEMORIA APPRESA DA CONVERSAZIONI PRECEDENTI — NON VERIFICATA (può riguardare un altro caso, un'altra azienda o "
                "una prova). Non affermarla come fatto, non usarla nei calcoli e non attribuirla all'utente senza conferma. Se ti "
                "serve, chiedi: «in una conversazione precedente risultava X: è ancora così?» e poi usa la risposta. Se l'utente "
                "dice ora qualcosa di diverso, vale ciò che dice ora. Se non c'entra con la domanda, ignorala senza citarla:\n- "
                + "\n- ".join(app) + "\n")
    return out
