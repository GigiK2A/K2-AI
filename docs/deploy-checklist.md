# Checklist deploy produzione — K2-AI 8e + K-BOT

**Stato codice**: tutto testato (8e smoke/all-boosts/security 21·21, integrazione K-BOT↔8e 8·8, frontend build). Manca solo il deploy (lo fa Luigi).

---

## 0. Generare i segreti (una volta)

```bash
cd kai-website/k2a-8e && bash scripts/gen_secrets.sh
```
Produce `K2A_ENTITLEMENT_SECRET` e `K2A_8E_API_KEY`. Vanno settati **IDENTICI**
su 8e e K-BOT backend.

---

## 1. Deploy servizio 8e (NUOVO container Railway)

```bash
cd kai-website/k2a-8e
railway up --detach
```
**Env da settare su Railway (8e)**:
| Var | Valore |
|---|---|
| `K2A_8E_API_KEY` | (da gen_secrets) |
| `K2A_ENTITLEMENT_SECRET` | (da gen_secrets) |
| `ANTHROPIC_API_KEY` | chiave Anthropic (filiera Sonnet) |
| `K2A_8E_MODEL` | `claude-sonnet-4-5` (default) |
| `K2A_8E_RL_MAX` / `K2A_8E_RL_WINDOW` | `30` / `60` (default, opz.) |

**Verifica post-deploy**: `GET https://<8e>/health` → `entitlement:"enforced"`,
`filiera:"anthropic"`, `warnings: []`. Se ci sono warning, manca un segreto.

> NB asset (blueprint/snapshot/catalog) sono vendorizzati nel container. Per
> aggiornarli: `scripts/sync_assets.sh` poi redeploy.

---

## 2. K-BOT backend — aggiungere env (servizio esistente)

| Var (nuove) | Valore |
|---|---|
| `K2A_8E_BASE_URL` | `https://<8e-railway-url>` |
| `K2A_8E_API_KEY` | (stesso del 8e) |
| `K2A_ENTITLEMENT_SECRET` | (stesso del 8e) |

Poi `railway up --detach` da `kbot/backend`.

**Migrazioni Supabase**: 004 (kbot_purchases) + 005 (kbot_preview_usage) **già
applicate** su progetto KAI via MCP. Nessuna azione.

---

## 3. K-BOT frontend — nessuna nuova env

`railway up --detach` da `kbot/`. Il pannello deliverable usa gli endpoint del
backend (stesso `NEXT_PUBLIC_API_BASE_URL`).

---

## 4. Sito vetrina (Vite) — già a posto

`js/kbot-tag.js` è iniettato nei 20 pillar; appende `?tag=Pxx` ai link `/app`.
`railway up --detach` da `kai-website/` se servono i pillar aggiornati.

---

## 5. Smoke produzione (dopo deploy)

```bash
# 8e vivo + configurato
curl -s https://<8e>/health | jq '.entitlement, .filiera, .warnings'

# catena dal K-BOT (form)
curl -s https://<api>/api/kbot/deliverables/form/primo_parere_legale | jq '.campi | length'
```
Poi un giro reale da browser: pillar legale → chat → anteprima gratuita →
checkout test → documento completo → PDF.

---

## 6. Checklist finale

- [ ] Segreti generati e settati identici (8e + K-BOT backend)
- [ ] 8e deployato, `/health` → enforced + anthropic, no warnings
- [ ] K-BOT backend con `K2A_8E_BASE_URL`/key/secret, redeploy
- [ ] Frontend redeploy
- [ ] Migrazioni 004/005 presenti (già applicate)
- [ ] Smoke prod: form + un deliverable reale end-to-end
- [ ] Stripe: prodotto/prezzo per i Boost a catalogo (oggi il catalog ha i prezzi; il checkout usa lo Stripe esistente)

---

## Cosa resta a livello PRODOTTO (non tecnico-bloccante)

1. **Stripe per i Boost**: il checkout attuale è per il report 19€. Per vendere i
   Boost (490-2500€) serve mappare i prezzi catalogo → Stripe (Payment Link o
   checkout dinamico). Il pannello chiama `onUnlock` = `startCheckoutFromUI` (il
   checkout esistente) — va esteso al prezzo del boost.
2. **Prosa per-voce corposa (40pp)**: oggi hybrid produce campi strutturati reali
   + prosa ~350char/voce (la chiamata prosa tronca a 9 voci). Per le 40pp piene =
   multi-call per-voce (Phase-2). Il documento è valido e grounded, ma più sintetico.
3. **AgevolazioniBoost**: nessuna chiave deterministica nel manifest (numeri dal
   MCP catalogo, non snapshot) → genera ma senza fatti deterministici. Da chiarire
   con Luca.
4. **Finding pre-esistenti Supabase** (non miei): ~37 tabelle aios_*/board_* RLS
   senza policy, leaked-password off — vedi security-debug-report.md.

---

*Tutto il codice è testato e pronto. Il deploy + la mappatura Stripe-Boost sono
gli unici passi che restano per andare live.*
