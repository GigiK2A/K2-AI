from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

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


def propose_tool() -> Tool:
    return Tool(name="proponi_marketing", action_type=PROPOSE_ACTION,
                run=lambda **payload: {"accettata": True, **payload})


class MarketingAgent:
    def __init__(self, *, kernel: Kernel, llm: LLM, founder: FounderModel,
                 skills: "SkillLibrary | None" = None, actor: str = "marketing_agent",
                 discover_competitors: bool = True) -> None:
        self.k = kernel
        self.llm = llm
        self.founder = founder
        self.skills = skills
        self.actor = actor
        self.discover = discover_competitors
        if "proponi_marketing" not in self.k.tools.names():
            self.k.register_tool(propose_tool())
        self.k.policy.set_level(PROPOSE_ACTION, AutonomyLevel.L1_PROPOSE)
        self.k.policy.set_cap(PROPOSE_ACTION, AutonomyLevel.L1_PROPOSE)
        if "programma_contenuto" in self.k.tools.names():
            self.k.policy.set_level(CALENDAR_ACTION, AutonomyLevel.L1_PROPOSE)
            self.k.policy.set_cap(CALENDAR_ACTION, AutonomyLevel.L1_PROPOSE)

    def _read(self, name, **a):
        return self.k.execute(name, actor=self.actor, args=a).result

    def _gather(self) -> dict:
        names = self.k.tools.names()
        data = {"servizi": self._read("leggi_servizi"), "topics": self._read("leggi_topics"),
                "profilo_ig": self._read("leggi_profilo_ig"),
                "post_ig": self._read("leggi_post_ig", limit=10)}
        if "leggi_insight_ig" in names:
            data["insight"] = self._read("leggi_insight_ig")
        if "leggi_calendario" in names:
            data["calendario"] = self._read("leggi_calendario")
        for opt in ("leggi_iscritti", "leggi_newsletter", "leggi_analytics", "leggi_voce_clienti",
                    "leggi_ranking_seo", "leggi_funnel_web", "leggi_competitor_web", "leggi_ads_meta",
                    "leggi_ads_google", "leggi_brand_mentions", "leggi_calendario_contenuti", "leggi_costi"):
            if opt in names:
                try:
                    data[opt] = self._read(opt)
                except Exception:
                    pass
        if "leggi_competitor_ig" in names:
            data["competitor_ig"] = self._read("leggi_competitor_ig")
        # NB: competitor discovery consumes one extra llm.complete() call BEFORE the proposals call
        elif self.discover and "analizza_competitor" in names:
            try:
                from aios.sources.competitor_discovery import discover_competitor_handles
                handles = discover_competitor_handles(self.llm, self.founder)
            except Exception:
                handles = []
            if handles:
                data["competitor_handles"] = handles
                data["competitor_ig"] = self._read("analizza_competitor", usernames=handles)
        return data

    def _skill_context(self) -> str:
        if not self.skills:
            return ""
        out = []
        for n in _FOCUS[:2]:
            try:
                out.append(f"## SKILL: {n}\n" + self.skills.load(n)[:500])
            except KeyError:
                pass
        return ("\n\n# FRAMEWORK (estratti)\n" + "\n\n".join(out)) if out else ""

    def run(self) -> MarketingResult:
        data = self._gather()
        # re-check policy for programma_contenuto in case tools were registered after __init__
        if "programma_contenuto" in self.k.tools.names():
            self.k.policy.set_level(CALENDAR_ACTION, AutonomyLevel.L1_PROPOSE)
            self.k.policy.set_cap(CALENDAR_ACTION, AutonomyLevel.L1_PROPOSE)

        # Prompt LEAN: Haiku con forced-JSON degrada oltre ~12k token → tenere ~9k.
        def sec(k, cap=1200):
            return json.dumps(data.get(k), ensure_ascii=False)[:cap]
        user = (self.founder.to_prompt()[:900]
                + "\n\n# DATI REALI\n## Servizi\n" + sec("servizi", 900)
                + "\n## Temi blog\n" + sec("topics", 800)
                + "\n## Profilo IG\n" + sec("profilo_ig", 400)
                + "\n## Post IG (analizza UNO PER UNO vs metriche)\n" + sec("post_ig", 1200))
        if "insight" in data:
            user += "\n## Insight IG\n" + sec("insight", 600)
        if "leggi_iscritti" in data:
            user += "\n## Iscritti newsletter (email/lifecycle)\n" + sec("leggi_iscritti", 800)
        if "leggi_newsletter" in data:
            user += "\n## Newsletter pubblicate\n" + sec("leggi_newsletter", 600)
        if "leggi_analytics" in data:
            user += "\n## Analytics snapshot (cross-canale)\n" + sec("leggi_analytics", 800)
        if "leggi_voce_clienti" in data:
            user += "\n## Voce clienti (sessioni K-BOT, per research)\n" + sec("leggi_voce_clienti", 1000)
        if data.get("leggi_ranking_seo"):
            user += "\n## Ranking SEO (Search Console)\n" + sec("leggi_ranking_seo", 1000)
        if data.get("leggi_funnel_web"):
            user += "\n## Funnel web (PostHog)\n" + sec("leggi_funnel_web", 800)
        if data.get("leggi_competitor_web"):
            user += "\n## Competitor web\n" + sec("leggi_competitor_web", 800)
        if data.get("leggi_ads_meta"):
            user += "\n## Ads Meta (paid)\n" + sec("leggi_ads_meta", 800)
        if data.get("leggi_ads_google"):
            user += "\n## Ads Google (paid)\n" + sec("leggi_ads_google", 600)
        if data.get("leggi_brand_mentions"):
            user += "\n## Brand mentions (PR)\n" + sec("leggi_brand_mentions", 1000)
        if data.get("leggi_calendario_contenuti"):
            user += "\n## Calendario contenuti (automation/ops)\n" + sec("leggi_calendario_contenuti", 800)
        if data.get("leggi_costi"):
            user += "\n## Costi (budget)\n" + sec("leggi_costi", 600)
        if "competitor_ig" in data:
            user += "\n## Competitor (analisi)\n" + sec("competitor_ig", 1000)
        if "calendario" in data:
            user += "\n## Calendario attuale\n" + sec("calendario", 600)
        user += self._skill_context()
        user += ("\n\nValuta i post uno per uno rispetto a reach/like, confronta coi competitor, "
                 "e proponi miglioramenti concreti (proposte) e, dove utile, voci di calendario datate. "
                 "Copri il PIÙ possibile delle 19 sotto-funzioni (incluse paid, demand_gen, "
                 "automation, pr, influencer, events, cro, creative, budget, strategy), una proposta "
                 "per area dove ha senso. Massimo 10 proposte.")
        schema = {"type": "object", "properties": {
            "proposte": {"type": "array", "items": {"type": "object", "properties": {
                "tipo": {"type": "string"}, "titolo": {"type": "string"},
                "contenuto": {"type": "string"}, "motivo": {"type": "string"}},
                "required": ["tipo", "titolo", "contenuto", "motivo"]}},
            "voci_calendario": {"type": "array", "items": {"type": "object", "properties": {
                "canale": {"type": "string"}, "titolo": {"type": "string"},
                "bozza": {"type": "string"}, "data_programmata": {"type": "string"}},
                "required": ["canale", "titolo"]}}},
            "required": ["proposte"]}
        parsed = self.llm.complete_json(system=_SYSTEM, user=user, schema=schema)
        proposte = _as_dict_list(parsed.get("proposte"))
        voci = _as_dict_list(parsed.get("voci_calendario"))
        ids, cal_ids = [], []
        for p in proposte:
            r = self.k.execute("proponi_marketing", actor=self.actor, args=p)
            if r.approval_id is not None:
                ids.append(r.approval_id)
        if "programma_contenuto" in self.k.tools.names():
            for v in voci:
                r = self.k.execute("programma_contenuto", actor=self.actor, args=v)
                if r.approval_id is not None:
                    cal_ids.append(r.approval_id)
        return MarketingResult(approval_ids=ids, proposals=proposte,
                               calendar_ids=cal_ids, calendar=voci)
