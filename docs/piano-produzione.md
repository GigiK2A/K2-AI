# Piano produzione — da "codice completo" a "production-ready"

**Obiettivo**: chiudere tutti i gap, testare end-to-end (1-100), arrivare a deployabile.
**Stato**: in esecuzione. Ogni fase ha gate verde prima della successiva.

## Gap noti da chiudere
1. Input chat → 8e non collegati (deliverable generato con inputs vuoti)
2. Catena intera (browser → K-BOT backend → 8e → PDF) mai girata insieme
3. `K2A_ENTITLEMENT_SECRET` non gestito (entitlement permissivo in dev)
4. Nessun test integrazione K-BOT backend ↔ 8e
5. Checklist produzione + env vars non consolidata

## Fasi

### F1 — Input wiring (chat/form → 8e)
- 8e: `GET /v1/form/{service_id}` → campi form.json del blueprint
- K-BOT: proxy `GET /api/kbot/deliverables/form/{servizio_id}`
- Frontend: DeliverablePanel raccoglie i campi prima di generare, li passa come inputs
- Gate: form reso + inputs arrivano al 8e (verificato)

### F2 — Entitlement hardening
- Generare segreto dev; 8e: warning su /health se FULL senza segreto in prod
- K-BOT + 8e leggono lo stesso `K2A_ENTITLEMENT_SECRET`
- Gate: con segreto, token forgiato → 402; token valido → 202

### F3 — Integrazione K-BOT backend ↔ 8e (end-to-end)
- venv backend K-BOT, boot app
- 8e avviato con segreto + chiave Anthropic
- Test integrazione: sessione→preview→(paid stub)→full deliverable, via TestClient kbot puntando all'8e reale
- Gate: catena completa verde

### F4 — Suite test completa (1-100)
- pytest 8e (smoke, all_boosts, security, entitlement, ratelimit, gate)
- pytest K-BOT (catalog, deliverables, preview, entitlement, ownership)
- frontend tsc + build
- Gate: tutti verdi

### F5 — Produzione readiness
- railway.toml verificati (8e + kbot backend + frontend)
- env vars documentate + script generazione segreti
- report finale + checklist deploy
- Gate: checklist completa, niente TODO bloccante

## Avanzamento — TUTTE COMPLETE ✅
- [x] **F1** input wiring: 8e `/v1/form/{id}` + proxy K-BOT + DeliverablePanel raccoglie i campi
- [x] **F2** entitlement hardening: /health warning, gen_secrets.sh, segreto condiviso
- [x] **F3** integrazione end-to-end: K-BOT backend ↔ 8e reale → **8/8 PASS** (form→preview→full con JWT)
- [x] **F4** suite completa: 8e smoke+all_boosts+security(21/21), integrazione(8/8), frontend tsc+build
- [x] **F5** produzione: railway.toml verificati, checkout Boost dinamico (prezzo catalogo) + webhook,
  deploy-checklist.md, gen_secrets.sh

## Extra chiusi in F5
- **Checkout Boost**: `/api/kbot/checkout/boost` (prezzo dal catalogo, non i 19€) +
  webhook registra `kbot_purchases` e marca paid (sblocca entitlement) + frontend `startBoostCheckout`
- **Catena completa** browser→K-BOT→8e→PDF testata in-process (TestClient + 8e reale)

## Resta solo (non automatizzabile da me)
- **Deploy** su Railway (3 servizi) + settare i segreti — vedi `docs/deploy-checklist.md`
- Decisioni prodotto: corposità 40pp (multi-call Phase-2), AgevolazioniBoost senza chiavi
