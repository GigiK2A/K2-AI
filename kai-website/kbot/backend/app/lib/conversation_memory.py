"""Sintesi progressiva della conversazione — memoria di lungo periodo del singolo dialogo.

Il problema che risolve: la finestra inviata al modello è per forza limitata, quindi in una
conversazione lunga i primi turni ne escono. Prima uscivano e finivano nel nulla: il bot
ri-chiedeva dati già forniti e perdeva il problema iniziale (la `diagnosi` teneva 4 ipotesi
e un dato mancante, non i FATTI). Qui, ogni N messaggi che escono dalla finestra vengono
compressi in un blocco di testo — fatti, numeri, decisioni, punti aperti — che viaggia nel
system prompt di tutti i turni successivi.

Dove vive: `collected_data.rolling_summary = {text, upto, at}`, dove `upto` è quanti
messaggi della conversazione la sintesi copre già. Nessuna tabella nuova.

Costo: 1 chiamata Haiku ogni ~6 messaggi usciti dalla finestra, eseguita DOPO che la
risposta è stata consegnata all'utente (mai sul percorso critico del turno). Fail-open
ovunque: un errore qui non deve mai rompere la chat. ROLLING_SUMMARY_EVERY=0 disattiva.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List, Optional

from ..settings import ROLLING_SUMMARY_EVERY, ROLLING_SUMMARY_MAX_CHARS

log = logging.getLogger(__name__)

KEY = "rolling_summary"
# Tetti del transcript mandato al modello. Servono a rendere il costo della sintesi
# COSTANTE invece che crescente con la lunghezza della conversazione.
_TRANSCRIPT_MSG_CAP = 2000
_TRANSCRIPT_TOTAL_CAP = 40000

_SYSTEM = (
    "Sei l'archivista di una consulenza aziendale in corso. Ti viene dato l'inizio di una "
    "conversazione tra un consulente (assistant) e un imprenditore (user), più la sintesi "
    "precedente se esiste. Produci UNA sintesi aggiornata che serva al consulente per non "
    "perdere nulla quando quei messaggi non saranno più visibili.\n"
    "Regole ferree:\n"
    "- Conserva TUTTI i fatti concreti detti dall'utente: numeri, importi, date, nomi, "
    "ruoli, settore, dimensioni, vincoli, scadenze. Se un numero c'è, deve restare.\n"
    "- Conserva le DECISIONI prese e le richieste esplicite dell'utente (es. «non voglio "
    "il report», «procedi», «prima risolviamo X»).\n"
    "- Conserva i punti ANCORA APERTI e le domande a cui l'utente non ha risposto.\n"
    "- NON inventare nulla, NON dedurre, NON aggiungere consigli tuoi, NON commentare.\n"
    "- Niente preamboli, niente titoli decorativi: solo il contenuto, in italiano, per "
    "punti brevi. Massimo {max_chars} caratteri."
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def enabled() -> bool:
    return ROLLING_SUMMARY_EVERY > 0


def get(collected: Optional[dict]) -> Optional[dict]:
    """La sintesi corrente, o None."""
    entry = (collected or {}).get(KEY)
    if isinstance(entry, dict) and str(entry.get("text") or "").strip():
        return entry
    return None


def render_block(collected: Optional[dict]) -> str:
    """Blocco per il system prompt ('' se non c'è sintesi)."""
    entry = get(collected)
    if not entry:
        return ""
    return (
        "\nSINTESI DELLA CONVERSAZIONE PRECEDENTE (i primi messaggi non sono più nel "
        "contesto: questo è ciò che è stato detto — USALO, non richiedere dati già presenti "
        "qui; se l'utente ORA contraddice la sintesi, vale ciò che dice ora):\n"
        + str(entry["text"]).strip() + "\n"
    )


def covered(collected: Optional[dict]) -> int:
    """Quanti messaggi della conversazione sono già coperti dalla sintesi."""
    entry = get(collected)
    try:
        return max(0, int((entry or {}).get("upto") or 0))
    except (TypeError, ValueError):
        return 0


def outside_window(total_messages: int, window_len: int) -> int:
    """Messaggi rimasti FUORI dalla finestra verbatim inviata al modello."""
    return max(0, int(total_messages) - int(window_len))


def is_stale(collected: Optional[dict], total_messages: int, window_len: int) -> bool:
    """True se sono usciti dalla finestra almeno ROLLING_SUMMARY_EVERY messaggi non ancora
    riassunti. Finché la conversazione sta tutta nella finestra, la sintesi non serve."""
    if not enabled():
        return False
    out = outside_window(total_messages, window_len)
    if out <= 0:
        return False
    return (out - covered(collected)) >= ROLLING_SUMMARY_EVERY


def _transcript(messages: List[dict], start: int, upto: int) -> tuple[str, int]:
    """Il transcript dei messaggi in `[start, upto)`, dentro tetti fissi.

    Ritorna `(testo, coperto_fino_a)`. Due proprietà che servono entrambe:

    - **Incrementale.** Si riparte da dove finiva la sintesi precedente, non da zero: la
      sintesi vecchia viene comunque data al modello, quindi rimandargli anche i messaggi
      già riassunti è spreco che cresce con la conversazione.
    - **Autolimitante.** Se la fetta sfonda il tetto complessivo, si include solo la parte
      iniziale e `coperto_fino_a` dice fin dove si è arrivati davvero: il refresh successivo
      riprende da lì. Senza questo, una conversazione lunga finiva per costruire un payload
      sempre più grande e, superata la finestra del modello, la sintesi falliva a ogni
      tentativo — per sempre, e in silenzio (build è fail-open).
    """
    lines: List[str] = []
    used = 0
    covered = start
    for i in range(max(0, start), min(int(upto), len(messages or []))):
        m = messages[i]
        if not isinstance(m, dict):
            covered = i + 1
            continue
        text = str(m.get("content") or "").strip()
        if not text:
            covered = i + 1
            continue
        if len(text) > _TRANSCRIPT_MSG_CAP:
            text = text[:_TRANSCRIPT_MSG_CAP - 1].rstrip() + "…"
        if lines and used + len(text) > _TRANSCRIPT_TOTAL_CAP:
            break
        role = "UTENTE" if m.get("role") == "user" else "CONSULENTE"
        lines.append(f"{role}: {text}")
        used += len(text)
        covered = i + 1
    return "\n\n".join(lines), covered


def build(client, model: str, messages: List[dict], collected: Optional[dict],
          window_len: int) -> Optional[dict]:
    """Genera la sintesi aggiornata. Ritorna la nuova entry o None (nulla da fare/errore)."""
    if not enabled():
        return None
    upto = outside_window(len(messages or []), window_len)
    if upto <= 0:
        return None
    previous = get(collected)
    start = covered(collected)
    if start >= upto:
        return None
    body, upto = _transcript(messages, start, upto)
    if not body.strip():
        return None
    prefix = ""
    if previous:
        prefix = (
            "SINTESI PRECEDENTE (aggiornala e integrala, non ripartire da zero):\n"
            + str(previous["text"]).strip() + "\n\n"
        )
    try:
        resp = client.messages.create(
            model=model,
            max_tokens=1500,
            system=_SYSTEM.format(max_chars=ROLLING_SUMMARY_MAX_CHARS),
            messages=[{"role": "user", "content":
                       f"{prefix}CONVERSAZIONE DA RIASSUMERE:\n{body}"}],
            timeout=45.0,
        )
        text = "".join(
            getattr(b, "text", "") for b in resp.content
            if getattr(b, "type", "") == "text"
        ).strip()
    except Exception:
        log.warning("sintesi conversazione: generazione fallita (fail-open)", exc_info=True)
        return None
    if not text:
        return None
    return {"text": text[:ROLLING_SUMMARY_MAX_CHARS], "upto": upto, "at": _now_iso()}


def refresh_if_stale(client, model: str, session_id: str, window_len: int) -> None:
    """Rigenera e persiste la sintesi se serve. Da chiamare DOPO aver consegnato la
    risposta all'utente: non deve mai aggiungere latenza al turno.

    Rilegge la sessione invece di fidarsi del `collected` in memoria, così non sovrascrive
    quello che il turno ha appena salvato. Best-effort: non solleva mai.
    """
    if not enabled():
        return
    try:
        from . import sessions
        session = sessions.get_session(session_id)
        if not session:
            return
        collected = dict(session.get("collected_data") or {})
        messages = session.get("messages") or []
        if not is_stale(collected, len(messages), window_len):
            return
        entry = build(client, model, messages, collected, window_len)
        if not entry:
            return
        collected[KEY] = entry
        sessions.update_session(session_id, {"collected_data": collected})
        log.info("sintesi conversazione aggiornata: session=%s copre %d messaggi",
                 session_id, entry["upto"])
    except Exception:
        log.warning("sintesi conversazione: refresh fallito (fail-open)", exc_info=True)
