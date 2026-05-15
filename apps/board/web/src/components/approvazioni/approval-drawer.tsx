"use client";

import { useEffect, useState } from "react";
import { X, Check, XCircle, Send } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/lib/api-client";
import type {
  Approval,
  ApprovalKind,
  ApprovalStatus,
  ApprovalUpdatePayload,
} from "@/types/approval";
import {
  APPROVAL_KIND_LABELS,
  APPROVAL_KIND_ORDER,
} from "@/lib/approvals";

interface Props {
  open: boolean;
  approval: Approval | null;
  onClose: () => void;
  onSaved: (a: Approval) => void;
  onDeleted: (id: string) => void;
}

interface FormState {
  title: string;
  body: string;
  kind: ApprovalKind;
  decision_note: string;
}

function initialFrom(a: Approval | null): FormState {
  return {
    title: a?.title ?? "",
    body: a?.body ?? "",
    kind: a?.kind ?? "email",
    decision_note: a?.decision_note ?? "",
  };
}

export function ApprovalDrawer({
  open,
  approval,
  onClose,
  onSaved,
  onDeleted,
}: Props) {
  const [form, setForm] = useState<FormState>(() => initialFrom(approval));
  const [busy, setBusy] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setForm(initialFrom(approval));
      setError(null);
    }
  }, [open, approval]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open || !approval) return null;

  function update<K extends keyof FormState>(k: K, v: FormState[K]) {
    setForm((f) => ({ ...f, [k]: v }));
  }

  async function decide(status: ApprovalStatus) {
    if (!approval) return;
    setBusy(true);
    setError(null);
    try {
      const payload: ApprovalUpdatePayload = {
        title: form.title.trim() || approval.title,
        body: form.body,
        kind: form.kind,
        decision_note: form.decision_note.trim() || null,
        status,
        decided_at: new Date().toISOString(),
      };
      const saved = await apiClient<Approval>(`/api/approvals/${approval.id}`, {
        method: "PATCH",
        body: JSON.stringify(payload),
      });
      onSaved(saved);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Errore di salvataggio");
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete() {
    if (!approval) return;
    if (!window.confirm("Eliminare definitivamente questa bozza?")) return;
    setDeleting(true);
    setError(null);
    try {
      await apiClient<void>(`/api/approvals/${approval.id}`, {
        method: "DELETE",
      });
      onDeleted(approval.id);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Errore di eliminazione");
    } finally {
      setDeleting(false);
    }
  }

  const isPending = approval.status === "pending";

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
        aria-label="Modifica approvazione"
        className="absolute right-0 top-0 flex h-full w-full flex-col border-l border-[color:var(--color-line)] bg-[color:var(--color-bg)] shadow-2xl md:w-[480px]"
      >
        <header className="flex items-center justify-between border-b border-[color:var(--color-line)] px-5 py-4">
          <div>
            <h2 className="font-display text-xl">Modifica bozza</h2>
            <p className="text-[11px] text-[color:var(--color-text-muted)]">
              ID {approval.id.slice(0, 8)} · stato {approval.status}
            </p>
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

        <div className="flex flex-1 flex-col gap-4 overflow-y-auto px-5 py-5">
          <Field label="Titolo">
            <Input
              value={form.title}
              onChange={(e) => update("title", e.target.value)}
              placeholder="Titolo della bozza"
            />
          </Field>

          <Field label="Tipo">
            <select
              value={form.kind}
              onChange={(e) => update("kind", e.target.value as ApprovalKind)}
              className="h-10 w-full rounded-lg border border-[color:var(--color-line-strong)] bg-[color:var(--color-bg-soft)] px-3 text-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[color:var(--color-teal)]"
            >
              {APPROVAL_KIND_ORDER.map((k) => (
                <option key={k} value={k}>
                  {APPROVAL_KIND_LABELS[k]}
                </option>
              ))}
            </select>
          </Field>

          <Field label="Corpo (markdown)">
            <textarea
              value={form.body}
              onChange={(e) => update("body", e.target.value)}
              rows={10}
              className="w-full rounded-lg border border-[color:var(--color-line-strong)] bg-[color:var(--color-bg-soft)] px-3 py-2 font-mono text-xs placeholder:text-[color:var(--color-text-muted)] focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[color:var(--color-teal)]"
              placeholder="Scrivi qui il corpo del messaggio…"
            />
          </Field>

          <Field label="Anteprima">
            <div className="rounded-lg border border-[color:var(--color-line)] bg-[color:var(--color-bg-soft)] px-3 py-2 text-sm text-[color:var(--color-text-soft)]">
              {form.body.trim() ? (
                <div className="prose-approval whitespace-pre-wrap text-sm">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {form.body}
                  </ReactMarkdown>
                </div>
              ) : (
                <span className="text-[color:var(--color-text-muted)]">
                  (vuoto)
                </span>
              )}
            </div>
          </Field>

          {approval.rationale && (
            <Field label="Razionale AI">
              <p className="rounded-lg border border-[color:var(--color-line)] bg-[color:var(--color-bg-soft)] px-3 py-2 text-xs italic text-[color:var(--color-text-muted)]">
                {approval.rationale}
              </p>
            </Field>
          )}

          <Field label="Nota decisione (opzionale)">
            <Input
              value={form.decision_note}
              onChange={(e) => update("decision_note", e.target.value)}
              placeholder="Es. inviato manualmente con piccole modifiche"
            />
          </Field>

          {error && (
            <div className="rounded-lg border border-[color:var(--color-danger)]/50 bg-[color:var(--color-danger)]/10 px-3 py-2 text-xs text-[color:var(--color-danger)]">
              {error}
            </div>
          )}
        </div>

        <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[color:var(--color-line)] bg-[color:var(--color-bg)] px-5 py-3">
          <Button
            type="button"
            variant="danger"
            size="sm"
            onClick={handleDelete}
            disabled={deleting || busy}
          >
            {deleting ? "…" : "Elimina"}
          </Button>
          <div className="flex flex-wrap justify-end gap-2">
            <Button type="button" variant="ghost" size="sm" onClick={onClose}>
              Annulla
            </Button>
            {isPending && (
              <>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => decide("rejected")}
                  disabled={busy}
                >
                  <XCircle className="h-4 w-4" />
                  Rifiuta
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => decide("edited_and_sent")}
                  disabled={busy}
                >
                  <Send className="h-4 w-4" />
                  Salva e segna inviato
                </Button>
                <Button
                  type="button"
                  size="sm"
                  onClick={() => decide("approved")}
                  disabled={busy}
                >
                  <Check className="h-4 w-4" />
                  {busy ? "…" : "Approva"}
                </Button>
              </>
            )}
            {!isPending && (
              <Button
                type="button"
                size="sm"
                onClick={() => decide(approval.status)}
                disabled={busy}
              >
                {busy ? "…" : "Salva modifiche"}
              </Button>
            )}
          </div>
        </div>
      </aside>
    </div>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <label className="flex flex-col gap-1.5">
      <span className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[color:var(--color-text-muted)]">
        {label}
      </span>
      {children}
    </label>
  );
}
