import { Conversation } from "@/types/chat";
import { cx } from "@/lib/utils";
import { Trash2 } from "lucide-react";

export function ConversationList({
  conversations,
  activeId,
  onSelect,
  onDelete,
}: {
  conversations: Conversation[];
  activeId: string;
  onSelect: (id: string) => void;
  onDelete?: (id: string) => void;
}) {
  return (
    <div className="space-y-2">
      {conversations.map((c) => (
        <div
          key={c.id}
          className={cx(
            "group flex w-full items-center gap-1 rounded-xl border px-3 py-2 transition",
            c.id === activeId
              ? "border-[var(--teal)] bg-[var(--teal-soft)]"
              : "border-[var(--line)] hover:border-[var(--line-strong)]",
          )}
        >
          <button onClick={() => onSelect(c.id)} className="min-w-0 flex-1 text-left">
            <p className="truncate text-sm font-medium">{c.title}</p>
            <p className="text-xs text-[var(--text-muted)]">
              {c.mode === "lead" ? "Lead" : "Report"}
            </p>
          </button>
          {onDelete && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                if (confirm(`Eliminare la chat "${c.title}"?`)) onDelete(c.id);
              }}
              className="flex-shrink-0 rounded-md p-1.5 text-[var(--text-muted)] opacity-0 transition hover:bg-red-500/10 hover:text-red-400 group-hover:opacity-100"
              aria-label="Elimina chat"
              title="Elimina chat"
            >
              <Trash2 size={14} />
            </button>
          )}
        </div>
      ))}
    </div>
  );
}
