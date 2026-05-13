# Login Page Split Screen Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Sostituire le pagine `/sign-in` e `/sign-up` con un layout split screen branded: sinistra K2-AI branding + 3 bullet, destra Clerk `<SignIn />`/`<SignUp />` con tema scuro.

**Architecture:** Due file Next.js App Router catch-all. Pannello sinistro statico (no JS). Pannello destro usa `<SignIn />`/`<SignUp />` di Clerk con `appearance` prop per tema scuro usando `variables` (colori) + `elements` (style objects — NON Tailwind classes, perché JIT le purga). Mobile: colonna singola, pannello sinistro collassato.

**Tech Stack:** Next.js 16 App Router, `@clerk/nextjs` (`SignIn`, `SignUp`), Tailwind CSS, inline styles per i valori dinamici Clerk.

---

## File Map

| File | Azione |
|------|--------|
| `src/app/sign-in/[[...sign-in]]/page.tsx` | Riscrivere interamente |
| `src/app/sign-up/[[...sign-up]]/page.tsx` | Riscrivere interamente |

---

### Task 1: Rewrite sign-in page

**Files:**
- Modify: `src/app/sign-in/[[...sign-in]]/page.tsx`

- [ ] **Step 1: Leggi il file corrente**

```bash
cat /Volumes/PARASSITA/kbot/src/app/sign-in/\[\[...sign-in\]\]/page.tsx
```

- [ ] **Step 2: Riscrivi l'intero file**

Sostituisci tutto il contenuto con:

```tsx
import { SignIn } from "@clerk/nextjs";

const BULLETS = [
  {
    title: "Report strategici pronti in minuti",
    sub: "Analisi, KPI e piano operativo generati dall'AI",
  },
  {
    title: "Copertura multi-settore",
    sub: "PMI, hospitality, legale, compliance, edilizia, tokenizzazione",
  },
  {
    title: "Documento consegnabile al cliente",
    sub: "PDF professionale scaricabile, nessun lavoro manuale",
  },
];

const clerkAppearance = {
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
    socialButtonsBlockButton: { border: "1px solid #1f1f1f", background: "#111111", color: "#d1d5db" },
    dividerLine: { background: "#1f1f1f" },
    dividerText: { color: "#4b5563" },
    footerActionLink: { color: "#14b8a6" },
    headerTitle: { display: "none" },
    headerSubtitle: { display: "none" },
  },
};

export default function SignInPage() {
  return (
    <div className="flex min-h-screen bg-[#050505]">
      {/* LEFT PANEL — hidden on mobile */}
      <div
        className="hidden md:flex md:flex-1 flex-col justify-between p-12 relative overflow-hidden"
        style={{ background: "linear-gradient(160deg,#071f1d 0%,#050d0c 60%,#050505 100%)" }}
      >
        {/* teal glow decoration */}
        <div
          style={{
            position: "absolute",
            top: "-80px",
            left: "-80px",
            width: "300px",
            height: "300px",
            background: "radial-gradient(circle,rgba(20,184,166,0.12) 0%,transparent 70%)",
            pointerEvents: "none",
          }}
        />

        {/* Logo */}
        <div className="flex items-center gap-3 relative">
          <div
            style={{
              width: "38px",
              height: "38px",
              background: "linear-gradient(135deg,#14b8a6,#0d9488)",
              borderRadius: "10px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontWeight: 900,
              color: "#000",
              fontSize: "16px",
              flexShrink: 0,
            }}
          >
            K2
          </div>
          <span style={{ fontWeight: 800, color: "#fff", fontSize: "16px", letterSpacing: "0.5px" }}>
            K2-AI
          </span>
        </div>

        {/* Headline + bullets */}
        <div className="flex flex-col gap-6 relative">
          <div>
            <h1
              style={{
                fontSize: "28px",
                fontWeight: 800,
                color: "#fff",
                lineHeight: 1.25,
                marginBottom: "8px",
              }}
            >
              Fai crescere il tuo
              <br />
              business con l&apos;AI
            </h1>
            <p style={{ fontSize: "13px", color: "#6b7280", lineHeight: 1.5 }}>
              Report professionali e analisi strategica
              <br />
              generati in pochi minuti.
            </p>
          </div>

          <div className="flex flex-col gap-4">
            {BULLETS.map((b) => (
              <div key={b.title} className="flex items-start gap-3">
                <div
                  style={{
                    width: "22px",
                    height: "22px",
                    background: "rgba(20,184,166,0.15)",
                    border: "1px solid rgba(20,184,166,0.3)",
                    borderRadius: "6px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    flexShrink: 0,
                    marginTop: "2px",
                  }}
                >
                  <span style={{ color: "#14b8a6", fontSize: "11px", fontWeight: 700 }}>✓</span>
                </div>
                <div>
                  <div style={{ fontSize: "13px", fontWeight: 600, color: "#e5e7eb" }}>{b.title}</div>
                  <div style={{ fontSize: "11px", color: "#6b7280", marginTop: "2px" }}>{b.sub}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div style={{ fontSize: "10px", color: "#374151" }} className="relative">
          © 2026 K2-AI — k2-ai.it
        </div>
      </div>

      {/* RIGHT PANEL */}
      <div
        className="flex flex-1 flex-col items-center justify-center p-6 md:p-12"
        style={{ background: "#0a0a0a", borderLeft: "1px solid #111" }}
      >
        {/* Mobile-only logo */}
        <div className="flex md:hidden items-center gap-3 mb-8">
          <div
            style={{
              width: "32px",
              height: "32px",
              background: "linear-gradient(135deg,#14b8a6,#0d9488)",
              borderRadius: "8px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontWeight: 900,
              color: "#000",
              fontSize: "14px",
            }}
          >
            K2
          </div>
          <span style={{ fontWeight: 800, color: "#fff", fontSize: "15px" }}>K2-AI</span>
        </div>

        {/* Clerk SignIn */}
        <div className="w-full max-w-sm">
          <div className="mb-6 hidden md:block">
            <h2 style={{ fontSize: "20px", fontWeight: 700, color: "#fff", marginBottom: "4px" }}>
              Accedi al tuo account
            </h2>
          </div>
          <SignIn appearance={clerkAppearance} />
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Verifica TypeScript**

```bash
cd /Volumes/PARASSITA/kbot && npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 4: Verifica visivamente**

Apri http://localhost:3000/sign-in nel browser. Dovresti vedere:
- Sinistra: sfondo gradient teal scuro, logo K2-AI, headline, 3 bullet
- Destra: form Clerk con tema scuro
- Su mobile (< 768px): solo il pannello destro con logo compatto in cima

- [ ] **Step 5: Commit**

```bash
cd /Volumes/PARASSITA/kbot && git add src/app/sign-in/ && git commit -m "feat: sign-in split screen branded layout"
```

---

### Task 2: Rewrite sign-up page

**Files:**
- Modify: `src/app/sign-up/[[...sign-up]]/page.tsx`

Stesso layout identico a Task 1 ma con `<SignUp />` al posto di `<SignIn />` e titolo "Crea il tuo account".

- [ ] **Step 1: Leggi il file corrente**

```bash
cat /Volumes/PARASSITA/kbot/src/app/sign-up/\[\[...sign-up\]\]/page.tsx
```

- [ ] **Step 2: Riscrivi l'intero file**

```tsx
import { SignUp } from "@clerk/nextjs";

const BULLETS = [
  {
    title: "Report strategici pronti in minuti",
    sub: "Analisi, KPI e piano operativo generati dall'AI",
  },
  {
    title: "Copertura multi-settore",
    sub: "PMI, hospitality, legale, compliance, edilizia, tokenizzazione",
  },
  {
    title: "Documento consegnabile al cliente",
    sub: "PDF professionale scaricabile, nessun lavoro manuale",
  },
];

const clerkAppearance = {
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
    socialButtonsBlockButton: { border: "1px solid #1f1f1f", background: "#111111", color: "#d1d5db" },
    dividerLine: { background: "#1f1f1f" },
    dividerText: { color: "#4b5563" },
    footerActionLink: { color: "#14b8a6" },
    headerTitle: { display: "none" },
    headerSubtitle: { display: "none" },
  },
};

export default function SignUpPage() {
  return (
    <div className="flex min-h-screen bg-[#050505]">
      {/* LEFT PANEL — hidden on mobile */}
      <div
        className="hidden md:flex md:flex-1 flex-col justify-between p-12 relative overflow-hidden"
        style={{ background: "linear-gradient(160deg,#071f1d 0%,#050d0c 60%,#050505 100%)" }}
      >
        <div
          style={{
            position: "absolute",
            top: "-80px",
            left: "-80px",
            width: "300px",
            height: "300px",
            background: "radial-gradient(circle,rgba(20,184,166,0.12) 0%,transparent 70%)",
            pointerEvents: "none",
          }}
        />

        <div className="flex items-center gap-3 relative">
          <div
            style={{
              width: "38px",
              height: "38px",
              background: "linear-gradient(135deg,#14b8a6,#0d9488)",
              borderRadius: "10px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontWeight: 900,
              color: "#000",
              fontSize: "16px",
              flexShrink: 0,
            }}
          >
            K2
          </div>
          <span style={{ fontWeight: 800, color: "#fff", fontSize: "16px", letterSpacing: "0.5px" }}>
            K2-AI
          </span>
        </div>

        <div className="flex flex-col gap-6 relative">
          <div>
            <h1
              style={{
                fontSize: "28px",
                fontWeight: 800,
                color: "#fff",
                lineHeight: 1.25,
                marginBottom: "8px",
              }}
            >
              Fai crescere il tuo
              <br />
              business con l&apos;AI
            </h1>
            <p style={{ fontSize: "13px", color: "#6b7280", lineHeight: 1.5 }}>
              Report professionali e analisi strategica
              <br />
              generati in pochi minuti.
            </p>
          </div>

          <div className="flex flex-col gap-4">
            {BULLETS.map((b) => (
              <div key={b.title} className="flex items-start gap-3">
                <div
                  style={{
                    width: "22px",
                    height: "22px",
                    background: "rgba(20,184,166,0.15)",
                    border: "1px solid rgba(20,184,166,0.3)",
                    borderRadius: "6px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    flexShrink: 0,
                    marginTop: "2px",
                  }}
                >
                  <span style={{ color: "#14b8a6", fontSize: "11px", fontWeight: 700 }}>✓</span>
                </div>
                <div>
                  <div style={{ fontSize: "13px", fontWeight: 600, color: "#e5e7eb" }}>{b.title}</div>
                  <div style={{ fontSize: "11px", color: "#6b7280", marginTop: "2px" }}>{b.sub}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div style={{ fontSize: "10px", color: "#374151" }} className="relative">
          © 2026 K2-AI — k2-ai.it
        </div>
      </div>

      {/* RIGHT PANEL */}
      <div
        className="flex flex-1 flex-col items-center justify-center p-6 md:p-12"
        style={{ background: "#0a0a0a", borderLeft: "1px solid #111" }}
      >
        <div className="flex md:hidden items-center gap-3 mb-8">
          <div
            style={{
              width: "32px",
              height: "32px",
              background: "linear-gradient(135deg,#14b8a6,#0d9488)",
              borderRadius: "8px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontWeight: 900,
              color: "#000",
              fontSize: "14px",
            }}
          >
            K2
          </div>
          <span style={{ fontWeight: 800, color: "#fff", fontSize: "15px" }}>K2-AI</span>
        </div>

        <div className="w-full max-w-sm">
          <div className="mb-6 hidden md:block">
            <h2 style={{ fontSize: "20px", fontWeight: 700, color: "#fff", marginBottom: "4px" }}>
              Crea il tuo account
            </h2>
          </div>
          <SignUp appearance={clerkAppearance} />
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Verifica TypeScript**

```bash
cd /Volumes/PARASSITA/kbot && npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 4: Verifica visivamente**

Apri http://localhost:3000/sign-up. Stesso layout di sign-in, con `<SignUp />`.

- [ ] **Step 5: Commit**

```bash
cd /Volumes/PARASSITA/kbot && git add src/app/sign-up/ && git commit -m "feat: sign-up split screen branded layout"
```
