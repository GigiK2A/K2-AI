import type { Task, TaskPriority, TaskStatus } from "@/types/task";

export const TASK_PRIORITY_ORDER: TaskPriority[] = ["alta", "media", "bassa"];

export const TASK_PRIORITY_LABELS: Record<TaskPriority, string> = {
  alta: "Alta",
  media: "Media",
  bassa: "Bassa",
};

export const TASK_PRIORITY_DOT: Record<TaskPriority, string> = {
  alta: "bg-[color:var(--color-danger)]",
  media: "bg-amber-500",
  bassa: "bg-[color:var(--color-text-muted)]",
};

export const TASK_PRIORITY_RANK: Record<TaskPriority, number> = {
  alta: 0,
  media: 1,
  bassa: 2,
};

export const TASK_STATUS_LABELS: Record<TaskStatus, string> = {
  todo: "Da fare",
  doing: "In corso",
  done: "Fatto",
  cancelled: "Annullato",
};

export type TaskColumnKey = "today" | "week" | "backlog" | "done";

export const TASK_COLUMN_LABELS: Record<TaskColumnKey, string> = {
  today: "Oggi e scaduti",
  week: "Settimana",
  backlog: "Backlog",
  done: "Fatti",
};

function startOfDay(d: Date): Date {
  return new Date(d.getFullYear(), d.getMonth(), d.getDate());
}

export function columnForTask(task: Task, now: Date = new Date()): TaskColumnKey | null {
  if (task.status === "cancelled") return null;
  if (task.status === "done") {
    if (!task.completed_at) return "done";
    const completed = new Date(task.completed_at);
    const diffDays = (now.getTime() - completed.getTime()) / 86_400_000;
    return diffDays <= 7 ? "done" : null;
  }
  if (!task.due_at) return "backlog";
  const due = startOfDay(new Date(task.due_at));
  const today = startOfDay(now);
  const diffDays = Math.round((due.getTime() - today.getTime()) / 86_400_000);
  if (diffDays <= 0) return "today";
  if (diffDays <= 7) return "week";
  return "backlog";
}
