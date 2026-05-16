import Link from "next/link";
import { Plus, MessageSquare } from "lucide-react";
import type { AgentConversationSummary } from "@/types/agent";

interface ConversationsSidebarProps {
  conversations: AgentConversationSummary[];
  activeId?: string;
}

function formatWhen(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleDateString("it-IT", { day: "2-digit", month: "short" });
  } catch {
    return "";
  }
}

export function ConversationsSidebar({ conversations, activeId }: ConversationsSidebarProps) {
  return (
    <aside className="hidden lg:flex w-[240px] shrink-0 flex-col gap-2 border-r border-[color:var(--color-line)] py-4 pr-4">
      <div className="mb-1 flex items-center justify-between px-2">
        <h2 className="text-xs font-semibold uppercase tracking-wide text-[color:var(--color-text-muted)]">
          Conversazioni
        </h2>
        <Link
          href="/agente"
          className="inline-flex h-7 w-7 items-center justify-center rounded-md text-[color:var(--color-text-soft)] hover:bg-[color:var(--color-bg-elevated)] hover:text-[color:var(--color-teal)]"
          title="Nuova conversazione"
        >
          <Plus size={14} />
        </Link>
      </div>
      {conversations.length === 0 ? (
        <p className="px-2 text-xs text-[color:var(--color-text-muted)]">
          Nessuna conversazione ancora.
        </p>
      ) : (
        <ul className="flex flex-col gap-0.5">
          {conversations.map(c => {
            const active = c.id === activeId;
            return (
              <li key={c.id}>
                <Link
                  href={`/agente?c=${c.id}`}
                  className={`group flex items-start gap-2 rounded-md px-2 py-1.5 text-xs transition-colors ${
                    active
                      ? "bg-[color:var(--color-bg-elevated)] text-[color:var(--color-text)]"
                      : "text-[color:var(--color-text-soft)] hover:bg-[color:var(--color-bg-elevated)] hover:text-[color:var(--color-text)]"
                  }`}
                >
                  <MessageSquare size={12} className="mt-0.5 shrink-0 text-[color:var(--color-text-muted)]" />
                  <span className="flex-1 truncate">{c.title || "(senza titolo)"}</span>
                  <span className="shrink-0 text-[10px] text-[color:var(--color-text-muted)]">
                    {formatWhen(c.updated_at)}
                  </span>
                </Link>
              </li>
            );
          })}
        </ul>
      )}
    </aside>
  );
}
