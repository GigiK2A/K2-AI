"""Telegram e il cockpit sono LA STESSA conversazione.

Prima su Telegram parlavi col CommandRouter — istruzione singola, esegui, dimentica: né
storico, né memoria, né dibattito fra reparti. Nel cockpit invece c'era il
ChatOrchestrator con sessioni persistenti. Due chat diverse sugli stessi agenti: quello
che chiedevi da telefono non esisteva per quello che vedevi dal browser.

Qui il testo di Telegram passa dal ChatOrchestrator e si appoggia alle STESSE tabelle
(`aios_chat_sessions`, `aios_chat_messages`), su una sessione stabile per chat: quindi
la conversazione compare nel cockpit, si può continuare da lì, e viceversa.

Il CommandRouter non si perde per due motivi: la chat lo usa già al suo interno per
eseguire (`_classify`/`_queue`/`_exec_internal`, vedi chat_runner), e resta comunque
raggiungibile in forma secca col prefisso «!» per quando vuoi un comando e non una
conversazione.
"""
from __future__ import annotations

from typing import Any

from aios.notify import telegram

TITOLO_SESSIONE = "Telegram"
STORICO_MAX = 40          # turni caricati come memoria
MESSAGGIO_MAX = 3500      # Telegram taglia a 4096: si sta sotto con margine
PREFISSO_COMANDO = "!"    # "!fai X" → CommandRouter secco, senza conversazione


def _client(platform: Any):
    return getattr(getattr(platform, "kernel", None), "_supabase", None)


def sessione(client: Any, chat_id: str) -> str | None:
    """Id della sessione di QUESTA chat Telegram; la crea se non esiste.

    Vive nelle tabelle del cockpit, quindi la conversazione è visibile e continuabile
    da browser: è questo che rende «la stessa cosa» vera e non una somiglianza."""
    if client is None:
        return None
    titolo = f"{TITOLO_SESSIONE} {chat_id}".strip()
    try:
        righe = client.select("aios_chat_sessions", {
            "select": "id", "title": f"eq.{titolo}", "order": "updated_at.desc",
            "limit": "1"})
        if righe:
            return righe[0].get("id")
    except Exception:
        return None
    try:
        out = client.insert("aios_chat_sessions", {"title": titolo, "agents": "auto"})
        return (out or [{}])[0].get("id")
    except Exception:
        return None


def storico(client: Any, sid: str | None) -> list[dict]:
    if client is None or not sid:
        return []
    try:
        return client.select("aios_chat_messages", {
            "select": "role,agent,content", "session_id": f"eq.{sid}",
            "order": "id.asc", "limit": str(STORICO_MAX)})
    except Exception:
        return []


def _salva(client: Any, sid: str | None, role: str, testo: str,
           agente: str | None = None) -> None:
    if client is None or not sid or not (testo or "").strip():
        return
    riga = {"session_id": sid, "role": role, "content": testo}
    if agente:
        riga["agent"] = agente
    try:
        client.insert("aios_chat_messages", riga)
    except Exception:
        pass


def _card_azioni(azioni: list[dict]) -> None:
    """Le azioni del turno con gli stessi bottoni di conferma di prima: la chat mette in
    coda i casi sensibili col token `cmdok:`, che il poller già gestisce.

    Le `non_riuscito` (tentate e andate male) vanno nella stessa colonna di quelle
    rifiutate: per l'owner contano allo stesso modo — non è stato fatto — ma il motivo
    dice che è un errore da correggere, non un divieto."""
    if not azioni:
        return
    fallite = [{**a, "motivo": f"non riuscito: {a.get('motivo') or 'errore'}"}
               for a in azioni if a.get("stato") == "non_riuscito"]
    telegram.send_command_card({
        "eseguite": [a for a in azioni if a.get("stato") == "eseguito"],
        "rifiutate": [a for a in azioni if a.get("stato") == "rifiutato"] + fallite,
        "da_confermare": [a for a in azioni if a.get("stato") == "da_confermare"]})


def conversa(platform: Any, testo: str, chat_id: str = "principale") -> dict:
    """Un turno di conversazione su Telegram, dentro la chat del board.

    Ritorna un riassunto ({turni, azioni, sessione}) per i log e i test."""
    chat = getattr(platform, "chat", None)
    if chat is None:
        telegram.send_text("Chat non disponibile.")
        return {"turni": 0, "azioni": 0, "sessione": None}

    client = _client(platform)
    sid = sessione(client, chat_id)
    memoria = storico(client, sid)
    _salva(client, sid, "user", testo)

    turni: list[tuple[str, str]] = []
    azioni: list[dict] = []
    try:
        for ev in chat.stream(testo, "auto", memoria):
            fase = ev.get("phase")
            if fase == "done":
                if ev.get("azioni"):
                    azioni = list(ev["azioni"])
                agente, txt = ev.get("agent") or "", (ev.get("text") or "").strip()
                if agente and txt:
                    turni.append((agente, txt))
            elif fase == "error":
                telegram.send_text(
                    f"⚠️ {ev.get('agent') or 'chat'}: {str(ev.get('error'))[:200]}")
            elif fase == "triage" and ev.get("agenti"):
                telegram.send_text("🧭 Ne parlo con: " + ", ".join(ev["agenti"]))
    except Exception as exc:
        telegram.send_text(f"⚠️ Conversazione interrotta: {str(exc)[:180]}")

    for agente, txt in turni:
        telegram.send_text(f"*{agente}*\n{txt[:MESSAGGIO_MAX]}")
        _salva(client, sid, "assistant", txt, agente)
    if not turni:
        telegram.send_text("Nessuna risposta dagli agenti su questo giro.")
    _card_azioni(azioni)
    return {"turni": len(turni), "azioni": len(azioni), "sessione": sid}


def gestisci_testo(platform: Any, testo: str, chat_id: str = "principale") -> str:
    """Punto d'ingresso del messaggio Telegram. Ritorna il modo usato, per i log.

    Default: la conversazione del board. Col prefisso «!» il comando secco, che serve
    quando vuoi solo che una cosa venga fatta senza discuterne."""
    testo = (testo or "").strip()
    if testo.startswith(PREFISSO_COMANDO):
        comando = testo[len(PREFISSO_COMANDO):].strip()
        router = getattr(platform, "commands", None)
        if router is None or not comando:
            telegram.send_text("Comandi non disponibili.")
            return "comando_non_disponibile"
        res = router.handle(comando, actor="telegram")
        telegram.send_command_card(res.to_dict())
        return "comando"
    conversa(platform, testo, chat_id)
    return "conversazione"
