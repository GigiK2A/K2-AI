"use client";

import { useEffect, useState } from "react";
import { X, Trash2, ListTodo } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/lib/api-client";
import type {
  Contact,
  ContactCreatePayload,
  Lead,
  LeadCreatePayload,
  LeadSource,
  LeadStatus,
  LeadUpdatePayload,
} from "@/types/lead";
import { LEAD_STATUS_LABELS, LEAD_STATUS_ORDER, SOURCE_LABELS } from "@/lib/leads";

interface BaseProps {
  open: boolean;
  onClose: () => void;
  onSaved: (lead: Lead) => void;
  onDeleted?: (id: string) => void;
  onContactCreated?: (c: Contact) => void;
  contacts: Contact[];
}

interface EditProps extends BaseProps {
  mode: "edit";
  lead: Lead;
}

interface CreateProps extends BaseProps {
  mode: "create";
  lead?: undefined;
}

type Props = EditProps | CreateProps;

interface FormState {
  title: string;
  description: string;
  status: LeadStatus;
  source: LeadSource;
  value_eur: string;
  probability: number;
  next_action_at: string;
  next_action_note: string;
  contact_id: string;
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

function initialFromLead(lead: Lead | undefined): FormState {
  return {
    title: lead?.title ?? "",
    description: lead?.description ?? "",
    status: lead?.status ?? "nuovo",
    source: lead?.source ?? "other",
    value_eur: lead?.value_eur != null ? String(lead.value_eur) : "",
    probability: lead?.probability ?? 50,
    next_action_at: isoToLocalInput(lead?.next_action_at ?? null),
    next_action_note: lead?.next_action_note ?? "",
    contact_id: lead?.contact_id ?? "",
  };
}

export function LeadDrawer(props: Props) {
  const { open, onClose, onSaved, onDeleted, onContactCreated, contacts, mode } = props;
  const lead = mode === "edit" ? props.lead : undefined;

  const [form, setForm] = useState<FormState>(() => initialFromLead(lead));
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showNewContact, setShowNewContact] = useState(false);
  const [newContact, setNewContact] = useState<ContactCreatePayload>({});
  const [creatingContact, setCreatingContact] = useState(false);
  const [taskBusy, setTaskBusy] = useState(false);
  const [taskOk, setTaskOk] = useState(false);

  useEffect(() => {
    if (open) {
      setForm(initialFromLead(lead));
      setError(null);
      setShowNewContact(false);
      setNewContact({});
      setTaskOk(false);
    }
  }, [open, lead]);

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
      const payload: LeadCreatePayload & LeadUpdatePayload = {
        title: form.title.trim(),
        description: form.description.trim() || null,
        status: form.status,
        source: form.source,
        value_eur: form.value_eur === "" ? null : Number(form.value_eur),
        probability: form.probability,
        next_action_at: localInputToIso(form.next_action_at),
        next_action_note: form.next_action_note.trim() || null,
        contact_id: form.contact_id || null,
      };

      let saved: Lead;
      if (mode === "edit" && lead) {
        saved = await apiClient<Lead>(`/api/leads/${lead.id}`, {
          method: "PATCH",
          body: JSON.stringify(payload),
        });
      } else {
        saved = await apiClient<Lead>(`/api/leads/`, {
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
    if (mode !== "edit" || !lead) return;
    if (!window.confirm("Eliminare definitivamente questo lead?")) return;
    setDeleting(true);
    setError(null);
    try {
      await apiClient<void>(`/api/leads/${lead.id}`, { method: "DELETE" });
      onDeleted?.(lead.id);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Errore di eliminazione");
    } finally {
      setDeleting(false);
    }
  }

  async function handleCreateContact() {
    setCreatingContact(true);
    setError(null);
    try {
      const payload: ContactCreatePayload = {
        company: newContact.company?.trim() || null,
        person_name: newContact.person_name?.trim() || null,
        email: newContact.email?.trim() || null,
        phone: newContact.phone?.trim() || null,
      };
      if (!payload.company && !payload.person_name) {
        setError("Azienda o nome persona obbligatori");
        return;
      }
      const created = await apiClient<Contact>(`/api/contacts/`, {
        method: "POST",
        body: JSON.stringify(payload),
      });
      onContactCreated?.(created);
      update("contact_id", created.id);
      setShowNewContact(false);
      setNewContact({});
    } catch (err) {
      setError(err instanceof Error ? err.message : "Errore creazione contatto");
    } finally {
      setCreatingContact(false);
    }
  }

  async function handleOpenAsTask() {
    if (mode !== "edit" || !lead) return;
    setTaskBusy(true);
    setError(null);
    try {
      await apiClient<unknown>(`/api/tasks/`, {
        method: "POST",
        body: JSON.stringify({
          lead_id: lead.id,
          title: lead.title,
          notes: lead.next_action_note ?? null,
          priority: "media",
          status: "todo",
          due_at: lead.next_action_at,
        }),
      });
      setTaskOk(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Errore creazione task");
    } finally {
      setTaskBusy(false);
    }
  }

  const title = mode === "edit" ? "Modifica lead" : "Nuovo lead";

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
            {mode === "edit" && lead && (
              <p className="text-[11px] text-[color:var(--color-text-muted)]">
                ID {lead.id.slice(0, 8)}
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
              placeholder="Es. Studio Rossi — automazione email"
              required
            />
          </Field>

          <Field label="Descrizione">
            <textarea
              value={form.description}
              onChange={(e) => update("description", e.target.value)}
              rows={3}
              className="w-full rounded-lg border border-[color:var(--color-line-strong)] bg-[color:var(--color-bg-soft)] px-3 py-2 text-sm placeholder:text-[color:var(--color-text-muted)] focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[color:var(--color-teal)]"
              placeholder="Note libere"
            />
          </Field>

          <div className="grid grid-cols-2 gap-3">
            <Field label="Stato">
              <Select
                value={form.status}
                onChange={(v) => update("status", v as LeadStatus)}
                options={LEAD_STATUS_ORDER.map((s) => ({
                  value: s,
                  label: LEAD_STATUS_LABELS[s],
                }))}
              />
            </Field>
            <Field label="Sorgente">
              <Select
                value={form.source}
                onChange={(v) => update("source", v as LeadSource)}
                options={(Object.keys(SOURCE_LABELS) as LeadSource[]).map((s) => ({
                  value: s,
                  label: SOURCE_LABELS[s],
                }))}
              />
            </Field>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Field label="Valore (€)">
              <Input
                type="number"
                inputMode="decimal"
                value={form.value_eur}
                onChange={(e) => update("value_eur", e.target.value)}
                placeholder="0"
                min={0}
              />
            </Field>
            <Field label={`Probabilità: ${form.probability}%`}>
              <input
                type="range"
                min={0}
                max={100}
                step={5}
                value={form.probability}
                onChange={(e) => update("probability", Number(e.target.value))}
                className="h-10 w-full accent-[color:var(--color-teal)]"
              />
            </Field>
          </div>

          <Field label="Prossima azione (data)">
            <input
              type="datetime-local"
              value={form.next_action_at}
              onChange={(e) => update("next_action_at", e.target.value)}
              className="h-10 w-full rounded-lg border border-[color:var(--color-line-strong)] bg-[color:var(--color-bg-soft)] px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[color:var(--color-teal)]"
            />
          </Field>

          <Field label="Nota prossima azione">
            <Input
              value={form.next_action_note}
              onChange={(e) => update("next_action_note", e.target.value)}
              placeholder="Es. Chiamare per follow-up"
            />
          </Field>

          <Field label="Contatto">
            <div className="flex flex-col gap-2">
              <Select
                value={form.contact_id}
                onChange={(v) => update("contact_id", v)}
                options={[
                  { value: "", label: "— Nessuno —" },
                  ...contacts.map((c) => ({
                    value: c.id,
                    label: c.company || c.person_name || c.email || c.id.slice(0, 8),
                  })),
                ]}
              />
              {!showNewContact ? (
                <button
                  type="button"
                  onClick={() => setShowNewContact(true)}
                  className="self-start text-xs text-[color:var(--color-teal)] hover:underline"
                >
                  + Nuovo contatto
                </button>
              ) : (
                <div className="flex flex-col gap-2 rounded-lg border border-[color:var(--color-line)] p-3">
                  <Input
                    placeholder="Azienda"
                    value={newContact.company ?? ""}
                    onChange={(e) =>
                      setNewContact((n) => ({ ...n, company: e.target.value }))
                    }
                  />
                  <Input
                    placeholder="Persona"
                    value={newContact.person_name ?? ""}
                    onChange={(e) =>
                      setNewContact((n) => ({ ...n, person_name: e.target.value }))
                    }
                  />
                  <Input
                    type="email"
                    placeholder="Email"
                    value={newContact.email ?? ""}
                    onChange={(e) =>
                      setNewContact((n) => ({ ...n, email: e.target.value }))
                    }
                  />
                  <Input
                    placeholder="Telefono"
                    value={newContact.phone ?? ""}
                    onChange={(e) =>
                      setNewContact((n) => ({ ...n, phone: e.target.value }))
                    }
                  />
                  <div className="flex gap-2">
                    <Button
                      type="button"
                      size="sm"
                      onClick={handleCreateContact}
                      disabled={creatingContact}
                    >
                      {creatingContact ? "Salvo…" : "Crea contatto"}
                    </Button>
                    <Button
                      type="button"
                      size="sm"
                      variant="ghost"
                      onClick={() => {
                        setShowNewContact(false);
                        setNewContact({});
                      }}
                    >
                      Annulla
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </Field>

          {mode === "edit" && lead?.kbot_session_id && (
            <Field label="Sessione K-BOT">
              <Input value={lead.kbot_session_id} readOnly className="opacity-60" />
            </Field>
          )}

          {error && (
            <div className="rounded-lg border border-[color:var(--color-danger)]/50 bg-[color:var(--color-danger)]/10 px-3 py-2 text-xs text-[color:var(--color-danger)]">
              {error}
            </div>
          )}

          {taskOk && (
            <div className="rounded-lg border border-[color:var(--color-success)]/50 bg-[color:var(--color-success)]/10 px-3 py-2 text-xs text-[color:var(--color-success)]">
              Task creato con successo
            </div>
          )}

          <div className="sticky bottom-0 -mx-5 -mb-5 mt-auto flex flex-wrap items-center justify-between gap-2 border-t border-[color:var(--color-line)] bg-[color:var(--color-bg)] px-5 py-3">
            <div className="flex gap-2">
              {mode === "edit" && (
                <>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={handleOpenAsTask}
                    disabled={taskBusy}
                  >
                    <ListTodo className="h-4 w-4" />
                    {taskBusy ? "…" : "Apri come task"}
                  </Button>
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
                </>
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
