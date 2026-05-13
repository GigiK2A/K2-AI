import { Menu, Sparkles } from "lucide-react";
import { SignInButton, UserButton } from "@clerk/nextjs";
import Link from "next/link";
import { AIStatusIndicator } from "@/components/ui/AIStatusIndicator";
import { SkillBadge } from "@/components/chat/SkillBadge";

export function ChatLayoutHeader({
  mode,
  usedSkills,
  activeSkills,
  loading,
  onOpenSidebar,
  isSignedIn,
}: {
  mode: "lead" | "report";
  usedSkills: string[];
  activeSkills: string[];
  loading: boolean;
  onOpenSidebar: () => void;
  isSignedIn?: boolean | null;
}) {
  return (
    <header className="sticky top-0 z-20 border-b border-[var(--line)] bg-[rgba(5,5,5,0.82)] px-4 py-3 backdrop-blur">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <button onClick={onOpenSidebar} className="rounded-lg border border-[var(--line)] p-2 lg:hidden"><Menu size={16} /></button>
          <div>
            <p className="text-sm font-semibold">{mode === "lead" ? "Acquisizione clienti" : "Report premium"}</p>
            <AIStatusIndicator online label="Motore Claude operativo" />
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className="hidden items-center gap-2 md:flex">
            <span className="inline-flex items-center gap-1 rounded-full border border-[var(--teal)]/30 bg-[var(--teal)]/10 px-2 py-1 text-xs text-[var(--teal)]">
              <Sparkles size={12} /> Premium
            </span>
            {isSignedIn && (
              <Link href="/dashboard" className="rounded-lg border border-[var(--line)] px-3 py-1.5 text-xs text-[var(--text-soft)] hover:border-[var(--line-strong)]">
                Dashboard
              </Link>
            )}
          </div>
          {isSignedIn ? (
            <UserButton />
          ) : (
            <SignInButton mode="modal">
              <button className="rounded-lg bg-[var(--teal)] px-3 py-1.5 text-xs font-semibold text-black">
                Accedi
              </button>
            </SignInButton>
          )}
        </div>
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        {(loading ? activeSkills : usedSkills).slice(0, 6).map((skill) => <SkillBadge key={skill} name={skill} />)}
        {loading && activeSkills.length > 0 && (
          <span className="rounded-full border border-[var(--teal)] px-2 py-1 text-xs text-[var(--teal)]">In uso ora</span>
        )}
      </div>
    </header>
  );
}
