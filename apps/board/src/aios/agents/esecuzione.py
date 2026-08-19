"""Chi decide se un'azione parte da sola o va in coda — e cosa si racconta all'owner.

Regola dell'owner (ago 2026): «non voglio dare autorizzazioni su cose banali; se
qualcosa legalmente è sbagliata l'agente la sistema in automatico senza chiedermelo,
ma dicendomelo». Tradotto:

- INTERNO (insert/update/upsert su tabelle del board) → si fa subito e si riporta;
- ESTERNO (email, social, n8n, ads), DELETE e DDL → restano ad approvazione umana,
  perché escono dall'azienda o sono distruttivi.

L'autonomia interna si accende con AIOS_INTERNAL_AUTONOMY=1. Anche quando è accesa
tutto passa dall'audit: autonomo non vuol dire invisibile.
"""
from __future__ import annotations

import os
from collections import Counter
from typing import Any


def autonomia_interna_attiva() -> bool:
    return os.environ.get("AIOS_INTERNAL_AUTONOMY") == "1"


def applica_o_accoda(kernel: Any, tool_name: str, actor: str,
                     proposta: dict[str, Any]) -> tuple[str, Any]:
    """Esegue subito o accoda, secondo la classificazione dell'azione.

    Ritorna ('eseguita', dict_esito) oppure ('in_coda', approval_id | None).
    Il dict_esito porta titolo/tabella/op/ok/errore: è quello che finisce nel
    riepilogo mandato all'owner."""
    from aios.actuator import is_autonomous_internal

    azione = proposta.get("azione") or {}
    if autonomia_interna_attiva() and is_autonomous_internal(azione):
        res = kernel.execute_now(tool_name, actor=actor, args=proposta)
        esito = res.esito or {}
        return "eseguita", {
            "titolo": str(proposta.get("titolo") or "")[:120],
            "reparto": actor,
            "tabella": esito.get("tabella") or azione.get("tabella") or "?",
            "op": esito.get("op") or azione.get("op") or "?",
            "ok": bool(res.eseguita_davvero),
            "errore": esito.get("errore"),
        }
    res = kernel.execute(tool_name, actor=actor, args=proposta)
    return "in_coda", res.approval_id


def riepilogo(eseguite: list[dict[str, Any]]) -> str:
    """Riga leggibile di cosa gli agenti hanno fatto da soli. Vuota se non c'è nulla:
    un messaggio per ogni singola scrittura sarebbe 40 notifiche al giorno, quindi si
    riassume per tabella e si dettagliano solo i fallimenti."""
    if not eseguite:
        return ""
    ok = [e for e in eseguite if e.get("ok")]
    ko = [e for e in eseguite if not e.get("ok")]
    righe = []
    if ok:
        conteggio = Counter(f"{e['tabella']}" for e in ok)
        dettaglio = ", ".join(f"{t}×{n}" if n > 1 else t
                              for t, n in conteggio.most_common())
        righe.append(f"✅ {len(ok)} scritture interne fatte da sole: {dettaglio}")
    for e in ko:
        righe.append(f"⚠️ NON riuscita — {e['titolo']} ({e['tabella']}): "
                     f"{e.get('errore') or 'causa non riportata'}")
    return "\n".join(righe)
