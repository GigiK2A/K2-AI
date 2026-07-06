"""Chat multi-agente in streaming: parli con gli agenti di dominio (uno, alcuni o
tutti insieme) e vedi lo stato REALE di ognuno — «sta pensando», «usa il sensore X»,
«sta scrivendo» — perché gli stati sono mappati sui veri eventi dello streaming
Anthropic e sull'esecuzione reale dei tool (loop tool-use), non su timer finti.

Architettura:
- ChatAgent: un agente di dominio come loop agentico streaming. I tool esposti al
  modello sono i SENSORI del reparto (sola lettura) + `esegui` (scrittura/azione).
  La sicurezza è identica al resto del board: ogni `esegui` passa dall'ATTUATORE via
  CommandRouter (`_classify`/`_exec_internal`/`_queue`) → allowlist, interne sicure
  subito, esterne/delete/DDL in conferma, fuori-perimetro rifiutate.
- ChatOrchestrator: risolve i destinatari. UN agente → chat 1-1. PIÙ agenti → DIBATTITO
  SEQUENZIALE su trascritto condiviso (turni: ognuno legge chi ha parlato prima e reagisce),
  più giri finché convergono o max, poi una SINTESI conclusiva.

La conferma delle azioni sensibili riusa la coda esistente del CommandRouter e
l'endpoint `/api/command/confirm` — nessun nuovo meccanismo di approvazione.
"""
from __future__ import annotations

import threading
from typing import Any, Iterator

DOMINI = ["marketing", "vendite", "finance", "operations", "legal", "hr"]

# Routing per parole chiave riusato dal CommandRouter (se disponibile), qui solo per
# validare la scelta manuale. Marketing non ha DomainConfig → sensori/sistema di ripiego.
_MK_SENSORS: list[tuple[str, dict]] = [
    ("leggi_calendario", {}), ("leggi_post_ig", {"limit": 6}),
    ("leggi_servizi", {}), ("leggi_topics", {}), ("leggi_iscritti", {}),
    ("leggi_analytics", {}), ("leggi_prospects", {}), ("leggi_ranking_seo", {}),
]
_MK_SYSTEM = (
    "Sei il responsabile Marketing di K2-AI (PMI italiana, AI operativa per PMI). "
    "Cresci il brand e i contenuti con pragmatismo, numeri e zero buzzword. "
    "PROPONI ed esegui solo dentro il perimetro consentito (L1)."
)

# Preambolo comune: come lavora l'agente in chat (leggi coi sensori, agisci con `esegui`).
_CHAT_PREAMBLE = (
    "\n\n# COME LAVORI IN CHAT\n"
    "Rispondi all'owner in italiano, diretto e conciso. Prima LEGGI i dati reali coi "
    "tuoi tool sensore (nomi che iniziano per 'leggi_'), poi — se l'istruzione è "
    "corretta e fattibile — AGISCI chiamando il tool `esegui`. Non inventare numeri: "
    "usa solo ciò che leggi. Se un'azione non è nel tuo perimetro, spiega perché. "
    "Chiudi con una frase che dice cosa hai fatto o proposto."
)

_ESEGUI_DEF = {
    "name": "esegui",
    "description": (
        "Esegui un'azione concreta nel tuo reparto. Tre forme:\n"
        "1) scrittura interna: {tabella, op:'insert'|'update'|'delete', match, dati} "
        "(update/delete richiedono match; delete solo per id);\n"
        "2) azione esterna (pubblicare/inviare): {canale:'n8n', workflow, payload};\n"
        "3) modifica schema DB non distruttiva: {sql:'ALTER TABLE ... ADD COLUMN ...'}.\n"
        "Le interne sicure partono subito; esterne, delete e DDL vanno in conferma; "
        "ciò che è fuori perimetro viene rifiutato. Metti sempre 'descrizione'."),
    "input_schema": {
        "type": "object",
        "properties": {
            "descrizione": {"type": "string"},
            "tabella": {"type": "string"},
            "op": {"type": "string"},
            "match": {"type": "object"},
            "dati": {"type": "object"},
            "canale": {"type": "string"},
            "workflow": {"type": "string"},
            "payload": {"type": "object"},
            "sql": {"type": "string"},
        },
        "required": ["descrizione"],
        "additionalProperties": True,
    },
}

_CARICA_SKILL_DEF = {
    "name": "carica_skill",
    "description": ("Carica il testo pieno di una skill (metodo operativo K2-AI) per "
                    "seguirne il procedimento. Usa il nome esatto dall'indice SKILL "
                    "DISPONIBILI o da cerca_skill."),
    "input_schema": {"type": "object", "properties": {"nome": {"type": "string"}},
                     "required": ["nome"]},
}
_CERCA_SKILL_DEF = {
    "name": "cerca_skill",
    "description": ("Cerca una skill in TUTTA la libreria (~300, tutti i reparti) per "
                    "parole chiave; ritorna nome+descrizione. Poi carica quella giusta "
                    "con carica_skill."),
    "input_schema": {"type": "object", "properties": {"query": {"type": "string"}},
                     "required": ["query"]},
}

_CALCOLA_DEF = {
    "name": "calcola",
    "description": (
        "Calcolo DETERMINISTICO (motore 8e, numeri veri con provenance normativa; "
        "NON stimare a occhio). Operazioni:\n"
        "- 'indici_bilancio' params {voci:[{sezione:'attivo'|'passivo'|'ricavi'|'costi'|"
        "'risultato', descrizione, importo}], anno?, wacc_pct?} → riclassificazione, "
        "indici (D/E, ROE, ROS, current/quick ratio, EBITDA margin), valutazione;\n"
        "- 'carico_fiscale' params {forma_giuridica, imponibile_eur, "
        "valore_produzione_irap_eur?, anno?} → IRES/IRPEF + IRAP;\n"
        "- 'imposta' params {tipo:'irpef'|'ires'|'irap'|'iva', base?, tipo_iva?};\n"
        "- 'aliquote' → aliquote correnti + riferimenti normativi."),
    "input_schema": {
        "type": "object",
        "properties": {
            "operazione": {"type": "string",
                           "enum": ["indici_bilancio", "carico_fiscale", "imposta", "aliquote"]},
            "params": {"type": "object"},
        },
        "required": ["operazione"],
        "additionalProperties": True,
    },
}
# I calcolatori vendorizzati coprono finanza/fisco → tool esposto a questi reparti.
_CALCOLA_DOMINI = {"finance"}

_FORBIDDEN = ("fuori dal perimetro consentito (solo allowlist; mai control-plane o "
              "registri immutabili; delete solo per id)")

# Istruzione delicata → modello forte (Sonnet), come nel CommandRouter.
_STRONG_HINTS = (" schema", "tabella", "colonna", "migrazione", "alter", "ddl",
                 " bug", "codice", "errore", "refactor", "n8n", "workflow", "automazion")

_SYNTH_SYS = ("Sei il coordinatore esecutivo di K2-AI (PMI italiana). Sintetizzi una "
              "discussione tra reparti in UNA decisione chiara e azionabile: integri i "
              "punti, evidenzi accordi e trade-off, chiudi coi prossimi passi. Pragmatico, "
              "numeri quando ci sono, niente buzzword, non ripetere pari pari gli interventi.")


class ChatAgent:
    """Un agente di dominio che risponde in chat come loop agentico streaming."""

    def __init__(self, orch: "ChatOrchestrator", dominio: str, llm: Any) -> None:
        self.orch = orch
        self.dominio = dominio
        self.llm = llm
        self.actor = f"chat_{dominio}"
        self.kernel = orch.kernel
        self.azioni: list[dict] = []   # esiti delle azioni `esegui` di questo turno
        agent = orch.platform.agents.get(dominio)
        cfg = getattr(agent, "cfg", None)
        if cfg is not None:
            self.system = cfg.system
            self.sensors = list(cfg.sensors)
            self.skill_focus = list(getattr(cfg, "skill_focus", []) or [])
        else:                          # marketing (nessun DomainConfig)
            self.system = _MK_SYSTEM
            self.sensors = list(_MK_SENSORS)
            self.skill_focus = []

    # ---- tool esposti al modello ----
    def _tool_defs(self) -> list[dict]:
        names = set(self.kernel.tools.names())
        defs: list[dict] = []
        for tname, _args in self.sensors:
            if tname in names:
                defs.append({
                    "name": tname,
                    "description": f"Sensore di reparto (sola lettura): {tname}.",
                    "input_schema": {"type": "object", "properties": {},
                                     "additionalProperties": True},
                })
        defs.append(_ESEGUI_DEF)
        if self.orch.skills is not None:      # skill invocabili (progressive disclosure)
            defs.append(_CARICA_SKILL_DEF)
            defs.append(_CERCA_SKILL_DEF)
        if self.dominio in _CALCOLA_DOMINI:   # calcolatori deterministici 8e (numeri veri)
            defs.append(_CALCOLA_DEF)
        return defs

    def _sensor_args(self, tname: str) -> dict:
        for n, a in self.sensors:
            if n == tname:
                return a
        return {}

    def _exec_tool(self, name: str, tinput: dict) -> Any:
        if name == "esegui":
            return self._do_action(tinput or {})
        if name in ("carica_skill", "cerca_skill"):
            return self._skill_tool(name, tinput or {})
        if name == "calcola":
            from aios import quant
            return quant.calcola(str((tinput or {}).get("operazione") or ""),
                                 (tinput or {}).get("params") or {})
        names = set(self.kernel.tools.names())
        if name in names:
            args = tinput or self._sensor_args(name)
            try:
                return self.kernel.execute(name, actor=self.actor, args=args or {}).result
            except Exception as exc:
                return {"error": str(exc)}
        return {"error": f"tool sconosciuto: {name}"}

    def _do_action(self, tinput: dict) -> dict:
        """Costruisce l'azione e la instrada per l'ATTUATORE via CommandRouter.
        Serializza l'accesso al router con un lock (più agenti girano in parallelo)."""
        router = self.orch.router
        descr = str(tinput.get("descrizione") or "azione")
        if tinput.get("sql"):
            az: dict = {"tipo": "ddl", "sql": str(tinput.get("sql"))}
        elif tinput.get("canale") or tinput.get("workflow"):
            az = {"canale": (tinput.get("canale") or "n8n"),
                  "workflow": tinput.get("workflow") or "k2ai",
                  "payload": tinput.get("payload") or {}}
        else:
            az = {"tabella": tinput.get("tabella"), "op": (tinput.get("op") or "insert"),
                  "match": tinput.get("match"), "dati": tinput.get("dati") or {}}
            az = {k: v for k, v in az.items() if v is not None}
        if router is None:
            rec = {"stato": "rifiutato", "descrizione": descr,
                   "motivo": "esecuzione non disponibile"}
            self.azioni.append(rec)
            return rec
        with self.orch.lock:
            kind = router._classify(az)
            if kind == "forbidden":
                rec = {"stato": "rifiutato", "descrizione": descr, "motivo": _FORBIDDEN}
            elif kind == "internal_confirm":
                tok = router._queue("internal", descr, self.actor, az=az)
                rec = {"stato": "da_confermare", "id": tok, "descrizione": descr,
                       "tipo": self._confirm_label(az)}
            else:                       # internal_auto → esegui ORA
                try:
                    out = router._exec_internal(az, self.actor)
                    rec = {"stato": "eseguito", "descrizione": descr,
                           "tabella": az.get("tabella"), "op": az.get("op"), "esito": out}
                except Exception as exc:
                    rec = {"stato": "rifiutato", "descrizione": descr,
                           "motivo": str(exc)[:160]}
        self.azioni.append(rec)
        return rec

    @staticmethod
    def _confirm_label(az: dict) -> str:
        if az.get("tipo") == "ddl":
            return "modifica schema DB (DDL)"
        if str(az.get("canale") or "").lower() in ("n8n", "esterno", "external", "webhook"):
            return f"esterna (n8n · {az.get('workflow') or '?'})"
        if str(az.get("op") or "").lower() == "delete":
            return f"cancellazione ({az.get('tabella')})"
        return f"interna sensibile ({az.get('tabella')})"

    def _skill_tool(self, name: str, tinput: dict) -> Any:
        skills = self.orch.skills
        if skills is None:
            return {"error": "skill non disponibili"}
        if name == "cerca_skill":
            return {"risultati": skills.search(str(tinput.get("query") or ""), 8)}
        # carica_skill
        nm = str(tinput.get("nome") or "").strip()
        try:
            return {"nome": nm, "skill": skills.load(nm)[:8000]}
        except KeyError:
            return {"error": f"skill '{nm}' non trovata",
                    "forse": skills.search(nm, 5)}

    # ---- contesto (system) ----
    def _system_prompt(self) -> str:
        out = self.system + _CHAT_PREAMBLE
        if self.dominio in _CALCOLA_DOMINI:
            out += ("\n\n# NUMERI VERI — hai il tool `calcola` (motore deterministico 8e). "
                    "Per indici di bilancio, carico fiscale (IRES/IRPEF/IRAP), aliquote: "
                    "USA `calcola`, NON stimare a memoria. Cita i numeri che ti restituisce.")
        skills = self.orch.skills
        if skills is not None:
            try:
                names = list(dict.fromkeys(
                    list(self.skill_focus) + skills.for_domain(self.dominio, 12)))
            except Exception:
                names = list(self.skill_focus)
            if names:
                out += ("\n\n# SKILL DISPONIBILI (metodi operativi K2-AI — carica il "
                        "testo con carica_skill PRIMA di applicarne uno; non citarle "
                        "senza averle lette)\n" + skills.index(names)
                        + "\n\nNon trovi quella giusta qui? Usa cerca_skill(query) per "
                        "cercare in tutta la libreria (~300 skill, ogni reparto).")
        return out

    def _history_for_agent(self, history: list[dict] | None) -> list[dict]:
        """Ricostruisce il thread 1-1 di QUESTO agente con l'owner dallo storico sessione:
        tutti i messaggi 'user' + le risposte 'assistant' del proprio dominio, in ordine.
        Cap agli ultimi 20 turni e 4000 char/turno per limitare il contesto."""
        if not history:
            return []
        out: list[dict] = []
        for m in history:
            role = m.get("role")
            content = str(m.get("content") or "").strip()
            if not content:
                continue
            if role == "user":
                out.append({"role": "user", "content": content[:4000]})
            elif role == "assistant" and m.get("agent") == self.dominio:
                out.append({"role": "assistant", "content": content[:4000]})
        return out[-20:]

    # ---- loop streaming ----
    def stream(self, text: str | None, history: list[dict] | None = None,
               user_prompt: str | None = None) -> Iterator[dict]:
        """Genera gli eventi del turno per QUESTO agente (non taggati: lo fa l'orch.).
        `user_prompt` (dibattito): messaggio utente già composto col trascritto condiviso →
        in quel caso lo storico è nel prompt (history nativa vuota). Altrimenti (1-1):
        prompt di default + storico per-agente nativo."""
        if user_prompt is not None:
            user, hist = user_prompt, []
        else:
            user = (f"ISTRUZIONE OWNER: {text}\n\n"
                    "Leggi i dati reali coi tuoi sensori e, se corretto, agisci con `esegui`.")
            hist = self._history_for_agent(history)
        try:
            for ev in self.llm.stream_agentic(
                    system=self._system_prompt(), user=user,
                    tools=self._tool_defs(), tool_exec=self._exec_tool,
                    web_search=bool(self.orch.web), history=hist):
                if ev.get("phase") == "done":
                    ev = {**ev, "azioni": list(self.azioni)}
                yield ev
        except Exception as exc:
            yield {"phase": "error", "error": str(exc)[:200]}


class ChatOrchestrator:
    """Risolve i destinatari e conduce la conversazione. UN agente → chat 1-1. PIÙ agenti
    → DIBATTITO: turni SEQUENZIALI su un trascritto condiviso (ognuno legge chi ha parlato
    prima e reagisce), più giri finché convergono, poi una SINTESI conclusiva. Gli eventi
    sono taggati per speaker (`key` = dominio#giro, o 'synthesis')."""

    def __init__(self, platform: Any, llm: Any, llm_strong: Any = None,
                 skills: Any = None, web_search: bool = False) -> None:
        self.platform = platform
        self.llm = llm
        self.llm_strong = llm_strong or llm
        self.skills = skills
        self.web = web_search       # web search nativa Claude per gli agenti chat
        self.kernel = platform.kernel
        self.router = getattr(platform, "commands", None)   # CommandRouter (attuatore+coda)
        self.lock = threading.Lock()

    # ---- destinatari ----
    def resolve_targets(self, text: str, agents: Any) -> list[str]:
        """agents: None/"auto"/"" → il router sceglie 1 dominio. Lista/str → quei domini
        (validati). Duplicati rimossi, ordine preservato."""
        if agents is None or agents == "" or agents == "auto":
            return [self._route_one(text)]
        if isinstance(agents, str):
            agents = [agents]
        seen: list[str] = []
        for a in agents:
            d = str(a).strip().lower()
            if d == "auto":
                for r in [self._route_one(text)]:
                    if r not in seen:
                        seen.append(r)
            elif d in DOMINI and d not in seen:
                seen.append(d)
        return seen or [self._route_one(text)]

    def _route_one(self, text: str) -> str:
        if self.router is not None:
            try:
                d = self.router.route(text)
                if d in DOMINI:
                    return d
            except Exception:
                pass
        return "marketing"

    def _pick_llm(self, text: str) -> Any:
        tl = " " + (text or "").lower() + " "
        return self.llm_strong if any(k in tl for k in _STRONG_HINTS) else self.llm

    # ---- trascritto condiviso (dibattito) ----
    @staticmethod
    def _label(agent: str) -> str:
        return {"marketing": "Marketing", "vendite": "Vendite", "finance": "Finance",
                "operations": "Operations", "legal": "Legal", "hr": "HR",
                "owner": "Owner", "sintesi": "Sintesi"}.get(agent, agent.capitalize())

    def _transcript_from_history(self, history: list[dict] | None) -> list[dict]:
        out: list[dict] = []
        for m in (history or []):
            c = str(m.get("content") or "").strip()
            if not c:
                continue
            sp = "owner" if m.get("role") == "user" else (m.get("agent") or "ai")
            out.append({"speaker": sp, "text": c})
        return out[-24:]

    def _fmt(self, transcript: list[dict], cap: int = 7000) -> str:
        txt = "\n\n".join(f"[{self._label(t['speaker'])}]: {t['text']}" for t in transcript)
        return txt[-cap:]

    def _debate_prompt(self, dom: str, text: str, transcript: list[dict], rnd: int) -> str:
        base = (f"ISTRUZIONE DELL'OWNER: {text}\n\n"
                f"Sei il responsabile {self._label(dom)} e partecipi a una DISCUSSIONE "
                "operativa tra reparti di K2-AI. Discussione finora:\n\n"
                f"<discussione>\n{self._fmt(transcript)}\n</discussione>\n\n")
        if rnd <= 1:
            task = ("Dai il tuo contributo dal punto di vista del tuo reparto. Leggi i dati "
                    "reali coi sensori se serve, usa `calcola` per i numeri, agisci con "
                    "`esegui` se opportuno. È una conversazione: conciso e concreto, non un report.")
        else:
            task = ("REAGISCI a quanto hanno detto gli altri reparti: sei d'accordo? Cosa "
                    "aggiungi, correggi o contesti dal tuo punto di vista? Rivolgiti a loro per "
                    "nome quando serve. Se non hai nulla di nuovo, dillo in una riga "
                    "('Concordo, nulla da aggiungere.'). Conciso.")
        return base + task

    def _speaker(self, dom: str, user_prompt: str, llm: Any, key: str, rnd: int):
        """Un intervento: yield eventi taggati (agent/key/round), RITORNA il testo finale."""
        final = ""
        for ev in ChatAgent(self, dom, llm).stream(None, user_prompt=user_prompt):
            if ev.get("phase") == "done":
                final = ev.get("text") or ""
            yield {**ev, "agent": dom, "key": key, "round": rnd}
        return final

    def _converged(self, transcript: list[dict], targets: list[str]) -> bool:
        """Gli ultimi interventi mostrano consenso / nessun punto nuovo? (giudice Haiku)."""
        last = transcript[-len(targets):]
        cj = getattr(self.llm, "complete_json", None)
        if not last or cj is None:
            return False
        try:
            r = cj(system="Valuti se una discussione tra reparti aziendali ha raggiunto "
                          "consenso e non emergono punti NUOVI e rilevanti.",
                   user=("Ultimi interventi:\n" + self._fmt(last, cap=4000)
                         + "\n\nHanno converso (accordo + nessun nuovo punto)?"),
                   schema={"type": "object", "properties": {"converged": {"type": "boolean"}},
                           "required": ["converged"]})
            return bool(r.get("converged"))
        except Exception:
            return False

    def _synthesis(self, text: str, transcript: list[dict], targets: list[str]):
        """Voce di chiusura: integra la discussione in una decisione unica (Sonnet)."""
        up = ("I reparti " + ", ".join(self._label(d) for d in targets) + " hanno discusso "
              "l'istruzione dell'owner. Produci una SINTESI conclusiva UNICA: la "
              "raccomandazione/decisione che integra i punti chiave di ciascun reparto, "
              "evidenzia accordi e trade-off e chiude coi prossimi passi concreti.\n\n"
              f"ISTRUZIONE OWNER: {text}\n\n<discussione>\n{self._fmt(transcript)}\n</discussione>")
        final = ""
        try:
            for ev in self.llm_strong.stream_agentic(
                    system=_SYNTH_SYS, user=up, tools=[], tool_exec=lambda n, i: {}):
                if ev.get("phase") == "done":
                    final = ev.get("text") or ""
                yield {**ev, "agent": "sintesi", "key": "synthesis", "round": 0}
        except Exception as exc:
            yield {"phase": "error", "agent": "sintesi", "key": "synthesis",
                   "error": str(exc)[:200]}
        return final

    # ---- stream principale ----
    def stream(self, text: str, agents: Any = None,
               history: list[dict] | None = None) -> Iterator[dict]:
        if not text or not text.strip():
            yield {"phase": "error", "agent": "", "error": "istruzione vuota"}
            return
        targets = self.resolve_targets(text, agents)
        llm = self._pick_llm(text)
        yield {"phase": "start", "agents": targets}

        # UN agente → conversazione 1-1 (storico per-agente nativo).
        if len(targets) == 1:
            dom = targets[0]
            try:
                for ev in ChatAgent(self, dom, llm).stream(text, history):
                    yield {**ev, "agent": dom, "key": dom}
            except Exception as exc:
                yield {"phase": "error", "agent": dom, "key": dom, "error": str(exc)[:200]}
            yield {"phase": "all_done", "agents": targets}
            return

        # PIÙ agenti → DIBATTITO sequenziale su trascritto condiviso: ognuno legge chi ha
        # parlato prima e reagisce; giri finché convergono (giudice) o max; poi SINTESI.
        transcript = self._transcript_from_history(history)
        transcript.append({"speaker": "owner", "text": text})
        MAX_ROUNDS = 3
        for rnd in range(1, MAX_ROUNDS + 1):
            yield {"phase": "round", "round": rnd, "agents": targets}
            for dom in targets:
                final = yield from self._speaker(
                    dom, self._debate_prompt(dom, text, transcript, rnd),
                    llm, f"{dom}#r{rnd}", rnd)
                if final.strip():
                    transcript.append({"speaker": dom, "text": final})
            if rnd >= 2 and self._converged(transcript, targets):
                break
        yield from self._synthesis(text, transcript, targets)
        yield {"phase": "all_done", "agents": targets}
