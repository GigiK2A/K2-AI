"use client";

import { LogOut, UserCircle2 } from "lucide-react";
import { useKbotAuth } from "@/app/providers";

export function AccountButton({ compact = false }: { compact?: boolean }) {
  const { user, signOut } = useKbotAuth();
  const label = user?.email ?? "Account";

  return (
    <button
      type="button"
      onClick={() => void signOut()}
      className={
        compact
          ? "flex flex-col items-center gap-1 text-[var(--text-soft)]"
          : "inline-flex items-center gap-2 rounded-lg border border-[var(--line)] px-3 py-1.5 text-xs text-[var(--text-soft)] hover:border-[var(--line-strong)]"
      }
      title={`Esci da ${label}`}
    >
      {compact ? <UserCircle2 size={16} /> : <LogOut size={13} />}
      <span>{compact ? "Account" : "Esci"}</span>
    </button>
  );
}
