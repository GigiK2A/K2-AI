"""Autodiagnosi del board: i numeri della propria salute, letti dalle proprie tabelle.

Fino al 20 ago 2026 questo censimento lo faceva una routine esterna una volta al
giorno: contava i `failed`, le decisioni ferme, le bozze mai inviate e la qualità
delle proposte, e li riferiva all'owner. Ma sono tutte letture di `aios_audit`,
`aios_approvals`, `email_messages` e `aios_deliverables` — tabelle di casa. Non
serve nessuno da fuori per guardarsi allo specchio.

Il senso non è il report: è che un difetto STRUTTURALE si vede solo contando. Un
reparto che ripiega cinque volte sulla stessa tabella inesistente non lo scopri
leggendo i task a mano; lo scopri raggruppando gli eventi `ripiegata` per
`tabella_voluta`. `esperienza.py` fa la stessa cosa per un reparto alla volta —
qui si guarda il board intero.

SOLA LETTURA, per scelta e non per caso: questo modulo non scrive niente, da
nessuna parte. Il piano di controllo resta di chi lo controlla. Tutto best-effort:
se Supabase non risponde, il loop gira come prima.
"""
from __future__ import annotations

import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any

# Eventi che raccontano un insuccesso, ognuno col suo significato:
#   failed    → l'attuatore ha provato e non ha scritto niente
#   ripiegata → l'azione non era eseguibile ed è diventata un task generico
#   queue_full→ il reparto propone più di quanto l'owner decida
#   duplicate → si è riproposto da solo
INSUCCESSI = ("failed", "ripiegata", "queue_full", "duplicate")

# Le tre cose che ESIGENZA_QUALITA chiede a ogni proposta (competenza.py). Misurarle
# è l'unico modo di dire se gli agenti stanno migliorando o solo scrivendo di più.
_KW_ALTERNATIVA = ("alternativa scartata", "alternativa che ho scartato", "scartata",
                   "invece di", "anziché", "anzichè")
_KW_RIPENSAMENTO = ("cambierebbe idea", "farebbe cambiare idea", "cambierei idea",
                    "mi farebbe cambiare", "se invece")


def _righe(client: Any, tabella: str, params: dict) -> list[dict]:
    try:
        out = client.select(tabella, params)
        return out if isinstance(out, list) else []
    except Exception:
        return []


def _da_ore(ore: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=ore)).isoformat()


def _eta_giorni(iso: Any) -> int | None:
    """Quanti giorni sono passati da un timestamp ISO. None se illeggibile."""
    if not isinstance(iso, str) or not iso:
        return None
    try:
        t = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except ValueError:
        return None
    if t.tzinfo is None:
        t = t.replace(tzinfo=timezone.utc)
    return max(0, (datetime.now(timezone.utc) - t).days)


def _testo_proposta(riga: dict) -> str:
    return " ".join(str(riga.get(c) or "") for c in ("motivo", "contenuto", "titolo")).lower()


def qualita(righe: list[dict]) -> dict[str, int]:
    """% di proposte che rispettano l'esigenza: numeri, alternativa scartata, ripensamento."""
    n = len(righe)
    if not n:
        return {"proposte": 0, "numeri": 0, "alternativa": 0, "ripensamento": 0}
    num = alt = rip = 0
    for r in righe:
        t = _testo_proposta(r)
        if re.search(r"\d", t):
            num += 1
        if any(k in t for k in _KW_ALTERNATIVA):
            alt += 1
        if any(k in t for k in _KW_RIPENSAMENTO):
            rip += 1
    return {"proposte": n, "numeri": 100 * num // n,
            "alternativa": 100 * alt // n, "ripensamento": 100 * rip // n}


def esamina(client: Any, *, ore: int = 24) -> dict[str, Any]:
    """Fotografia della salute del board nelle ultime `ore`. Sola lettura."""
    if client is None:
        return {}
    da = _da_ore(ore)
    audit = _righe(client, "aios_audit", {
        "select": "event,actor,action_key,detail,created_at",
        "created_at": f"gte.{da}", "order": "seq.desc", "limit": "2000"})
    eventi = Counter(r.get("event") for r in audit)

    # Insuccessi raggruppati per causa: è qui che si vede il difetto strutturale.
    cause: dict[str, Counter] = {ev: Counter() for ev in INSUCCESSI}
    for r in audit:
        ev = r.get("event")
        if ev not in cause:
            continue
        d = r.get("detail") or {}
        if not isinstance(d, dict):
            continue
        if ev == "ripiegata":
            chiave = f"{d.get('tabella_voluta') or '?'} — {d.get('causa') or 'causa non riportata'}"
        elif ev == "failed":
            esito = d.get("esito") or {}
            chiave = str(esito.get("errore") or "causa non riportata")
        else:
            chiave = str(r.get("actor") or "?")
        cause[ev][chiave[:120]] += 1

    pendenti = _righe(client, "aios_approvals", {
        "select": "id,actor,created_at", "status": "eq.PENDING",
        "order": "id.asc", "limit": "500"})
    bozze = _righe(client, "email_messages", {
        "select": "id,created_at", "direction": "eq.out", "status": "eq.bozza",
        "order": "created_at.asc", "limit": "500"})
    proposte = _righe(client, "aios_deliverables", {
        "select": "dominio,titolo,contenuto,motivo,created_at",
        "created_at": f"gte.{da}", "order": "id.desc", "limit": "200"})

    return {
        "ore": ore,
        "eventi": dict(eventi),
        "cause": {ev: c.most_common(5) for ev, c in cause.items() if c},
        "pendenti": len(pendenti),
        "pendenti_per_reparto": Counter(p.get("actor") for p in pendenti).most_common(),
        "pendenti_eta_giorni": _eta_giorni(pendenti[0].get("created_at")) if pendenti else None,
        "bozze": len(bozze),
        "bozze_eta_giorni": _eta_giorni(bozze[0].get("created_at")) if bozze else None,
        "qualita": qualita(proposte),
    }


def _plurale(n: int, singolare: str, plurale: str) -> str:
    """«1 decisione in attesa da 1 giorno», non «1 decisioni da 1 giorni». È un
    messaggio che l'owner legge ogni mattina: se è scritto male non lo legge."""
    return f"{n} {singolare if n == 1 else plurale}"


def _riga_eventi(ev: dict[str, int]) -> str:
    fatte = ev.get("executed", 0)
    parti = [_plurale(fatte, "azione eseguita", "azioni eseguite")]
    for nome, etichetta in (("ripiegata", "ripiegate a task"), ("failed", "fallite"),
                            ("queue_full", "scartate per coda piena"),
                            ("duplicate", "doppioni")):
        if ev.get(nome):
            parti.append(f"{ev[nome]} {etichetta}")
    return ", ".join(parti)


def referto(dati: dict[str, Any]) -> str:
    """Il referto da mandare all'owner. Vuoto se non c'è niente da dire.

    Niente riga per ogni evento: si mandano i numeri e SOLO le cause che si
    ripetono, perché una causa che torna è un difetto, una che appare una volta è
    un caso. Un referto ogni giorno che nessuno legge non serve a nulla."""
    if not dati:
        return ""
    ev = dati.get("eventi") or {}
    q = dati.get("qualita") or {}
    righe = [f"🩺 *Salute del board* — ultime {dati.get('ore', 24)}h",
             _riga_eventi(ev)]

    for nome, titolo in (("ripiegata", "Proposte ripiegate a task, per causa"),
                         ("failed", "Azioni fallite, per causa"),
                         ("queue_full", "Coda piena, per reparto"),
                         ("duplicate", "Doppioni, per reparto")):
        voci = (dati.get("cause") or {}).get(nome) or []
        ripetute = [(c, n) for c, n in voci if n > 1]
        if ripetute:
            righe.append(f"\n*{titolo}:*")
            righe += [f"· {n}× {c}" for c, n in ripetute]

    if q.get("proposte"):
        righe.append(f"\nQualità: {q['proposte']} proposte — numeri {q['numeri']}%, "
                     f"alternativa scartata {q['alternativa']}%, "
                     f"cosa cambierebbe idea {q['ripensamento']}%")

    fermo = []
    if dati.get("pendenti"):
        eta = dati.get("pendenti_eta_giorni")
        per_reparto = ", ".join(f"{a}: {n}" for a, n in (dati.get("pendenti_per_reparto") or []))
        fermo.append(_plurale(dati["pendenti"], "decisione in attesa", "decisioni in attesa")
                     + (f", la più vecchia da {_plurale(eta, 'giorno', 'giorni')}" if eta else "")
                     + (f" ({per_reparto})" if per_reparto else ""))
    if dati.get("bozze"):
        eta = dati.get("bozze_eta_giorni")
        fermo.append(_plurale(dati["bozze"], "bozza email mai inviata",
                              "bozze email mai inviate")
                     + (f", la più vecchia da {_plurale(eta, 'giorno', 'giorni')}" if eta else ""))
    if fermo:
        righe.append("\n*Fermo in attesa di te:*")
        righe += [f"· {f}" for f in fermo]

    return "\n".join(righe)
