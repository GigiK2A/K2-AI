"use client";

import { useEffect, useState } from "react";
import { X, Trash2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/lib/api-client";
import type {
  Task,
  TaskCreatePayload,
  TaskPriority,
  TaskStatus,
  TaskUpdatePayload,
} from "@/types/task";
import type { Lead } from "@/types/lead";
import {
  TASK_PRIORITY_LABELS,
  TASK_PRIORITY_ORDER,
  TASK_STATUS_LABELS,
} from "@/lib/tasks";

interface BaseProps {
  open: boolean;
  onClose: () => void;
  onSaved: (task: Task) => void;
  onDeleted?: (id: string) => void;
  leads: Lead[];
}

interface EditProps extends BaseProps {
  mode: "edit";
  task: Task;
}

interface CreateProps extends BaseProps {
  mode: "create";
  task?: undefined;
}

type Props = EditProps | CreateProps;

interface FormState {
  title: string;
  notes: string;
  priority: TaskPriority;
  status: TaskStatus;
  due_at: string;
  lead_id: string;
}

function isoToLocalInput(iso: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function localInputToIso(local: string): string | null {
  if (!local) return null;
  const d = new Date(local);
  return Number.isNaN(d.getTime()) ? null : d.toISOString();
}

function initialFrom(task: Task | undefined): FormState {
  return {
    title: task?.title ?? "",
    notes: task?.notes ?? "",
    priority: task?.priority ?? "media",
    status: task?.status ?? "todo",
    due_at: isoToLocalInput(task?.due_at ?? null),
    lead_id: task?.lead_id ?? "",
  };
}

const STATUSES: TaskStatus[] = ["todo", "doing", "done", "cancelled"];

export function TaskDrawer(props: Props) {
  const { open, onClose, onSaved, onDeleted, leads, mode } = props;
  const task = mode === "edit" ? props.task : undefined;

  const [form, setForm] = useState<FormState>(() => initialFrom(task));
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setForm(initialFrom(task));
      setError(null);
    }
  }, [open, task]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  function update<K extends keyof FormState>(k: K, v: FormState[K]) {
    setForm((f) => ({ ...f, [k]: v }));
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!form.title.trim()) {
      setError("Il titolo è obbligatorio");
      return;
    }
    setSaving(true);
    try {
      const payload: TaskCreatePayload & TaskUpdatePayload = {
        title: form.title.trim(),
        notes: form.notes.trim() || null,
        priority: form.priority,
        status: form.status,
        due_at: localInputToIso(form.due_at),
        lead_id: form.lead_id || null,
      };
      // ensure completed_at consistency
      if (form.status === "done") {
        payload.completed_at = task?.completed_at ?? new Date().toISOString();
      } else if (task?.completed_at) {
        payload.completed_at = null;
      }

      let saved: Task;
      if (mode === "edit" && task) {
        saved = await apiClient<Task>(`/api/tasks/${task.id}`, {
          method: "PATCH",
          body: JSON.stringify(payload),
        });
      } else {
        saved = await apiClient<Task>(`/api/tasks/`, {
          method: "POST",
          body: JSON.stringify(payload),
        });
      }
      onSaved(saved);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Errore di salvataggio");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (mode !== "edit" || !task) return;
    if (!window.confirm("Eliminare definitivamente questo task?")) return;
    setDeleting(true);
    setError(null);
    try {
      await apiClient<void>(`/api/tasks/${task.id}`, { method: "DELETE" });
      onDeleted?.(task.id);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Errore di eliminazione");
    } finally {
      setDeleting(false);
    }
  }

  const title = mode === "edit" ? "Modifica task" : "Nuovo task";

  return (
    <div className="fixed inset-0 z-50">
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden
      />
      <aside
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className="absolute right-0 top-0 flex h-full w-full flex-col border-l border-[color:var(--color-line)] bg-[color:var(--color-bg)] shadow-2xl md:w-[480px]"
      >
        <header className="flex items-center justify-between border-b border-[color:var(--color-line)] px-5 py-4">
          <div>
            <h2 className="font-display text-xl">{title}</h2>
            {mode === "edit" && task && (
              <p className="text-[11px] text-[color:var(--color-text-muted)]">
                ID {task.id.slice(0, 8)}
              </p>
            )}
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Chiudi"
            className="rounded-md p-1 text-[color:var(--color-text-soft)] hover:bg-[color:var(--color-bg-elevated)] hover:text-[color:var(--color-text)]"
          >
            <X className="h-5 w-5" />
          </button>
        </header>

        <form
          onSubmit={handleSave}
          className="flex flex-1 flex-col gap-4 overflow-y-auto px-5 py-5"
        >
          <Field label="Titolo" required>
            <Input
              value={form.title}
              onChange={(e) => update("title", e.target.value)}
              placeholder="Es. Richiamare Studio Rossi"
              required
            />
          </Field>

          <Field label="Note">
            <textarea
              value={form.notes}
              onChange={(e) => update("notes", e.target.value)}
              rows={4}
              className="w-full rounded-lg border border-[color:var(--color-line-strong)] bg-[color:var(--color-bg-soft)] px-3 py-2 text-sm placeholder:text-[color:var(--color-text-muted)] focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[color:var(--color-teal)]"
              placeholder="Dettagli liberi"
            />
          </Field>

          <div className="grid grid-cols-2 gap-3">
            <Field label="Priorità">
              <Select
                value={form.priority}
                onChange={(v) => update("priority", v as TaskPriority)}
                options={TASK_PRIORITY_ORDER.map((p) => ({
                  value: p,
                  label: TASK_PRIORITY_LABELS[p],
                }))}
              />
            </Field>
            <Field label="Stato">
              <Select
                value={form.status}
                onChange={(v) => update("status", v as TaskStatus)}
                options={STATUSES.map((s) => ({
                  value: s,
                  label: TASK_STATUS_LABELS[s],
                }))}
              />
            </Field>
          </div>

          <Field label="Scadenza">
            <input
              type="datetime-local"
              value={form.due_at}
              onChange={(e) => update("due_at", e.target.value)}
              className="h-10 w-full rounded-lg border border-[color:var(--color-line-strong)] bg-[color:var(--color-bg-soft)] px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[color:var(--color-teal)]"
            />
          </Field>

          <Field label="Lead collegato">
            <Select
              value={form.lead_id}
              onChange={(v) => update("lead_id", v)}
              options={[
                { value: "", label: "— Nessuno —" },
                ...leads.map((l) => ({ value: l.id, label: l.title })),
              ]}
            />
          </Field>

          {error && (
            <div className="rounded-lg border border-[color:var(--color-danger)]/50 bg-[color:var(--color-danger)]/10 px-3 py-2 text-xs text-[color:var(--color-danger)]">
              {error}
            </div>
          )}

          <div className="sticky bottom-0 -mx-5 -mb-5 mt-auto flex flex-wrap items-center justify-between gap-2 border-t border-[color:var(--color-line)] bg-[color:var(--color-bg)] px-5 py-3">
            <div className="flex gap-2">
              {mode === "edit" && (
                <Button
                  type="button"
                  variant="danger"
                  size="sm"
                  onClick={handleDelete}
                  disabled={deleting}
                >
                  <Trash2 className="h-4 w-4" />
                  {deleting ? "…" : "Elimina"}
                </Button>
              )}
            </div>
            <div className="flex gap-2">
              <Button type="button" variant="ghost" size="sm" onClick={onClose}>
                Annulla
              </Button>
              <Button type="submit" size="sm" disabled={saving}>
                {saving ? "Salvo…" : "Salva"}
              </Button>
            </div>
          </div>
        </form>
      </aside>
    </div>
  );
}

function Field({
  label,
  required,
  children,
}: {
  label: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <label className="flex flex-col gap-1.5">
      <span className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[color:var(--color-text-muted)]">
        {label}
        {required && <span className="text-[color:var(--color-danger)]"> *</span>}
      </span>
      {children}
    </label>
  );
}

function Select({
  value,
  onChange,
  options,
}: {
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="h-10 w-full rounded-lg border border-[color:var(--color-line-strong)] bg-[color:var(--color-bg-soft)] px-3 text-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[color:var(--color-teal)]"
    >
      {options.map((o) => (
        <option key={o.value} value={o.value}>
          {o.label}
        </option>
      ))}
    </select>
  );
}
