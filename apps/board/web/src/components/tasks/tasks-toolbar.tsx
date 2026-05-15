"use client";

import { Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import type { TaskPriority } from "@/types/task";
import { TASK_PRIORITY_LABELS, TASK_PRIORITY_ORDER } from "@/lib/tasks";

export type TaskSortKey = "due" | "created";

const SORT_LABELS: Record<TaskSortKey, string> = {
  due: "Scadenza",
  created: "Creazione",
};

interface Props {
  search: string;
  onSearch: (s: string) => void;
  priorities: Set<TaskPriority>;
  onTogglePriority: (p: TaskPriority) => void;
  sort: TaskSortKey;
  onSort: (s: TaskSortKey) => void;
  onNewTask: () => void;
}

export function TasksToolbar({
  search,
  onSearch,
  priorities,
  onTogglePriority,
  sort,
  onSort,
  onNewTask,
}: Props) {
  return (
    <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
      <div className="flex flex-1 flex-col gap-3 lg:flex-row lg:items-center">
        <div className="relative w-full lg:max-w-xs">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[color:var(--color-text-muted)]" />
          <Input
            value={search}
            onChange={(e) => onSearch(e.target.value)}
            placeholder="Cerca task"
            className="pl-9"
          />
        </div>

        <div className="flex flex-wrap gap-2">
          {TASK_PRIORITY_ORDER.map((p) => {
            const active = priorities.has(p);
            return (
              <button
                key={p}
                type="button"
                onClick={() => onTogglePriority(p)}
                className={
                  "rounded-full border px-3 py-1 text-xs font-medium transition-colors " +
                  (active
                    ? "border-[color:var(--color-teal)] bg-[color:var(--color-teal)]/10 text-[color:var(--color-teal)]"
                    : "border-[color:var(--color-line-strong)] text-[color:var(--color-text-soft)] hover:text-[color:var(--color-text)]")
                }
              >
                {TASK_PRIORITY_LABELS[p]}
              </button>
            );
          })}
        </div>
      </div>

      <div className="flex items-center gap-2">
        <label className="text-xs uppercase tracking-[0.18em] text-[color:var(--color-text-muted)]">
          Ordina
        </label>
        <select
          value={sort}
          onChange={(e) => onSort(e.target.value as TaskSortKey)}
          className="h-9 rounded-lg border border-[color:var(--color-line-strong)] bg-[color:var(--color-bg-soft)] px-2 text-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[color:var(--color-teal)]"
        >
          {(Object.keys(SORT_LABELS) as TaskSortKey[]).map((k) => (
            <option key={k} value={k}>
              {SORT_LABELS[k]}
            </option>
          ))}
        </select>
        <button
          type="button"
          onClick={onNewTask}
          className="inline-flex h-9 items-center gap-1 rounded-lg bg-[color:var(--color-teal)] px-3 text-sm font-medium text-black transition-colors hover:bg-[color:var(--color-teal-soft)]"
        >
          + Nuovo task
        </button>
      </div>
    </div>
  );
}
