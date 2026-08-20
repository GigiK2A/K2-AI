"""L'esperienza di un reparto: cosa è andato storto e cosa ha già proposto.

Il buco: gli agenti ripartivano da zero ogni mattina. Nessuno diceva loro com'era finita
l'azione di ieri. Effetto misurato in produzione: **10 insert identici su
`privacy_registro_trattamenti` falliti uno dopo l'altro** e 6 update su un
`policy_register` vuoto, perché il legale non ha mai saputo che quelle colonne non
esistono. Il dedup evita i doppioni in coda; non evita l'errore ripetuto domani.

È il fattore 9 dei 12-Factor Agents — *compact errors into context*: il fallimento
torna nel contesto e il modello si corregge da solo.

Tutto in sola lettura e best-effort: se l'audit non risponde, l'agente lavora come prima.
"""
from __future__ import annotations

import os
from typing import Any

FALLIMENTI_MAX = int(os.environ.get("AIOS_FALLIMENTI_IN_CONTESTO", "6"))
PROPOSTE_RECENTI_MAX = int(os.environ.get("AIOS_PROPOSTE_RECENTI_IN_CONTESTO", "12"))


def _righe(client: Any, tabella: str, params: dict) -> list[dict]:
    try:
        out = client.select(tabella, params)
        return out if isinstance(out, list) else []
    except Exception:
        return []


def fallimenti_recenti(client: Any, action_key: str,
                       limit: int = FALLIMENTI_MAX) -> list[dict]:
    """Le azioni di questo reparto che NON hanno fatto quello che dicevano, con la causa.

    Due eventi, non uno:
    - `failed`: l'attuatore ha provato e non ha scritto niente;
    - `ripiegata`: l'azione non era nemmeno eseguibile (tabella fuori allowlist,
      nessun campo riconosciuto) ed è diventata un task generico.

    Il secondo caso era il buco: non produce un `failed`, quindi il reparto non
    sapeva di aver sbagliato e riproponeva la stessa tabella inesistente il giorno
    dopo. Il 20 ago tutte e quattro le proposte di vendite sono finite così."""
    righe = _righe(client, "aios_audit", {
        "select": "seq,event,detail", "action_key": f"eq.{action_key}",
        "event": "in.(failed,ripiegata)", "order": "seq.desc",
        "limit": str(max(1, limit))})
    fuori = []
    for r in righe:
        d = r.get("detail") or {}
        if r.get("event") == "ripiegata" or d.get("causa"):
            fuori.append({
                "titolo": str(d.get("titolo") or "")[:120],
                "tabella": str(d.get("tabella_voluta") or "?")[:60],
                "op": "azione voluta",
                "errore": str(d.get("causa") or "azione non eseguibile")[:160]})
            continue
        esito = d.get("esito") or {}
        args = d.get("args") or {}
        azione = args.get("azione") or {}
        fuori.append({
            "titolo": str(args.get("titolo") or "")[:120],
            "tabella": esito.get("tabella") or azione.get("tabella") or "?",
            "op": esito.get("op") or azione.get("op") or "?",
            "errore": str(esito.get("errore") or "causa non riportata")[:160]})
    return fuori


def gia_proposto(client: Any, dominio: str,
                 limit: int = PROPOSTE_RECENTI_MAX) -> list[str]:
    """Titoli di quello che questo reparto ha già prodotto (deliverable recenti)."""
    righe = _righe(client, "aios_deliverables", {
        "select": "titolo", "dominio": f"eq.{dominio}",
        "order": "id.desc", "limit": str(max(1, limit))})
    visti, fuori = set(), []
    for r in righe:
        t = str(r.get("titolo") or "").strip()
        if t and t.lower() not in visti:
            visti.add(t.lower())
            fuori.append(t[:120])
    return fuori


def blocco_esperienza(client: Any, dominio: str, action_key: str) -> str:
    """Blocco da mettere nel prompt: gli errori da non ripetere e il già fatto."""
    if client is None:
        return ""
    falliti = fallimenti_recenti(client, action_key)
    fatti = gia_proposto(client, dominio)
    if not falliti and not fatti:
        return ""
    parti = ["\n\n# LA TUA ESPERIENZA (leggila prima di proporre)"]
    if falliti:
        parti.append("Queste TUE azioni recenti NON hanno scritto niente. Non riproporle "
                     "nella stessa forma: correggi campi e tabella, o cambia approccio.")
        for f in falliti:
            parti.append(f"- «{f['titolo']}» → {f['op']} su {f['tabella']}: {f['errore']}")
        parti.append("Regola: se una colonna non esiste, non esiste — non inventarla una "
                     "seconda volta. Se un update non trova la riga, prima va creata. "
                     "Se una tabella non è fra quelle del tuo reparto, non chiederla di "
                     "nuovo: usa una di quelle elencate sotto o proponi un task.")
    if fatti:
        parti.append("Hai già prodotto questo di recente: "
                     + "; ".join(f"«{t}»" for t in fatti)
                     + ". Non riproporre le stesse cose con parole diverse: o le porti "
                       "avanti con un passo NUOVO e concreto, o passi ad altro.")
    return "\n".join(parti)
