# k2a-8e-agent-poc — AdvisorBoost come agente a guinzaglio corto

PoC isolato (NON collegato al K-BOT live): l'agente (Claude Agent SDK) ESEGUE la
skill `flusso-advisorboost-pmi` di Luca, i numeri escono SOLO dai tool quant
deterministici in-process (`quant_server.py`, surrogato di k2a-mcp-quant con
snapshot multipli PLACEHOLDER), gli hook fanno da gate (PreToolUse=allowlist
tier, Stop=anti-omissione con tracciabilità numeri), audit trace completo.

Run: `set -a; . ../kai-website/kbot/backend/.env.local; set +a && .venv/bin/python run_poc.py`
Output: `out/deliverable.json`, `out/audit.json`, `out/metrics.json`.

Primo run (bilancio Juventus 2023/24, dati reali): deliverable completo al primo
Stop, 22 tool call, 1 deny PreToolUse (ToolSearch fuori allowlist), $0.91, 8.3 min.
EV riconciliato 833M (multipli 947M / DCF 862M / patrimoniale 190M), alert CCII
dichiarato. Decisione promozione: vedi docs/messaggio-luca-poc-agent-sdk.md.
