from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from aios.agents import competenza, esperienza, sensori
from aios.autonomy import ActionType, AutonomyLevel
from aios.kernel import Kernel
from aios.founder import FounderModel
from aios.llm import LLM
from aios.tools import Tool
from aios.skills import SkillLibrary

PROPOSE_ACTION = ActionType("marketing", "content.proposta")
CALENDAR_ACTION = ActionType("marketing", "calendario.voce")

_SYSTEM = (
    "Sei il direttore marketing (CMO) di K2-AI. Rispetti SEMPRE il Founder Model e i "
    "framework forniti. Non pubblichi nulla: PROPONI (L1).\n\n"
    "Copri l'INTERO reparto marketing di una multinazionale — 19 sotto-funzioni. "
    "[D]=hai dati reali, usali; [S]=nessuna fonte ancora, lavora in modalità strategia e "
    "dichiaralo (NON inventare numeri):\n"
    "1 brand[D] · 2 content[D] · 3 social[D] · 4 seo[D] · 5 email[D] · 6 product_mkt[D] · "
    "7 analytics[D] · 8 research[D] · 9 competitor[D] · "
    "10 paid (ads Meta/Google, se presenti) · 11 demand_gen (pipeline da lead/funnel) · "
    "12 automation (calendario contenuti, igiene UTM/CRM, workflow) · "
    "13 pr (brand mentions / ufficio stampa) · 14 influencer (scouting profili in nicchia) · "
    "15 events[S] (webinar dai gap di contenuto) · 16 cro (funnel sito/landing, se PostHog) · "
    "17 creative[S] (brief/asset, prompt immagini) · 18 budget (costi marketing) · "
    "19 strategy (piano trimestrale che lega le aree sopra).\n\n"
    "Regole: copri PIÙ aree diverse (non solo i post). Numeri sempre quando hai i dati; "
    "se una funzione è [S] o senza dati, proponi comunque l'azione strategica e scrivi "
    "'[strategia: dati non collegati]' nel motivo. Niente buzzword. Ogni proposta azionabile.\n\n"
    "Rispondi SOLO con JSON:\n"
    '{"proposte":[{"tipo":"brand|content|social|seo|email|product_mkt|analytics|research|'
    'competitor|paid|demand_gen|automation|pr|influencer|events|cro|creative|budget|strategy|fix",'
    '"titolo":"...","contenuto":"...","motivo":"..."}],'
    '"voci_calendario":[{"canale":"instagram|blog","titolo":"...","bozza":"...","data_programmata":"YYYY-MM-DD"}]}\n'
    "Niente testo fuori dal JSON."
)
_FOCUS = ["brand-voice", "content-creation", "campaign-plan", "seo-italia",
          "email-sequence", "marketing-analytics", "posizionamento-strategico"]


@dataclass
class MarketingResult:
    approval_ids: list[int]
    proposals: list[dict]
    calendar_ids: list[int] = field(default_factory=list)
    calendar: list[dict] = field(default_factory=list)
    # azioni interne partite da sole, da riportare all'owner
    eseguite: list[dict] = field(default_factory=list)


def _extract_json(text: str) -> dict:
    t = text.strip()
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        pass
    m = re.search(r"```(?:json)?\s*(.*?)```", t, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            t = m.group(1).strip()
    a, b = t.find("{"), t.rfind("}")
    if a >= 0 and b > a:
        return json.loads(t[a:b + 1])
    raise ValueError("nessun oggetto JSON nella risposta")


def _as_dict_list(x) -> list[dict]:
    """Coerce a model field to a list of dicts. Handles the model returning a
    JSON-encoded string instead of an array, or non-dict items."""
    if isinstance(x, str):
        try:
            x = json.loads(x)
        except Exception:
            return []
    if not isinstance(x, list):
        return []
    return [i for i in x if isinstance(i, dict)]


def propose_tool(client=None) -> Tool:
    """Tool di proposta marketing. Su approvazione, se la proposta porta un'azione
    strutturata valida, la esegue via attuatore (allowlist, no delete/denaro)."""
    def _run(**payload):
        out = {"accettata": True, **payload}
        az = payload.get("azione")
        if az and client is not None:
            try:
                from aios.actuator import apply_action
                out["attuatore"] = apply_action(client, az)
            except Exception as exc:
                out["attuatore"] = {"ok": False, "errore": str(exc)}
        return out
    return Tool(name="proponi_marketing", action_type=PROPOSE_ACTION, run=_run)


class MarketingAgent:
    def __init__(self, *, kernel: Kernel, llm: LLM, founder: FounderModel,
                 skills: "SkillLibrary | None" = None, actor: str = "marketing_agent",
                 discover_competitors: bool = True, llm_strong: "LLM | None" = None) -> None:
        self.k = kernel
        self.llm = llm
        # scelta playbook e letture col modello economico, GIUDIZIO col forte
        self.llm_giudizio = llm_strong or llm
        self.founder = founder
        self.skills = skills
        self.actor = actor
        self.discover = discover_competitors
        self._client = getattr(self.k, "_supabase", None)
        if "proponi_marketing" not in self.k.tools.names():
            self.k.register_tool(propose_tool(self._client))
        self.k.policy.set_level(PROPOSE_ACTION, AutonomyLevel.L1_PROPOSE)
        self.k.policy.set_cap(PROPOSE_ACTION, AutonomyLevel.L1_PROPOSE)
        if "programma_contenuto" in self.k.tools.names():
            self.k.policy.set_level(CALENDAR_ACTION, AutonomyLevel.L1_PROPOSE)
            self.k.policy.set_cap(CALENDAR_ACTION, AutonomyLevel.L1_PROPOSE)

    def _read(self, name, **a):
        return self.k.execute(name, actor=self.actor, args=a).result

    def _leggi_sicuro(self, name, **a):
        """Legge un sensore isolando il guasto e registrando la provenienza in
        self.fonti. Con il token Instagram invalidato (ago 2026) `_gather` sollevava
        sul primo read e il marketing non produceva NIENTE per giorni: un sensore rotto
        deve costare quel sensore, non la giornata del reparto."""
        return sensori.leggi_sicuro(self._read, name, self.fonti, **a)

    def _gather(self) -> dict:
        names = self.k.tools.names()
        self.fonti: dict[str, str] = {}
        data: dict = {}
        # Nessun sensore è obbligatorio: il reparto lavora su quello che risponde.
        for chiave, tool, args in (
                ("servizi", "leggi_servizi", {}), ("topics", "leggi_topics", {}),
                ("profilo_ig", "leggi_profilo_ig", {}),
                ("post_ig", "leggi_post_ig", {"limit": 10}),
                ("insight", "leggi_insight_ig", {}), ("calendario", "leggi_calendario", {})):
            if tool in names:
                v = self._leggi_sicuro(tool, **args)
                if v is not None:
                    data[chiave] = v
        for opt in ("leggi_iscritti", "leggi_newsletter", "leggi_analytics", "leggi_voce_clienti",
                    "leggi_ranking_seo", "leggi_funnel_web", "leggi_competitor_web", "leggi_ads_meta",
                    "leggi_ads_google", "leggi_brand_mentions", "leggi_calendario_contenuti",
                    "leggi_costi", "leggi_suite", "leggi_prospects",
                    "leggi_competitor_trovati", "leggi_lead", "leggi_lead_kbot",
                    "leggi_clienti", "leggi_inbox"):
            if opt in names:
                v = self._leggi_sicuro(opt)
                if v is not None:
                    data[opt] = v
        if "leggi_competitor_ig" in names:
            v = self._leggi_sicuro("leggi_competitor_ig")
            if v is not None:
                data["competitor_ig"] = v
        # NB: competitor discovery consumes one extra llm.complete() call BEFORE the proposals call
        elif self.discover and "analizza_competitor" in names:
            try:
                from aios.sources.competitor_discovery import discover_competitor_handles
                handles = discover_competitor_handles(self.llm, self.founder)
            except Exception:
                handles = []
            if handles:
                data["competitor_handles"] = handles
                v = self._leggi_sicuro("analizza_competitor", usernames=handles)
                if v is not None:
                    data["competitor_ig"] = v
        return data

    def _stato_fonti(self) -> str:
        return sensori.blocco_stato(getattr(self, "fonti", {}))

    def _skill_context(self, dati: str = "") -> str:
        """Il metodo professionale che il CMO ha in mano.

        Prima: 2 skill × 500 caratteri, cioè frontmatter YAML e titolo — zero metodo su
        una libreria di 43 playbook del reparto. Ora: indice di TUTTI i suoi playbook
        (sa cosa ha) più il testo pieno di quelli che sceglie per i dati di oggi."""
        return competenza.competenza(self.skills, self.llm, "marketing", _FOCUS, dati)

    def run(self) -> MarketingResult:
        from aios import billing
        # Hard-stop di budget: agente oltre il tetto mensile → non parte.
        status = billing.get_meter().check(self.actor)
        if status.over:
            try:
                self.k.audit.append(action_key=PROPOSE_ACTION.key, event="budget_block",
                                    actor=self.actor, detail={
                                        "spent_eur": status.spent_eur, "cap_eur": status.cap_eur,
                                        "period": status.period})
            except Exception:
                pass
            return MarketingResult(approval_ids=[], proposals=[])
        with billing.attribute(self.actor):
            return self._run_inner()

    def _run_inner(self) -> MarketingResult:
        data = self._gather()
        # re-check policy for programma_contenuto in case tools were registered after __init__
        if "programma_contenuto" in self.k.tools.names():
            self.k.policy.set_level(CALENDAR_ACTION, AutonomyLevel.L1_PROPOSE)
            self.k.policy.set_cap(CALENDAR_ACTION, AutonomyLevel.L1_PROPOSE)

        # Prompt LEAN: Haiku con forced-JSON degrada oltre ~12k token → tenere ~9k.
        def sec(k, cap=1200):
            return json.dumps(data.get(k), ensure_ascii=False)[:cap]
        from aios import org, goals
        role_ctx = org.get_chart().context_for(self.actor)
        goals_ctx = goals.ancestry_context(self._client)
        user = (self.founder.to_prompt()[:900]
                + (("\n\n" + role_ctx) if role_ctx else "")
                + (("\n\n" + goals_ctx) if goals_ctx else "")
                + "\n\n# DATI REALI")
        # Solo le sezioni che hanno davvero dati: una sezione con "null" dentro insegna
        # all'agente che quel canale esiste e va commentato, ed è così che nascono le
        # proposte su metriche immaginarie.
        for chiave, etichetta, cap in (
                ("servizi", "Servizi", 900),
                ("topics", "Temi blog", 800),
                ("leggi_suite", "Catalogo prodotti K2-AI (suite, fonte unica)", 1200),
                ("leggi_ranking_seo", "Ranking SEO (Search Console)", 1000),
                ("leggi_funnel_web", "Funnel web (PostHog)", 800),
                ("leggi_analytics", "Analytics snapshot (cross-canale)", 800),
                ("leggi_voce_clienti", "Voce clienti (sessioni K-BOT, per research)", 1000),
                ("leggi_iscritti", "Iscritti newsletter (email/lifecycle)", 800),
                ("leggi_newsletter", "Newsletter pubblicate", 600),
                ("leggi_prospects", "Prospect qualificati (ricerca clienti)", 1000),
                ("leggi_lead", "Pipeline lead (demand gen)", 800),
                ("leggi_lead_kbot", "Lead dal K-BOT (chi ha chiesto la diagnosi)", 800),
                ("leggi_clienti", "Clienti attivi", 600),
                ("leggi_competitor_trovati", "Competitor trovati (ricerca web)", 800),
                ("leggi_competitor_web", "Competitor web", 800),
                ("leggi_brand_mentions", "Brand mentions (PR)", 1000),
                ("leggi_ads_meta", "Ads Meta (paid)", 800),
                ("leggi_ads_google", "Ads Google (paid)", 600),
                ("leggi_calendario_contenuti", "Calendario contenuti (automation/ops)", 800),
                ("leggi_costi", "Costi (budget)", 600),
                ("profilo_ig", "Profilo IG", 400),
                ("post_ig", "Post IG (analizza UNO PER UNO vs metriche)", 1200),
                ("insight", "Insight IG", 600),
                ("competitor_ig", "Competitor IG (analisi)", 1000),
                ("calendario", "Calendario attuale", 600)):
            if data.get(chiave):
                user += f"\n## {etichetta}\n" + sec(chiave, cap)
        user += self._stato_fonti()
        user += esperienza.blocco_esperienza(self._client, "marketing",
                                             PROPOSE_ACTION.key)
        user += self._skill_context(sec('servizi', 600) + sec('leggi_ranking_seo', 600))
        # Coda del prompt costruita su cosa risponde: chiedere l'analisi post-per-post
        # quando Instagram è giù produce solo invenzioni.
        coperte = [n for n, s in getattr(self, "fonti", {}).items() if s.startswith("ok")]
        if data.get("post_ig"):
            user += ("\n\nValuta i post uno per uno rispetto a reach/like, confronta coi "
                     "competitor, e proponi miglioramenti concreti.")
        else:
            user += ("\n\nInstagram non è disponibile in questo giro: NON parlare di post, "
                     "reach o follower. Il reparto marketing è molto più largo di un canale "
                     "social — lavora su ciò che risponde davvero.")
        user += (f"\n\nFonti con dati adesso: {', '.join(coperte) or 'nessuna'}. "
                 "Copri il PIÙ possibile delle 19 sotto-funzioni tra quelle che le fonti "
                 "disponibili permettono (seo, email, demand_gen, research, competitor, cro, "
                 "analytics, product_mkt, budget, strategy, automation, pr…), una proposta per "
                 "area dove ha senso, e dove utile voci di calendario datate. "
                 "una proposta per area dove ha senso." + competenza.ESIGENZA_QUALITA)
        schema = {"type": "object", "properties": {
            "proposte": {"type": "array", "items": {"type": "object", "properties": {
                "tipo": {"type": "string"}, "titolo": {"type": "string"},
                "contenuto": {"type": "string"}, "motivo": {"type": "string"},
                "azione": {"type": "object", "properties": {
                    "tabella": {"type": "string"}, "op": {"type": "string"},
                    "match": {"type": "object"}, "dati": {"type": "object"}}}},
                "required": ["tipo", "titolo", "contenuto", "motivo"]}},
            "voci_calendario": {"type": "array", "items": {"type": "object", "properties": {
                "canale": {"type": "string"}, "titolo": {"type": "string"},
                "bozza": {"type": "string"}, "data_programmata": {"type": "string"}},
                "required": ["canale", "titolo"]}}},
            "required": ["proposte"]}
        # giudizio col modello forte, letture e scelta dei playbook col leggero
        parsed = self.llm_giudizio.complete_json(system=_SYSTEM, user=user, schema=schema)
        proposte = _as_dict_list(parsed.get("proposte"))
        voci = _as_dict_list(parsed.get("voci_calendario"))
        ids, cal_ids, eseguite = [], [], []
        from aios.agents import esecuzione
        from aios.agents.domain import _ensure_action
        for p in proposte:
            p["azione"] = _ensure_action(p)   # attuatore: ogni proposta ha azione valida
            # interno → si fa subito e si riporta; esterno/delete/DDL → in coda
            modo, out = esecuzione.applica_o_accoda(self.k, "proponi_marketing", self.actor, p)
            if modo == "eseguita":
                eseguite.append(out)
            elif out is not None:
                ids.append(out)
        if "programma_contenuto" in self.k.tools.names():
            for v in voci:
                r = self.k.execute("programma_contenuto", actor=self.actor, args=v)
                if r.approval_id is not None:
                    cal_ids.append(r.approval_id)
        return MarketingResult(approval_ids=ids, proposals=proposte,
                               calendar_ids=cal_ids, calendar=voci,
                               eseguite=eseguite)
