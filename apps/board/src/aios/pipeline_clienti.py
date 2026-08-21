"""La tabella clienti si aggiorna dalla posta, da sola.

Un lead in `pipeline_leads` invecchia male: viene creato `nuovo`, gli si scrive, il
cliente risponde — e nessuno sposta lo stato. Dopo due settimane la pipeline dice
«dieci lead nuovi» e non è vero per nessuno dei dieci.

Qui lo stato lo muove la posta. `email_messages` (alimentata da n8n con Outlook) porta
le email in entrata e in uscita; questo modulo le accoppia ai lead e sposta lo stato
lungo un ciclo dichiarato:

    nuovo → contattato → risposto → interessato → riunione → proposta → cliente
                              ↓                                  ↓
                            perso                             scartato

Le transizioni AUTOMATICHE sono solo le due che si deducono da un fatto, non da
un'interpretazione:
- email in USCITA verso il lead   → `contattato`  (e `last_contact_at`)
- email in ENTRATA dal lead       → `risposto`    (e `last_contact_at`)

`interessato`, `riunione`, `proposta`, `cliente`, `perso` richiedono di CAPIRE cosa
dice l'email: le propone l'agente Vendite leggendo il contenuto, non questo codice.
Meglio uno stato indietro che uno stato inventato.

LIMITE NOTO (21 ago 2026): il flusso n8n scrive `subject`, `body` e `direction` ma
lascia `from_email` e `received_at` a NULL su tutte le 200 email presenti. Senza
mittente l'accoppiamento si basa sul dominio del lead cercato nel testo, che prende
molto meno. Appena n8n mappa il mittente, l'accoppiamento diventa esatto senza
toccare questo file: `_mittente()` lo usa già se c'è.
"""
from __future__ import annotations

import re
from typing import Any

# Il ciclo di vita di un lead. `status` in pipeline_leads è testo libero: questo è il
# posto dove diventa un contratto invece di una convenzione a memoria.
STATI = ("nuovo", "contattato", "risposto", "interessato", "riunione", "proposta",
         "cliente", "perso", "scartato")
# Stati da cui una risposta del cliente ha senso come avanzamento. Da `cliente` o
# `perso` non si torna indietro per un'email: quelli li muove una persona.
_AVANZABILI = ("nuovo", "contattato", "risposto", "in_attesa", None, "")
_CHIUSI = ("cliente", "perso", "scartato")

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")


def _mittente(msg: dict) -> str:
    """L'indirizzo del mittente: dal campo se c'è, altrimenti dal testo.

    Il campo è la strada giusta ed è quella che si userà appena n8n lo mappa. Il
    ripiego sul testo serve a non stare fermi nel frattempo, e prende solo quando
    l'indirizzo compare nel corpo (firme, «rispondi a», thread citati)."""
    diretto = str(msg.get("from_email") or "").strip().lower()
    if diretto:
        return diretto
    testo = f"{msg.get('subject') or ''} {msg.get('body') or msg.get('body_preview') or ''}"
    trovati = [m.lower() for m in EMAIL_RE.findall(testo)]
    return trovati[0] if trovati else ""


def _dominio(indirizzo: str) -> str:
    return indirizzo.split("@")[-1].strip().lower() if "@" in indirizzo else ""


def accoppia(msg: dict, lead: list[dict]) -> dict | None:
    """Il lead a cui appartiene questa email, o None.

    Prima per indirizzo esatto, poi per dominio: `info@modulonet.com` e
    `commerciale@modulonet.com` sono la stessa azienda. Mai per nome dell'azienda nel
    testo: «Modulo» dentro il corpo di una newsletter accoppierebbe a caso."""
    mitt = _mittente(msg)
    if not mitt:
        return None
    for x in lead:
        if str(x.get("email") or "").strip().lower() == mitt:
            return x
    dom = _dominio(mitt)
    if not dom or dom in _DOMINI_GENERICI:
        return None
    for x in lead:
        if _dominio(str(x.get("email") or "")) == dom:
            return x
    return None


# Domini di posta condivisi: due lead diversi possono avere entrambi una @gmail.com,
# quindi il dominio da solo non identifica nessuno.
_DOMINI_GENERICI = frozenset({
    "gmail.com", "hotmail.com", "outlook.com", "outlook.it", "libero.it", "yahoo.it",
    "yahoo.com", "icloud.com", "live.it", "alice.it", "tin.it", "virgilio.it", "pec.it",
    "tiscali.it", "fastwebnet.it", "me.com", "protonmail.com",
})


def prossimo_stato(attuale: str | None, direzione: str) -> str | None:
    """Lo stato dopo un'email, o None se lo stato NON deve cambiare.

    None non vuol dire «ignora l'email»: un messaggio da un lead che è già `risposto`
    non lo fa avanzare — capire se è interessato è lavoro dell'agente — ma aggiorna
    quando l'abbiamo sentito l'ultima volta. Sono due cose distinte e chi chiama le
    tratta separatamente."""
    att = (attuale or "").strip().lower()
    if att in _CHIUSI:
        return None                      # una firma non si annulla per un'email
    if direzione == "in":
        nuovo = "risposto" if att in _AVANZABILI else None
    elif direzione == "out":
        # una nostra email non «declassa» un lead che ha già risposto
        nuovo = "contattato" if att in ("nuovo", "", None) else None
    else:
        return None
    return None if nuovo == att else nuovo


def aggiorna_da_email(client: Any, *, limite_email: int = 60,
                      limite_lead: int = 200) -> dict[str, Any]:
    """Sposta gli stati dei lead in base alle email, e riporta cosa ha cambiato.

    Non solleva: è pensata per girare dentro il loop di autonomia, dove un errore di
    lettura non deve fermare il resto del giro. Ritorna sempre un resoconto leggibile,
    compresi i motivi per cui NON ha fatto niente — che è l'informazione che serve
    quando la posta non porta il mittente."""
    resoconto: dict[str, Any] = {"email_lette": 0, "accoppiate": 0, "aggiornati": [],
                                 "contatti_registrati": [], "senza_mittente": 0,
                                 "non_accoppiate": 0, "errori": []}
    try:
        lead = client.select("pipeline_leads",
                             {"select": "id,name,email,status,last_contact_at",
                              "order": "created_at.desc", "limit": str(limite_lead)})
    except Exception as exc:
        resoconto["errori"].append(f"lettura lead: {str(exc)[:160]}")
        return resoconto
    lead = [x for x in (lead or []) if str(x.get("email") or "").strip()]
    if not lead:
        resoconto["errori"].append("nessun lead con email: niente da accoppiare")
        return resoconto
    try:
        email = client.select("email_messages",
                              {"select": "id,from_email,subject,body,body_preview,"
                                         "direction,received_at,created_at",
                               "order": "created_at.desc", "limit": str(limite_email)})
    except Exception as exc:
        resoconto["errori"].append(f"lettura email: {str(exc)[:160]}")
        return resoconto

    resoconto["email_lette"] = len(email or [])
    visti: set[str] = set()               # un lead si muove una volta per giro
    for msg in (email or []):
        if not _mittente(msg):
            resoconto["senza_mittente"] += 1
            continue
        trovato = accoppia(msg, lead)
        if trovato is None:
            resoconto["non_accoppiate"] += 1
            continue
        resoconto["accoppiate"] += 1
        chiave = str(trovato.get("id"))
        if chiave in visti:
            continue
        stato = str(trovato.get("status") or "")
        nuovo = prossimo_stato(stato, str(msg.get("direction") or ""))
        quando = msg.get("received_at") or msg.get("created_at")
        if stato.lower() in _CHIUSI:
            continue                     # su un lead chiuso non si scrive nulla
        patch: dict[str, Any] = {}
        if nuovo:
            patch["status"] = nuovo
        if quando:
            # Anche senza avanzamento di stato: «quando l'abbiamo sentito» è
            # esattamente ciò che serve per capire quali lead stanno morendo.
            patch["last_contact_at"] = quando
        if not patch:
            continue
        try:
            client.update("pipeline_leads", {"id": f"eq.{trovato['id']}"}, patch)
        except Exception as exc:
            resoconto["errori"].append(f"{trovato.get('name')}: {str(exc)[:120]}")
            continue
        visti.add(chiave)
        voce = {"lead": trovato.get("name"), "email": str(msg.get("subject") or "")[:80]}
        if nuovo:
            resoconto["aggiornati"].append({**voce, "da": stato, "a": nuovo})
        else:
            resoconto["contatti_registrati"].append({**voce, "stato": stato})
    return resoconto


def tabella(client: Any, limite: int = 100) -> dict[str, Any]:
    """La tabella clienti come la si vuole leggere: righe più conteggio per stato.

    Serve all'agente e all'owner per avere lo STESSO quadro: senza un conteggio
    dichiarato, «come va la pipeline?» si risponde a impressione."""
    try:
        righe = client.select("pipeline_leads",
                              {"select": "name,email,status,score,next_action,"
                                         "next_action_date,last_contact_at,sector",
                               "order": "score.desc", "limit": str(limite)})
    except Exception as exc:
        return {"errore": str(exc)[:160], "righe": [], "per_stato": {}}
    righe = [x for x in (righe or []) if not str(x.get("name") or "").startswith("Sonda")]
    per_stato: dict[str, int] = {}
    for x in righe:
        s = str(x.get("status") or "senza stato").lower()
        per_stato[s] = per_stato.get(s, 0) + 1
    aperti = sum(n for s, n in per_stato.items() if s not in _CHIUSI)
    return {"totale": len(righe), "aperti": aperti, "per_stato": per_stato,
            "stati_possibili": list(STATI), "righe": righe}
