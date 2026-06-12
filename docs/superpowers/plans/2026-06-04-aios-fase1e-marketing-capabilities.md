# AIOS Fase 1e — Marketing capabilities (calendar write, competitor, trends) Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`).

**Goal:** Give the Marketing agent real powers beyond reading: write/modify an editorial calendar (via L1 proposals), spy competitors on Instagram, and research web trends.

**Architecture:** New read-only (L0) sensors for competitors (IG `business_discovery`). A calendar capability split in two: a read tool (L0) and a `programma_contenuto` action tool (L1, capped L1) whose `run` writes a row to `aios_content_calendar` only after human approval. Web trends via Claude's server-side `web_search` tool, toggled on `AnthropicLLM`. The agent gathers competitor data + reads the calendar, and can file calendar entries through the kernel approval queue. Unit-tested with fakes; live needs service_role key (calendar writes) + IG token (competitors) + Anthropic key (web search).

**Tech Stack:** Python 3.12, pytest, anthropic SDK, existing aios kernel/REST/sensors. Table `aios_content_calendar` already created (RLS on).

---

### Task 1: Competitor Instagram sensor

**Files:**
- Modify: `aios/src/aios/sources/instagram.py` (add `business_discovery`)
- Modify: `aios/src/aios/sources/tools.py` (add `competitor_tools`)
- Test: `aios/tests/test_sources_competitor.py`

- [ ] **Step 1: test `aios/tests/test_sources_competitor.py`**

```python
from aios.sources.instagram import InstagramClient
from aios.sources.tools import competitor_tools
from aios.kernel import Kernel, ExecOutcome


def _client(payload):
    return InstagramClient(token="T", ig_user_id="999",
                           fetch=lambda url: payload)


def test_business_discovery_parses():
    payload = {"business_discovery": {"username": "rival", "followers_count": 5000,
                                      "media_count": 120,
                                      "media": {"data": [{"caption": "x", "like_count": 40}]}}}
    bd = _client(payload).business_discovery("rival")
    assert bd["followers_count"] == 5000
    assert bd["media"]["data"][0]["like_count"] == 40


def test_business_discovery_sends_username_in_fields():
    seen = {}
    def fetch(url):
        seen["url"] = url
        return {"business_discovery": {"username": "rival"}}
    InstagramClient(token="T", ig_user_id="999", fetch=fetch).business_discovery("rival")
    assert "business_discovery.username(rival)" in seen["url"]


def test_competitor_tool_runs_via_kernel():
    payload = {"business_discovery": {"username": "rival", "followers_count": 10}}
    k = Kernel()
    for t in competitor_tools(_client(payload), ["rival"]):
        k.register_tool(t)
    res = k.execute("leggi_competitor_ig", actor="marketing", args={})
    assert res.outcome == ExecOutcome.EXECUTED
    assert res.result["rival"]["followers_count"] == 10
```

- [ ] **Step 2: run** `cd aios && .venv/bin/pytest tests/test_sources_competitor.py -q` → FAIL.

- [ ] **Step 3: add to `aios/src/aios/sources/instagram.py`** (a method on `InstagramClient`)

```python
    def business_discovery(self, username: str, media_limit: int = 6) -> dict[str, Any]:
        fields = (
            f"business_discovery.username({username})"
            "{username,followers_count,media_count,"
            f"media.limit({media_limit})"
            "{caption,like_count,comments_count,timestamp,media_type,permalink}}"
        )
        data = self._get(self._uid, {"fields": fields})
        return data.get("business_discovery", {})
```

- [ ] **Step 4: add to `aios/src/aios/sources/tools.py`**

```python
def competitor_tools(ig_client: Any, usernames: list[str]) -> list[Tool]:
    def _run(**_):
        out = {}
        for u in usernames:
            try:
                out[u] = ig_client.business_discovery(u)
            except Exception as exc:  # competitor private / not found / rate limited
                out[u] = {"error": str(exc)}
        return out
    return [Tool(name="leggi_competitor_ig", action_type=None, readonly=True, run=_run)]
```

- [ ] **Step 5: run** `cd aios && .venv/bin/pytest tests/test_sources_competitor.py -q` → 3 passed.
- [ ] **Step 6: full suite + commit**
```bash
cd aios && .venv/bin/pytest -q
cd /Volumes/PARASSITA/K-AI/.claude/worktrees/kind-lumiere-240e75
git add aios/src/aios/sources/instagram.py aios/src/aios/sources/tools.py aios/tests/test_sources_competitor.py
git commit -m "feat(aios): competitor Instagram sensor (business_discovery)"
```

---

### Task 2: Editorial calendar tools (read L0 + propose-write L1)

**Files:**
- Create: `aios/src/aios/sources/calendar.py`
- Test: `aios/tests/test_calendar.py`

- [ ] **Step 1: test `aios/tests/test_calendar.py`**

```python
from aios.kernel import Kernel, ExecOutcome
from aios.autonomy import AutonomyLevel
from aios.sources.calendar import calendar_tools, CALENDAR_ACTION


class FakeClient:
    def __init__(self):
        self.rows = []
        self._id = 0
    def select(self, table, params):
        return list(self.rows)
    def insert(self, table, row):
        self._id += 1
        r = {"id": self._id, **row}
        self.rows.append(r)
        return [r]


def _kernel_with_calendar():
    k = Kernel()
    c = FakeClient()
    for t in calendar_tools(c):
        k.register_tool(t)
    return k, c


def test_read_calendar_is_readonly():
    k, c = _kernel_with_calendar()
    c.rows = [{"id": 1, "canale": "instagram", "titolo": "x"}]
    res = k.execute("leggi_calendario", actor="m", args={})
    assert res.outcome == ExecOutcome.EXECUTED and res.result[0]["titolo"] == "x"


def test_schedule_is_L1_and_queues_then_writes_on_approval():
    k, c = _kernel_with_calendar()
    args = {"canale": "instagram", "titolo": "Post agenti email",
            "bozza": "70% email gestite...", "data_programmata": "2026-06-11"}
    res = k.execute("programma_contenuto", actor="marketing_agent", args=args)
    # L1 -> queued, NOT written yet
    assert res.outcome == ExecOutcome.QUEUED
    assert c.rows == []
    # approve -> now it writes
    run = k.resolve_approval(res.approval_id, approve=True)
    assert run.outcome == ExecOutcome.EXECUTED
    assert len(c.rows) == 1 and c.rows[0]["titolo"] == "Post agenti email"
    assert c.rows[0]["stato"] == "approvato"


def test_calendar_action_capped_at_L1():
    k, c = _kernel_with_calendar()
    k.execute("programma_contenuto", actor="m", args={"canale": "blog", "titolo": "t"})
    assert k.policy.level_for(CALENDAR_ACTION) == AutonomyLevel.L1_PROPOSE
```

- [ ] **Step 2: run** `cd aios && .venv/bin/pytest tests/test_calendar.py -q` → FAIL.

- [ ] **Step 3: `aios/src/aios/sources/calendar.py`**

```python
from __future__ import annotations

from typing import Any

from aios.autonomy import ActionType
from aios.tools import Tool

CALENDAR_ACTION = ActionType("marketing", "calendario.voce")


def calendar_tools(client: Any) -> list[Tool]:
    def _schedule(canale: str, titolo: str, bozza: str = "",
                  data_programmata: str | None = None,
                  fonte_tipo: str | None = None, fonte_id: int | None = None,
                  note: str | None = None, **_) -> Any:
        row = {"canale": canale, "titolo": titolo, "bozza": bozza, "stato": "approvato"}
        if data_programmata:
            row["data_programmata"] = data_programmata
        if fonte_tipo:
            row["fonte_tipo"] = fonte_tipo
        if fonte_id is not None:
            row["fonte_id"] = fonte_id
        if note:
            row["note"] = note
        return client.insert("aios_content_calendar", row)

    return [
        Tool(name="leggi_calendario", action_type=None, readonly=True,
             run=lambda **_: client.select(
                 "aios_content_calendar",
                 {"select": "*", "order": "data_programmata.asc"})),
        Tool(name="programma_contenuto", action_type=CALENDAR_ACTION, run=_schedule),
    ]
```

Note: `programma_contenuto` has an `action_type` (not readonly) → governed by policy. The agent (Task 3) sets it to L1 + cap L1, so a call QUEUES an approval; the row is inserted only when `resolve_approval(..., approve=True)` runs the tool.

- [ ] **Step 4: run** `cd aios && .venv/bin/pytest tests/test_calendar.py -q` → 3 passed.
- [ ] **Step 5: full suite + commit**
```bash
cd aios && .venv/bin/pytest -q
cd /Volumes/PARASSITA/K-AI/.claude/worktrees/kind-lumiere-240e75
git add aios/src/aios/sources/calendar.py aios/tests/test_calendar.py
git commit -m "feat(aios): editorial calendar tools (read L0 + schedule L1)"
```

---

### Task 3: Web-search-enabled LLM

**Files:**
- Modify: `aios/src/aios/llm.py` (add web search toggle to AnthropicLLM)
- Test: `aios/tests/test_llm.py` (append)

- [ ] **Step 1: append tests to `aios/tests/test_llm.py`**

```python
def test_anthropic_web_search_tool_is_added_when_enabled(monkeypatch):
    import aios.llm as llmmod

    captured = {}

    class _FakeMessages:
        def create(self, **kw):
            captured.update(kw)
            class _Block:
                type = "text"; text = "ok"
            class _Resp:
                content = [_Block()]
            return _Resp()

    class _FakeClient:
        def __init__(self, *a, **k):
            self.messages = _FakeMessages()

    monkeypatch.setattr(llmmod, "_anthropic_client", lambda key: _FakeClient())
    llm = llmmod.AnthropicLLM(api_key="K", enable_web_search=True)
    out = llm.complete(system="s", user="u")
    assert out == "ok"
    tools = captured.get("tools") or []
    assert any(t.get("type", "").startswith("web_search") for t in tools)


def test_anthropic_no_tools_when_web_search_disabled(monkeypatch):
    import aios.llm as llmmod

    captured = {}

    class _FakeMessages:
        def create(self, **kw):
            captured.update(kw)
            class _Block:
                type = "text"; text = "ok"
            class _Resp:
                content = [_Block()]
            return _Resp()

    class _FakeClient:
        def __init__(self, *a, **k):
            self.messages = _FakeMessages()

    monkeypatch.setattr(llmmod, "_anthropic_client", lambda key: _FakeClient())
    llm = llmmod.AnthropicLLM(api_key="K")
    llm.complete(system="s", user="u")
    assert "tools" not in captured or not captured["tools"]
```

- [ ] **Step 2: run** `cd aios && .venv/bin/pytest tests/test_llm.py -q` → the 2 new FAIL (no `_anthropic_client` / no `enable_web_search`).

- [ ] **Step 3: edit `aios/src/aios/llm.py`** — refactor `AnthropicLLM` to use a module-level `_anthropic_client` factory (so tests can patch it) and support web search:

```python
def _anthropic_client(api_key: str):
    import anthropic
    return anthropic.Anthropic(api_key=api_key)


class AnthropicLLM:
    def __init__(self, api_key: str | None = None,
                 model: str = "claude-haiku-4-5-20251001",
                 max_tokens: int = 2000, enable_web_search: bool = False) -> None:
        import os
        self._client = _anthropic_client(api_key or os.environ["ANTHROPIC_API_KEY"])
        self._model = model
        self._max_tokens = max_tokens
        self._web = enable_web_search

    def complete(self, *, system: str, user: str) -> str:
        kwargs = dict(model=self._model, max_tokens=self._max_tokens, system=system,
                      messages=[{"role": "user", "content": user}])
        if self._web:
            kwargs["tools"] = [{"type": "web_search_20250305",
                                "name": "web_search", "max_uses": 5}]
        msg = self._client.messages.create(**kwargs)
        return "".join(b.text for b in msg.content
                       if getattr(b, "type", None) == "text")
```

(Keep `LLM` protocol and `FakeLLM` unchanged.)

- [ ] **Step 4: run** `cd aios && .venv/bin/pytest tests/test_llm.py -q` → all pass (5 total).
- [ ] **Step 5: full suite + commit**
```bash
cd aios && .venv/bin/pytest -q
cd /Volumes/PARASSITA/K-AI/.claude/worktrees/kind-lumiere-240e75
git add aios/src/aios/llm.py aios/tests/test_llm.py
git commit -m "feat(aios): optional Claude web-search in AnthropicLLM (trends)"
```

---

### Task 4: Wire competitor + calendar into the agent; update runner

**Files:**
- Modify: `aios/src/aios/agents/marketing.py` (gather competitor + calendar; allow scheduling)
- Modify: `aios/run_marketing_supabase.py` (register new tools, enable web search, pass competitors)
- Test: `aios/tests/test_agent_marketing.py` (append)

- [ ] **Step 1: append test to `aios/tests/test_agent_marketing.py`**

```python
def test_agent_gathers_competitor_and_calendar_when_present():
    import json
    from aios.tools import Tool
    k = _kernel_with_fake_sensors()
    k.register_tool(Tool(name="leggi_competitor_ig", action_type=None, readonly=True,
                         run=lambda **_: {"rival": {"followers_count": 999}}))
    k.register_tool(Tool(name="leggi_calendario", action_type=None, readonly=True,
                         run=lambda **_: [{"titolo": "gia in calendario"}]))
    llm = FakeLLM(responses=['{"proposte": []}'])
    agent = MarketingAgent(kernel=k, llm=llm, founder=default_founder_model())
    agent.run()
    _, user = llm.calls[0]
    assert "999" in user            # competitor data reached the prompt
    assert "gia in calendario" in user  # calendar reached the prompt
```

- [ ] **Step 2: run** `cd aios && .venv/bin/pytest tests/test_agent_marketing.py -q` → the new one FAILs.

- [ ] **Step 3: edit `_gather` in `aios/src/aios/agents/marketing.py`** to include competitor + calendar when those tools are registered (optional, so existing tests pass):

```python
    def _gather(self) -> dict:
        def read(name, **a):
            return self.k.execute(name, actor=self.actor, args=a).result
        data = {
            "servizi": read("leggi_servizi"),
            "topics": read("leggi_topics"),
            "profilo_ig": read("leggi_profilo_ig"),
            "post_ig": read("leggi_post_ig", limit=10),
        }
        names = self.k.tools.names()
        if "leggi_competitor_ig" in names:
            data["competitor_ig"] = read("leggi_competitor_ig")
        if "leggi_calendario" in names:
            data["calendario"] = read("leggi_calendario")
        return data
```

And in `run()`, after the existing data sections, append the optional ones to the `user` prompt before the instruction line:

```python
        if "competitor_ig" in data:
            user += "\n## Competitor Instagram\n" + json.dumps(data["competitor_ig"], ensure_ascii=False)
        if "calendario" in data:
            user += "\n## Calendario editoriale attuale\n" + json.dumps(data["calendario"], ensure_ascii=False)
```

(Place these additions where the other `user += "## ..."` lines are, before the final "Valuta cosa funziona…" instruction.)

- [ ] **Step 4: run** `cd aios && .venv/bin/pytest tests/test_agent_marketing.py -q` → all pass.

- [ ] **Step 5: update `aios/run_marketing_supabase.py`** — register calendar + competitor tools and enable web search. After registering content + IG tools, add:

```python
    from aios.sources.calendar import calendar_tools
    from aios.sources.tools import competitor_tools
    for t in calendar_tools(k._supabase):
        k.register_tool(t)
    COMPETITORS = ["aizwei", "ey_italy"]  # placeholder @handles — edit to real competitors
    for t in competitor_tools(ig, COMPETITORS):
        k.register_tool(t)
```

and change the LLM line to `AnthropicLLM(enable_web_search=True)`. Verify parse:
`cd aios && .venv/bin/python -c "import ast; ast.parse(open('run_marketing_supabase.py').read()); print('ok')"`

- [ ] **Step 6: full suite + commit**
```bash
cd aios && .venv/bin/pytest -q
cd /Volumes/PARASSITA/K-AI/.claude/worktrees/kind-lumiere-240e75
git add aios/src/aios/agents/marketing.py aios/run_marketing_supabase.py aios/tests/test_agent_marketing.py
git commit -m "feat(aios): agent gathers competitor+calendar, can schedule; runner wires web search"
```

---

## Self-Review

**Spec coverage:** modify calendar (write at L1) → Task 2; spy competitors → Task 1; trends → Task 3; agent uses them → Task 4. Calendar writes flow through the autonomy ladder (propose→approve→write), consistent with §4.

**Placeholder scan:** the `COMPETITORS` list in the runner is an explicit placeholder the user must edit with real @handles — flagged inline, not a silent gap.

**Type consistency:** `CALENDAR_ACTION` ActionType used by tool + policy + test. `business_discovery` returns dict consumed by `competitor_tools`. `_anthropic_client` factory patched in tests and used by `AnthropicLLM`. `_gather` optional keys guarded by `tools.names()` so existing tests (no competitor/calendar tools) stay green.

**Live verification (controller):** needs service_role key (calendar writes to aios_content_calendar) + IG token (business_discovery) + Anthropic key (web search). Run `run_marketing_supabase.py` and check `aios_content_calendar` / `aios_approvals` via MCP.
