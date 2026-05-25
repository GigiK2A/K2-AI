# K2-AI blog autopilot

Ogni mercoledì alle 06:00 CET il workflow GitHub Actions `blog-autopilot`
legge la prossima riga "da usare" dal Google Sheet, chiama Claude per
generare un articolo teaser brand-aligned, lo valida, lo committa nel
repo e fa push su `main`. Railway redeploya automaticamente.

Alle 18:00 CET dello stesso mercoledì, il workflow n8n esistente
("Spotlight Instagram") pesca la stessa riga, pubblica il post IG e
include nella caption il link `https://www.k2-ai.it{blog_url}` che
adesso esiste perché il blog è stato pubblicato 12h prima.

## Struttura

```
tools/blog-bot/
├── generate-article.ts        ← orchestrator: brief→Claude→HTML→validators→publish
├── lib/
│   ├── sheet-client.ts        ← Google Sheets API: read next row, mark as published
│   ├── claude.ts              ← Anthropic SDK wrapper
│   ├── template.ts            ← HTML article template
│   ├── sitemap.ts             ← inject <url> into src/public/sitemap.xml
│   ├── git.ts                 ← commit + push via simple shell
│   └── notify.ts              ← Telegram alert (success / fail)
├── prompts/
│   ├── article-draft.md       ← skill K2-AI brand voice + teaser rules
│   ├── article-revise.md      ← second-pass: strip AI-typical, sharpen
│   └── teaser-check.md        ← Claude self-check: does this leak the solution?
└── validators/
    ├── seo.ts                 ← title/meta length, schema, links, words
    ├── voice.ts               ← banned terms, AI-typical phrases
    ├── teaser.ts              ← runs teaser-check.md + structural checks
    └── facts.ts               ← whitelist numbers from facts-allowed.yaml
```

## Env vars richieste (GitHub Secrets)

| Secret | Da dove |
|---|---|
| `ANTHROPIC_API_KEY` | console.anthropic.com — stessa key di kai-website |
| `GOOGLE_SHEETS_CREDENTIALS` | JSON service account, vedi setup-guide |
| `GOOGLE_SHEET_ID` | ID del foglio K2AI Spotlight (URL ...spreadsheets/d/**ID**/edit) |
| `GH_PAT_BLOG_PUSH` | Personal Access Token con scope `contents:write` per push automatici |
| `TELEGRAM_BOT_TOKEN` | bot @K2AIBot — stessa di IG workflow |
| `TELEGRAM_CHAT_ID` | 278384928 |

## Test locale

```bash
cd tools/blog-bot
npm install
export ANTHROPIC_API_KEY=sk-ant-...
export GOOGLE_SHEETS_CREDENTIALS=$(cat path/to/service-account.json)
export GOOGLE_SHEET_ID=...
npm run run -- --dry-run    # genera ma non pubblica
npm run run                  # genera + pubblica
```

## Failure modes

| Scenario | Comportamento |
|---|---|
| Nessuna riga "da usare" | exit 0, alert Telegram "queue vuota" |
| Claude API down | retry 3x + alert Telegram, exit 1 |
| Validator boccia articolo | salva in `drafts-rejected/`, alert Telegram con motivo |
| Git push fail | retry 2x + alert Telegram, exit 1 |
| Sheet API quota | retry con backoff, alert se persiste |

## Costo a regime

- Claude API: ~€0.30/articolo (Sonnet draft + Haiku revise) → ~€1.20/mese (4 articoli/mese)
- GitHub Actions: gratis (sotto 2000 min/mese free tier)
- Google Sheets API: gratis (sotto 60 req/min)

**Totale: ~€2/mese.**
