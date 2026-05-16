"use client";

import { useState, KeyboardEvent } from "react";
import { Send, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ComposerProps {
  onSend: (text: string) => void;
  busy: boolean;
}

const SUGGESTIONS = [
  "Cosa devo fare oggi?",
  "Quanti lead in pipeline?",
  "Riassumi le approvazioni in attesa",
  "Prepara un'email di follow-up per il lead più caldo",
];

export function Composer({ onSend, busy }: ComposerProps) {
  const [value, setValue] = useState("");

  function submit() {
    const text = value.trim();
    if (!text || busy) return;
    onSend(text);
    setValue("");
  }

  function handleKey(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  }

  return (
    <div className="sticky bottom-0 mt-4 border-t border-[color:var(--color-line)] bg-[color:var(--color-bg)] pb-2 pt-3">
      <div className="mb-2 flex flex-wrap gap-1.5">
        {SUGGESTIONS.map(s => (
          <button
            key={s}
            type="button"
            onClick={() => !busy && onSend(s)}
            disabled={busy}
            className="rounded-full border border-[color:var(--color-line)] bg-[color:var(--color-bg-soft)] px-3 py-1 text-xs text-[color:var(--color-text-soft)] transition-colors hover:border-[color:var(--color-teal)] hover:text-[color:var(--color-text)] disabled:opacity-50"
          >
            {s}
          </button>
        ))}
      </div>
      <div className="flex items-end gap-2">
        <textarea
          value={value}
          onChange={e => setValue(e.target.value)}
          onKeyDown={handleKey}
          rows={2}
          placeholder="Scrivi a Giuseppina…"
          disabled={busy}
          className="flex-1 resize-none rounded-lg border border-[color:var(--color-line)] bg-[color:var(--color-bg-soft)] px-3 py-2 text-sm text-[color:var(--color-text)] placeholder:text-[color:var(--color-text-muted)] focus:border-[color:var(--color-teal)] focus:outline-none disabled:opacity-50"
        />
        <Button onClick={submit} disabled={busy || !value.trim()} size="md">
          {busy ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
          Invia
        </Button>
      </div>
    </div>
  );
}
