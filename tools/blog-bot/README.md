# K2-AI blog autopilot

Ogni mercoledì alle **03:40 UTC** (05:40 CEST / 04:40 CET) il workflow GitHub Actions
`blog-autopilot` legge la prossima riga da pubblicare da **`schedule.json`**, chiama
Claude per generare un articolo teaser brand-aligned, lo valida, aggiorna indice blog,
sitemap e sezione "Dal blog" della pillar padre, committa e fa push su `main`.
Railway redeploya automaticamente.

> L'orario non è tondo di proposito: il cron di GitHub Actions è solo UTC e best-effort,
> e i job schedulati al minuto `:00` finiscono nella congestione massima. Vedi il commento
> in testa a `.github/workflows/blog-autopilot.yml`.

Alle 18:00 CET dello stesso mercoledì il workflow n8n "Spotlight Instagram" pubblica il
post IG con il link `https://www.k2-ai.it{blog_url}`, che a quel punto esiste perché il
blog è stato pubblicato ~12h prima.

## ⚠️ Dove vive lo stato (leggere prima di toccare qualsiasi cosa)

| | Blog | Instagram |
|---|---|---|
| Fonte di verità | `schedule.json`, campo `blog_pubblicato` | Supabase `public.servizi`, colonne `"Stato"` e `"Data"` |
| Chi scrive | questo bot, commit su `main` | workflow n8n (non versionato in questo repo) |

Sono **due contatori indipendenti**: nulla segnala quando divergono.

I campi `stato_ig` e `data_ig` dentro `schedule.json` **non sono mantenuti da nessuno**:
valgono `"da usare"` e `""` su tutte le righe, anche per servizi già passati su IG.
Restano però dentro il filtro di `pickNextForBlog()`, quindi **marcare `stato_ig: "usato"`
su una riga la fa saltare per sempre al blog**. Non toccarli.

Per sapere a che punto è davvero il blog: `origin/main` o il sito live, **mai** il branch
di lavoro corrente — il bot pusha su `main` e ogni altro branch è cieco rispetto a lui.

## Fonte dei dati: perché un JSON e non Google Sheets

L'organizzazione Google ha la policy `iam.disableServiceAccountKeyCreation`, che impedisce
di creare chiavi service account: il bot non può autenticarsi alle Sheets API. La scaletta
è quindi un file versionato nel repo, `schedule.json`, e lo stato sta in git.
`lib/sheet-client.ts` conserva il nome storico ma **non parla con nessuna API Google**.

## Struttura

```
tools/blog-bot/
├── generate-article.ts        ← orchestrator: pick→Claude→HTML→validators→publish
├── schedule.json              ← LA SCALETTA: 25 servizi, source of truth del blog
├── lib/
│   ├── sheet-client.ts        ← legge/scrive schedule.json (nessuna Google API)
│   ├── claude.ts              ← Anthropic SDK wrapper (draft + revise)
│   ├── images.ts              ← generazione immagini via OpenAI gpt-image-1
│   ├── template.ts            ← HTML article template
│   ├── sitemap.ts             ← inietta <url> in src/public/sitemap.xml
│   ├── index-injector.ts      ← card articolo in src/blog/index.html (sentinel BLOG_INDEX_AUTO)
│   ├── pillar.ts              ← URL scaletta → codice pillar (P01…P20, LAB)
│   ├── pillar-injector.ts     ← sezione "Dal blog" nelle pillar (sentinel PILLAR_BLOG_AUTO)
│   ├── git.ts                 ← commit + push via shell
│   └── notify.ts              ← alert Telegram (successo / fallimento)
├── prompts/
│   ├── article-draft.md       ← skill K2-AI brand voice + regole teaser
│   ├── article-revise.md      ← seconda passata: togli l'AI-typical, asciuga
│   └── teaser-check.md        ← self-check Claude: l'articolo rivela la soluzione?
└── validators/
    ├── seo.ts                 ← lunghezza title/meta, schema, link, parole
    ├── voice.ts               ← termini vietati, frasi AI-typical
    ├── teaser.ts              ← esegue teaser-check.md + controlli strutturali
    └── facts.ts               ← numeri whitelisted da facts-allowed.yaml
```

## Blocchi HTML auto-generati

Il bot riscrive da zero due sezioni delimitate da sentinel. Modificarle a mano è
inutile ma innocuo: alla pubblicazione successiva vengono rigenerate.

| Sentinel | File | Se i sentinel mancano |
|---|---|---|
| `BLOG_INDEX_AUTO_BEGIN/END` | `kai-website/src/blog/index.html` | `injectIndexCard()` **lancia** e il run fallisce — non rimuoverli |
| `PILLAR_BLOG_AUTO_BEGIN/END` | `kai-website/src/suite-ai/*.html` | `injectPillarSection()` **ricrea** il blocco prima della CTA finale |

## Env vars richieste (GitHub Secrets)

| Secret | Da dove | Se manca |
|---|---|---|
| `ANTHROPIC_API_KEY` | console.anthropic.com — stessa key di kai-website | il run fallisce |
| `OPENAI_API_KEY` | usata solo per le immagini (gpt-image-1) | articolo pubblicato **senza** immagini, con warning |
| `GH_PAT_BLOG_PUSH` | PAT con scope `contents:write` per il push automatico | fallback su `GITHUB_TOKEN` |
| `TELEGRAM_BOT_TOKEN` | bot @K2AIBot — stessa del workflow IG | nessuna notifica |
| `TELEGRAM_CHAT_ID` | `278384928` | nessuna notifica |

Nessuna variabile Google è più necessaria.

## Test locale

```bash
cd tools/blog-bot
npm install
npm test                     # suite unitaria, nessuna API key richiesta
export ANTHROPIC_API_KEY=sk-ant-...
export OPENAI_API_KEY=sk-...  # opzionale: senza, niente immagini
npm run run -- --dry-run     # genera e valida, NON pubblica
npm run run                  # genera + pubblica + push su main
```

## Failure modes

| Scenario | Comportamento |
|---|---|
| Nessuna riga `da usare` con blog non pubblicato | exit 0, alert Telegram "coda vuota" |
| Claude API down | alert Telegram, exit 1 |
| Validator boccia l'articolo | salva in `drafts-rejected/`, alert Telegram col motivo, exit 1, scaletta **non** aggiornata |
| Generazione immagini fallita | articolo pubblicato lo stesso, alert Telegram di warning |
| Sentinel `BLOG_INDEX_AUTO` assenti | eccezione, exit 1 |
| Git push fail | alert Telegram, exit 1 |

## Costo a regime

- Claude API: ~€0,30/articolo (Sonnet draft + Haiku revise) → ~€1,20/mese su 4 articoli
- Immagini OpenAI `gpt-image-1`: 3 immagini per articolo, costo non misurato
- GitHub Actions: gratis (sotto i 2000 min/mese del free tier)
