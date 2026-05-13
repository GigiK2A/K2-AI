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
        <Link
          href="/sign-in"
          className="block w-full rounded-xl bg-[var(--teal)] py-3 text-center text-sm font-semibold text-black"
        >
          Accedi o registrati
        </Link>
      </div>
    );
  }

  return <>{children}</>;
}
