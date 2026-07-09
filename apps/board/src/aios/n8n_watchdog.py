"""Watchdog n8n: controlla lo stato delle esecuzioni e interviene.

Modello di autonomia (deciso con l'owner):
- fallimenti TRANSITORI (rete/5xx/rate-limit/Meta is_transient) → RIAVVIO automatico,
  con tetto ai retry (per non insistere su qualcosa che rifallisce all'infinito);
- tutto il resto (credenziali, validazione, workflow disattivato, blocco in esecuzione)
  → NON si tocca: si DIAGNOSTICA e si PROPONE il fix, che l'owner conferma.

Non modifica mai da solo il JSON di un workflow di produzione. Le proposte finiscono
nel report e (best-effort) nella tabella `n8n_watchdog_log` su Supabase.
"""
from __future__ import annotations

import re
import time
from typing import Any, Callable

from aios.sources.n8n import (list_executions, get_execution, list_workflows,
                              restart_workflow, n8n_api_enabled)

# Errori su cui il riavvio ha senso (transitori). Default = strutturale (serve l'owner):
# meglio non riavviare in loop qualcosa che rifallirà comunque.
_TRANSIENT = re.compile(
    r"(network|timeout|timed out|etimedout|econnreset|econnrefused|econnaborted|"
    r"enetunreach|ehostunreach|socket hang up|connection reset|"
    r"getaddrinfo|EAI_AGAIN|temporar|rate.?limit|too many requests|\b429\b|"
    r"\b50[234]\b|bad gateway|service unavailable|gateway timeout|is_transient|"
    r"2207032|prova a crearlo|riprova|please try again)", re.I)

# Indizi per il suggerimento di fix (solo per la PROPOSTA, non si esegue nulla).
_FIX_HINTS = [
    (re.compile(r"(token|oauth|401|403|unauthorized|forbidden|credential|access.?denied|"
                r"code.?190|session)", re.I),
     "Sembra un problema di credenziale/token: rinnova la credenziale del nodo in n8n."),
    (re.compile(r"(400|bad request|invalid|validation|required|missing|schema|parametro)", re.I),
     "Sembra un parametro/campo non valido: controlla i dati in ingresso del nodo."),
    (re.compile(r"(not found|404|no such|undefined|cannot read|null)", re.I),
     "Un riferimento manca (campo/URL/risorsa): verifica mapping e sorgente dati."),
]

STUCK_MINUTES = 30            # 'running' più vecchio di così = probabilmente bloccato
DEFAULT_LIMIT = 50


def classify(msg: str) -> str:
    """transient (riavviabile) | structural (serve l'owner)."""
    return "transient" if _TRANSIENT.search(msg or "") else "structural"


def _fix_hint(msg: str) -> str:
    for pat, hint in _FIX_HINTS:
        if pat.search(msg or ""):
            return hint
    return "Guarda il nodo che fallisce nell'esecuzione n8n per capire la causa."


def _deep_signal(err: dict) -> str:
    """Segnali PROFONDI dell'errore n8n oltre a 'message': description + messages[] spesso
    contengono il vero errore dell'API (es. il JSON Meta col error_subcode 2207032), che
    serve a classificare bene transient vs structural."""
    bits: list[str] = []
    if err.get("description"):
        bits.append(str(err["description"]))
    for m in (err.get("messages") or []):
        bits.append(str(m))
        # se dentro c'è un JSON tipo Graph API, estrai i campi utili
        s = str(m)
        i, j = s.find("{"), s.rfind("}")
        if 0 <= i < j:
            try:
                blob = json.loads(s[i:j + 1])
                e = blob.get("error", blob) if isinstance(blob, dict) else {}
                for k in ("error_subcode", "error_user_title", "error_user_msg",
                          "is_transient", "code"):
                    if e.get(k) not in (None, ""):
                        bits.append(f"{k}={e[k]}")
            except Exception:
                pass
    return " ".join(bits)[:600]


def _extract_error(execdata: Any) -> tuple[str, str]:
    """Trova (messaggio, nodo) nell'oggetto esecuzione n8n, in modo difensivo.
    Il messaggio include anche i segnali profondi (subcode Meta, ecc.) così la classify
    non si ferma alla stringa generica 'Bad request'."""
    msg, node = "", ""

    def walk(o: Any, depth: int = 0):
        nonlocal msg, node
        if msg or depth > 6 or not isinstance(o, (dict, list)):
            return
        if isinstance(o, dict):
            err = o.get("error")
            if isinstance(err, dict) and (err.get("message") or err.get("messages")):
                base = str(err.get("message") or "")[:200]
                deep = _deep_signal(err)
                msg = (base + (" | " + deep if deep else "")).strip()[:600]
                n = err.get("node")
                node = str((n or {}).get("name") if isinstance(n, dict) else n or "")[:120]
                return
            if o.get("lastNodeExecuted"):
                node = node or str(o.get("lastNodeExecuted"))[:120]
            for v in o.values():
                walk(v, depth + 1)
        else:
            for v in o:
                walk(v, depth + 1)

    walk(execdata)
    return msg, node


def _latest_per_workflow(execs: list[dict]) -> list[dict]:
    """Le esecuzioni arrivano dalla più recente: tiene la prima vista per ogni workflow."""
    seen, out = set(), []
    for e in execs:
        wid = e.get("workflowId")
        if wid in seen:
            continue
        seen.add(wid)
        out.append(e)
    return out


def _minutes_since(iso: str | None, now: float) -> float | None:
    if not iso:
        return None
    try:
        from datetime import datetime
        t = datetime.fromisoformat(str(iso).replace("Z", "+00:00")).timestamp()
        return max(0.0, (now - t) / 60.0)
    except Exception:
        return None


def _retry_count(log_client: Any, workflow_id: str, day: str) -> int:
    if log_client is None or not workflow_id:
        return 0
    try:
        rows = log_client.select("n8n_watchdog_log", {
            "select": "id", "workflow_id": f"eq.{workflow_id}",
            "azione": "eq.riavvio", "giorno": f"eq.{day}"})
        return len(rows or [])
    except Exception:
        return 0


def _log(log_client: Any, row: dict) -> None:
    if log_client is None:
        return
    try:
        log_client.insert("n8n_watchdog_log", row)
    except Exception:
        pass


def check_and_heal(*, log_client: Any = None, retry_cap: int = 2, retrigger: bool = True,
                   limit: int = DEFAULT_LIMIT,
                   list_exec: Callable = list_executions, get_exec: Callable = get_execution,
                   list_wf: Callable = list_workflows, restart: Callable = restart_workflow,
                   now: float | None = None) -> dict[str, Any]:
    """Giro del watchdog: legge le esecuzioni recenti, riavvia i transitori (con tetto),
    propone i fix per gli strutturali/bloccati. Ritorna un report strutturato."""
    if not n8n_api_enabled():
        return {"ok": False, "errore": "n8n API non configurata (N8N_API_URL/N8N_API_KEY)"}
    now = now if now is not None else time.time()
    from datetime import datetime, timezone
    day = datetime.fromtimestamp(now, tz=timezone.utc).strftime("%Y-%m-%d")

    res = list_exec(limit=limit)
    if not res.get("ok"):
        return {"ok": False, "errore": res.get("errore"), "controllati": 0}

    names: dict[str, str] = {}
    try:
        for w in (list_wf() or []):
            names[str(w.get("id"))] = str(w.get("name") or w.get("id"))
    except Exception:
        pass

    latest = _latest_per_workflow(res.get("esecuzioni") or [])
    ok_count, riavviati, proposte = 0, [], []

    for e in latest:
        wid = str(e.get("workflowId") or "")
        wname = names.get(wid, wid or "?")
        status = str(e.get("status") or "").lower()

        if status in ("success", "succeeded"):
            ok_count += 1
            continue

        if status == "running":
            mins = _minutes_since(e.get("startedAt"), now)
            if mins is not None and mins >= STUCK_MINUTES:
                proposte.append({"workflow": wname, "workflow_id": wid, "tipo": "bloccato",
                                 "dettaglio": f"in esecuzione da {int(mins)} min — probabile blocco",
                                 "suggerimento": "Verifica in n8n e, se serve, ferma/rilancia a mano."})
            else:
                ok_count += 1        # ancora in corso, tempo normale
            continue

        if status in ("error", "failed", "crashed"):
            msg, node = _extract_error(get_exec(e.get("id")))
            kind = classify(msg)
            if kind == "transient" and retrigger:
                already = _retry_count(log_client, wid, day)
                if already >= retry_cap:
                    proposte.append({"workflow": wname, "workflow_id": wid, "tipo": "retry_esaurito",
                                     "nodo": node, "errore": msg,
                                     "suggerimento": (f"Già riavviato {already} volte oggi senza "
                                                      "successo: serve un intervento manuale.")})
                    continue
                out = restart(wid, wname)
                riavviato = bool(out.get("ok"))
                riavviati.append({"workflow": wname, "workflow_id": wid, "nodo": node,
                                  "errore": msg, "riavviato": riavviato,
                                  "via": out.get("via"),
                                  "esito": out.get("errore") if not riavviato else "ri-eseguito"})
                _log(log_client, {"giorno": day, "workflow_id": wid, "workflow": wname,
                                  "azione": "riavvio", "esito": "ok" if riavviato else "ko",
                                  "errore": msg[:300]})
            else:
                proposte.append({"workflow": wname, "workflow_id": wid, "tipo": "strutturale",
                                 "nodo": node, "errore": msg, "suggerimento": _fix_hint(msg)})
                _log(log_client, {"giorno": day, "workflow_id": wid, "workflow": wname,
                                  "azione": "proposta", "esito": "in_attesa", "errore": msg[:300]})

    return {"ok": True, "giorno": day, "controllati": len(latest), "in_ordine": ok_count,
            "riavviati": riavviati, "proposte": proposte,
            "riassunto": (f"{len(latest)} workflow controllati · {ok_count} ok · "
                          f"{len(riavviati)} riavviati · {len(proposte)} da vedere")}
