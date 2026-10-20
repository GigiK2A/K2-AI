import { FileText, Menu } from "lucide-react";
import Link from "next/link";
import { AccountButton } from "@/components/auth/AccountButton";
import { ThemeToggle } from "@/components/ui/ThemeToggle";

export function ChatLayoutHeader({
  titolo,
  sottotitolo,
  onOpenSidebar,
  onOpenPannello,
  schedeConContenuto,
  isSignedIn,
}: {
  titolo: string;
  sottotitolo?: string;
  onOpenSidebar: () => void;
  /** Solo telefono: apre la pratica (bozza, documenti, fatti, fonti) a tutto schermo. */
  onOpenPannello: () => void;
  schedeConContenuto: number;
  isSignedIn?: boolean | null;
}) {
  return (
    <header className="flex items-center gap-2 border-b border-[var(--line)] bg-[var(--bg-1)] px-3 py-2.5">
      <button onClick={onOpenSidebar} className="rounded-md p-2 text-[var(--text-soft)] lg:hidden" aria-label="Apri le pratiche">
        <Menu size={18} />
      </button>
      <div className="min-w-0 flex-1">
        <p className="font-doc truncate text-base font-semibold">{titolo}</p>
        {sottotitolo && <p className="truncate text-xs text-[var(--text-muted)]">{sottotitolo}</p>}
      </div>
      <button
        onClick={onOpenPannello}
        className="inline-flex items-center gap-1.5 rounded-lg border border-[var(--line-strong)] px-2.5 py-1.5 text-xs font-medium xl:hidden"
      >
        <FileText size={14} /> Pratica
        {schedeConContenuto > 0 && (
          <span className="rounded-full bg-[var(--teal)] px-1.5 text-[11px] text-[var(--on-accent)]">{schedeConContenuto}</span>
        )}
      </button>
      <ThemeToggle />
      {isSignedIn ? (
        <AccountButton />
      ) : (
        <Link href="/sign-in" className="rounded-lg bg-[var(--teal)] px-3 py-1.5 text-xs font-semibold text-[var(--on-accent)]">
          Accedi
        </Link>
      )}
    </header>
  );
}
