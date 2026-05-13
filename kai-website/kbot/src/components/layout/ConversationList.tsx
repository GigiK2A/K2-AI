import { Conversation } from "@/types/chat";
import { cx } from "@/lib/utils";

export function ConversationList({
  conversations,
  activeId,
  onSelect,
}: {
  conversations: Conversation[];
  activeId: string;
  onSelect: (id: string) => void;
}) {
  return (
    <div className="space-y-2">
      {conversations.map((c) => (
        <button
          key={c.id}
          onClick={() => onSelect(c.id)}
          className={cx(
            "w-full rounded-xl border px-3 py-2 text-left transition",
            c.id === activeId ? "border-[var(--teal)] bg-[var(--teal-soft)]" : "border-[var(--line)] hover:border-[var(--line-strong)]",
          )}
        >
          <p className="truncate text-sm font-medium">{c.title}</p>
          <p className="text-xs text-[var(--text-muted)]">{c.mode === "lead" ? "Lead" : "Report"}</p>
        </button>
      ))}
    </div>
  );
}
