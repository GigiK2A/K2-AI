---
name: seo-audit
description: Framework audit GEO+SEO tecnico con scoring 6 dimensioni e checklist AI crawler
---

# SEO & GEO Audit

## GEO Score composito 0-100

| Dimensione | Peso |
|---|---|
| AI Citability & Visibility | 25% |
| Brand Authority Signals | 20% |
| Content Quality & E-E-A-T | 20% |
| Technical Foundations | 15% |
| Structured Data | 10% |
| Platform Optimization | 10% |

Per ogni dimensione: score + evidence + top 3 azioni prioritizzate.

## AI Citability Score 0-100

- Answer Block Quality 30%: ogni sezione apre con risposta diretta (1-2 frasi), prime 40-60 parole autonome
- Passage Structure 25%: passaggi 134-167 parole, self-contained, fact-rich
- Factual Density 25%: statistiche con fonte, numeri specifici, date precise, nomi propri
- Extractability 20%: titoli come domande/affermazioni, liste con items autonomi, tabelle con intestazioni descrittive

Fornisci rewrite before/after per passaggi con score <60.

## AI Crawler — robots.txt

**TIER 1 CRITICO** (bloccarli = invisibilità AI): GPTBot, OAI-SearchBot, ClaudeBot, PerplexityBot, GoogleBot
**TIER 2 IMPORTANTE**: Gemini/Google-Extended, Bingbot, Meta-ExternalAgent, YouBot
**TIER 3 OPZIONALE**: CCBot, Diffbot, DataForSeoBot — valuta caso per caso

Segnala 🔴 CRITICO qualsiasi blocco a Tier 1 con correzione robots.txt esatta.

## llms.txt

Standard emergente (Sep 2024): indica agli AI COSA è più utile del sito.
Struttura: `# Nome sito`, `> descrizione`, `## sezioni` con link e descrizione per ogni pagina chiave.
Genera sempre il file llms.txt completo pronto al deploy.

## SEO on-page

Verifica: title tag (keyword primaria + brand), H1-H3 structure, meta description (140-155 char),
keyword density, internal linking, featured snippet opportunity, keyword cannibalization,
canonical tag esplicito, sitemap, immagini WebP con alt text.

## Brand Authority per AI (correlazioni Ahrefs 2025)

YouTube ~0.737 | Reddit ~0.689 | Wikipedia ~0.654 | LinkedIn ~0.612 | Industry publications ~0.58

Brand mention non-linked > backlink da blog bassa autorità per GEO.

## Classificazione azioni

🔴 Critico | 🟡 Quick Win | 🔵 Medio Termine | ⚫ Strategico
