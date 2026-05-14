"use client";

import { useEffect, useRef } from "react";
import { ArrowUp, Paperclip } from "lucide-react";
import { UploadedFile } from "@/types/chat";

export function Composer({
  value,
  onChange,
  onSubmit,
  disabled,
  suggestions,
  onPickFiles,
  files,
}: {
  value: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
  disabled?: boolean;
  suggestions: string[];
  onPickFiles: (files: File[]) => void;
  files: UploadedFile[];
}) {
  const ref = useRef<HTMLTextAreaElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "0px";
    el.style.height = `${Math.min(el.scrollHeight, 170)}px`;
  }, [value]);

  return (
    <div className="sticky bottom-0 mt-4 border-t border-[var(--line)] bg-[linear-gradient(180deg,rgba(5,5,5,0.2),rgba(5,5,5,0.95))] pt-3">
      <div className="mb-2 flex gap-2 overflow-x-auto pb-1">
        {suggestions.map((s) => (
          <button key={s} onClick={() => onChange(s)} className="rounded-full border border-[var(--line)] px-3 py-1 text-xs text-[var(--text-soft)] hover:border-[var(--line-strong)]">
            {s}
          </button>
        ))}
      </div>

      <div className="k2-panel rounded-2xl p-2">
        {files.length > 0 && (
          <div className="mb-2 flex flex-wrap gap-2 px-1">
            {files.map((f) => (
              <span key={f.path} className="rounded-full border border-[var(--line)] px-2 py-1 text-xs text-[var(--text-soft)]">
                {f.name}
              </span>
            ))}
          </div>
        )}
        <textarea
          ref={ref}
          rows={1}
          value={value}
          disabled={disabled}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Scrivi la tua richiesta..."
          className="k2-focus max-h-[170px] w-full resize-none rounded-xl border border-transparent bg-transparent px-3 py-2 text-sm leading-6"
        />
        <div className="mt-2 flex items-center justify-between px-1">
          <input
            ref={fileRef}
            type="file"
            multiple
            className="hidden"
            onChange={(e) => {
              const selected = Array.from(e.target.files ?? []);
              if (selected.length) onPickFiles(selected);
              e.currentTarget.value = "";
            }}
          />
          <button
            onClick={() => fileRef.current?.click()}
            className="rounded-lg border border-[var(--line)] p-2 text-[var(--text-soft)] hover:border-[var(--line-strong)]"
          >
            <Paperclip size={15} />
          </button>
          <button onClick={onSubmit} disabled={disabled || !value.trim()} className="rounded-xl bg-[var(--teal)] p-2 text-black disabled:opacity-50">
            <ArrowUp size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
