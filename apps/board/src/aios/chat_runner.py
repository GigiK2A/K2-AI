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
    ("leggi_commenti_ig", {}),
    ("leggi_servizi", {}), ("leggi_topics", {}), ("leggi_iscritti", {}),
    ("leggi_analytics", {}), ("leggi_prospects", {}), ("leggi_ranking_seo", {}),
]
# Descrizioni sensori dove il nome non basta (l'agente deve sapere cosa fa/che input prende)
_SENSOR_DESC = {
    "leggi_commenti_ig": ("Legge il TESTO dei commenti sotto i post Instagram (non solo il "
                          "numero). Senza parametri scorre i post recenti con commenti e ne "
                          "riporta il contenuto; con {media_id} legge quel post specifico."),
}
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
        "Esegui un'azione concreta. Forme:\n"
        "1) scrittura interna: {tabella, op:'insert'|'update'|'delete', match, dati};\n"
        "2) azione esterna (workflow): {canale:'n8n', workflow, payload};\n"
        "3) schema DB non distruttivo: {sql:'ALTER TABLE ... ADD COLUMN ...'};\n"
        "4) INSTAGRAM — pubblica un post: {canale:'instagram', azione:'pubblica_post', "
        "caption, image_url}  (image_url = immagine a URL PUBBLICO, obbligatoria);\n"
        "5) INSTAGRAM — rispondi a un commento: {canale:'instagram', "
        "azione:'rispondi_commento', comment_id, message};\n"
        "6) ADS Meta — crea campagna: {canale:'meta_ads', azione:'crea_campagna', nome, "
        "obiettivo:'traffico'|'lead'|'engagement'|'notorieta'|'vendite'}. La campagna nasce "
        "SEMPRE in PAUSA: non spende finché l'owner non la attiva in Ads Manager.\n"
        "Le interne sicure partono subito; Instagram/Ads, esterne, delete e DDL vanno SEMPRE "
        "in conferma dell'owner; fuori perimetro = rifiutato. Metti sempre 'descrizione'."),
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
            "azione": {"type": "string"},
            "caption": {"type": "string"},
            "image_url": {"type": "string"},
            "comment_id": {"type": "string"},
            "message": {"type": "string"},
            "nome": {"type": "string"},
            "obiettivo": {"type": "string"},
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

# Tool trasversali a TUTTI gli agenti (registrati in platform.py). Lettura Supabase di
# qualsiasi tabella + verifica stato dei workflow n8n.
_BASE_TOOL_DEFS = [
    {"name": "leggi_tabella",
     "description": ("Leggi QUALSIASI tabella Supabase (sola lettura). params: {tabella, "
                     "filtri? (PostgREST, es. {\"stato\":\"eq.usato\",\"canale\":\"eq.instagram\"}), "
                     "ordine? (es. \"created_at.desc\"), limit? (max 200)}."),
     "input_schema": {"type": "object", "properties": {
         "tabella": {"type": "string"}, "filtri": {"type": "object"},
         "ordine": {"type": "string"}, "limit": {"type": "integer"}},
         "required": ["tabella"], "additionalProperties": True}},
    {"name": "leggi_n8n_workflows",
     "description": "Elenca i workflow n8n (id, nome, attivo).",
     "input_schema": {"type": "object", "properties": {}, "additionalProperties": True}},
    {"name": "leggi_n8n_esecuzioni",
     "description": ("Verifica se i workflow n8n sono PARTITI e con che ESITO "
                     "(success/error/running). params: {workflow_id?, solo_errori? (bool), "
                     "limit? (max 100)}. Usalo dopo aver avviato un workflow per controllare "
                     "che sia andato a buon fine o se c'è un errore."),
     "input_schema": {"type": "object", "properties": {
         "workflow_id": {"type": "string"}, "solo_errori": {"type": "boolean"},
         "limit": {"type": "integer"}}, "additionalProperties": True}},
    {"name": "genera_immagine",
     "description": ("Genera un'immagine con l'AI (GPT Image) da una descrizione testuale; "
                     "ritorna un URL pubblico già caricato, usabile come image_url in "
                     "`esegui` pubblica_post. params: {prompt}. Descrivi bene soggetto, stile, "
                     "testo eventuale, formato."),
     "input_schema": {"type": "object", "properties": {"prompt": {"type": "string"}},
                      "required": ["prompt"], "additionalProperties": True}},
]

_FORBIDDEN = ("fuori dal perimetro consentito (solo allowlist; mai control-plane o "
              "registri immutabili; delete solo per id)")

# Istruzione delicata → modello forte (Sonnet), come nel CommandRouter.
_STRONG_HINTS = (" schema", "tabella", "colonna", "migrazione", "alter", "ddl",
                 " bug", "codice", "errore", "refactor", "n8n", "workflow", "automazion")

_CEO_SYS = ("Sei il CEO di K2-AI (PMI italiana). Conosci le posizioni dei reparti e DECIDI. "
            "Parli chiaro e pragmatico, numeri quando ci sono, niente buzzword né riunioni "
            "inutili. Quando chiudi una discussione tra reparti, integri i punti in UNA "
            "decisione azionabile con i prossimi passi, senza ripetere pari pari gli interventi.")

# Triage del CEO (modalità Auto): rispondere lui o convocare i reparti rilevanti.
# Bias forte verso 'rispondi': il CEO è competente e ha i metodi (skill); convoca solo
# quando serve davvero un'analisi di reparto o una decisione contesa tra funzioni.
_CEO_TRIAGE_SYS = (
    "Sei il CEO di K2-AI: competente, operativo, e coordini un team di specialisti "
    "(marketing, vendite, finance, operations, legal, hr). Il tuo lavoro è decidere se una "
    "richiesta la gestisci tu o se serve lo specialista.\n"
    "- modo='rispondi' per il GENERICO: una domanda ampia, un consiglio di alto livello, un "
    "chiarimento, una conferma, un follow-up di un discorso in corso, come impostare un lavoro, "
    "una richiesta trasversale che non entra nel dettaglio di un reparto.\n"
    "- modo='consulta' quando si ENTRA NEL DETTAGLIO di un dominio: un'analisi specialistica, "
    "un dato/numero di reparto, un deliverable concreto (post, campagna, calcolo, contratto, "
    "report, workflow), l'uso di uno strumento specifico, o competenza verticale che è propria "
    "di quel reparto. In questi casi passa la parola a chi di dovere. In 'agenti' metti il "
    "MINIMO: di norma UN SOLO reparto (marketing, vendite, finance, operations, legal, hr); "
    "più di uno solo se la richiesta è davvero contesa tra funzioni.\n"
    "Regola pratica: appena la richiesta diventa specifica/operativa di un reparto, consulta "
    "quel reparto invece di rispondere in proprio. Il generico lo tieni tu, il dettaglio lo "
    "porti allo specialista.")


class ChatAgent:
    """Un agente di dominio che risponde in chat come loop agentico streaming."""

    def __init__(self, orch: "ChatOrchestrator", dominio: str, llm: Any,
                 request: str = "", media: list[dict] | None = None) -> None:
        self.orch = orch
        self.dominio = dominio
        self.llm = llm
        self.request = request or ""     # richiesta owner → scelta della skill/metodo
        self.media = media               # allegati (immagini/PDF) per questo turno
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
                    "description": _SENSOR_DESC.get(
                        tname, f"Sensore di reparto (sola lettura): {tname}."),
                    "input_schema": {"type": "object", "properties": {},
                                     "additionalProperties": True},
                })
        defs.append(_ESEGUI_DEF)
        if self.orch.skills is not None:      # skill invocabili (progressive disclosure)
            defs.append(_CARICA_SKILL_DEF)
            defs.append(_CERCA_SKILL_DEF)
        if self.dominio in _CALCOLA_DOMINI:   # calcolatori deterministici 8e (numeri veri)
            defs.append(_CALCOLA_DEF)
        # tool TRASVERSALI a tutti gli agenti (se registrati): lettura Supabase generica +
        # verifica esecuzioni n8n. Così ogni reparto legge qualsiasi tabella e controlla i workflow.
        for td in _BASE_TOOL_DEFS:
            if td["name"] in names:
                defs.append(td)
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
        canale = str(tinput.get("canale") or "").lower()
        if tinput.get("sql"):
            az: dict = {"tipo": "ddl", "sql": str(tinput.get("sql"))}
        elif canale in ("instagram", "meta_ads", "meta"):
            # azione Meta (publish/commento/ads): porta tutti i campi utili all'attuatore
            az = {k: v for k, v in tinput.items() if k != "descrizione" and v is not None}
            az["canale"] = canale
        elif canale or tinput.get("workflow"):
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
        canale = str(az.get("canale") or "").lower()
        if canale in ("instagram", "meta_ads", "meta"):
            azm = str(az.get("azione") or "").lower()
            if "campagn" in azm or "ads" in azm or canale == "meta_ads":
                return "🟠 crea campagna ADS Meta (in PAUSA, non spende)"
            if "commento" in azm or "reply" in azm:
                return "🌐 rispondi a un commento Instagram"
            return "🌐 PUBBLICA un post su Instagram"
        if canale in ("n8n", "esterno", "external", "webhook"):
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
            # METODO PRE-CARICATO: l'LLM sceglie la skill del reparto più adatta alla
            # richiesta → l'agente risponde SEGUENDO un metodo vero, non improvvisando.
            picked = self.orch._choose_skill(self.request, self.dominio)
            out += self.orch._skill_method(picked)
            # indice compatto delle altre skill del reparto (per approfondire via carica_skill)
            try:
                idx = [n for n in skills.for_domain(self.dominio, 10) if n not in picked]
            except Exception:
                idx = []
            if idx:
                out += ("\n\n# ALTRE SKILL DEL REPARTO (se il metodo sopra non basta, "
                        "caricale con carica_skill; o cerca_skill per tutta la libreria):\n"
                        + skills.index(idx, desc_len=80))
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
                    web_search=bool(self.orch.web), history=hist, media=self.media):
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

    def _skill_method(self, names: list[str]) -> str:
        """Blocco 'metodo da applicare' col testo pieno delle skill scelte → così l'agente
        segue un metodo vero invece di improvvisare. Vuoto se niente skill."""
        if not self.skills or not names:
            return ""
        blocks = []
        for n in names:
            try:
                blocks.append(f"## {n}\n" + self.skills.load(n)[:2500])
            except Exception:
                pass
        if not blocks:
            return ""
        return ("\n\n# METODO K2-AI DA APPLICARE (segui questo procedimento, non improvvisare "
                "né fare premesse generiche):\n" + "\n\n".join(blocks)
                + "\n\nApplica il metodo sopra alla richiesta: professionale, concreto, coi "
                "passi del metodo.")

    def _choose_skill(self, request: str, domain: str | None) -> list[str]:
        """Sceglie la skill (metodo) più adatta alla richiesta. È l'LLM a decidere dalla
        rosa pertinente (giudizio, non keyword); se non può, ripiego deterministico."""
        if not self.skills:
            return []
        try:
            cands = (self.skills.for_domain(domain, 25) if domain
                     else [h["nome"] for h in self.skills.search(request, 12)])
        except Exception:
            cands = []
        if not cands:
            return []
        cj = getattr(self.llm, "complete_json", None)
        if cj is not None:
            try:
                r = cj(system=("Scegli il METODO (skill) più adatto a svolgere la richiesta, "
                               "dalla lista. Rispondi col NOME ESATTO di UNA skill, oppure "
                               "'nessuna' se davvero nessuna è pertinente."),
                       user=(f"RICHIESTA: {request}\n\nMETODI DISPONIBILI:\n"
                             + self.skills.index(cands, desc_len=110)
                             + "\n\nNome della skill più adatta:"),
                       schema={"type": "object", "properties": {"skill": {"type": "string"}},
                               "required": ["skill"]})
                name = str(r.get("skill") or "").strip()
                if name in cands:
                    return [name]
                if name.lower() in ("nessuna", "none", ""):
                    return []               # l'LLM dice: nessun metodo calza → non forzare
            except Exception:
                pass
        # ripiego deterministico (no-LLM o risposta non valida)
        try:
            return (self.skills.pick_for(domain, request, 1) if domain
                    else [h["nome"] for h in self.skills.search(request, 1)])
        except Exception:
            return []

    def _ceo_method(self, text: str) -> str:
        """Metodo pre-caricato per il CEO: la skill più pertinente su tutta la libreria."""
        return self._skill_method(self._choose_skill(text, None))

    def _speaker(self, dom: str, user_prompt: str, llm: Any, key: str, rnd: int,
                 request: str = "", media: list[dict] | None = None):
        """Un intervento: yield eventi taggati (agent/key/round), RITORNA il testo finale."""
        final = ""
        agent = ChatAgent(self, dom, llm, request=request, media=media)
        for ev in agent.stream(None, user_prompt=user_prompt):
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

    def _ceo_close(self, text: str, transcript: list[dict], targets: list[str],
                   media: list[dict] | None = None):
        """Il CEO chiude la discussione: integra i pareri in UNA decisione (Sonnet)."""
        up = ("I reparti " + ", ".join(self._label(d) for d in targets) + " hanno discusso "
              "la richiesta dell'owner. Come CEO, chiudi con UNA decisione unica che integra "
              "i punti chiave, evidenzia accordi e trade-off e dà i prossimi passi concreti."
              + self._ceo_method(text)
              + f"\n\nRICHIESTA OWNER: {text}\n\n<discussione>\n{self._fmt(transcript)}\n</discussione>")
        return (yield from self._ceo_voice(up, media))

    def _ceo_answer(self, text: str, transcript: list[dict], media: list[dict] | None = None):
        """Il CEO risponde DIRETTAMENTE (info/conferma/già discussa), senza convocare i reparti."""
        ctx = self._fmt(transcript) if transcript else ""
        up = (f"RICHIESTA OWNER: {text}\n\n"
              + (f"CONTESTO (posizioni dei reparti finora):\n<discussione>\n{ctx}\n</discussione>\n\n"
                 if ctx else "")
              + "Rispondi tu direttamente come CEO, professionale e concreto, applicando il "
                "metodo qui sotto. Se ti manca un dato specifico, dillo e proponi di consultare "
                "il reparto competente."
              + self._ceo_method(text))
        return (yield from self._ceo_voice(up, media))

    def _ceo_voice(self, user_prompt: str, media: list[dict] | None = None):
        """Voce del CEO in streaming (nessun tool); yield eventi keyed 'ceo', ritorna il testo."""
        final = ""
        try:
            for ev in self.llm_strong.stream_agentic(
                    system=_CEO_SYS, user=user_prompt, tools=[], tool_exec=lambda n, i: {},
                    media=media):
                if ev.get("phase") == "done":
                    final = ev.get("text") or ""
                yield {**ev, "agent": "ceo", "key": "ceo", "round": 0}
        except Exception as exc:
            yield {"phase": "error", "agent": "ceo", "key": "ceo", "error": str(exc)[:200]}
        return final

    def _ceo_triage(self, text: str, transcript: list[dict]) -> dict:
        """Il CEO decide (auto): rispondere lui o consultare quali reparti."""
        cj = getattr(self.llm, "complete_json", None)
        if cj is None:
            return {"modo": "consulta", "agenti": [self._route_one(text)], "motivo": ""}
        ctx = self._fmt(transcript, cap=4000) if transcript else "(nessuna discussione precedente)"
        try:
            r = cj(system=_CEO_TRIAGE_SYS,
                   user=(f"RICHIESTA OWNER: {text}\n\nCONTESTO FINORA:\n{ctx}\n\nDecidi."),
                   schema={"type": "object", "properties": {
                       "modo": {"type": "string", "enum": ["rispondi", "consulta"]},
                       "agenti": {"type": "array", "items": {"type": "string"}},
                       "motivo": {"type": "string"}}, "required": ["modo"]})
            modo = r.get("modo") if r.get("modo") in ("rispondi", "consulta") else "consulta"
            ag = [d for d in (r.get("agenti") or []) if d in DOMINI]
            return {"modo": modo, "agenti": ag, "motivo": str(r.get("motivo") or "")}
        except Exception:
            return {"modo": "consulta", "agenti": [self._route_one(text)], "motivo": ""}

    # ---- flussi conversazione ----
    def _one_to_one(self, dom: str, text: str, history: list[dict] | None, llm: Any,
                    media: list[dict] | None = None):
        try:
            for ev in ChatAgent(self, dom, llm, request=text, media=media).stream(text, history):
                yield {**ev, "agent": dom, "key": dom}
        except Exception as exc:
            yield {"phase": "error", "agent": dom, "key": dom, "error": str(exc)[:200]}

    def _debate(self, text: str, targets: list[str], transcript: list[dict], llm: Any,
                media: list[dict] | None = None):
        """Dibattito sequenziale su trascritto condiviso + chiusura del CEO. Si ferma appena
        i reparti convergono (anche dopo 1 solo giro): niente giri di parole se sono d'accordo."""
        MAX_ROUNDS = 3
        for rnd in range(1, MAX_ROUNDS + 1):
            yield {"phase": "round", "round": rnd, "agents": targets}
            for dom in targets:
                final = yield from self._speaker(
                    dom, self._debate_prompt(dom, text, transcript, rnd),
                    llm, f"{dom}#r{rnd}", rnd, request=text, media=media)
                if final.strip():
                    transcript.append({"speaker": dom, "text": final})
            if self._converged(transcript, targets):   # accordo → stop (anche dopo il 1° giro)
                break
        yield from self._ceo_close(text, transcript, targets, media)

    # ---- stream principale ----
    def stream(self, text: str, agents: Any = None,
               history: list[dict] | None = None,
               media: list[dict] | None = None) -> Iterator[dict]:
        if not text or not text.strip():
            yield {"phase": "error", "agent": "", "error": "istruzione vuota"}
            return
        llm = self._pick_llm(text)
        auto = agents is None or agents == "" or agents == "auto"

        # ── SELEZIONE MANUALE (override): 1 → 1-1; 2+ → dibattito + chiusura CEO ──
        if not auto:
            targets = self.resolve_targets(text, agents)
            yield {"phase": "start", "agents": targets}
            if len(targets) == 1:
                yield from self._one_to_one(targets[0], text, history, llm, media)
            else:
                transcript = self._transcript_from_history(history)
                transcript.append({"speaker": "owner", "text": text})
                yield from self._debate(text, targets, transcript, llm, media)
            yield {"phase": "all_done", "agents": targets}
            return

        # ── AUTO = guidata dal CEO: decide se rispondere lui o convocare i reparti ──
        transcript = self._transcript_from_history(history)
        tri = self._ceo_triage(text, transcript)
        yield {"phase": "triage", "modo": tri["modo"],
               "agenti": tri.get("agenti") or [], "motivo": tri.get("motivo", "")}

        if tri["modo"] == "rispondi":     # il CEO risponde direttamente
            yield {"phase": "start", "agents": ["ceo"]}
            yield from self._ceo_answer(text, transcript, media)
            yield {"phase": "all_done", "agents": ["ceo"]}
            return

        # consulta i reparti rilevanti (subset scelto dal CEO)
        targets = tri.get("agenti") or [self._route_one(text)]
        yield {"phase": "start", "agents": targets}
        if len(targets) == 1:             # un reparto basta → risponde lui
            yield from self._one_to_one(targets[0], text, history, llm, media)
        else:                             # più reparti → dibattito + chiusura CEO
            transcript.append({"speaker": "owner", "text": text})
            yield from self._debate(text, targets, transcript, llm, media)
        yield {"phase": "all_done", "agents": targets}
