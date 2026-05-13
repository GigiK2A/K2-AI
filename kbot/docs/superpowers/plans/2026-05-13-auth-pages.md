# Auth Pages Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add dedicated `/sign-in` and `/sign-up` pages with Clerk components, make UserButton always visible, fix AuthGate to redirect instead of modal, and wire up the mobile nav Account button.

**Architecture:** Clerk catch-all route pattern for Next.js App Router. `<SignIn />` and `<SignUp />` components live at `/sign-in/[[...sign-in]]` and `/sign-up/[[...sign-up]]`. Middleware marks these as public. AuthGate uses Next.js `<Link>` to redirect. Mobile nav Account button links to `/sign-in` or renders `<UserButton />` inline.

**Tech Stack:** `@clerk/nextjs` (SignIn, SignUp, UserButton, useUser), Next.js 16 App Router, TypeScript.

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `src/app/sign-in/[[...sign-in]]/page.tsx` | Create | Clerk SignIn hosted UI |
| `src/app/sign-up/[[...sign-up]]/page.tsx` | Create | Clerk SignUp hosted UI |
| `src/middleware.ts` | Modify | Add `/sign-in(.*)` and `/sign-up(.*)` to public routes |
| `src/components/auth/AuthGate.tsx` | Modify | Replace modal with Link to /sign-in |
| `src/components/layout/ChatLayout.tsx` | Modify | Remove `hidden md:flex` so UserButton is always in header |
| `src/app/page.tsx` | Modify | Mobile nav Account button: link to /sign-in or show UserButton |
| `.env.local` | Modify | Add Clerk redirect env vars |

---

### Task 1: Add Clerk redirect env vars

**Files:**
- Modify: `.env.local`

- [ ] **Step 1: Add four env vars**

Open `.env.local` (currently at `/Volumes/PARASSITA/kbot/.env.local`) and add these four lines at the end:

```
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL=/
NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL=/
```

Full file after edit:
```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_ZGlzdGluY3QtbWl0ZS02NC5jbGVyay5hY2NvdW50cy5kZXYk
CLERK_SECRET_KEY=sk_test_REPLACE_ME
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_REPLACE_ME
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL=/
NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL=/
```

- [ ] **Step 2: Commit**

```bash
git add .env.local
git commit -m "feat: add Clerk sign-in/sign-up redirect env vars"
```

---

### Task 2: Add sign-in and sign-up to public middleware routes

**Files:**
- Modify: `src/middleware.ts`

Current `isPublicRoute` array:
```ts
const isPublicRoute = createRouteMatcher([
  "/",
  "/api/chat(.*)",
  "/api/skills(.*)",
  "/api/upload(.*)",
  "/api/leads(.*)",
  "/api/report-access(.*)",
  "/api/stripe/webhook(.*)",
]);
```

- [ ] **Step 1: Add sign-in and sign-up routes**

Replace the `isPublicRoute` definition with:

```ts
const isPublicRoute = createRouteMatcher([
  "/",
  "/sign-in(.*)",
  "/sign-up(.*)",
  "/api/chat(.*)",
  "/api/skills(.*)",
  "/api/upload(.*)",
  "/api/leads(.*)",
  "/api/report-access(.*)",
  "/api/stripe/webhook(.*)",
]);
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd /Volumes/PARASSITA/kbot && npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add src/middleware.ts
git commit -m "feat: add /sign-in and /sign-up as public routes in middleware"
```

---

### Task 3: Create sign-in page

**Files:**
- Create: `src/app/sign-in/[[...sign-in]]/page.tsx`

- [ ] **Step 1: Create directory and file**

Create `src/app/sign-in/[[...sign-in]]/page.tsx` with this content:

```tsx
import { SignIn } from "@clerk/nextjs";

export default function SignInPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--bg-0)]">
      <SignIn />
    </div>
  );
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd /Volumes/PARASSITA/kbot && npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add src/app/sign-in/
git commit -m "feat: add /sign-in page with Clerk SignIn component"
```

---

### Task 4: Create sign-up page

**Files:**
- Create: `src/app/sign-up/[[...sign-up]]/page.tsx`

- [ ] **Step 1: Create directory and file**

Create `src/app/sign-up/[[...sign-up]]/page.tsx` with this content:

```tsx
import { SignUp } from "@clerk/nextjs";

export default function SignUpPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--bg-0)]">
      <SignUp />
    </div>
  );
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd /Volumes/PARASSITA/kbot && npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add src/app/sign-up/
git commit -m "feat: add /sign-up page with Clerk SignUp component"
```

---

### Task 5: Update AuthGate — replace modal with redirect link

**Files:**
- Modify: `src/components/auth/AuthGate.tsx`

Current file at `/Volumes/PARASSITA/kbot/src/components/auth/AuthGate.tsx`:
```tsx
"use client";

import { SignInButton, useUser } from "@clerk/nextjs";

export function AuthGate({ children }: { children: React.ReactNode }) {
  const { isLoaded, isSignedIn } = useUser();

  if (!isLoaded) {
    return (
      <div className="flex items-center justify-center py-20 text-[var(--text-muted)] text-sm">
        Caricamento...
      </div>
    );
  }

  if (!isSignedIn) {
    return (
      <div className="k2-panel mx-auto mt-12 max-w-sm rounded-2xl p-8 text-center">
        <p className="mb-2 text-lg font-semibold">Report Premium</p>
        <p className="mb-6 text-sm text-[var(--text-soft)]">
          Accedi per usare il report premium. La chat è gratuita, i download richiedono un pagamento one-time.
        </p>
        <SignInButton mode="modal">
          <button className="w-full rounded-xl bg-[var(--teal)] py-3 text-sm font-semibold text-black">
            Accedi o registrati
          </button>
        </SignInButton>
      </div>
    );
  }

  return <>{children}</>;
}
```

- [ ] **Step 1: Replace SignInButton modal with Link**

Replace the entire file content:

```tsx
"use client";

import Link from "next/link";
import { useUser } from "@clerk/nextjs";

export function AuthGate({ children }: { children: React.ReactNode }) {
  const { isLoaded, isSignedIn } = useUser();

  if (!isLoaded) {
    return (
      <div className="flex items-center justify-center py-20 text-[var(--text-muted)] text-sm">
        Caricamento...
      </div>
    );
  }

  if (!isSignedIn) {
    return (
      <div className="k2-panel mx-auto mt-12 max-w-sm rounded-2xl p-8 text-center">
        <p className="mb-2 text-lg font-semibold">Report Premium</p>
        <p className="mb-6 text-sm text-[var(--text-soft)]">
          Accedi per usare il report premium. La chat è gratuita, i download richiedono un pagamento one-time.
        </p>
        <Link href="/sign-in">
          <button className="w-full rounded-xl bg-[var(--teal)] py-3 text-sm font-semibold text-black">
            Accedi o registrati
          </button>
        </Link>
      </div>
    );
  }

  return <>{children}</>;
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd /Volumes/PARASSITA/kbot && npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add src/components/auth/AuthGate.tsx
git commit -m "feat: AuthGate redirects to /sign-in instead of modal"
```

---

### Task 6: Make UserButton always visible in header

**Files:**
- Modify: `src/components/layout/ChatLayout.tsx`

Current header right section:
```tsx
<div className="hidden items-center gap-2 md:flex">
  {(isReportMode ?? mode === "report") && (
    <span className="inline-flex items-center gap-1 rounded-full border border-[var(--teal)]/30 bg-[var(--teal)]/10 px-2 py-1 text-xs text-[var(--teal)]">
      <Sparkles size={12} /> Premium
    </span>
  )}
  <a href="#" className="rounded-lg border border-[var(--line)] px-3 py-1.5 text-xs text-[var(--text-soft)]">Apri dashboard</a>
  <UserButton />
</div>
```

- [ ] **Step 1: Split into two divs — UserButton always visible, rest md-only**

Replace that `<div className="hidden items-center gap-2 md:flex">` block with:

```tsx
<div className="flex items-center gap-2">
  <div className="hidden items-center gap-2 md:flex">
    {(isReportMode ?? mode === "report") && (
      <span className="inline-flex items-center gap-1 rounded-full border border-[var(--teal)]/30 bg-[var(--teal)]/10 px-2 py-1 text-xs text-[var(--teal)]">
        <Sparkles size={12} /> Premium
      </span>
    )}
    <a href="#" className="rounded-lg border border-[var(--line)] px-3 py-1.5 text-xs text-[var(--text-soft)]">Apri dashboard</a>
  </div>
  <UserButton />
</div>
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd /Volumes/PARASSITA/kbot && npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add src/components/layout/ChatLayout.tsx
git commit -m "feat: UserButton always visible in header on all screen sizes"
```

---

### Task 7: Fix mobile nav Account button

**Files:**
- Modify: `src/app/page.tsx`

Current mobile nav (bottom of the file):
```tsx
<nav className="fixed inset-x-0 bottom-0 z-30 border-t border-[var(--line)] bg-[rgba(5,5,5,0.95)] px-4 py-2 xl:hidden">
  <div className="mx-auto flex max-w-xl items-center justify-around text-xs text-[var(--text-soft)]">
    <button className="flex flex-col items-center gap-1 text-[var(--teal)]"><MessageCircle size={16} />Chat</button>
    <button className="flex flex-col items-center gap-1"><LayoutDashboard size={16} />Dashboard</button>
    <button className="flex flex-col items-center gap-1"><Home size={16} />Report</button>
    <button className="flex flex-col items-center gap-1"><UserCircle2 size={16} />Account</button>
  </div>
</nav>
```

- [ ] **Step 1: Add Link import and replace Account button**

At top of `src/app/page.tsx`, `Link` from `next/link` is not yet imported. Add it to existing imports.

Find the imports block and add:
```tsx
import Link from "next/link";
```

Then replace the mobile nav `<nav>` block with:

```tsx
<nav className="fixed inset-x-0 bottom-0 z-30 border-t border-[var(--line)] bg-[rgba(5,5,5,0.95)] px-4 py-2 xl:hidden">
  <div className="mx-auto flex max-w-xl items-center justify-around text-xs text-[var(--text-soft)]">
    <button className="flex flex-col items-center gap-1 text-[var(--teal)]"><MessageCircle size={16} />Chat</button>
    <button className="flex flex-col items-center gap-1"><LayoutDashboard size={16} />Dashboard</button>
    <button className="flex flex-col items-center gap-1"><Home size={16} />Report</button>
    {isSignedIn ? (
      <div className="flex flex-col items-center gap-1">
        <UserButton />
        <span>Account</span>
      </div>
    ) : (
      <Link href="/sign-in" className="flex flex-col items-center gap-1">
        <UserCircle2 size={16} />Account
      </Link>
    )}
  </div>
</nav>
```

`isSignedIn` is available from `const { getToken, isSignedIn } = useAuth();` — update the destructuring of `useAuth()` on the line where `getToken` is extracted:

Find:
```tsx
const { getToken } = useAuth();
```

Replace with:
```tsx
const { getToken, isSignedIn } = useAuth();
```

- [ ] **Step 2: Remove now-unused UserCircle2 import if it causes an error**

`UserCircle2` is still used in the `else` branch so no removal needed.

- [ ] **Step 3: Verify TypeScript compiles**

```bash
cd /Volumes/PARASSITA/kbot && npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 4: Commit**

```bash
git add src/app/page.tsx
git commit -m "feat: mobile nav Account links to /sign-in or shows UserButton when signed in"
```
