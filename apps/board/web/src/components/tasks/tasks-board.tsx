"use client";

import { useMemo, useState } from "react";
import type { Task, TaskPriority } from "@/types/task";
import type { Lead } from "@/types/lead";
import { apiClient } from "@/lib/api-client";
import {
  TASK_COLUMN_LABELS,
  TASK_PRIORITY_RANK,
  columnForTask,
  type TaskColumnKey,
} from "@/lib/tasks";
import { TasksToolbar, type TaskSortKey } from "./tasks-toolbar";
import { TaskRow } from "./task-row";
import { TaskDrawer } from "./task-drawer";
import { ChevronDown, ChevronRight } from "lucide-react";

interface Props {
  initialTasks: Task[];
  leads: Lead[];
}

type DrawerState =
  | { mode: "edit"; task: Task }
  | { mode: "create" }
  | null;

const COLUMNS: TaskColumnKey[] = ["today", "week", "backlog", "done"];

export function TasksBoard({ initialTasks, leads }: Props) {
  const [tasks, setTasks] = useState<Task[]>(initialTasks);
  const [drawer, setDrawer] = useState<DrawerState>(null);
  const [search, setSearch] = useState("");
  const [priorities, setPriorities] = useState<Set<TaskPriority>>(new Set());
  const [sort, setSort] = useState<TaskSortKey>("due");
  const [busyIds, setBusyIds] = useState<Set<string>>(new Set());
  const [error, setError] = useState<string | null>(null);
  const [doneCollapsed, setDoneCollapsed] = useState(true);

  const leadsById = useMemo(() => {
    const m = new Map<string, Lead>();
    for (const l of leads) m.set(l.id, l);
    return m;
  }, [leads]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return tasks.filter((t) => {
      if (priorities.size > 0 && !priorities.has(t.priority)) return false;
      if (q && !t.title.toLowerCase().includes(q)) return false;
      return true;
    });
  }, [tasks, search, priorities]);

  const grouped = useMemo(() => {
    const groups: Record<TaskColumnKey, Task[]> = {
      today: [],
      week: [],
      backlog: [],
      done: [],
    };
    for (const t of filtered) {
      const col = columnForTask(t);
      if (col) groups[col].push(t);
    }
    const sortFn = (a: Task, b: Task) => {
      if (sort === "due") {
        const av = a.due_at ? new Date(a.due_at).getTime() : Infinity;
        const bv = b.due_at ? new Date(b.due_at).getTime() : Infinity;
        if (av !== bv) return av - bv;
        return TASK_PRIORITY_RANK[a.priority] - TASK_PRIORITY_RANK[b.priority];
      }
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
    };
    for (const c of COLUMNS) groups[c].sort(sortFn);
    return groups;
  }, [filtered, sort]);

  function togglePriority(p: TaskPriority) {
    setPriorities((prev) => {
      const next = new Set(prev);
      if (next.has(p)) next.delete(p);
      else next.add(p);
      return next;
    });
  }

  function setBusy(id: string, on: boolean) {
    setBusyIds((curr) => {
      const next = new Set(curr);
      if (on) next.add(id);
      else next.delete(id);
      return next;
    });
  }

  function applyUpdate(updated: Task) {
    setTasks((curr) => {
      const idx = curr.findIndex((t) => t.id === updated.id);
      if (idx === -1) return [updated, ...curr];
      const next = [...curr];
      next[idx] = updated;
      return next;
    });
  }

  async function handleToggleDone(task: Task) {
    const nowDone = task.status !== "done";
    const optimistic: Task = {
      ...task,
      status: nowDone ? "done" : "todo",
      completed_at: nowDone ? new Date().toISOString() : null,
    };
    applyUpdate(optimistic);
    setBusy(task.id, true);
    setError(null);
    try {
      const saved = await apiClient<Task>(`/api/tasks/${task.id}`, {
        method: "PATCH",
        body: JSON.stringify({
          status: optimistic.status,
          completed_at: optimistic.completed_at,
        }),
      });
      applyUpdate(saved);
    } catch (err) {
      applyUpdate(task);
      setError(err instanceof Error ? err.message : "Errore aggiornamento task");
    } finally {
      setBusy(task.id, false);
    }
  }

  function handleSaved(task: Task) {
    applyUpdate(task);
  }

  function handleDeleted(id: string) {
    setTasks((curr) => curr.filter((t) => t.id !== id));
  }

  return (
    <div className="flex flex-col gap-4">
      <TasksToolbar
        search={search}
        onSearch={setSearch}
        priorities={priorities}
        onTogglePriority={togglePriority}
        sort={sort}
        onSort={setSort}
        onNewTask={() => setDrawer({ mode: "create" })}
      />

      {error && (
        <div className="flex items-center justify-between rounded-lg border border-[color:var(--color-danger)]/50 bg-[color:var(--color-danger)]/10 px-3 py-2 text-xs text-[color:var(--color-danger)]">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="underline">
            Chiudi
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
        {COLUMNS.map((col) => {
          const items = grouped[col];
          const isDone = col === "done";
          const collapsed = isDone && doneCollapsed;
          return (
            <div
              key={col}
              className="flex flex-col rounded-2xl border border-[color:var(--color-line)] bg-[color:var(--color-bg-soft)]"
            >
              <button
                type="button"
                onClick={() => isDone && setDoneCollapsed((v) => !v)}
                className={
                  "flex items-center justify-between border-b border-[color:var(--color-line)] px-4 py-3 text-left " +
                  (isDone ? "cursor-pointer hover:bg-[color:var(--color-bg-elevated)]" : "cursor-default")
                }
              >
                <div className="flex items-center gap-2">
                  {isDone &&
                    (collapsed ? (
                      <ChevronRight className="h-4 w-4 text-[color:var(--color-text-muted)]" />
                    ) : (
                      <ChevronDown className="h-4 w-4 text-[color:var(--color-text-muted)]" />
                    ))}
                  <h2 className="text-sm font-semibold">{TASK_COLUMN_LABELS[col]}</h2>
                </div>
                <span className="rounded-full bg-[color:var(--color-bg-elevated)] px-2 py-0.5 text-[11px] font-medium text-[color:var(--color-text-soft)]">
                  {items.length}
                </span>
              </button>

              {!collapsed && (
                <div className="flex flex-1 flex-col gap-2 p-3">
                  {items.length === 0 && (
                    <div className="rounded-lg border border-dashed border-[color:var(--color-line)] p-4 text-center text-xs text-[color:var(--color-text-muted)]">
                      Nessuno
                    </div>
                  )}
                  {items.map((t) => (
                    <TaskRow
                      key={t.id}
                      task={t}
                      lead={t.lead_id ? leadsById.get(t.lead_id) ?? null : null}
                      onOpen={(task) => setDrawer({ mode: "edit", task })}
                      onToggleDone={handleToggleDone}
                      busy={busyIds.has(t.id)}
                    />
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {drawer?.mode === "edit" && (
        <TaskDrawer
          mode="edit"
          open
          task={drawer.task}
          leads={leads}
          onClose={() => setDrawer(null)}
          onSaved={handleSaved}
          onDeleted={handleDeleted}
        />
      )}
      {drawer?.mode === "create" && (
        <TaskDrawer
          mode="create"
          open
          leads={leads}
          onClose={() => setDrawer(null)}
          onSaved={handleSaved}
        />
      )}
    </div>
  );
}
