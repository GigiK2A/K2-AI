"""Marketing agent fully on Supabase REST (state persists) + live IG + Claude.
Env: AIOS_SUPABASE_URL, AIOS_SUPABASE_SERVICE_KEY, AIOS_IG_TOKEN, ANTHROPIC_API_KEY.
Run: cd aios && set -a && . ./.env && set +a && .venv/bin/python run_marketing_supabase.py
"""
import os
from aios.kernel import Kernel
from aios.founder import default_founder_model
from aios.llm import AnthropicLLM
from aios.skills import SkillLibrary
from aios.sources.instagram import InstagramClient
from aios.sources.tools import content_tools_rest, instagram_tools
from aios.agents.marketing import MarketingAgent


def main() -> None:
    k = Kernel.with_supabase_rest(os.environ["AIOS_SUPABASE_URL"],
                                  os.environ["AIOS_SUPABASE_SERVICE_KEY"])
    for t in content_tools_rest(k._supabase):
        k.register_tool(t)
    ig = InstagramClient(token=os.environ["AIOS_IG_TOKEN"],
                         ig_user_id=os.environ.get("AIOS_IG_USER_ID", "17841429842127461"))
    for t in instagram_tools(ig):
        k.register_tool(t)
    from aios.sources.calendar import calendar_tools
    from aios.sources.tools import competitor_tools
    for t in calendar_tools(k._supabase):
        k.register_tool(t)
    # set the calendar scheduling action to L1 (propose -> human approves -> writes)
    from aios.sources.calendar import CALENDAR_ACTION
    from aios.autonomy import AutonomyLevel
    k.policy.set_level(CALENDAR_ACTION, AutonomyLevel.L1_PROPOSE)
    k.policy.set_cap(CALENDAR_ACTION, AutonomyLevel.L1_PROPOSE)
    COMPETITORS = ["aizwei", "ey_italy"]  # PLACEHOLDER @handles — replace with real competitors
    for t in competitor_tools(ig, COMPETITORS):
        k.register_tool(t)

    fm = default_founder_model()
    posts = k.execute("leggi_post_ig", actor="bootstrap", args={"limit": 10}).result
    fm.voice_samples = [p.get("caption", "") for p in posts if p.get("caption")][:5]

    agent = MarketingAgent(kernel=k, llm=AnthropicLLM(enable_web_search=True), founder=fm, skills=SkillLibrary())
    result = agent.run()
    print(f"{len(result.proposals)} proposte scritte in Supabase (aios_approvals, L1).")
    for appr in k.approvals.pending():
        print(f"  [#{appr.id}] {appr.payload.get('tipo')}: {appr.payload.get('titolo')}")


if __name__ == "__main__":
    main()
