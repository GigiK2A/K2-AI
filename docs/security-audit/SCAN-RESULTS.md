# Automated Scan Results — 2026-05-15

## Strumenti usati
- `pip-audit 2.10.0` (PyPI vuln DB)
- `npm audit` (GitHub Advisory DB)
- grep manuale per hardcoded secrets + verifica `.gitignore` su `.env`
- **NON usati** (richiedono setup separato): semgrep, OWASP ZAP, Burp, nuclei

---

## Python dependencies

### kbot backend (`kai-website/kbot/backend/requirements.txt`)
**Risultato**: ✅ **0 vulnerabilità note**

Tutte le dipendenze (fastapi, anthropic, supabase, stripe, resend, httpx, pdfplumber, playwright, PyJWT, pytest, ecc.) sono pulite secondo PyPI advisory DB.

### ai-board (`pyproject.toml`)
**Risultato**: ✅ **0 vulnerabilità note**

Tutte le dipendenze (agno, anthropic, openai, supabase, fastapi, python-telegram-bot, ddgs, ecc.) pulite.

---

## Node dependencies

### kai-website (`package.json`)
**Risultato**: ⚠️ **5 vulnerabilità** (4 moderate, 1 **HIGH**)

| Severity | Package | CVE | Fix |
|----------|---------|-----|-----|
| 🔴 **HIGH** | `protobufjs` ≤ 7.5.5 | Code injection + prototype injection + DoS (7 CVE) | `npm audit fix` (transitive — likely via `puppeteer-core` o `@sparticuz/chromium`) |
| 🟡 Moderate | `esbuild` ≤ 0.24.2 | Dev server can serve any origin → exfiltration in dev | `npm audit fix --force` → vite@8 (breaking) |
| 🟡 Moderate | `vite` ≤ 6.4.1 | Depends on esbuild vuln | Stesso fix |
| 🟡 Moderate | `postcss` < 8.5.10 | XSS via `</style>` in stringify | `npm audit fix` |
| 🟡 Moderate | `@protobufjs/utf8` ≤ 1.1.0 | Overlong UTF-8 | `npm audit fix` |

**Azione**: eseguire `cd kai-website && npm audit fix` (non `--force` per evitare vite 5→8 breaking). Se protobufjs è ancora vulnerabile, valutare upgrade puppeteer-core / @sparticuz/chromium.

### kbot frontend (`kai-website/kbot/package.json`)
**Risultato**: ⚠️ **2 vulnerabilità moderate**

| Severity | Package | CVE | Fix |
|----------|---------|-----|-----|
| 🟡 Moderate | `postcss` < 8.5.10 | XSS via stringify | `npm audit fix --force` → next@9.3.3 (breaking — sconsigliato) |
| 🟡 Moderate | `next` 9.3.4-canary - 16.x | Transitive postcss | Stesso |

**Azione**: il fix automatico vuole downgradare Next.js a 9.3.3 — inaccettabile. Aspettare nuova release Next con postcss patched, oppure pin diretto di postcss in package.json overrides.

---

## Hardcoded secrets

Scansione regex `(api[_-]?key|secret|token|password|bearer)\s*[:=]\s*['"][a-zA-Z0-9_.-]{16,}['"]` su `.py/.js/.ts/.tsx/.json` (escluso node_modules, .venv, dist, lock files, riferimenti a env vars):

**Risultato**: ✅ **Nessun secret hardcoded trovato in file tracciati**.

### File `.env` locali
| File | Esiste localmente | Gitignored |
|------|-------------------|------------|
| `ai-board/.env` | ✓ | ✓ (line 1 di `ai-board/.gitignore`) |
| `kai-website/.env` | ✓ | ✓ (line 3 di `kai-website/.gitignore`) |
| `kai-website/kbot/backend/.env` | ✗ (assente) | n/a |

Tutti gli `.env.example` sono tracciati (corretto, sono placeholder).

⚠️ **Resta valido il finding C-1 ai-board**: il file `.env` locale contiene segreti vivi e va comunque ruotato anche se non in git. Il rischio è che laptop compromesso / backup non cifrato / SVN locale non legato a git possa esporli.

---

## Cosa NON è stato scansionato (gap rimanenti)

| Tool | Cosa farebbe | Priorità |
|------|--------------|----------|
| `semgrep --config auto` | Static analysis pattern matching (SQL injection, XSS, command injection, hardcoded secrets avanzati, taint analysis) | Alta |
| `bandit` (Python) | Python-specific issues (eval, exec, pickle, weak crypto, SSL verify=False) | Media |
| `gitleaks` / `trufflehog` | Storia git per secret accidentalmente committati e poi rimossi | Alta |
| `nuclei` | Scan attivo HTTP per misconfigurations (CSP, headers, exposed paths) | Media |
| `OWASP ZAP` baseline | Dynamic scan su istanza dev del sito | Media |
| `puppeteer-core` / `@sparticuz/chromium` upgrade check | Verificare versioni più recenti che fixano protobufjs HIGH | Alta (immediata) |
| Penetration test manuale | Logic flaws, auth bypass, IDOR — solo terza parte indipendente | Annuale |

---

## Riassunto severità

| Source | Critical | High | Moderate | Low | Pulito |
|--------|----------|------|----------|-----|--------|
| pip-audit kbot | 0 | 0 | 0 | 0 | ✓ |
| pip-audit ai-board | 0 | 0 | 0 | 0 | ✓ |
| npm audit kai-website | 0 | **1** (protobufjs) | 4 | 0 | ✗ |
| npm audit kbot-ui | 0 | 0 | 2 | 0 | ✗ |
| Hardcoded secrets | 0 | 0 | 0 | 0 | ✓ |

**Combinato con audit manuale (EXECUTIVE-SUMMARY.md)**: 3 Critical + 20 High totali.

---

## Comandi per riprodurre

```bash
# Python (usa il venv esistente di kbot per riusare pip-audit)
cd /Volumes/PARASSITA/K-AI/kai-website/kbot/backend
.venv/bin/pip install pip-audit
.venv/bin/pip-audit -r requirements.txt

# ai-board (estrai deps prima)
cd /Volumes/PARASSITA/K-AI/ai-board
grep -oE '"[a-zA-Z][a-zA-Z0-9_-]+>=[0-9][0-9.]*[a-zA-Z0-9.]*"' pyproject.toml | tr -d '"' > /tmp/ai-board-deps.txt
/Volumes/PARASSITA/K-AI/kai-website/kbot/backend/.venv/bin/pip-audit -r /tmp/ai-board-deps.txt

# Node
cd /Volumes/PARASSITA/K-AI/kai-website && npm audit
cd /Volumes/PARASSITA/K-AI/kai-website/kbot && npm audit
```

Step successivi consigliati in ordine:
1. `npm audit fix` su kai-website (non `--force`)
2. Aggiungere `pip-audit` e `npm audit` al pipeline CI (fail su HIGH+)
3. Installare `semgrep` e `gitleaks` per scan più profondi
4. Penetration test esterno da terza parte indipendente (post-fix Critical/High)
