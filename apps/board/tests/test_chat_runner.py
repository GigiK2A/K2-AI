"""Chat multi-agente in streaming (ChatOrchestrator/ChatAgent):
- risoluzione destinatari: auto (router) vs selezione manuale multi
- fan-out reale: più agenti in parallelo, ognuno col proprio stream di eventi
- sicurezza invariata: `esegui` passa dall'attuatore via CommandRouter
  (interna sicura → subito; esterna/delete → conferma; fuori perimetro → rifiuto)
"""
import json
from types import SimpleNamespace

from aios.kernel import Kernel
from aios.tools import Tool
from aios.command import CommandRouter
from aios.llm import FakeLLM
from aios.chat_runner import ChatOrchestrator
from aios.agents.finance_config import FINANCE_CONFIG


class FakeClient:
    def __init__(self):
        self.writes = []

    def insert(self, table, row):
        self.writes.append(("insert", table, row)); return [row]

    def update(self, table, filters, data):
        self.writes.append(("update", table, filters, data)); return [data]

    def delete(self, table, filters):
        self.writes.append(("delete", table, filters)); return []

    def select(self, table, params):
        return []


class FakeStreamLLM:
    """Streaming deterministico: emette gli eventi del loop e, per ogni voce dello
    script, chiama davvero tool_exec (così l'azione passa dall'attuatore reale)."""

    def __init__(self, script):
        self.script = list(script)          # list[(tool_name, input_dict)]
        self.calls = []
        # decisione del CEO in modalità auto (schema con 'modo'); default: consulta i due
        self.triage = {"modo": "consulta", "agenti": ["finance", "marketing"]}
        self.converged = True   # giudice convergenza dibattito (default: converge subito)
        self.skill_pick = None  # nome skill scelta dall'LLM (schema 'skill'); None → 'nessuna'

    def stream_agentic(self, *, system, user, tools, tool_exec, max_iters=6,
                       max_tokens=None, web_search=False, history=None):
        self.calls.append((system, user, history))
        yield {"phase": "thinking"}
        for name, inp in self.script:
            yield {"phase": "tool", "tool": name}
            yield {"phase": "tool_run", "tool": name}
            tool_exec(name, inp)            # esegue sensore o `esegui` sui dati reali
        yield {"phase": "writing"}
        yield {"phase": "delta", "text": "ok"}
        yield {"phase": "done", "text": "fatto"}

    def complete_json(self, *, system, user, schema=None):
        props = (schema or {}).get("properties", {})
        if "modo" in props:                 # triage del CEO
            return dict(self.triage)
        if "skill" in props:                 # scelta del metodo/skill
            return {"skill": self.skill_pick or "nessuna"}
        return {"converged": self.converged}   # giudice convergenza dibattito


def _orch(script):
    k = Kernel()
    client = FakeClient()
    k._supabase = client
    k.register_tool(Tool(name="leggi_revenue", action_type=None, readonly=True,
                         run=lambda **_: [{"mrr": 1000}]))
    agents = {"finance": SimpleNamespace(cfg=FINANCE_CONFIG),
              "marketing": SimpleNamespace()}   # marketing: nessun cfg → ripiego
    platform = SimpleNamespace(kernel=k, agents=agents, commands=None, chat=None)
    platform.commands = CommandRouter(platform, FakeLLM(['{"dominio":"finance"}']))
    fake = FakeStreamLLM(script)
    orch = ChatOrchestrator(platform, fake, fake, skills=None)
    return orch, client


def _events(orch, text, agents):
    return list(orch.stream(text, agents))


def _done(events, dom):
    return next(e for e in events if e.get("phase") == "done" and e.get("agent") == dom)


# ---- routing / destinatari ----
def test_resolve_auto_uses_router_keyword():
    orch, _ = _orch([])
    assert orch.resolve_targets("come sono i ricavi?", None) == ["finance"]
    assert orch.resolve_targets("come sono i ricavi?", "auto") == ["finance"]


def test_resolve_manual_multi_validated_dedup():
    orch, _ = _orch([])
    assert orch.resolve_targets("x", ["finance", "marketing"]) == ["finance", "marketing"]
    # domini fasulli scartati, duplicati rimossi
    assert orch.resolve_targets("x", ["finance", "bogus", "finance"]) == ["finance"]


# ---- dibattito multi-agente (turni sequenziali + giri + chiusura CEO) ----
def test_multi_agent_debate_converges_and_ceo_closes():
    orch, _ = _orch([])   # converged=True → si ferma dopo il 1° giro (niente giri di parole)
    ev = _events(orch, "che facciamo per la crescita?", ["finance", "marketing"])
    assert ev[0]["phase"] == "start" and set(ev[0]["agents"]) == {"finance", "marketing"}
    assert ev[-1]["phase"] == "all_done"
    assert any(e["phase"] == "round" for e in ev)
    spoke = {e.get("agent") for e in ev if e.get("phase") == "done"}
    assert {"finance", "marketing", "ceo"} <= spoke       # reparti + chiusura CEO
    # accordo dopo 1 giro → finance ha parlato UNA volta (non trascina)
    fin_keys = {e.get("key") for e in ev if e.get("agent") == "finance" and e.get("key")}
    assert len(fin_keys) == 1


def test_debate_multiround_when_not_converged():
    orch, _ = _orch([])
    orch.llm.converged = False        # nessun accordo → più giri (fino a MAX_ROUNDS=3)
    ev = _events(orch, "questione contesa", ["finance", "marketing"])
    fin_keys = {e.get("key") for e in ev if e.get("agent") == "finance" and e.get("key")}
    assert len(fin_keys) >= 2          # finance reagisce in più giri
    assert any(e.get("agent") == "ceo" and e.get("phase") == "done" for e in ev)


def test_single_agent_is_one_to_one():
    orch, _ = _orch([])
    ev = _events(orch, "come sono i ricavi?", ["finance"])
    # 1-1: nessun giro, nessuna chiusura CEO; un solo done finance
    assert not any(e["phase"] == "round" for e in ev)
    assert not any(e.get("agent") == "ceo" for e in ev)
    assert _done(ev, "finance")["text"] == "fatto" and ev[-1]["phase"] == "all_done"


# ---- CEO-led (modalità auto): il CEO decide se rispondere o consultare ----
def test_ceo_auto_answers_directly():
    orch, _ = _orch([])
    orch.llm.triage = {"modo": "rispondi"}
    ev = _events(orch, "ok, confermi?", "auto")
    assert any(e["phase"] == "triage" and e["modo"] == "rispondi" for e in ev)
    assert _done(ev, "ceo")["text"] == "fatto"          # risponde il CEO
    assert not any(e["phase"] == "round" for e in ev)    # nessun dibattito
    assert not any(e.get("agent") in ("finance", "marketing") for e in ev)


def test_ceo_auto_consults_subset():
    orch, _ = _orch([])
    orch.llm.triage = {"modo": "consulta", "agenti": ["finance", "marketing"]}
    ev = _events(orch, "che facciamo per la crescita?", "auto")
    assert any(e["phase"] == "triage" and e["modo"] == "consulta" for e in ev)
    assert any(e["phase"] == "round" for e in ev)        # dibattito
    spoke = {e.get("agent") for e in ev if e.get("phase") == "done"}
    assert {"finance", "marketing", "ceo"} <= spoke       # reparti + chiusura CEO


def test_ceo_auto_consult_single_no_debate():
    orch, _ = _orch([])
    orch.llm.triage = {"modo": "consulta", "agenti": ["finance"]}
    ev = _events(orch, "quanti lead abbiamo?", "auto")
    assert not any(e["phase"] == "round" for e in ev)     # un reparto → 1-1, niente dibattito
    assert _done(ev, "finance")["text"] == "fatto"


# ---- sicurezza `esegui` (identica al CommandRouter) ----
def test_esegui_internal_safe_executes_now():
    script = [("esegui", {"descrizione": "registra conversione",
                          "tabella": "kbot_conversions", "op": "insert",
                          "dati": {"amount_eur": 19}})]
    orch, client = _orch(script)
    ev = _events(orch, "registra una conversione", ["finance"])
    azioni = _done(ev, "finance")["azioni"]
    assert len(azioni) == 1 and azioni[0]["stato"] == "eseguito"
    assert client.writes and client.writes[0][1] == "kbot_conversions"


def test_esegui_external_goes_to_confirm_not_executed():
    script = [("esegui", {"descrizione": "pubblica su IG", "canale": "n8n",
                          "workflow": "publish_ig", "payload": {"x": 1}})]
    orch, client = _orch(script)
    ev = _events(orch, "pubblica il post", ["finance"])
    azioni = _done(ev, "finance")["azioni"]
    assert azioni[0]["stato"] == "da_confermare" and "id" in azioni[0]
    assert client.writes == []                       # niente eseguito senza conferma


def test_esegui_forbidden_control_plane_refused():
    script = [("esegui", {"descrizione": "alza autonomia",
                          "tabella": "aios_policy_state", "op": "insert",
                          "dati": {"level": 3}})]
    orch, client = _orch(script)
    ev = _events(orch, "alza la tua autonomia", ["finance"])
    azioni = _done(ev, "finance")["azioni"]
    assert azioni[0]["stato"] == "rifiutato" and client.writes == []


def test_empty_text_yields_error():
    orch, _ = _orch([])
    ev = _events(orch, "   ", None)
    assert ev and ev[0]["phase"] == "error"


# ---- memoria conversazionale: ogni agente rivede SOLO il proprio thread ----
def test_history_threaded_per_agent():
    hist = [{"role": "user", "agent": None, "content": "ciao finance"},
            {"role": "assistant", "agent": "finance", "content": "risposta finance"},
            {"role": "assistant", "agent": "marketing", "content": "risposta marketing"},
            {"role": "user", "content": "e adesso?"}]
    orch, _ = _orch([])
    list(orch.stream("continua", ["finance"], hist))
    _sys, _user, h = orch.llm.calls[-1]        # la fake registra anche la history
    pairs = [(m["role"], m["content"]) for m in h]
    assert ("assistant", "risposta finance") in pairs       # la SUA risposta
    assert ("assistant", "risposta marketing") not in pairs  # non quella altrui
    assert ("user", "ciao finance") in pairs and ("user", "e adesso?") in pairs


# ---- skill invocabili (progressive disclosure sulla libreria vendorizzata) ----
def test_skill_tools_search_and_load():
    from aios.chat_runner import ChatAgent
    from aios.skills import SkillLibrary
    orch, _ = _orch([])
    orch.skills = SkillLibrary()
    a = ChatAgent(orch, "finance", None)
    # i tool skill compaiono nelle definizioni esposte al modello
    names = [t["name"] for t in a._tool_defs()]
    assert "cerca_skill" in names and "carica_skill" in names
    # cerca su tutta la libreria
    res = a._exec_tool("cerca_skill", {"query": "analisi bilancio indici"})
    assert res["risultati"] and any("bilancio" in r["nome"] for r in res["risultati"])
    # carica il testo pieno della prima
    nome = res["risultati"][0]["nome"]
    full = a._exec_tool("carica_skill", {"nome": nome})
    assert full.get("nome") == nome and len(full.get("skill", "")) > 100
    # nome inesistente → errore + suggerimenti (mai crash)
    miss = a._exec_tool("carica_skill", {"nome": "skill-inesistente-xyz"})
    assert "error" in miss and "forse" in miss


def test_system_prompt_preloads_chosen_skill():
    from aios.chat_runner import ChatAgent
    from aios.skills import SkillLibrary
    orch, _ = _orch([])
    orch.skills = SkillLibrary()
    fin_skill = orch.skills.for_domain("finance", 1)[0]
    orch.llm.skill_pick = fin_skill                      # l'LLM sceglie questa skill
    sysp = ChatAgent(orch, "finance", None, request="analisi di bilancio")._system_prompt()
    assert "METODO K2-AI DA APPLICARE" in sysp and fin_skill in sysp  # metodo pre-caricato
    assert "cerca_skill" in sysp                          # altre skill accessibili


def test_choose_skill_respects_nessuna():
    from aios.chat_runner import ChatAgent
    from aios.skills import SkillLibrary
    orch, _ = _orch([])
    orch.skills = SkillLibrary()
    orch.llm.skill_pick = None                            # l'LLM dice 'nessuna'
    sysp = ChatAgent(orch, "finance", None, request="ciao")._system_prompt()
    assert "METODO K2-AI DA APPLICARE" not in sysp        # non forza un metodo irrilevante


# ---- calcolatori deterministici 8e (tool `calcola`, solo finance) ----
def test_calcola_tool_only_for_finance():
    from aios.chat_runner import ChatAgent
    orch, _ = _orch([])
    fin = [t["name"] for t in ChatAgent(orch, "finance", None)._tool_defs()]
    hr = [t["name"] for t in ChatAgent(orch, "hr", None)._tool_defs()]
    assert "calcola" in fin and "calcola" not in hr


def test_calcola_returns_real_numbers():
    from aios.chat_runner import ChatAgent
    orch, _ = _orch([])
    a = ChatAgent(orch, "finance", None)
    # carico fiscale SRL: IRES 24% di 100k = 24000
    r = a._exec_tool("calcola", {"operazione": "carico_fiscale",
                                 "params": {"forma_giuridica": "srl",
                                            "imponibile_eur": 100000,
                                            "valore_produzione_irap_eur": 120000}})
    ires = next(d for d in r["dettaglio"] if d["imposta"] == "IRES")
    assert ires["imposta_eur"] == 24000.0 and r["totale_eur"] == 28680.0
    # operazione sconosciuta → errore gestito (no crash)
    assert "error" in a._exec_tool("calcola", {"operazione": "boh"})
