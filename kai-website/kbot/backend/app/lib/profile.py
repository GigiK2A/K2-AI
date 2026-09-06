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
    except Exception as exc:
        # Tabella assente = memoria cross-sessione SPENTA per tutti, non un errore di un
        # utente: va detto in modo distinguibile, altrimenti si confonde con un blip di
        # rete e la feature resta morta per mesi (è già successo: la migration di questa
        # tabella non esisteva nel repo). Vedi migration 008 e /api/kbot/diagnostics.
        from .conversations_index import is_missing_table_error

        if is_missing_table_error(exc):
            log.error("profilo: tabella %s ASSENTE — memoria cross-sessione disattivata, "
                      "applica la migration 008_kbot_client_memory.sql", TABLE)
        else:
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
    changed = False

    coll = session.get("collected_data") or session.get("collected") or {}
    extracted = coll.get("extractedData") or {}

    # ── anagrafica: dai campi già estratti (summary + autofill), l'ultimo vince ──
    for pkey, sources in (
        ("ragione_sociale", ("ragione_sociale", "companyName", "azienda")),
        ("settore", ("businessType", "settore", "settore_ateco")),
        ("forma_giuridica", ("forma_giuridica",)),
        ("dipendenti", ("n_dipendenti", "dipendenti")),
        ("fatturato", ("fatturato", "fatturato_ultimo_anno")),
        ("clienti_principali", ("clienti_principali",)),
    ):
        for src in (coll, extracted, coll.get("deliverable_inputs") or {}):
            for k in sources:
                v = _clean(src.get(k)) if isinstance(src, dict) else None
                if v and ana.get(pkey) != v:
                    ana[pkey] = v
                    changed = True
                    break
            else:
                continue
            break

    # ── contesto operativo: problemi/obiettivi dalle sintesi (dedupe) ──
    problemi = list(ctx.get("problemi") or [])
    obiettivi = list(ctx.get("obiettivi") or [])
    for v, dest in ((extracted.get("summary"), problemi), (extracted.get("objective"), obiettivi)):
        s = _clean(v)
        if s and _push_unique(dest, s[:220]):
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
    if ctx.get("problemi") or ctx.get("obiettivi"):
        p["contesto"] = ctx
    if storico:
        p["storico"] = storico
    return p, changed


def load_anagrafica(user_id: Optional[str]) -> dict:
    """Dati azienda impostati sull'account (per il form dashboard/signup). {} se assente."""
    prof = load(user_id) or {}
    ana = prof.get("anagrafica") if isinstance(prof, dict) else None
    return {k: v for k, v in (ana or {}).items() if k in ANAGRAFICA_FIELDS and _clean(v)}


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
    for k in ANAGRAFICA_FIELDS:
        if k in data:
            v = _clean(data.get(k))
            if v:
                ana[k] = v[:120]
            else:
                ana.pop(k, None)
    ana = {k: v for k, v in ana.items() if k in ANAGRAFICA_FIELDS or _clean(v)}
    prof["anagrafica"] = ana
    _save(user_id, prof)
    return {k: v for k, v in ana.items() if k in ANAGRAFICA_FIELDS}


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


def render_block(profile: Optional[dict]) -> str:
    """Blocco PROFILO CLIENTE per il system prompt ('' se profilo vuoto)."""
    if not isinstance(profile, dict) or not profile:
        return ""
    parts = []
    ana = profile.get("anagrafica") or {}
    if ana:
        parts.append("Anagrafica: " + "; ".join(
            f"{_ANAGRAFICA_LABELS.get(k, k.replace('_', ' '))}: {v}" for k, v in ana.items()))
    ctx = profile.get("contesto") or {}
    if ctx.get("problemi"):
        parts.append("Problemi/temi già trattati: " + " | ".join(ctx["problemi"][-5:]))
    if ctx.get("obiettivi"):
        parts.append("Obiettivi noti: " + " | ".join(ctx["obiettivi"][-5:]))
    storico = profile.get("storico") or []
    if storico:
        parts.append("Report già prodotti: " + " | ".join(
            f"{e.get('data')} {e.get('tema')}" for e in storico[-5:]))
    if not parts:
        return ""
    return (
        "\nPROFILO CLIENTE (memoria dalle conversazioni precedenti — USALA: non richiedere "
        "MAI dati già presenti qui; personalizza consigli ed esempi su questa azienda; "
        "se ciò che l'utente dice ORA contraddice il profilo, vale ciò che dice ora):\n- "
        + "\n- ".join(parts) + "\n"
    )
