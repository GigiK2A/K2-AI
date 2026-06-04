"""Marketing Agent v2 fully on Supabase REST (state persists) + live IG + Claude.
The agent reads insights, DISCOVERS competitors itself, reads the calendar, applies
full marketing skills, analyzes posts one-by-one, and files content proposals +
calendar entries — all queued at L1 for human approval.
Env: AIOS_SUPABASE_URL, AIOS_SUPABASE_SERVICE_KEY, AIOS_IG_TOKEN, ANTHROPIC_API_KEY.
Run: cd aios && set -a && . ./.env && set +a && .venv/bin/python run_marketing_supabase.py
"""
import os

from aios.kernel import Kernel
from aios.founder import default_founder_model
from aios.llm import AnthropicLLM
from aios.skills import SkillLibrary
from aios.sources.instagram import InstagramClient
from aios.sources.tools import (content_tools_rest, instagram_tools,
                                insights_tools, competitor_lookup_tool)
from aios.sources.calendar import calendar_tools
from aios.agents.marketing import MarketingAgent


def main() -> None:
    k = Kernel.with_supabase_rest(os.environ["AIOS_SUPABASE_URL"],
                                  os.environ["AIOS_SUPABASE_SERVICE_KEY"])
    ig = InstagramClient(token=os.environ["AIOS_IG_TOKEN"],
                         ig_user_id=os.environ.get("AIOS_IG_USER_ID", "17841429842127461"))

    # the agent's senses
    for t in content_tools_rest(k._supabase):
        k.register_tool(t)
    for t in instagram_tools(ig):
        k.register_tool(t)
    for t in insights_tools(ig):
        k.register_tool(t)
    k.register_tool(competitor_lookup_tool(ig))      # agent feeds self-discovered handles
    for t in calendar_tools(k._supabase):            # programma_contenuto (L1, writes on approval)
        k.register_tool(t)

    fm = default_founder_model()
    posts = k.execute("leggi_post_ig", actor="bootstrap", args={"limit": 10}).result
    fm.voice_samples = [p.get("caption", "") for p in posts if p.get("caption")][:5]

    # max_tokens alto per JSON ricco; web search off in questo run per JSON affidabile
    agent = MarketingAgent(kernel=k, llm=AnthropicLLM(max_tokens=4096),
                           founder=fm, skills=SkillLibrary())
    result = agent.run()

    print(f"{len(result.proposals)} proposte + {len(result.calendar)} voci calendario "
          f"(tutte in coda L1 su Supabase).")
    for appr in k.approvals.pending():
        titolo = appr.payload.get("titolo") if isinstance(appr.payload, dict) else str(appr.payload)[:40]
        print(f"  [#{appr.id}] {appr.action_key.split('.')[-1]}: {titolo}")


if __name__ == "__main__":
    main()
