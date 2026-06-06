# Stato agenti K2-AI AIOS — cosa fanno / cosa non fanno

> Snapshot di avanzamento. Legenda: ✅ dati reali · 🔌 codice pronto, serve credenziale ·
> 📝 modalità strategia (nessuna fonte dati) · ❌ non implementato.
> **Limite trasversale a TUTTI**: gli agenti **PROPONGONO** (cap autonomia L1), **non eseguono**
> ancora (manca l'attuatore: Approva → azione reale). Mai-automatico: soldi, firme, permessi, cancellazioni.

---

## Marketing — 19/19 funzioni coperte (testa), esecuzione ❌
| # | Funzione | Stato | Fonte |
|---|---|---|---|
| 1 | Brand & positioning | ✅ | Founder Model |
| 2 | Content marketing | ✅ | `topics` |
| 3 | Social media | ✅ | Instagram Graph API |
| 4 | SEO organico | ✅ contenuti · 🔌 ranking | `topics`/pillar · Google Search Console |
| 5 | Paid / SEM | 🔌 | Meta/Google Ads |
| 6 | Demand gen | ✅ | lead + funnel |
| 7 | Email / lifecycle | ✅ lista · 🔌 eventi | `newsletter_subscribers`/`issues` · Resend |
| 8 | Marketing automation / ops | ✅ | `aios_content_calendar` |
| 9 | Product marketing | ✅ | `servizi` + `suite_services` + knowledge |
| 10 | PR / comunicazione | ✅ (gratis) | Google News RSS (`AIOS_BRAND_NAME`) |
| 11 | Influencer | ✅ | scouting LLM + IG |
| 12 | Events / field | 📝 | — |
| 13 | Analytics / attribution | ✅ | `analytics_snapshots` + IG · 🔌 PostHog |
| 14 | Competitive intelligence | ✅ IG · 🔌 web | competitor IG · `COMPETITOR_URLS` |
| 15 | Market research | ✅ | `kbot_sessions` (voce clienti) |
| 16 | Creative / design ops | 📝 | — |
| 17 | Web / CRO | 🔌 | PostHog |
| 18 | Budget / ops | ✅ | `board_cost_items` |
| 19 | Strategy / planning | ✅ | sintesi |

**Non fa**: pubblicare post, inviare newsletter, scrivere blog sul sito (manca attuatore + alcune credenziali).

---

## Sales / CRM — 18/18 funzioni coperte (testa), esecuzione ❌
| # | Funzione | Stato | Fonte |
|---|---|---|---|
| 1 | Lead gen / prospecting | ✅ · 🔌 inbox | `pipeline_leads` + `leggi_lead_kbot`(28) · IMAP |
| 2 | Qualification (ICP/score) | ✅ | `pipeline_leads` |
| 3 | Account research | ✅ | — |
| 4 | Discovery | ✅ | — |
| 5 | Demo / sales engineering | 📝 | — |
| 6 | Proposal / pricing | ✅ | `suite_services` (tier) + ROI |
| 7 | Negotiation / closing | ✅ | note/memo lead |
| 8 | Contract / order | ✅ | `board_revenue_events` |
| 9 | Account mgmt / upsell | ✅ | `kbot_conversions` (clienti) |
| 10 | Customer success / retention | ✅ | clienti |
| 11 | Pipeline management | ✅ | `pipeline_leads` |
| 12 | Forecasting | ✅ | value×prob |
| 13 | Territory / quota | 📝 | — |
| 14 | Enablement | ✅ | `suite_services` |
| 15 | Analytics | ✅ | pipeline |
| 16 | Comp / incentivi | 📝 | — |
| 17 | Channel / partner | 📝 | — |
| 18 | Win/loss | ✅ | note/stato lead |

**Non fa**: inviare email al lead, aggiornare il CRM, creare eventi calendario, inserire in automatico i lead K-BOT in pipeline (li propone). Manca attuatore + credenziali inbox/calendar.

---

## Finance — 16/16 funzioni coperte (testa), esecuzione ❌
| # | Funzione | Stato | Fonte |
|---|---|---|---|
| 1 | General ledger / riconciliazione | ✅ | `finance_journal` + costi/ricavi |
| 2 | Accounts payable | ✅ | `board_cost_items` |
| 3 | Accounts receivable / solleciti | ✅ | `invoices` (fatture) |
| 4 | Treasury / cashflow / runway | ✅ | costi + pipeline |
| 5 | FP&A / scenari | ✅ | `shared_memory` target |
| 6 | KPI (MRR/CAC/LTV) | ✅ | conversions + leads |
| 7 | Month-end close | ✅ checklist | tabelle disponibili |
| 8 | Controllership / anomalie | ✅ | `board_cost_items` |
| 9 | Tax & compliance IT | ✅ | calendario IVA/LIPE/IRPEF |
| 10 | Payroll | ✅ | `employees` (organico, vuota finché non popolata) |
| 11 | Revenue / MRR & billing | ✅ K-BOT · 🔌 Stripe | `kbot_conversions` · Stripe |
| 12 | Cost control / procurement | ✅ | `board_cost_items` (cap 65€) |
| 13 | Pricing / margin | ✅ | `suite_services` tier + `projects` |
| 14 | Audit support | ✅ | assembla evidenze |
| 15 | Risk (concentrazione clienti) | ✅ | `projects` + contratti |
| 16 | Investor relations | 📝 | cap table (`shared_memory`) |

**Non fa**: pagare/incassare, emettere fatture reali, registrare scritture nel gestionale (manca attuatore + Stripe/gestionale).

---

## Spina dorsale (condivisa)
- Catalogo prodotti unico `suite_services` (20) ← `services-data.json`, letto da sito/kbot/AIOS (`sync_suite.py`).
- Lead K-BOT visibili alle vendite (`leggi_lead_kbot`).
- Knowledge condivisa in `aios_knowledge`.

## Prossimi salti (validi per tutti)
1. **Attuatore Livello 1** (scritture interne Supabase): Approva → aggiorna davvero le tabelle.
2. **Livello 2** (azioni esterne): email, pubblicazioni, calendario — con credenziali.
