"use client";

import { useEffect, useRef, useState } from "react";
import { Conversation } from "@/types/chat";
import { cx } from "@/lib/utils";
import { Pencil, Trash2, X } from "lucide-react";

export function ConversationList({
  conversations,
  activeId,
  onSelect,
  onDelete,
  onRename,
}: {
  conversations: Conversation[];
  activeId: string;
  onSelect: (id: string) => void;
  onDelete?: (id: string) => void;
  onRename?: (id: string, title: string) => void;
}) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (editingId && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [editingId]);

  function commit() {
    if (editingId && onRename) {
      const clean = draft.trim().slice(0, 80);
      if (clean) onRename(editingId, clean);
    }
    setEditingId(null);
    setDraft("");
  }

  function cancel() {
    setEditingId(null);
    setDraft("");
  }

  return (
    <div className="space-y-2">
      {conversations.map((c) => {
        const isEditing = editingId === c.id;
        return (
          <div
            key={c.id}
            className={cx(
              "group flex w-full items-center gap-1 rounded-xl border px-3 py-2 transition",
              c.id === activeId
                ? "border-[var(--teal)] bg-[var(--teal-soft)]"
                : "border-[var(--line)] hover:border-[var(--line-strong)]",
            )}
          >
            {isEditing ? (
              <input
                ref={inputRef}
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    commit();
                  } else if (e.key === "Escape") {
                    e.preventDefault();
                    cancel();
                  }
                }}
                onBlur={commit}
                className="min-w-0 flex-1 rounded-md border border-[var(--line)] bg-[var(--bg-1)] px-2 py-1 text-sm text-[var(--text-main)] outline-none focus:border-[var(--teal)]"
                maxLength={80}
                aria-label="Rinomina conversazione"
              />
            ) : (
              <button
                onClick={() => onSelect(c.id)}
                onDoubleClick={() => {
                  if (!onRename) return;
                  setEditingId(c.id);
                  setDraft(c.title);
                }}
                className="min-w-0 flex-1 text-left"
                title="Doppio click per rinominare"
              >
                <p className="truncate text-sm font-medium">{c.title}</p>
                <p className="text-xs text-[var(--text-muted)]">
                  {c.mode === "lead" ? "Lead" : "Report"}
                </p>
              </button>
            )}
            {!isEditing && onRename && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setEditingId(c.id);
                  setDraft(c.title);
                }}
                className="flex-shrink-0 rounded-md p-1.5 text-[var(--text-muted)] opacity-0 transition hover:bg-white/5 hover:text-[var(--text-soft)] group-hover:opacity-100"
                aria-label="Rinomina chat"
                title="Rinomina chat"
              >
                <Pencil size={13} />
              </button>
            )}
            {!isEditing && onDelete && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  if (window.confirm("Eliminare?")) onDelete(c.id);
                }}
                className="flex-shrink-0 rounded-md p-1.5 text-[var(--text-muted)] opacity-0 transition hover:bg-red-500/10 hover:text-red-400 group-hover:opacity-100"
                aria-label="Elimina chat"
                title="Elimina chat"
              >
                <Trash2 size={14} />
              </button>
            )}
            {isEditing && (
              <button
                onMouseDown={(e) => {
                  e.preventDefault();
                  cancel();
                }}
                className="flex-shrink-0 rounded-md p-1.5 text-[var(--text-muted)] hover:text-[var(--text-soft)]"
                aria-label="Annulla rinomina"
                title="Annulla"
              >
                <X size={13} />
              </button>
            )}
          </div>
        );
      })}
    </div>
  );
}
