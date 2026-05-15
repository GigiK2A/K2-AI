import { requireUser } from "@/lib/auth";
import { apiFetch } from "@/lib/api";
import type { Task } from "@/types/task";
import type { Lead } from "@/types/lead";
import { TasksBoard } from "@/components/tasks/tasks-board";

export const dynamic = "force-dynamic";

export default async function TasksPage() {
  await requireUser();

  const [tasks, leads] = await Promise.all([
    apiFetch<Task[]>("/api/tasks/?limit=500"),
    apiFetch<Lead[]>("/api/leads/?limit=500"),
  ]);

  return (
    <div className="flex flex-col gap-5 p-4 md:p-6 lg:p-8">
      <header className="flex flex-col gap-1">
        <h1 className="font-display text-2xl md:text-3xl">Tasks</h1>
        <p className="text-sm text-[color:var(--color-text-soft)]">
          Cosa c&apos;è da fare oggi, questa settimana, dopo.
        </p>
      </header>

      <TasksBoard initialTasks={tasks} leads={leads} />
    </div>
  );
}
