# K2-AI AIOS — Design

Date: 2026-06-04
Owner: Luigi Rossi (rluigiluca@gmail.com)
Status: Draft per review

---

## 1. Visione

K2-AI diventa la **prima azienda AI-first italiana, gestita dal suo stesso AIOS** (AI Operating System).
Non un gestionale con qualche automazione: un sistema operativo per agenti che fa girare l'azienda
in tutti gli ambiti, con destinazione **pieno autopilota** raggiunto a gradi.

**Ambiti (dominî) target** — confermati dal mockup cockpit 2026-06-04:
Marketing · Sales/CRM · Finance · Operations · **Legal & Compliance** · **HR** + funzioni di supporto
(**Projects**, **Documents**, **Analytics**). I primi 4 restano il nucleo; Legal/HR/Projects/Documents
entrano come domini propri nelle fasi successive. **Marketing è il primo verticale.**

L'AIOS è anche:
- il **caso studio vetrina** ("i primi clienti siamo stati noi")
- un futuro **prodotto** vendibile alle PMI (per questo: single-tenant ben fatto, moduli isolati)

Riferimenti: AIOS paper (Mei et al., arXiv 2403.16971); agentic organization (McKinsey/SAP/Microsoft).
Sostituisce il sistema `ai-board/` (audit `docs/ai-board-rebuild/CURRENT-STATE-AUDIT.md`, "multi-agente è teatro").

### Principi
- **Greenfield**: repo nuovo, nessun vincolo dal vecchio. Si porta avanti solo conoscenza, non codice.
- **Approach A**: kernel AIOS scritto da zero, di proprietà, zero framework agenti di terzi.
- **Personalizzato su Luigi**: il Founder Model è cuore del sistema, non un add-on.
- **Autonomia guadagnata, non concessa**: ogni azione sale di livello dimostrando affidabilità.
- **Sicuro per costruzione**: kill-switch + audit log dal giorno 1; soldi/contratti restano L1 finché Luigi non li promuove a mano.
- **Moduli isolati**: ogni unità ha uno scopo chiaro, interfaccia definita, testabile da sola (futuro multi-tenant senza rifare).

---

## 2. Architettura

```
CONTROL PLANE (Luigi, unico umano del board)
  Dashboard web + Telegram → feed live · coda approvazioni · KILL-SWITCH · audit log
        │
AIOS KERNEL (custom, da zero)
  ① Scheduler      — chi gira, quando, con quale priorità (cron + eventi)
  ② Context Mgr    — assembla il contesto per ogni invocazione agente
  ③ Memory Mgr     — memoria breve (sessione) + lunga (Postgres + pgvector)
  ④ Storage Mgr    — source of truth dati azienda (Postgres/Supabase)
  ⑤ Tool Mgr       — registro tool + chi può usare cosa
  ⑥ Access/Policy  — GUARDRAIL: scaletta autonomia L0–L3 per azione/ambito
  ⑦ Founder Model  — clone di Luigi (stile, priorità, voce, regole, conoscenza tacita)
        │  ogni agente legge Founder Model + policy prima di agire
APP LAYER (agenti di dominio)
  Marketing · [Sales · Operations · Finance — fasi successive]
  ogni dominio = un Director-agent che orchestra sotto-funzioni (skill-agente)
        │
INTEGRAZIONI (mondo reale)
  IG Graph API · Supabase (contenuti+dati) · blog-bot · n8n · PostHog · Resend · sito K2-AI · [Stripe · Calendar · Email — fasi succ.]
```

### Stack (proposto, da confermare in plan)
- **Linguaggio kernel + agenti**: Python (Claude SDK maturo, già know-how nel team).
- **Modello**: Claude (Anthropic) primario, con prompt caching sui system prompt lunghi. Fallback opzionale.
- **DB / source of truth**: Postgres su Supabase EU (già in uso, RLS, GDPR).
- **Memory vettoriale**: pgvector su Supabase.
- **Control plane**: dashboard web **Next.js + Tailwind + shadcn/ui** (SPA ricca, vedi §10) + bot Telegram (chat `278384928`) per ping/approvazioni al volo. Companion mobile-web da subito (PWA-ready), app nativa Fase 4.
- **Deploy**: Railway (coerente con resto progetto).
- **Observability**: audit log strutturato su Postgres dal giorno 1; trace per invocazione agente.

---

## 3. Founder Model (modulo ⑦) — il clone di Luigi

Modello vivo di Luigi che ogni agente consulta prima di valutare/agire. Contiene:
- **Stile decisionale**: rischio, velocità vs prudenza, quando spingere.
- **Priorità**: obiettivi del periodo (trimestre/anno).
- **Voce**: come scrive/parla → output (email, post, articoli, proposte) suonano come lui.
- **Regole di delega**: cosa si fida a delegare, cosa vuole sempre vedere.
- **Conoscenza tacita**: clienti, fornitori, storia, preferenze, no-go.

### Origine della conoscenza (tutti e tre combinati)
1. **Intervista guidata** (chat/voce): onboarding profondo → foto del "Luigi di oggi".
2. **Ingestione passato**: post IG, articoli blog, proposte, chat, documenti → estrazione voce/stile/preferenze.
3. **Osserva e impara**: ogni correzione/approvazione affina il modello nel tempo.

Persistenza: tabelle dedicate (`founder_profile`, `founder_voice_samples`, `founder_rules`) + embedding in pgvector
per recupero contestuale.

---

## 4. Scaletta di Autonomia (modulo ⑥) — il guardrail

Ogni **tipo di azione** in ogni ambito ha un livello:

| Livello | Comportamento |
|---|---|
| **L0 osserva** | solo lettura/analisi, nessuna azione esterna |
| **L1 propone** | prepara bozza/proposta → coda approvazioni; Luigi approva |
| **L2 routine** | agisce da solo su azioni sicure → notifica a posteriori |
| **L3 auto** | agisce senza chiedere |

### Regole di promozione
- Tutto parte L0/L1.
- Un'azione sale L1→L2 dopo **N approvazioni consecutive senza correzioni** (N configurabile, default proposto: 10).
- L2→L3 solo con promozione **manuale** di Luigi.
- **Soldi, contratti, comunicazioni legali**: cap a L1 — promozione sempre manuale, mai automatica.
- **Kill-switch globale**: blocca ogni azione esterna istantaneamente, riportando tutto a L0.
- Ogni azione (proposta, eseguita, approvata, rifiutata) → **audit log** immutabile.

---

## 5. Dominio Marketing — reparto completo (primo verticale)

Modello: **Marketing Director Agent** che orchestra ~10 sotto-funzioni (basato su struttura reparto
marketing in aziende grandi: Gartner, mkt1, theorgchart). Ogni sotto-funzione è una skill-agente sulla scaletta.

| # | Sotto-funzione | Cosa fa | Stato K2-AI | Start | In Fase 1? |
|---|---|---|---|---|---|
| 1 | Brand & Voice | custodisce voce/narrativa/identità | Founder Model | L0 | ✅ |
| 2 | Content | blog, articoli, autorità | blog-bot esiste | L0/L1 | ✅ |
| 3 | Social Media | IG + canali, calendario, caption | n8n WF07 esiste | L0/L1 | ✅ |
| 4 | SEO | keyword, on-page, pillar/cluster | regole CLAUDE.md | L0/L1 | ✅ |
| 5 | Analytics & Ops | misura, report, insight, infra | PostHog | L0 | ✅ |
| 6 | Competitive Intel | osserva competitor, posizionamento | NUOVO (richiesto) | L0 | ✅ |
| 7 | Lifecycle / Email | newsletter, nurturing | infra Resend | L0/L1 | — Fase 2 |
| 8 | Product Marketing | messaggi, posizionamento, lanci | positioning v2 | L0/L1 | — Fase 2 |
| 9 | Demand Gen / Paid | campagne, ads, pipeline mkt | futuro | L0 | — Fase 2 |
| 10 | PR & Comms | comunicazione esterna | futuro | L0 | — Fase 2 |

**Fase 1 accende 6 funzioni** (le 5 con dati già esistenti + Competitive Intel).

### Fonti dati Marketing (integrazioni Fase 1)
- **IG Graph API**: insight profilo (reach, engagement, crescita follower, performance per post). `business_discovery` per sé e competitor. (Edit bio non supportato — fuori scope.)
- **Supabase**: **tabella contenuti** (source of truth dei post — migrata da Google Sheets) + asset.
- **blog-bot**: `tools/blog-bot/` + GitHub Action (pubblica mercoledì 06:00).
- **n8n**: Workflow 07 "Spotlight Instagram" (post mercoledì 18:00).
- **PostHog**: traffico sito, conversioni.
- **sito K2-AI**: pillar/cluster, blog pubblicato.

### Giro operativo (end-to-end)
1. Scheduler attiva il Marketing Director (cron + su evento, es. nuovo post pubblicato).
2. Context Mgr assembla stato: insight IG + contenuti Supabase + stato blog/n8n + segnali competitor.
3. Ogni sotto-funzione valuta sul Founder Model (voce/priorità di Luigi).
4. Le proposte (L1) vanno in coda nel cockpit web + ping Telegram.
5. Luigi approva / corregge.
6. Memory Mgr registra la correzione → Founder Model si affina.
7. Access/Policy aggiorna il conteggio affidabilità → eventuale promozione di livello.
8. Tutto a audit log.

### Azioni per livello (Fase 1)
- **L0** (subito attive): leggere insight, leggere contenuti, valutare performance, generare report, scan competitor.
- **L1** (proposta + approvazione): nuova caption/variante, nuovo tema/calendario editoriale, fix SEO on-page, suggerimento articolo, modifica riga tabella contenuti Supabase, trigger n8n.
- **L2/L3**: nessuna in Fase 1 (si guadagnano dopo, Fase 3).

---

## 6. Decomposizione in fasi

| Fase | Contenuto | Esito |
|---|---|---|
| **0** | Fondamenta + scheletro kernel: repo, stack, Postgres source of truth, auth, layer Claude, audit log, kill-switch, Tool Mgr, Access/Policy (scaletta), Context Mgr, Memory Mgr base | ossatura che regge tutto, nessun agente |
| **1** | Founder Model v1 + Marketing Director con 6 sotto-funzioni a L0/L1 + Control Plane (web + Telegram) + integrazioni IG/Supabase/blog/n8n/PostHog | primo reparto vivo, giro completo osserva→propone→approva→impara |
| **2** | Completa Marketing (4 funzioni restanti) + apre Sales/Operations/Finance, stesso schema | tutta l'azienda coperta a L0/L1 |
| **3** | Motore di promozione autonomia (L1→L2) + alert deterministici data-driven | il sistema si muove da solo sul sicuro |
| **4** | L2→L3 dove guadagnato + app mobile + estrazione modulo prodotto multi-tenant | pieno autopilota dove affidabile; prodotto vendibile |

**Questo documento copre la visione + Fase 0 + Fase 1.** Le fasi 2-4 sono mappa, non spec.
Ogni fase successiva avrà la sua spec → plan → implementazione.

---

## 7. Confini moduli (per isolamento)

- **Kernel** non conosce i domini: espone API (scheduling, context, memory, storage, tool-call, policy-check).
- **Agenti di dominio** non parlano col DB direttamente: passano da Storage Mgr / tool registrati.
- **Founder Model** è un servizio interrogabile, non logica sparsa nei prompt.
- **Control Plane** legge audit log + coda; non contiene business logic.
- **Integrazioni** (IG, Supabase, n8n, PostHog) dietro adapter con interfaccia uniforme → sostituibili.

---

## 8. Da confermare nel plan (non bloccano il design)

1. Schema esatto della tabella contenuti Supabase (campi, asset, stato).
2. Token IG Graph: riuso quello di n8n o credenziale dedicata AIOS.
3. ~~Stack dashboard web~~ → **RISOLTO**: Next.js + Tailwind + shadcn/ui (mockup 2026-06-04, vedi §9).
4. Valore default N per promozione L1→L2.
5. Confini precisi tra "trigger n8n da AIOS" vs "AIOS sostituisce n8n" per il flusso IG.

---

## 9. Cockpit UI (control plane) — riferimento mockup 2026-06-04

Stack: **Next.js + Tailwind + shadcn/ui**. Mobile-web responsive da subito.

**Layout Overview (home cockpit)**:
- **Sidebar**: Overview · AI Agents · Marketing · Sales/CRM · Finance · Legal & Compliance · Operations · HR · Projects · Documents · Automations · Analytics · Settings · "Ask AIOS" (assistente).
- **Header**: barra "Ask AIOS anything" (comando naturale) + Generate Report + Launch Automation + profilo.
- **Company Pulse**: indice salute azienda (%) + agenti online + automazioni attive + approvazioni umane pending.
- **Striscia KPI**: Monthly Revenue, Net Margin, Active Leads, Contracts Reviewed, Tasks Automated, Hours Saved, AI Agent Accuracy, Risk Level.
- **Card per-dominio**: una per ambito, con metrica chiave + mini-grafico + "Open <X> Agent →".
- **AI Agents**: lista agenti con stato (Active/Waiting/Idle) + **accuracy %** (= segnale di affidabilità che alimenta la scaletta autonomia).
- **Human Approval Queue**: coda azioni L1 con **Approve / Edit / Reject** per riga (cuore del control plane).
- **Automation Center**: automazioni attive, run riusciti/falliti, tempo risparmiato, top automations.
- **Company Intelligence**: growth score, operational efficiency, financial stability, legal risk, marketing momentum, sales velocity.
- **Core Status** (sidebar footer): agenti online, automazioni attive, approvazioni pending, System Health %.
- **Companion mobile**: stessa Overview compatta (Pulse, KPI, agenti, approvazioni).

Mapping ai moduli kernel:
- "AI Agent Accuracy / accuracy %" ← metrica di affidabilità del modulo ⑥ (Access/Policy) → guida promozioni L1→L2.
- "Human Approval Queue" ← coda L1 del modulo ⑥ + audit log.
- "Automation Center" ← scheduler (①) + tool runs (⑤).
- "Company Pulse / Intelligence" ← Analytics & Ops + storage (④).
- "Ask AIOS" ← entry point linguaggio naturale verso il Director-agent del dominio.

In **Fase 1** il cockpit nasce con: Overview (Pulse + KPI marketing + card Marketing), pagina Marketing,
AI Agents (le 6 sotto-funzioni marketing), Human Approval Queue, Automation Center (blog-bot/n8n), Settings.
Gli altri domini compaiono come card/voci "in arrivo" finché non vengono accesi.

---

## 10. Non-obiettivi (YAGNI in questa fase)
- Multi-tenant reale (solo architettura che non lo preclude).
- App mobile (Fase 4).
- Sales/Operations/Finance (Fasi 2+).
- L2/L3 e autopilota (Fasi 3-4).
- Demand Gen/Paid, PR, Lifecycle, Product Marketing (Fase 2).
