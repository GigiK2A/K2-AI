# Stato K-BOT verso "operativo" — handoff

> Obiettivo: un cliente vero paga e riceve un report buono, da solo. Questo doc è la
> fotografia onesta dopo il run autonomo del 2026-06-17: cosa è fatto nel codice, cosa
> resta, e i **muri esterni** che non si scavalcano con altro codice.

## Architettura confermata con Luca
- I **numeri** vengono dai suoi **MCP server** (repo `inglucarossi73/*`), non da copie.
  Il `k2a-quant` pubblicato è su github e aggiornato (4 tool nuovi + snapshot rf 2,95 /
  erp 6,69). **Tutto su github tranne il corpus normattiva** (verificato).
- **A2**: i Boost "che ragionano" (AdvisorBoost) li genera un **agente tool-use** che
  chiama i suoi MCP per ogni numero. I Boost compilativi restano in pipeline 8e.
- L'MCP gira **nel backend kbot**. Scoperta: l'agente NON usa l'Agent SDK (richiede la
  CLI `claude` nel container) ma il **raw Anthropic SDK** → nessuna CLI da installare.

## Fatto in questo run (tutto committato, testato fin dove possibile senza crediti)

1. **Ponte pagamento→generazione** (era rotto: il webhook marcava `paid` ma il
   frontend non gestiva il rientro da Stripe → cliente pagava e vedeva la UI vecchia).
   - backend `POST /api/kbot/checkout/exchange` (token opaco → session_id) + `sessions.get_session_by_success_token`.
   - frontend: `exchangeToken`, handler `?kbot_paid=1&t=…` in `page.tsx`, auto-resume in `ReportGenerator`.
2. **Il suo quant MCP gira nel backend** (`lib/mcp_quant.py`, client stdio) + `GET /api/kbot/quant/health`.
   Provato: 31 tool, i 4 nuovi, `capm` hotel ke 15,83% / ev 6,912M / snapshot 2026-06-15.
   `requirements`: `mcp` + `k2a-quant` (git, **da pinnare a un tag prima del deploy**).
3. **Agente A2** (`lib/boost_agent.py`): loop tool-use raw + gate IN-LOOP (contratto
   assunzioni: DCF negato senza `valida_assunzioni` OK/WARN), provenienza per call_id,
   fail-closed. Grounding **testato col suo MCP reale**: catena valida→DCF, ev_dcf
   4.619.813 con provenienza verificata. (Il loop del modello = crediti, non testato.)
4. **Endpoint A2 reachable**: `POST /api/kbot/deliverables/agent` (gated: ownership +
   entitlement + autofill + skill di dominio). Flag `K2A_BOOST_AGENT` (default OFF),
   `K2A_BOOST_AGENT_SERVIZI=checkup_advisor`.
5. **Demo pagamento finto** (run precedente): `KBOT_FAKE_PAYMENT` + `POST /checkout/boost/demo`.

Backend `app.main` importa pulito, frontend `tsc` verde.

## I muri esterni (nessun codice li apre — servono te/Luca)

| Muro | Cosa blocca | Chi |
|---|---|---|
| **Crediti Anthropic** | OGNI generazione (report, agente A2, giro 8e reale) | tu (ricarica) |
| **Stripe live** | pagamento reale (oggi checkout → 503) | tu/Luca (chiavi + webhook) |
| **Corpus normattiva** | LegalBoost/FiscoBoost col testo di legge | Luca (non su github) |
| **Deploy Railway** | mandare in prod (`railway login` interattivo) | tu |
| **Mappa `ateco_to_sector`** | ungate AdvisorBoost vendibile | Luca |

## Cosa manca lato codice (completabile, ma alcune cose servono i muri sopra per il test)

- **Job async per l'agente A2**: oggi `/deliverables/agent` è sincrono (rischio timeout
  su run lunghi). In prod va reso job + polling come il motore 8e.
- **Webhook → generazione server-side** (safety-net se il cliente chiude la tab):
  oggi il resume è lato frontend. Va agganciato al job async A2/8e.
- **Pinnare `k2a-quant`** a un tag (non `@main`) e installare i suoi MCP nel container
  (Dockerfile backend): `pip install` dei repo `inglucarossi73/k2a-mcp-*`.
- **Altri MCP via stdio** (agevolazioni/elettrico/strutturale/norme) come `mcp_quant`,
  se si vuole la stessa freschezza del quant (oggi sono vendorizzati, funzionano).
- **17 Boost manuali → self-serve**: blueprint 8e + skill (i `k-bot-*-skills` di Luca).
- **Quality-gate pre-consegna** + email affidabile (retry) + monitoring.

## Come si accende, quando i muri cadono
1. Ricarica crediti + metti i secret su Railway (Stripe, Anthropic, `K2A_ENTITLEMENT_SECRET`
   condiviso, Resend).
2. Pinna `k2a-quant` a un tag, installa i MCP nel container, `railway up`.
3. `K2A_BOOST_AGENT=1` + ateco di Luca → 1 giro live AdvisorBoost → ispeziona il PDF →
   togli `checkup_advisor` da `_NON_VENDIBILI`.
4. Smoke end-to-end: chat → paga (Stripe) → rientro → report. Il ponte ora regge.
