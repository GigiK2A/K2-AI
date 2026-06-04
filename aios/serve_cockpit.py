"""Serve the AIOS cockpit on http://localhost:8800 over the Supabase-backed kernel.
The cockpit shows ONLY what the agent reads through its own sensor tools (registered
on the kernel below) — nothing is hardcoded.
Env: AIOS_SUPABASE_URL, AIOS_SUPABASE_SERVICE_KEY, AIOS_IG_TOKEN.
Run: cd aios && set -a && . ./.env && set +a && .venv/bin/python serve_cockpit.py
"""
import os

import uvicorn

from aios.kernel import Kernel
from aios.api.app import create_app
from aios.sources.instagram import InstagramClient
from aios.sources.tools import content_tools_rest, instagram_tools, insights_tools

kernel = Kernel.with_supabase_rest(os.environ["AIOS_SUPABASE_URL"],
                                   os.environ["AIOS_SUPABASE_SERVICE_KEY"])

# register the agent's read-only sensors so the cockpit reads live, agent-sourced data
for t in content_tools_rest(kernel._supabase):
    kernel.register_tool(t)
ig = InstagramClient(token=os.environ["AIOS_IG_TOKEN"],
                     ig_user_id=os.environ.get("AIOS_IG_USER_ID", "17841429842127461"))
for t in instagram_tools(ig):
    kernel.register_tool(t)
for t in insights_tools(ig):
    kernel.register_tool(t)

app = create_app(kernel)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8800)
