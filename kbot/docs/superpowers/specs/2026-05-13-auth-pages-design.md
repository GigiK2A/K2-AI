# Auth Pages Design

**Goal:** Add dedicated `/sign-in` and `/sign-up` pages using Clerk's hosted components so users can register and log in from anywhere in the app.

**Architecture:** Clerk catch-all route pattern for Next.js App Router. Two pages host `<SignIn />` and `<SignUp />` components respectively. Middleware marks these routes public. AuthGate redirects to `/sign-in` instead of showing a modal. Nav mobile Account button links to `/sign-in`.

**Tech Stack:** `@clerk/nextjs` (already installed), Next.js 16 App Router catch-all routes.

---

## Files

- **Create:** `src/app/sign-in/[[...sign-in]]/page.tsx` — renders `<SignIn />` centered on dark background
- **Create:** `src/app/sign-up/[[...sign-up]]/page.tsx` — renders `<SignUp />` centered on dark background
- **Modify:** `src/middleware.ts` — add `/sign-in(.*)` and `/sign-up(.*)` to public routes
- **Modify:** `src/components/auth/AuthGate.tsx` — replace `<SignInButton mode="modal">` with `<Link href="/sign-in">` button
- **Modify:** `src/app/page.tsx` — nav mobile "Account" (UserCircle2) navigates to `/sign-in` when not signed in, shows `<UserButton />` when signed in
- **Modify:** `src/components/layout/ChatLayout.tsx` — remove `hidden md:flex` so `UserButton` is always visible in header
- **Modify:** `.env.local` — add `NEXT_PUBLIC_CLERK_SIGN_IN_URL`, `NEXT_PUBLIC_CLERK_SIGN_UP_URL`, `NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL`, `NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL`

## Behavior

- `/sign-in` — Clerk SignIn UI, after auth redirects to `/`
- `/sign-up` — Clerk SignUp UI, after auth redirects to `/`
- Already-signed-in user visiting `/sign-in` → Clerk auto-redirects to `/`
- AuthGate: if not signed in → router.push("/sign-in") or Link to /sign-in (no modal)
- Nav mobile Account button: if signed in → `<UserButton />` inline; if not → `<Link href="/sign-in">`
- Header UserButton: always visible (remove `hidden md:flex` restriction on that div)
