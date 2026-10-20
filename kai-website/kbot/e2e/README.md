# Prove nel browser della chat K-BOT (senza Supabase)

La chat richiede il login. Per provarla in locale si usa un backend con **utente finto** e un database in memoria con filtri
veri (conversazioni, profilo), e una sessione Supabase finta nel browser (letta dal client senza rete).

```bash
# 1) backend con utente finto (porta 8200)
python3 backend/evals/server_ui.py backend 8200
# 2) frontend (porta 3100) puntato al backend e con Supabase finto
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8200 NEXT_PUBLIC_SUPABASE_URL=http://127.0.0.1:54399 \
  NEXT_PUBLIC_SUPABASE_ANON_KEY=finta NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=finta npx next dev --webpack -p 3100
# 3) browser headless (playwright-core, senza modificare package.json)
npm i --no-save playwright-core
CHROME_PATH=/usr/bin/chromium-browser node e2e/chat_dashboard.mjs out.png   # chat → dashboard → ritorno: la chat deve esserci
node e2e/schermate.mjs                                                       # screenshot desktop, telefono, dashboard
```

`chat_dashboard.mjs` riproduce il difetto del 20/10/2026 (la chat spariva tornando dalla dashboard: la sessione veniva
azzerata e, anche conservata, la cronologia non veniva riletta dal backend). Il nome del localStorage di Supabase è
`sb-<primo pezzo dell'host>-auth-token` (qui `sb-127-auth-token`).
