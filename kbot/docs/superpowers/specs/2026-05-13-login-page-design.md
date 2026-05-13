# Login Page Design

**Goal:** Sostituire la pagina `/sign-in` attuale (testo su nero) con una split screen branded che sia il primo schermo che l'utente vede aprendo K2-AI.

**Architecture:** Pagina Next.js App Router a `/sign-in/[[...sign-in]]/page.tsx`. Layout split 50/50: pannello sinistro branding statico (no JS), pannello destro `<SignIn />` Clerk. Mobile: colonna singola, bullets collassati. Nessun backend aggiuntivo — Clerk gestisce tutto l'auth.

**Tech Stack:** Next.js 16 App Router, `@clerk/nextjs` (`<SignIn />`), Tailwind CSS, CSS vars esistenti (`--bg-0`, `--teal`, `--text-main`, `--text-soft`).

---

## Layout

### Desktop (≥ 768px) — split 50/50

**Pannello sinistro** (`flex:1`, `bg: linear-gradient(160deg, #071f1d → #050d0c → #050505)`):
- Glow radiale teal in alto a sinistra (decorativo, `position:absolute`)
- Logo: box 38×38 gradient teal con "K2", testo "K2-AI" bold bianco
- Headline: `"Fai crescere il tuo business con l'AI"` — 28px bold bianco
- Sottotitolo: `"Report professionali e analisi strategica generati in pochi minuti."` — 13px grigio
- 3 bullet con icona checkmark teal:
  1. **Report strategici pronti in minuti** — Analisi, KPI e piano operativo generati dall'AI
  2. **Copertura multi-settore** — PMI, hospitality, legale, compliance, edilizia, tokenizzazione
  3. **Documento consegnabile al cliente** — PDF professionale scaricabile, nessun lavoro manuale
- Footer: `"© 2026 K2-AI — k2-ai.it"` — 10px grigio scuro

**Pannello destro** (`flex:1`, `bg: #0a0a0a`, `border-left: 1px solid #111`):
- Titolo: `"Accedi al tuo account"` — 20px bold bianco
- Link: `"Non hai un account? Registrati"` (Clerk gestisce il tab internamente)
- `<SignIn />` Clerk con `appearance` override per tema scuro
- Privacy note: `"Accedendo accetti i Termini e la Privacy Policy"` — 10px grigio

### Mobile (< 768px) — colonna singola
- Logo + nome in alto (riga orizzontale, compatta)
- Bullets visibili ma padding ridotto
- `<SignIn />` sotto, full width

## Clerk Appearance Override

```ts
appearance={{
  variables: {
    colorPrimary: "#14b8a6",
    colorBackground: "#0a0a0a",
    colorInputBackground: "#111111",
    colorInputText: "#e5e7eb",
    colorText: "#e5e7eb",
    colorTextSecondary: "#6b7280",
    borderRadius: "8px",
  },
  elements: {
    card: { boxShadow: "none", border: "1px solid #1f1f1f", background: "#050505" },
    formButtonPrimary: { background: "#14b8a6", color: "#000", fontWeight: "700" },
    socialButtonsBlockButton: { border: "1px solid #1f1f1f", background: "#111", color: "#d1d5db" },
    dividerLine: { background: "#1f1f1f" },
    dividerText: { color: "#4b5563" },
    footerActionLink: { color: "#14b8a6" },
    headerTitle: { display: "none" },
    headerSubtitle: { display: "none" },
  },
}}
```

## File

| File | Azione |
|------|--------|
| `src/app/sign-in/[[...sign-in]]/page.tsx` | Riscrivere interamente |
| `src/app/sign-up/[[...sign-up]]/page.tsx` | Stesso layout, `<SignUp />` al posto di `<SignIn />` |

Nessun altro file da modificare — middleware e env vars già corretti.
