# AIOS Fase 2b — Marketing Agent v2 (full senses, skills, per-post, calendar) Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development. Steps use `- [ ]`.

**Goal:** Upgrade the Marketing agent to (1) use real IG insights + auto-discover & analyze competitors + read the calendar; (2) ground proposals in FULL relevant skills (not just the menu); (3) analyze posts one-by-one vs their metrics; (4) emit real calendar entries that schedule via `programma_contenuto`.

**Architecture:** A param-driven competitor tool (`analizza_competitor(usernames=...)`) lets the agent feed self-discovered handles. `MarketingAgent.run()` gathers insights/competitors(discovered)/calendar, injects the Founder Model + full focus-skills + per-post data into the prompt, asks Claude for `proposte` AND `voci_calendario`, files content via `proponi_marketing` (L1) and calendar entries via `programma_contenuto` (L1). All backward-compatible (new prompt fields are optional; FakeLLM returning only `{"proposte":[...]}` still works).

**Tech Stack:** Python 3.12, pytest, existing aios. No new deps.

---

### Task 1: Param-driven competitor lookup tool

**Files:**
- Modify: `aios/src/aios/sources/tools.py` (add `competitor_lookup_tool`)
- Test: `aios/tests/test_competitor_lookup.py`

- [ ] **Step 1: test**
```python
from aios.sources.tools import competitor_lookup_tool
from aios.kernel import Kernel, ExecOutcome


class _IG:
    def business_discovery(self, u):
        return {"username": u, "followers_count": {"a": 10, "b": 20}[u]}


def test_lookup_runs_for_passed_usernames():
    k = Kernel()
    k.register_tool(competitor_lookup_tool(_IG()))
    res = k.execute("analizza_competitor", actor="marketing", args={"usernames": ["a", "b"]})
    assert res.outcome == ExecOutcome.EXECUTED
    assert res.result["a"]["followers_count"] == 10
    assert res.result["b"]["followers_count"] == 20


def test_lookup_empty_list_returns_empty():
    k = Kernel()
    k.register_tool(competitor_lookup_tool(_IG()))
    assert k.execute("analizza_competitor", actor="m", args={"usernames": []}).result == {}
```

- [ ] **Step 2: run** `cd aios && .venv/bin/pytest tests/test_competitor_lookup.py -q` → FAIL.

- [ ] **Step 3: add to `aios/src/aios/sources/tools.py`**
```python
def competitor_lookup_tool(ig_client: Any) -> Tool:
    def _run(usernames=None, **_):
        out = {}
        for u in (usernames or []):
            try:
                out[u] = ig_client.business_discovery(u)
            except Exception as exc:
                out[u] = {"error": str(exc)}
        return out
    return Tool(name="analizza_competitor", action_type=None, readonly=True, run=_run)
```

- [ ] **Step 4: run** → 2 passed. **Step 5:** full suite + commit
```bash
cd aios && .venv/bin/pytest -q
cd /Volumes/PARASSITA/K-AI/.claude/worktrees/kind-lumiere-240e75
git add aios/src/aios/sources/tools.py aios/tests/test_competitor_lookup.py
git commit -m "feat(aios): param-driven competitor lookup tool (agent feeds discovered handles)"
```

---

### Task 2: Marketing Agent v2

**Files:**
- Modify: `aios/src/aios/agents/marketing.py`
- Test: `aios/tests/test_agent_marketing.py` (append; keep existing tests green)

- [ ] **Step 1: append tests**
```python
def test_agent_uses_insights_competitors_calendar_and_full_skills():
    import json
    from aios.tools import Tool
    from aios.skills import SkillLibrary
    k = _kernel_with_fake_sensors()
    k.register_tool(Tool(name="leggi_insight_ig", action_type=None, readonly=True,
                         run=lambda **_: {"reach": 182, "total_interactions": 9}))
    k.register_tool(Tool(name="analizza_competitor", action_type=None, readonly=True,
                         run=lambda usernames=None, **_: {h: {"followers_count": 100} for h in (usernames or [])}))
    k.register_tool(Tool(name="leggi_calendario", action_type=None, readonly=True,
                         run=lambda **_: [{"titolo": "gia in cal"}]))
    # 1st LLM call = competitor discovery; 2nd = the proposals
    llm = FakeLLM(responses=['{"handles": ["rivale_uno"]}', '{"proposte": [], "voci_calendario": []}'])
    agent = MarketingAgent(kernel=k, llm=llm, founder=default_founder_model(), skills=SkillLibrary())
    agent.run()
    # the proposals prompt (last call) carries real insight + competitor + calendar + a FULL skill
    sys, user = llm.calls[-1]
    assert "182" in user                      # insight reach
    assert "rivale_uno" in user or "followers_count" in user  # competitor analyzed
    assert "gia in cal" in user               # calendar
    assert "SKILL:" in user                   # full skill text injected (not just menu)


def test_agent_files_calendar_entries_via_programma_contenuto():
    import json
    from aios.sources.calendar import calendar_tools, CALENDAR_ACTION
    from aios.autonomy import AutonomyLevel
    class FakeCal:
        def __init__(self): self.rows=[]; self._id=0
        def select(self,t,p): return list(self.rows)
        def insert(self,t,row): self._id+=1; r={"id":self._id,**row}; self.rows.append(r); return [r]
    k = _kernel_with_fake_sensors()
    cal = FakeCal()
    for t in calendar_tools(cal): k.register_tool(t)
    llm = FakeLLM(responses=['{"proposte": [], "voci_calendario": [{"canale":"instagram","titolo":"Post X","bozza":"b","data_programmata":"2026-06-15"}]}'])
    agent = MarketingAgent(kernel=k, llm=llm, founder=default_founder_model())
    res = agent.run()
    assert len(res.calendar_ids) == 1
    # queued at L1, not written until approved
    assert cal.rows == []
    k.resolve_approval(res.calendar_ids[0], approve=True)
    assert len(cal.rows) == 1 and cal.rows[0]["titolo"] == "Post X"
```

- [ ] **Step 2: run** `cd aios && .venv/bin/pytest tests/test_agent_marketing.py -q` → new ones FAIL.

- [ ] **Step 3: rewrite `aios/src/aios/agents/marketing.py`**
```python
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
    raise ValueError("nessun JSON")


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
        if "leggi_competitor_ig" in names:                 # fixed-list (back-compat)
            data["competitor_ig"] = self._read("leggi_competitor_ig")
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
        sec = lambda k: json.dumps(data.get(k), ensure_ascii=False)
        user = (self.founder.to_prompt()
                + "\n\n# DATI REALI\n## Servizi\n" + sec("servizi")
                + "\n## Temi blog\n" + sec("topics")
                + "\n## Profilo IG\n" + sec("profilo_ig")
                + "\n## Insight IG\n" + sec("insight")
                + "\n## Post IG (analizza UNO PER UNO vs metriche)\n" + sec("post_ig"))
        if "competitor_ig" in data:
            user += "\n## Competitor (analisi)\n" + sec("competitor_ig")
        if "calendario" in data:
            user += "\n## Calendario attuale\n" + sec("calendario")
        user += self._skill_context()
        user += ("\n\nValuta i post uno per uno rispetto a reach/like, confronta coi competitor, "
                 "e proponi: miglioramenti concreti (proposte) e, dove utile, voci di calendario datate. Max 6 proposte.")
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
```

NOTE: `discover_competitor_handles` consumes ONE llm.complete call before the proposals call. Tests that pass a single-response FakeLLM and DON'T register `analizza_competitor` won't trigger discovery (so they still use exactly one call). The new insight/competitor test supplies TWO responses (discovery + proposals).

- [ ] **Step 4: run** `cd aios && .venv/bin/pytest tests/test_agent_marketing.py -q` → all pass (existing + 2 new). Fix any wording mismatch in existing skill test (it asserts "FRAMEWORK MARKETING DISPONIBILI" and "content-creation" — both still present via `_skill_context`).

- [ ] **Step 5:** full suite + commit
```bash
cd aios && .venv/bin/pytest -q
cd /Volumes/PARASSITA/K-AI/.claude/worktrees/kind-lumiere-240e75
git add aios/src/aios/agents/marketing.py aios/tests/test_agent_marketing.py
git commit -m "feat(aios): Marketing Agent v2 — insights, auto-competitor, full skills, per-post, calendar"
```

---

### Task 3: wire v2 into the Supabase runner

**Files:**
- Modify: `aios/run_marketing_supabase.py`

- [ ] **Step 1:** register insights + competitor-lookup + calendar tools and enable web search. After IG tools registration add:
```python
    from aios.sources.tools import insights_tools, competitor_lookup_tool
    from aios.sources.calendar import calendar_tools
    for t in insights_tools(ig): k.register_tool(t)
    k.register_tool(competitor_lookup_tool(ig))
    for t in calendar_tools(k._supabase): k.register_tool(t)
```
Ensure the agent is built with `skills=SkillLibrary()` and the LLM with `enable_web_search=True` (already). Remove the old hardcoded `COMPETITORS`/`competitor_tools` fixed-list block if present (agent now discovers).

- [ ] **Step 2:** parse check + full suite + commit
```bash
cd aios && .venv/bin/python -c "import ast; ast.parse(open('run_marketing_supabase.py').read()); print('ok')" && .venv/bin/pytest -q
cd /Volumes/PARASSITA/K-AI/.claude/worktrees/kind-lumiere-240e75
git add aios/run_marketing_supabase.py
git commit -m "feat(aios): runner wires v2 senses (insights, competitor lookup, calendar)"
```

---

## Self-Review
- Spec: insights+auto-competitor+calendar in reasoning (T2 _gather), full skills (T2 _skill_context), per-post (T2 prompt), calendar scheduling (T2 voci_calendario → programma_contenuto). T1 enables agent-fed competitor handles.
- Back-compat: new prompt sections only added when data present; FakeLLM single-response tests still work (discovery only triggers if `analizza_competitor` registered); `MarketingResult` new fields have defaults.
- Placeholder scan: none. Types: `MarketingResult.calendar_ids/calendar` defined+used; CALENDAR_ACTION consistent with sources/calendar.py.
- Live verify: run `run_marketing_supabase.py` → proposals in aios_approvals, calendar entries queued; approving a calendar entry writes aios_content_calendar (check via MCP).
