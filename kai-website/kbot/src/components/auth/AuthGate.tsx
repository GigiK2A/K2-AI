"use client";

import Link from "next/link";
import { useKbotAuth } from "@/app/providers";

export function AuthGate({ children }: { children: React.ReactNode }) {
  const { loading, isSignedIn } = useKbotAuth();

  if (loading) {
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
        <div className="flex flex-col gap-2">
          <Link href="/app/sign-in" className="w-full rounded-xl bg-[var(--teal)] py-3 text-center text-sm font-semibold text-black">
            Accedi
          </Link>
          <Link href="/app/sign-up" className="w-full rounded-xl border border-[var(--line)] py-3 text-center text-sm font-semibold text-[var(--text-main)]">
            Crea account
          </Link>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
