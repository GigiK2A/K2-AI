import { Plus, UserRound, X } from "lucide-react";
import Link from "next/link";
import { Conversation } from "@/types/chat";
import { ConversationList } from "@/components/layout/ConversationList";

/** Elenco delle pratiche. Su computer sta sempre a sinistra, su telefono è un menu a scomparsa. */
export function Sidebar({
  open,
  conversations,
  activeId,
  onSelect,
  onNew,
  onDelete,
  onRename,
  onClose,
}: {
  open: boolean;
  conversations: Conversation[];
  activeId: string;
  onSelect: (id: string) => void;
  onNew: () => void;
  onDelete?: (id: string) => void;
  onRename?: (id: string, title: string) => void;
  onClose: () => void;
}) {
  return (
    <>
      {open && (
        <div
          className="fixed inset-0 z-30 bg-black/30 lg:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}
      <aside
        aria-label="Pratiche"
        className={
          "fixed inset-y-0 left-0 z-40 flex w-[280px] flex-col border-r border-[var(--line)] bg-[var(--bg-2)] p-3 transition-transform lg:static lg:w-[240px] lg:translate-x-0 " +
          (open ? "translate-x-0" : "-translate-x-full")
        }
      >
        <div className="flex items-center justify-between px-2 py-1">
          <p className="text-base font-semibold tracking-tight">K-BOT</p>
          <button onClick={onClose} className="rounded-md p-1.5 text-[var(--text-soft)] lg:hidden" aria-label="Chiudi il menu">
            <X size={16} />
          </button>
        </div>

        <button
          onClick={() => { onNew(); onClose(); }}
          className="mt-3 flex w-full items-center gap-2 rounded-lg border border-[var(--line-strong)] bg-[var(--bg-1)] px-3 py-2 text-sm font-medium hover:border-[var(--teal)]"
        >
          <Plus size={15} /> Nuova pratica
        </button>

        <p className="mb-1 mt-5 px-3 text-xs text-[var(--text-muted)]">Le tue pratiche</p>
        <div className="scroll-premium min-h-0 flex-1 overflow-y-auto">
          <ConversationList
            conversations={conversations}
            activeId={activeId}
            onSelect={(id) => { onSelect(id); onClose(); }}
            onDelete={onDelete}
            onRename={onRename}
          />
        </div>

        <Link
          href="/dashboard"
          className="mt-2 flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-[var(--text-soft)] hover:bg-[var(--bg-1)]"
        >
          <UserRound size={15} /> Account e crediti
        </Link>
      </aside>
    </>
  );
}
