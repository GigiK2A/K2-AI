"use client";

import { useState } from "react";
import { Plus, X } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/lib/api-client";
import type { Approval, ApprovalCreatePayload, ApprovalKind } from "@/types/approval";
import { APPROVAL_KIND_LABELS, APPROVAL_KIND_ORDER } from "@/lib/approvals";

interface Props {
  onCreated: (a: Approval) => void;
  variant?: "primary" | "ghost";
}

export function ManualDraftButton({ onCreated, variant = "primary" }: Props) {
  const [open, setOpen] = useState(false);
  const [kind, setKind] = useState<ApprovalKind>("email");
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!title.trim()) {
      setError("Il titolo è obbligatorio");
      return;
    }
    setBusy(true);
    try {
      const payload: ApprovalCreatePayload = {
        kind,
        title: title.trim(),
        body: body.trim(),
      };
      const created = await apiClient<Approval>(`/api/approvals/`, {
        method: "POST",
        body: JSON.stringify(payload),
      });
      onCreated(created);
      setOpen(false);
      setTitle("");
      setBody("");
      setKind("email");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Errore di creazione");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <Button
        type="button"
        size="sm"
        variant={variant === "ghost" ? "outline" : "default"}
        onClick={() => setOpen(true)}
      >
        <Plus className="h-4 w-4" />
        Crea draft manuale
      </Button>

      {open && (
        <div className="fixed inset-0 z-50">
          <div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={() => setOpen(false)}
            aria-hidden
          />
          <div className="absolute left-1/2 top-1/2 w-full max-w-lg -translate-x-1/2 -translate-y-1/2 rounded-xl border border-[color:var(--color-line)] bg-[color:var(--color-bg)] p-5 shadow-2xl">
            <header className="mb-4 flex items-center justify-between">
              <h3 className="font-display text-lg">Nuova bozza manuale</h3>
              <button
                type="button"
                onClick={() => setOpen(false)}
                aria-label="Chiudi"
                className="rounded-md p-1 text-[color:var(--color-text-soft)] hover:bg-[color:var(--color-bg-elevated)]"
              >
                <X className="h-5 w-5" />
              </button>
            </header>

            <form onSubmit={handleCreate} className="flex flex-col gap-3">
              <label className="flex flex-col gap-1.5">
                <span className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[color:var(--color-text-muted)]">
                  Tipo
                </span>
                <select
                  value={kind}
                  onChange={(e) => setKind(e.target.value as ApprovalKind)}
                  className="h-10 w-full rounded-lg border border-[color:var(--color-line-strong)] bg-[color:var(--color-bg-soft)] px-3 text-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[color:var(--color-teal)]"
                >
                  {APPROVAL_KIND_ORDER.map((k) => (
                    <option key={k} value={k}>
                      {APPROVAL_KIND_LABELS[k]}
                    </option>
                  ))}
                </select>
              </label>

              <label className="flex flex-col gap-1.5">
                <span className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[color:var(--color-text-muted)]">
                  Titolo
                </span>
                <Input
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Es. Email di follow-up Studio Rossi"
                  required
                />
              </label>

              <label className="flex flex-col gap-1.5">
                <span className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[color:var(--color-text-muted)]">
                  Corpo (markdown)
                </span>
                <textarea
                  value={body}
                  onChange={(e) => setBody(e.target.value)}
                  rows={8}
                  className="w-full rounded-lg border border-[color:var(--color-line-strong)] bg-[color:var(--color-bg-soft)] px-3 py-2 font-mono text-xs focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[color:var(--color-teal)]"
                  placeholder="Scrivi qui il corpo…"
                />
              </label>

              {error && (
                <div className="rounded-lg border border-[color:var(--color-danger)]/50 bg-[color:var(--color-danger)]/10 px-3 py-2 text-xs text-[color:var(--color-danger)]">
                  {error}
                </div>
              )}

              <div className="flex justify-end gap-2">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => setOpen(false)}
                >
                  Annulla
                </Button>
                <Button type="submit" size="sm" disabled={busy}>
                  {busy ? "Creo…" : "Crea bozza"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
