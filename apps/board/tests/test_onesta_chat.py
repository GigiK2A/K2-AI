"""Quello che la chat dichiara deve coincidere con quello che è successo.

Due bugie possibili, entrambe viste il 20 ago 2026:
1. un'azione tentata e andata male marcata «eseguito» — l'attuatore torna ok=False
   quando l'update non tocca righe o un canale esterno rifiuta;
2. Vendite che crea 6 lead su 10 e chiude con «tutti i lead sono stati inseriti
   correttamente»: vero su quello che ha fatto, falso sul lavoro chiesto.

E il registro: un'azione fallita non lasciava NESSUNA traccia in aios_audit, perché
l'audit stava dopo `apply_action` e un 400 solleva.
"""
from types import SimpleNamespace

from aios.chat_runner import _CHAT_PREAMBLE, conteggio


# ---- la riga di conteggio, scritta dal codice e non dal modello ----
def test_senza_azioni_nessuna_riga():
    assert conteggio([]) == ""


def test_conta_le_eseguite():
    r = conteggio([{"stato": "eseguito"}, {"stato": "eseguito"}])
    assert "2 eseguite" in r and "NON riuscite" not in r


def test_le_non_riuscite_si_vedono():
    r = conteggio([{"stato": "eseguito"}, {"stato": "non_riuscito"},
                   {"stato": "non_riuscito"}])
    assert "1 eseguite" in r and "2 NON riuscite" in r


def test_conta_anche_attese_e_rifiuti():
    r = conteggio([{"stato": "da_confermare"}, {"stato": "rifiutato"}])
    assert "in attesa di conferma" in r and "1 rifiutate" in r
    assert "0 eseguite" in r          # zero dichiarato, non omesso


def test_il_preambolo_vieta_il_falso_completato():
    assert "CONTA PRIMA DI DIRE «FATTO»" in _CHAT_PREAMBLE
    assert "fatte X su N" in _CHAT_PREAMBLE


# ---- «eseguito» solo se è andata davvero ----
class RouterFinto:
    def __init__(self, out=None, exc=None):
        self.out, self.exc = out, exc

    def _classify(self, az):
        return "internal_auto"

    def _exec_internal(self, az, actor):
        if self.exc:
            raise self.exc
        return self.out


def _agente(router):
    from aios.chat_runner import ChatAgent, ChatOrchestrator
    from aios.kernel import Kernel
    platform = SimpleNamespace(kernel=Kernel(), agents={}, commands=router, chat=None,
                               prospector=None)
    orch = ChatOrchestrator(platform, None, None, skills=None)
    return ChatAgent(orch, "vendite", None)


def test_una_scrittura_a_vuoto_non_e_eseguita():
    """ok=False significa che nessuna riga è stata scritta: dirlo «eseguito» è la bugia
    da cui è partito tutto."""
    a = _agente(RouterFinto(out={"ok": False, "errore": "nessuna riga aggiornata"}))
    rec = a._exec_tool("esegui", {"descrizione": "aggiorna il lead",
                                  "tabella": "pipeline_leads", "op": "update",
                                  "match": {"id": "x"}, "dati": {"score": 9}})
    assert rec["stato"] == "non_riuscito"
    assert "nessuna riga" in rec["motivo"]
    assert "1 NON riuscite" in conteggio(a.azioni)


def test_una_scrittura_riuscita_resta_eseguita():
    a = _agente(RouterFinto(out={"ok": True, "righe": [{"id": 1}]}))
    rec = a._exec_tool("esegui", {"descrizione": "crea lead",
                                  "tabella": "pipeline_leads", "op": "insert",
                                  "dati": {"name": "Alfa"}})
    assert rec["stato"] == "eseguito"


def test_un_400_e_non_riuscito_non_rifiutato():
    """`rifiutato` vuol dire fuori perimetro: la mossa giusta è diversa da un errore
    di dato, dove si corregge e si riprova."""
    a = _agente(RouterFinto(exc=RuntimeError("HTTP Error 400: Bad Request")))
    rec = a._exec_tool("esegui", {"descrizione": "crea lead",
                                  "tabella": "pipeline_leads", "op": "insert",
                                  "dati": {"score": 85}})
    assert rec["stato"] == "non_riuscito"
    assert "400" in rec["motivo"] and rec["tabella"] == "pipeline_leads"


# ---- il registro tiene anche i fallimenti ----
class KernelAudit:
    def __init__(self):
        self.eventi = []
        self.audit = SimpleNamespace(
            append=lambda **kw: self.eventi.append(kw))


def _router_vero(monkeypatch, esito=None, exc=None):
    from aios.command import CommandRouter
    import aios.command as C
    k = KernelAudit()
    r = CommandRouter(SimpleNamespace(kernel=k, agents={}), None)

    def finto(client, az):
        if exc:
            raise exc
        return esito
    monkeypatch.setattr(C, "apply_action", finto)
    return r, k


def test_un_azione_fallita_lascia_traccia(monkeypatch):
    """Prima l'audit stava DOPO apply_action: un 400 solleva, quindi dieci inserimenti
    falliti non lasciavano niente e la causa è stata trovata a mano."""
    r, k = _router_vero(monkeypatch, exc=RuntimeError("HTTP Error 400"))
    try:
        r._exec_internal({"tabella": "pipeline_leads", "op": "insert"}, "chat_vendite")
    except RuntimeError:
        pass
    assert len(k.eventi) == 1
    ev = k.eventi[0]
    assert ev["event"] == "failed" and ev["actor"] == "chat_vendite"
    assert "400" in ev["detail"]["errore"]
    assert ev["detail"]["azione"]["tabella"] == "pipeline_leads"


def test_un_esito_negativo_e_failed_non_executed(monkeypatch):
    r, k = _router_vero(monkeypatch, esito={"ok": False, "errore": "0 righe"})
    r._exec_internal({"tabella": "pipeline_leads", "op": "update"}, "chat_vendite")
    assert k.eventi[0]["event"] == "failed"
    assert k.eventi[0]["detail"]["errore"] == "0 righe"


def test_un_esito_positivo_resta_executed(monkeypatch):
    r, k = _router_vero(monkeypatch, esito={"ok": True})
    r._exec_internal({"tabella": "pipeline_leads", "op": "insert"}, "chat_vendite")
    assert k.eventi[0]["event"] == "executed"
