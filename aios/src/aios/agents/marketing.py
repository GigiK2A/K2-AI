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
    "Sei il responsabile marketing di K2-AI. Rispetti SEMPRE il Founder Model "
    "(voce, priorità, regole) e i framework forniti. Non pubblichi nulla: PROPONI. "
    "Analizza i dati reali (insight, post uno per uno, competitor, calendario) e "
    "produci proposte concrete e, dove utile, voci di calendario.\n\n"
    "Rispondi SOLO con JSON:\n"
    '{"proposte":[{"tipo":"nuovo_tema|caption|fix|analisi_post","titolo":"...","contenuto":"...","motivo":"..."}],'
    '"voci_calendario":[{"canale":"instagram|blog","titolo":"...","bozza":"...","data_programmata":"YYYY-MM-DD"}]}\n'
    "Niente testo fuori dal JSON."
)
_FOCUS = ["brand-voice", "content-creation", "campaign-plan"]


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
        for n in _FOCUS:
            try:
                out.append(f"## SKILL: {n}\n" + self.skills.load(n)[:1500])
            except KeyError:
                pass
        menu = "\n\n# FRAMEWORK MARKETING DISPONIBILI\n" + self.skills.menu()
        full = ("\n\n# FRAMEWORK DA APPLICARE (testo completo)\n" + "\n\n".join(out)) if out else ""
        return menu + full

    def run(self) -> MarketingResult:
        data = self._gather()
        # re-check policy for programma_contenuto in case tools were registered after __init__
        if "programma_contenuto" in self.k.tools.names():
            self.k.policy.set_level(CALENDAR_ACTION, AutonomyLevel.L1_PROPOSE)
            self.k.policy.set_cap(CALENDAR_ACTION, AutonomyLevel.L1_PROPOSE)

        def sec(k, cap=4000):
            return json.dumps(data.get(k), ensure_ascii=False)[:cap]
        user = (self.founder.to_prompt()
                + "\n\n# DATI REALI\n## Servizi\n" + sec("servizi", 3000)
                + "\n## Temi blog\n" + sec("topics", 2500)
                + "\n## Profilo IG\n" + sec("profilo_ig")
                + "\n## Post IG (analizza UNO PER UNO vs metriche)\n" + sec("post_ig", 3500))
        if "insight" in data:
            user += "\n## Insight IG\n" + sec("insight")
        if "competitor_ig" in data:
            user += "\n## Competitor (analisi)\n" + sec("competitor_ig", 3000)
        if "calendario" in data:
            user += "\n## Calendario attuale\n" + sec("calendario", 2500)
        user += self._skill_context()
        user += ("\n\nValuta i post uno per uno rispetto a reach/like, confronta coi competitor, "
                 "e proponi miglioramenti concreti (proposte) e, dove utile, voci di calendario datate. "
                 "Massimo 6 proposte.")
        parsed = _extract_json(self.llm.complete(system=_SYSTEM, user=user))
        proposte = parsed.get("proposte", [])
        voci = parsed.get("voci_calendario", [])
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
