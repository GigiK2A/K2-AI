import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface BriefMemo {
  id: string;
  subject: string;
  body: string;
  tags: string[] | null;
  created_at: string;
}

interface Props {
  memo: BriefMemo | null;
}

function isToday(iso: string): boolean {
  const d = new Date(iso);
  const now = new Date();
  return (
    d.getFullYear() === now.getFullYear() &&
    d.getMonth() === now.getMonth() &&
    d.getDate() === now.getDate()
  );
}

export function BriefCard({ memo }: Props) {
  if (!memo || !isToday(memo.created_at)) return null;
  return (
    <aside className="mb-3 rounded-xl border border-[color:var(--color-teal)]/40 bg-[color:var(--color-teal)]/5 p-4">
      <div className="mb-2 flex items-center justify-between gap-2">
        <span className="text-[11px] font-semibold uppercase tracking-wider text-[color:var(--color-teal)]">
          Brief mattutino — auto-generato
        </span>
        <span className="text-[11px] text-[color:var(--color-text-muted)]">
          {new Date(memo.created_at).toLocaleTimeString("it-IT", {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </span>
      </div>
      <div className="prose-approval text-sm">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{memo.body}</ReactMarkdown>
      </div>
    </aside>
  );
}
