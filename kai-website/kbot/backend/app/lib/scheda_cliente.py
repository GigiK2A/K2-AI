"""SCHEDA DEL CLIENTE: i fatti stabili che l'utente ha detto, estratti a ogni turno e rimessi nel prompt.

Il problema (misurato il 19/10/2026, 13 turni con il modello locale): il modello vede solo gli ultimi 12
messaggi e i più vecchi tagliati a 900 caratteri. Un fatto detto al turno 1 (città, quota del socio, nome)
dopo ~8 turni spariva, e al suo posto il modello ne INVENTAVA un altro: «siete a Torino» (l'utente aveva detto
Foligno), una ragione sociale mai pronunciata. Nessun dato veniva conservato finché non esisteva un summary.

Questo modulo, per ogni turno:
  1. chiede al modello (temperatura 0) i fatti NUOVI o CORRETTI nel messaggio dell'utente, ognuno con la
     CITAZIONE esatta del messaggio che lo sostiene;
  2. VERIFICA in codice: la citazione deve comparire davvero nel testo dell'utente e i numeri del valore
     devono stare nella citazione. Un fatto senza prova nel testo dell'utente viene scartato — è la difesa
     contro il modello che «ricorda» ciò che non è stato detto (e contro un fatto detto dal consulente);
  3. fonde nella scheda (l'ultimo valore vince: «in realtà siamo 15» sostituisce «14»);
  4. la scheda torna nel prompt di ogni turno, e per gli utenti autenticati confluisce nel profilo.

Tutto fail-open: su qualunque errore la scheda resta com'era e la chat funziona come prima.
KBOT_SCHEDA_CLIENTE=0 spegne.
"""
from __future__ import annotations

import logging
import os
import re
import unicodedata
from typing import Any, Optional

from .norme_evidence import _json_tollerante

log = logging.getLogger(__name__)

MAX_FATTI = int(os.getenv("KBOT_SCHEDA_MAX_FATTI", "40"))
MAX_VALORE = 160
MIN_CHARS_MESSAGGIO = 12
_TIMEOUT = float(os.getenv("KBOT_SCHEDA_TIMEOUT", "40"))
_CHIAVE = re.compile(r"^[a-z][a-z0-9_]{1,39}$")
_NUM = re.compile(r"\d+(?:[.,]\d+)*")

_SISTEMA = (
    "Estrai dal MESSAGGIO DELL'UTENTE i fatti stabili sull'utente e sulla sua azienda: chi è, ruolo, nome e forma "
    "dell'azienda, città della sede, settore, numero di dipendenti, fatturato, soci e quote, clienti o fornitori "
    "specifici, date, importi, contratti, problemi concreti con i loro numeri.\n"
    "REGOLE:\n"
    "- solo ciò che l'UTENTE ha scritto in questo messaggio; mai ciò che ha detto il consulente, mai ipotesi, "
    "mai domande;\n"
    "- per ogni fatto: chiave (snake_case, es. citta, dipendenti, fatturato, ragione_sociale, forma_giuridica, "
    "settore, nome_utente, soci, problema_principale), valore breve, e citazione = la frase o il pezzo di frase "
    "COPIATO ESATTAMENTE dal messaggio dell'utente che contiene quel fatto;\n"
    "- riporta i numeri come li ha scritti l'utente, senza convertirli o arrotondarli;\n"
    "- «citta» è la sede dell'azienda dell'utente, non la città di un cliente o di un fornitore;\n"
    "- se il messaggio corregge un fatto già in scheda, restituisci la stessa chiave col valore nuovo;\n"
    "- se non ci sono fatti nuovi o corretti: {\"fatti\": []}.\n"
    "Rispondi SOLO con JSON: {\"fatti\": [{\"chiave\": \"...\", \"valore\": \"...\", \"citazione\": \"...\"}]}"
)


def _enabled() -> bool:
    return os.getenv("KBOT_SCHEDA_CLIENTE", "1") != "0"


def _norm(t: str) -> str:
    """Minuscolo, senza accenti, spazi compressi, punteggiatura ridotta: per confrontare citazione e testo."""
    t = unicodedata.normalize("NFKD", str(t or "")).encode("ascii", "ignore").decode("ascii").lower()
    t = re.sub(r"[^a-z0-9%€,.\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _numeri(t: str) -> set[str]:
    return {m.group(0).strip(".,") for m in _NUM.finditer(str(t or ""))}


def verifica(fatto: dict, testo_utente: str) -> Optional[dict]:
    """Il fatto, ripulito, se è provato dal testo dell'utente; altrimenti None."""
    if not isinstance(fatto, dict):
        return None
    chiave = str(fatto.get("chiave") or "").strip().lower().replace(" ", "_").replace("-", "_")
    valore = re.sub(r"\s+", " ", str(fatto.get("valore") or "")).strip()[:MAX_VALORE]
    cit = re.sub(r"\s+", " ", str(fatto.get("citazione") or "")).strip()
    if not _CHIAVE.match(chiave) or not valore or len(cit) < 3:
        return None
    if _norm(cit) not in _norm(testo_utente):
        return None                                   # la citazione non è nel messaggio dell'utente
    if not _numeri(valore) <= _numeri(cit):
        return None                                   # numero nel valore che la citazione non contiene
    if re.search(r"scheda del cliente|profilo cliente", valore, re.I):
        return None                                   # niente marcatori del prompt dentro i valori
    return {"valore": valore, "citazione": cit[:200]}


def _chiedi_al_modello(client, modello: str, scheda: dict, messaggio: str, ultima_domanda: str) -> str:
    in_scheda = "\n".join(f"- {k}: {v['valore']}" for k, v in scheda.items()) or "(vuota)"
    utente = f"SCHEDA ATTUALE:\n{in_scheda}\n\n"
    if ultima_domanda.strip():
        utente += (f"ULTIMA DOMANDA DEL CONSULENTE (solo per capire a cosa risponde l'utente, "
                   f"NON è una fonte di fatti):\n{ultima_domanda.strip()[:400]}\n\n")
    utente += f"MESSAGGIO DELL'UTENTE:\n{messaggio.strip()[:3000]}"
    base = dict(model=modello, max_tokens=700, system=_SISTEMA,
                messages=[{"role": "user", "content": utente}], timeout=_TIMEOUT)
    try:
        r = client.messages.create(**base, extra_body={"temperature": 0})
    except Exception as e:  # alcuni modelli rifiutano la temperatura: si riprova senza
        if isinstance(e, TypeError) or getattr(e, "status_code", None) in (400, 422):
            r = client.messages.create(**base)
        else:
            raise
    return "".join(b.text for b in r.content if getattr(b, "type", "") == "text")


def aggiorna(client, modello: str, scheda: Optional[dict], messaggio: str,
             ultima_domanda: str = "", turno: int = 0, testo_utente_tutto: str = "") -> dict:
    """Come `aggiorna_ok`, ma ritorna solo la scheda."""
    return aggiorna_ok(client, modello, scheda, messaggio, ultima_domanda, turno, testo_utente_tutto)[0]


def aggiorna_ok(client, modello: str, scheda: Optional[dict], messaggio: str,
                ultima_domanda: str = "", turno: int = 0, testo_utente_tutto: str = "") -> tuple[dict, bool]:
    """(scheda aggiornata, elaborato). Non solleva mai: su errore ritorna la scheda com'era e elaborato=False,
    così il chiamante NON considera «letto» quel messaggio e al turno dopo lo riprova.

    `testo_utente_tutto` = tutti i messaggi dell'utente finora; la citazione può stare in uno qualsiasi
    (un utente che risponde «sì, il 30%» richiama la domanda precedente), ma il messaggio corrente è la fonte
    principale e per i fatti nuovi si controlla prima quello."""
    scheda = dict(scheda or {})
    if not _enabled() or len((messaggio or "").strip()) < MIN_CHARS_MESSAGGIO:
        return scheda, True                              # niente da leggere: il messaggio conta come elaborato
    try:
        out = _chiedi_al_modello(client, modello, scheda, messaggio, ultima_domanda)
        v = _json_tollerante(out) or {}
        nuovi = 0
        for f in (v.get("fatti") or [])[:20]:
            ok = verifica(f, messaggio) or (verifica(f, testo_utente_tutto) if testo_utente_tutto else None)
            if not ok:
                if isinstance(f, dict):
                    log.info("scheda_cliente: scartato senza prova nel testo: %s=%r", f.get("chiave"), f.get("valore"))
                continue
            chiave = str(f["chiave"]).strip().lower().replace(" ", "_").replace("-", "_")
            if scheda.get(chiave, {}).get("valore") != ok["valore"]:
                scheda[chiave] = {**ok, "turno": int(turno)}
                nuovi += 1
        if len(scheda) > MAX_FATTI:                     # si tengono i più recenti
            for k, _ in sorted(scheda.items(), key=lambda kv: kv[1].get("turno", 0))[:len(scheda) - MAX_FATTI]:
                scheda.pop(k, None)
        if nuovi:
            log.info("scheda_cliente: +%d fatti (totale %d)", nuovi, len(scheda))
        return scheda, True
    except Exception:
        log.warning("scheda_cliente: estrazione fallita (fail-open)", exc_info=True)
        return scheda, False


def render_block(scheda: Optional[dict]) -> str:
    """Blocco del system prompt ('' se la scheda è vuota)."""
    if not isinstance(scheda, dict) or not scheda:
        return ""
    righe = [f"{k.replace('_', ' ')}: {v.get('valore')}" for k, v in scheda.items()
             if isinstance(v, dict) and v.get("valore")]
    if not righe:
        return ""
    return (
        "\nSCHEDA DEL CLIENTE (fatti che l'UTENTE ha detto in questa conversazione — è la fonte di verità su "
        "di lui e sulla sua azienda. Non cambiarli, non ometterli quando servono, NON inventarne altri: se ti "
        "serve un dato che qui non c'è — nome dell'azienda, città, quote, numeri — dì che non lo hai e chiedilo. "
        "Se ciò che l'utente dice ADESSO li contraddice, vale ciò che dice adesso):\n- "
        + "\n- ".join(righe) + "\n"
    )


def piatta(scheda: Optional[dict]) -> dict:
    """{chiave: valore} per chi non ha bisogno di citazioni (profilo)."""
    if not isinstance(scheda, dict):
        return {}
    return {k: v["valore"] for k, v in scheda.items() if isinstance(v, dict) and v.get("valore")}
