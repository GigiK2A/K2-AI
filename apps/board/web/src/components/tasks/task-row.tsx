"use client";

import { Check, Calendar, ExternalLink } from "lucide-react";
import type { Task } from "@/types/task";
import type { Lead } from "@/types/lead";
import { TASK_PRIORITY_DOT, TASK_PRIORITY_LABELS } from "@/lib/tasks";
import { formatRelativeDay } from "@/lib/format";
import Link from "next/link";

interface Props {
  task: Task;
  lead: Lead | null;
  onOpen: (task: Task) => void;
  onToggleDone: (task: Task) => void;
  busy?: boolean;
}

export function TaskRow({ task, lead, onOpen, onToggleDone, busy }: Props) {
  const done = task.status === "done";
  const overdue =
    !done &&
    task.due_at != null &&
    new Date(task.due_at).getTime() < Date.now() - 5 * 60_000;

  return (
    <div
      className={
        "group flex items-center gap-2 rounded-lg border border-[color:var(--color-line)] bg-[color:var(--color-bg-elevated)] px-3 py-2 transition-colors hover:border-[color:var(--color-line-strong)] " +
        (busy ? "opacity-60" : "")
      }
    >
      <button
        type="button"
        aria-label={done ? "Riapri task" : "Segna come fatto"}
        onClick={(e) => {
          e.stopPropagation();
          onToggleDone(task);
        }}
        disabled={busy}
        className={
          "flex h-5 w-5 shrink-0 items-center justify-center rounded-md border transition-colors " +
          (done
            ? "border-[color:var(--color-success)] bg-[color:var(--color-success)]/20 text-[color:var(--color-success)]"
            : "border-[color:var(--color-line-strong)] hover:border-[color:var(--color-teal)]")
        }
      >
        {done && <Check className="h-3 w-3" />}
      </button>

      <span
        className={
          "inline-block h-2 w-2 shrink-0 rounded-full " +
          TASK_PRIORITY_DOT[task.priority]
        }
        title={TASK_PRIORITY_LABELS[task.priority]}
      />

      <button
        type="button"
        onClick={() => onOpen(task)}
        className="flex flex-1 items-center gap-2 truncate text-left text-sm"
      >
        <span
          className={
            "truncate " +
            (done
              ? "text-[color:var(--color-text-muted)] line-through"
              : "text-[color:var(--color-text)]")
          }
        >
          {task.title}
        </span>
      </button>

      {task.due_at && (
        <span
          className={
            "flex shrink-0 items-center gap-1 text-[11px] " +
            (overdue
              ? "text-[color:var(--color-danger)]"
              : "text-[color:var(--color-text-soft)]")
          }
        >
          <Calendar className="h-3 w-3" />
          {formatRelativeDay(task.due_at)}
        </span>
      )}

      {lead && (
        <Link
          href="/pipeline"
          onClick={(e) => e.stopPropagation()}
          title={lead.title}
          className="hidden shrink-0 items-center gap-1 text-[11px] text-[color:var(--color-teal)] hover:underline md:inline-flex"
        >
          <ExternalLink className="h-3 w-3" />
          lead
        </Link>
      )}
    </div>
  );
}
