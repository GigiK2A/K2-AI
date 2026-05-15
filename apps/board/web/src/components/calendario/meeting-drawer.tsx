"use client";

import { useEffect, useState } from "react";
import { X, Trash2, ExternalLink } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/lib/api-client";
import type {
  Meeting,
  MeetingCreatePayload,
  MeetingUpdatePayload,
} from "@/types/meeting";
import type { Contact, Lead } from "@/types/lead";

interface BaseProps {
  open: boolean;
  onClose: () => void;
  onSaved: (meeting: Meeting) => void;
  onDeleted?: (id: string) => void;
  leads: Lead[];
  contacts: Contact[];
}

interface EditProps extends BaseProps {
  mode: "edit";
  meeting: Meeting;
}

interface CreateProps extends BaseProps {
  mode: "create";
  meeting?: undefined;
}

type Props = EditProps | CreateProps;

interface FormState {
  title: string;
  description: string;
  starts_at: string;
  ends_at: string;
  location: string;
  meet_link: string;
  contact_id: string;
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

function initialFrom(m: Meeting | undefined): FormState {
  return {
    title: m?.title ?? "",
    description: m?.description ?? "",
    starts_at: isoToLocalInput(m?.starts_at ?? null),
    ends_at: isoToLocalInput(m?.ends_at ?? null),
    location: m?.location ?? "",
    meet_link: m?.meet_link ?? "",
    contact_id: m?.contact_id ?? "",
    lead_id: m?.lead_id ?? "",
  };
}

export function MeetingDrawer(props: Props) {
  const { open, onClose, onSaved, onDeleted, leads, contacts, mode } = props;
  const meeting = mode === "edit" ? props.meeting : undefined;

  const [form, setForm] = useState<FormState>(() => initialFrom(meeting));
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setForm(initialFrom(meeting));
      setError(null);
    }
  }, [open, meeting]);

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
    const startsIso = localInputToIso(form.starts_at);
    const endsIso = localInputToIso(form.ends_at);
    if (!startsIso || !endsIso) {
      setError("Inizio e fine sono obbligatori");
      return;
    }
    setSaving(true);
    try {
      const payload: MeetingCreatePayload & MeetingUpdatePayload = {
        title: form.title.trim(),
        description: form.description.trim() || null,
        starts_at: startsIso,
        ends_at: endsIso,
        location: form.location.trim() || null,
        meet_link: form.meet_link.trim() || null,
        contact_id: form.contact_id || null,
        lead_id: form.lead_id || null,
      };
      let saved: Meeting;
      if (mode === "edit" && meeting) {
        saved = await apiClient<Meeting>(`/api/meetings/${meeting.id}`, {
          method: "PATCH",
          body: JSON.stringify(payload),
        });
      } else {
        saved = await apiClient<Meeting>(`/api/meetings/`, {
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
    if (mode !== "edit" || !meeting) return;
    if (!window.confirm("Eliminare definitivamente questo meeting?")) return;
    setDeleting(true);
    setError(null);
    try {
      await apiClient<void>(`/api/meetings/${meeting.id}`, { method: "DELETE" });
      onDeleted?.(meeting.id);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Errore di eliminazione");
    } finally {
      setDeleting(false);
    }
  }

  const title = mode === "edit" ? "Modifica meeting" : "Nuovo meeting";

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
            {mode === "edit" && meeting && (
              <p className="text-[11px] text-[color:var(--color-text-muted)]">
                ID {meeting.id.slice(0, 8)}
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
              placeholder="Es. Demo Studio Verdi"
              required
            />
          </Field>

          <Field label="Descrizione">
            <textarea
              value={form.description}
              onChange={(e) => update("description", e.target.value)}
              rows={3}
              className="w-full rounded-lg border border-[color:var(--color-line-strong)] bg-[color:var(--color-bg-soft)] px-3 py-2 text-sm placeholder:text-[color:var(--color-text-muted)] focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[color:var(--color-teal)]"
              placeholder="Note, agenda…"
            />
          </Field>

          <div className="grid grid-cols-2 gap-3">
            <Field label="Inizio" required>
              <input
                type="datetime-local"
                value={form.starts_at}
                onChange={(e) => update("starts_at", e.target.value)}
                className="h-10 w-full rounded-lg border border-[color:var(--color-line-strong)] bg-[color:var(--color-bg-soft)] px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[color:var(--color-teal)]"
                required
              />
            </Field>
            <Field label="Fine" required>
              <input
                type="datetime-local"
                value={form.ends_at}
                onChange={(e) => update("ends_at", e.target.value)}
                className="h-10 w-full rounded-lg border border-[color:var(--color-line-strong)] bg-[color:var(--color-bg-soft)] px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[color:var(--color-teal)]"
                required
              />
            </Field>
          </div>

          <Field label="Luogo">
            <Input
              value={form.location}
              onChange={(e) => update("location", e.target.value)}
              placeholder="Es. Online / Via Roma 5"
            />
          </Field>

          <Field label="Link riunione">
            <Input
              value={form.meet_link}
              onChange={(e) => update("meet_link", e.target.value)}
              placeholder="https://meet.google.com/…"
              type="url"
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

          {mode === "edit" && meeting && meeting.attendees.length > 0 && (
            <Field label="Partecipanti">
              <ul className="flex flex-col gap-1 rounded-lg border border-[color:var(--color-line)] bg-[color:var(--color-bg-soft)] p-2 text-xs">
                {meeting.attendees.map((a, i) => (
                  <li
                    key={i}
                    className="flex items-center justify-between gap-2 text-[color:var(--color-text-soft)]"
                  >
                    <span className="truncate">
                      {a.name || a.email || "—"}
                    </span>
                    {a.status && (
                      <span className="text-[10px] uppercase tracking-[0.14em] text-[color:var(--color-text-muted)]">
                        {a.status}
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            </Field>
          )}

          {mode === "edit" && meeting?.meet_link && (
            <a
              href={meeting.meet_link}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1 self-start text-xs text-[color:var(--color-teal)] hover:underline"
            >
              <ExternalLink className="h-3 w-3" /> Apri link riunione
            </a>
          )}

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
