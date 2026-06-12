import json

from aios.kernel import Kernel
from aios.autonomy import AutonomyLevel
from aios.founder import default_founder_model
from aios.llm import FakeLLM
from aios.tools import Tool
from aios.agents.marketing import MarketingAgent, PROPOSE_ACTION


def _kernel_with_fake_sensors():
    k = Kernel()
    k.register_tool(Tool(name="leggi_servizi", action_type=None, readonly=True,
                         run=lambda **_: [{"Servizio": "Automazioni", "Stato": "da usare"}]))
    k.register_tool(Tool(name="leggi_topics", action_type=None, readonly=True,
                         run=lambda **_: [{"Tema": "RAG per PMI", "Stato": "da usare"}]))
    k.register_tool(Tool(name="leggi_profilo_ig", action_type=None, readonly=True,
                         run=lambda **_: {"username": "k2_ai.it", "followers_count": 5}))
    k.register_tool(Tool(name="leggi_post_ig", action_type=None, readonly=True,
                         run=lambda **_: [{"caption": "Automatizza la contabilità",
                                            "like_count": 2, "comments_count": 0}]))
    return k


def test_agent_files_proposals_into_approval_queue():
    k = _kernel_with_fake_sensors()
    proposals = [
        {"tipo": "nuovo_tema", "titolo": "Agenti email per studi",
         "contenuto": "Post su come un agente gestisce le email", "motivo": "alto volume ricerca"},
        {"tipo": "caption", "titolo": "Migliora caption contabilità",
         "contenuto": "Riscrittura con numero di ore risparmiate", "motivo": "manca il numero"},
    ]
    llm = FakeLLM(responses=[json.dumps({"proposte": proposals})])
    agent = MarketingAgent(kernel=k, llm=llm, founder=default_founder_model())

    result = agent.run()

    assert len(result.approval_ids) == 2
    pending = k.approvals.pending()
    assert len(pending) == 2
    assert pending[0].action_key == PROPOSE_ACTION.key
    system, user = llm.calls[0]
    assert "Founder Model" in system or "Founder Model" in user
    assert "k2_ai.it" in user and "RAG per PMI" in user


def test_agent_survives_messy_llm_json():
    k = _kernel_with_fake_sensors()
    messy = "Ecco le proposte:\n```json\n" + json.dumps(
        {"proposte": [{"tipo": "fix", "titolo": "x", "contenuto": "y", "motivo": "z"}]}
    ) + "\n```\nSpero siano utili!"
    agent = MarketingAgent(kernel=k, llm=FakeLLM(responses=[messy]),
                           founder=default_founder_model())
    result = agent.run()
    assert len(result.approval_ids) == 1


def test_proposals_default_to_L1_so_they_need_approval():
    k = _kernel_with_fake_sensors()
    agent = MarketingAgent(kernel=k, llm=FakeLLM(responses=['{"proposte": []}']),
                           founder=default_founder_model())
    agent.run()
    assert k.policy.level_for(PROPOSE_ACTION) == AutonomyLevel.L1_PROPOSE


def test_invalid_llm_json_raises_clear_error():
    import pytest
    k = _kernel_with_fake_sensors()
    agent = MarketingAgent(kernel=k, llm=FakeLLM(responses=["non sono json, scusa"]),
                           founder=default_founder_model())
    with pytest.raises(ValueError):
        agent.run()


def test_empty_proposals_is_ok():
    k = _kernel_with_fake_sensors()
    agent = MarketingAgent(kernel=k, llm=FakeLLM(responses=['{"proposte": []}']),
                           founder=default_founder_model())
    result = agent.run()
    assert result.approval_ids == [] and result.proposals == []


def test_value_with_backticks_parses():
    k = _kernel_with_fake_sensors()
    payload = {"proposte": [{"tipo": "fix", "titolo": "snippet",
                             "contenuto": "usa ``` per il codice", "motivo": "chiarezza"}]}
    agent = MarketingAgent(kernel=k, llm=FakeLLM(responses=[json.dumps(payload, ensure_ascii=False)]),
                           founder=default_founder_model())
    result = agent.run()
    assert len(result.approval_ids) == 1


def test_agent_includes_skill_menu_when_library_given():
    from aios.skills import SkillLibrary
    k = _kernel_with_fake_sensors()
    llm = FakeLLM(responses=['{"proposte": []}'])
    agent = MarketingAgent(kernel=k, llm=llm, founder=default_founder_model(),
                           skills=SkillLibrary())
    agent.run()
    system, user = llm.calls[0]
    assert "FRAMEWORK (estratti)" in user
    assert "content-creation" in user  # a real skill name from the library


def test_agent_works_without_skills():
    k = _kernel_with_fake_sensors()
    llm = FakeLLM(responses=['{"proposte": []}'])
    agent = MarketingAgent(kernel=k, llm=llm, founder=default_founder_model())
    result = agent.run()  # no skills => no crash
    assert result.approval_ids == []


def test_agent_gathers_competitor_and_calendar_when_present():
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
    assert "999" in user
    assert "gia in calendario" in user


def test_agent_uses_insights_competitors_calendar_and_full_skills():
    from aios.tools import Tool
    from aios.skills import SkillLibrary
    k = _kernel_with_fake_sensors()
    k.register_tool(Tool(name="leggi_insight_ig", action_type=None, readonly=True,
                         run=lambda **_: {"reach": 182, "total_interactions": 9}))
    k.register_tool(Tool(name="analizza_competitor", action_type=None, readonly=True,
                         run=lambda usernames=None, **_: {h: {"followers_count": 100} for h in (usernames or [])}))
    k.register_tool(Tool(name="leggi_calendario", action_type=None, readonly=True,
                         run=lambda **_: [{"titolo": "gia in cal"}]))
    llm = FakeLLM(responses=['{"handles": ["rivale_uno"]}', '{"proposte": [], "voci_calendario": []}'])
    agent = MarketingAgent(kernel=k, llm=llm, founder=default_founder_model(), skills=SkillLibrary())
    agent.run()
    sys, user = llm.calls[-1]
    assert "182" in user
    assert "rivale_uno" in user or "followers_count" in user
    assert "gia in cal" in user
    assert "SKILL:" in user


def test_agent_files_calendar_entries_via_programma_contenuto():
    from aios.sources.calendar import calendar_tools
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
    assert cal.rows == []
    k.resolve_approval(res.calendar_ids[0], approve=True)
    assert len(cal.rows) == 1 and cal.rows[0]["titolo"] == "Post X"


def test_agent_coerces_string_proposte_without_crash():
    # model returns proposte as a JSON-encoded STRING (Haiku quirk) -> no crash
    k = _kernel_with_fake_sensors()
    bad = '{"proposte": "[{\\"tipo\\":\\"fix\\",\\"titolo\\":\\"T\\",\\"contenuto\\":\\"C\\",\\"motivo\\":\\"M\\"}]"}'
    agent = MarketingAgent(kernel=k, llm=FakeLLM(responses=[bad]), founder=default_founder_model())
    res = agent.run()
    assert len(res.approval_ids) == 1  # the stringified array was recovered


def test_agent_ignores_garbage_proposte():
    k = _kernel_with_fake_sensors()
    agent = MarketingAgent(kernel=k, llm=FakeLLM(responses=['{"proposte": "non e una lista"}']),
                           founder=default_founder_model())
    res = agent.run()
    assert res.approval_ids == []  # coerced to empty, no crash
