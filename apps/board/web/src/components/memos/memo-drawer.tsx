"use client";

import { useEffect, useState } from "react";
import { X, Trash2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/lib/api-client";
import type { Memo, MemoCreatePayload, MemoUpdatePayload } from "@/types/memo";
import type { Contact, Lead } from "@/types/lead";
import { parseTagsInput } from "@/lib/memos";

interface BaseProps {
  open: boolean;
  onClose: () => void;
  onSaved: (memo: Memo) => void;
  onDeleted?: (id: string) => void;
  leads: Lead[];
  contacts: Contact[];
}

interface EditProps extends BaseProps {
  mode: "edit";
  memo: Memo;
}

interface CreateProps extends BaseProps {
  mode: "create";
  memo?: undefined;
}

type Props = EditProps | CreateProps;

interface FormState {
  subject: string;
  body: string;
  tags: string;
  contact_id: string;
  lead_id: string;
}

function initialFrom(memo: Memo | undefined): FormState {
  return {
    subject: memo?.subject ?? "",
    body: memo?.body ?? "",
    tags: memo?.tags?.join(", ") ?? "",
    contact_id: memo?.contact_id ?? "",
    lead_id: memo?.lead_id ?? "",
  };
}

export function MemoDrawer(props: Props) {
  const { open, onClose, onSaved, onDeleted, leads, contacts, mode } = props;
  const memo = mode === "edit" ? props.memo : undefined;

  const [form, setForm] = useState<FormState>(() => initialFrom(memo));
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setForm(initialFrom(memo));
      setError(null);
    }
  }, [open, memo]);

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
    if (!form.subject.trim()) {
      setError("Il titolo è obbligatorio");
      return;
    }
    setSaving(true);
    try {
      const payload: MemoCreatePayload & MemoUpdatePayload = {
        subject: form.subject.trim(),
        body: form.body,
        tags: parseTagsInput(form.tags),
        contact_id: form.contact_id || null,
        lead_id: form.lead_id || null,
      };
      let saved: Memo;
      if (mode === "edit" && memo) {
        saved = await apiClient<Memo>(`/api/memos/${memo.id}`, {
          method: "PATCH",
          body: JSON.stringify(payload),
        });
      } else {
        saved = await apiClient<Memo>(`/api/memos/`, {
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
    if (mode !== "edit" || !memo) return;
    if (!window.confirm("Eliminare definitivamente questo memo?")) return;
    setDeleting(true);
    setError(null);
    try {
      await apiClient<void>(`/api/memos/${memo.id}`, { method: "DELETE" });
      onDeleted?.(memo.id);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Errore di eliminazione");
    } finally {
      setDeleting(false);
    }
  }

  const title = mode === "edit" ? "Modifica memo" : "Nuovo memo";

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
        className="absolute right-0 top-0 flex h-full w-full flex-col border-l border-[color:var(--color-line)] bg-[color:var(--color-bg)] shadow-2xl md:w-[520px]"
      >
        <header className="flex items-center justify-between border-b border-[color:var(--color-line)] px-5 py-4">
          <div>
            <h2 className="font-display text-xl">{title}</h2>
            {mode === "edit" && memo && (
              <p className="text-[11px] text-[color:var(--color-text-muted)]">
                ID {memo.id.slice(0, 8)}
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
              value={form.subject}
              onChange={(e) => update("subject", e.target.value)}
              placeholder="Es. Incontro Studio Bianchi — appunti"
              required
            />
          </Field>

          <Field label="Corpo (markdown)">
            <textarea
              value={form.body}
              onChange={(e) => update("body", e.target.value)}
              rows={12}
              className="w-full rounded-lg border border-[color:var(--color-line-strong)] bg-[color:var(--color-bg-soft)] px-3 py-2 font-mono text-[13px] placeholder:text-[color:var(--color-text-muted)] focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[color:var(--color-teal)]"
              placeholder="Scrivi qui le tue note…"
            />
          </Field>

          <Field label="Tag (separati da virgola)">
            <Input
              value={form.tags}
              onChange={(e) => update("tags", e.target.value)}
              placeholder="es. cliente, automazione, urgente"
            />
          </Field>

          <div className="grid grid-cols-2 gap-3">
            <Field label="Contatto">
              <Select
                value={form.contact_id}
                onChange={(v) => update("contact_id", v)}
                options={[
                  { value: "", label: "— Nessuno —" },
                  ...contacts.map((c) => ({
                    value: c.id,
                    label:
                      c.company || c.person_name || c.email || c.id.slice(0, 8),
                  })),
                ]}
              />
            </Field>
            <Field label="Lead">
              <Select
                value={form.lead_id}
                onChange={(v) => update("lead_id", v)}
                options={[
                  { value: "", label: "— Nessuno —" },
                  ...leads.map((l) => ({ value: l.id, label: l.title })),
                ]}
              />
            </Field>
          </div>

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
