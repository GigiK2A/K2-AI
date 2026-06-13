"""Live run of the Marketing agent against real data.

Requires env: ANTHROPIC_API_KEY, AIOS_IG_TOKEN, AIOS_IG_USER_ID, AIOS_DATABASE_URL.
Reads sensors, asks Claude for proposals, files them as L1 approvals, prints them.
Usage: cd aios && set -a && . ./.env && set +a && .venv/bin/python run_marketing.py
"""
from __future__ import annotations

import os

import psycopg

from aios.kernel import Kernel
from aios.founder import default_founder_model
from aios.llm import AnthropicLLM
from aios.sources.instagram import InstagramClient
from aios.sources.tools import content_tools, instagram_tools
from aios.agents.marketing import MarketingAgent
from aios.skills import SkillLibrary


def main() -> None:
    conn = psycopg.connect(os.environ["AIOS_DATABASE_URL"])
    ig = InstagramClient(token=os.environ["AIOS_IG_TOKEN"],
                         ig_user_id=os.environ.get("AIOS_IG_USER_ID", "17841429842127461"))
    k = Kernel()
    for t in content_tools(conn):
        k.register_tool(t)
    for t in instagram_tools(ig):
        k.register_tool(t)

    fm = default_founder_model()
    posts = k.execute("leggi_post_ig", actor="bootstrap", args={"limit": 10}).result
    fm.voice_samples = [p.get("caption", "") for p in posts if p.get("caption")][:5]

    agent = MarketingAgent(kernel=k, llm=AnthropicLLM(), founder=fm, skills=SkillLibrary())
    result = agent.run()

    print(f"\n=== {len(result.proposals)} PROPOSTE (in coda approvazioni, L1) ===\n")
    for appr in k.approvals.pending():
        p = appr.payload
        print(f"[#{appr.id}] {p.get('tipo','?').upper()} — {p.get('titolo','')}")
        print(f"    {p.get('contenuto','')}")
        print(f"    perché: {p.get('motivo','')}\n")


if __name__ == "__main__":
    main()
