"use client";

import { useEffect, useRef, useState } from "react";
import { ArrowUp, Globe, Loader2, Paperclip, X } from "lucide-react";
import { UploadedFile } from "@/types/chat";

const URL_RE = /https?:\/\/[^\s<>"']{6,}/i;

export function Composer({
  value,
  onChange,
  onSubmit,
  disabled,
  suggestions,
  onPickFiles,
  files,
  uploadingFiles = [],
  onFetchUrl,
  fetchingUrl,
}: {
  value: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
  disabled?: boolean;
  suggestions: string[];
  onPickFiles: (files: File[]) => void;
  files: UploadedFile[];
  uploadingFiles?: { name: string; size: number; type: string }[];
  onFetchUrl?: (url: string) => void;
  fetchingUrl?: boolean;
}) {
  const ref = useRef<HTMLTextAreaElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const [urlMode, setUrlMode] = useState(false);
  const [urlInput, setUrlInput] = useState("");
  const urlRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "0px";
    el.style.height = `${Math.min(el.scrollHeight, 170)}px`;
  }, [value]);

  useEffect(() => {
    if (urlMode) urlRef.current?.focus();
  }, [urlMode]);

  function handlePaste(e: React.ClipboardEvent<HTMLTextAreaElement>) {
    const pasted = e.clipboardData.getData("text");
    const match = URL_RE.exec(pasted);
    if (match && onFetchUrl) {
      // Let the paste happen, then trigger fetch
      setTimeout(() => onFetchUrl(match[0]), 0);
    }
  }

  function handleUrlSubmit() {
    const trimmed = urlInput.trim();
    if (!trimmed || !onFetchUrl) return;
    onFetchUrl(trimmed);
    setUrlInput("");
    setUrlMode(false);
  }

  return (
    <div className="sticky bottom-0 mt-4 border-t border-[var(--line)] bg-[linear-gradient(180deg,rgba(5,5,5,0.2),rgba(5,5,5,0.95))] pt-3">
      <div className="mb-2 flex gap-2 overflow-x-auto pb-1">
        {suggestions.map((s) => (
          <button
            key={s}
            onClick={() => onChange(s)}
            className="rounded-full border border-[var(--line)] px-3 py-1 text-xs text-[var(--text-soft)] hover:border-[var(--line-strong)] whitespace-nowrap"
          >
            {s}
          </button>
        ))}
      </div>

      {urlMode && (
        <div className="mb-2 flex items-center gap-2 rounded-xl border border-[var(--line)] bg-[#0a0a0a] px-3 py-2">
          <Globe size={14} className="shrink-0 text-[var(--teal)]" />
          <input
            ref={urlRef}
            type="url"
            value={urlInput}
            onChange={(e) => setUrlInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") { e.preventDefault(); handleUrlSubmit(); }
              if (e.key === "Escape") { setUrlMode(false); setUrlInput(""); }
            }}
            placeholder="Incolla URL da analizzare…"
            className="flex-1 bg-transparent text-sm outline-none placeholder:text-[var(--text-muted)]"
            disabled={fetchingUrl}
          />
          {fetchingUrl ? (
            <span className="text-xs text-[var(--text-soft)]">Analisi…</span>
          ) : (
            <>
              <button
                onClick={handleUrlSubmit}
                disabled={!urlInput.trim()}
                className="rounded-lg bg-[var(--teal)] px-2 py-1 text-xs font-medium text-black disabled:opacity-40"
              >
                Analizza
              </button>
              <button
                type="button"
                aria-label="Annulla analisi URL"
                onClick={() => { setUrlMode(false); setUrlInput(""); }}
              >
                <X size={14} className="text-[var(--text-soft)]" />
              </button>
            </>
          )}
        </div>
      )}

      <div className="k2-panel rounded-2xl p-2">
        {(files.length > 0 || uploadingFiles.length > 0) && (
          <div className="mb-2 flex flex-wrap gap-2 px-1">
            {files.map((f) => (
              <span
                key={f.path}
                className="inline-flex items-center gap-1.5 rounded-full border border-[var(--line)] px-2 py-1 text-xs text-[var(--text-soft)]"
              >
                <Paperclip size={11} className="text-[var(--teal)]" />
                {f.name}
              </span>
            ))}
            {uploadingFiles.map((f, i) => (
              <span
                key={`up-${i}-${f.name}`}
                className="inline-flex items-center gap-1.5 rounded-full border border-[var(--teal)]/50 bg-[var(--teal)]/10 px-2 py-1 text-xs text-[var(--text-soft)] animate-pulse"
              >
                <Loader2 size={11} className="animate-spin text-[var(--teal)]" />
                <span className="truncate max-w-[180px]">{f.name}</span>
                <span className="text-[var(--text-muted)]">caricamento…</span>
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
          onPaste={handlePaste}
          placeholder="Scrivi la tua richiesta…"
          className="k2-focus max-h-[170px] w-full resize-none rounded-xl border border-transparent bg-transparent px-3 py-2 text-sm leading-6"
        />
        <div className="mt-2 flex items-center justify-between px-1">
          <div className="flex items-center gap-2">
            <input
              ref={fileRef}
              type="file"
              multiple
              accept="image/*,.pdf,.txt,.md,.csv,.json,.xml"
              className="hidden"
              onChange={(e) => {
                const selected = Array.from(e.target.files ?? []);
                if (selected.length) onPickFiles(selected);
                e.currentTarget.value = "";
              }}
            />
            <button
              type="button"
              onClick={() => fileRef.current?.click()}
              title="Allega file"
              aria-label="Allega file"
              className="rounded-lg border border-[var(--line)] p-2 text-[var(--text-soft)] hover:border-[var(--line-strong)]"
            >
              <Paperclip size={15} />
            </button>
            {onFetchUrl && (
              <button
                type="button"
                onClick={() => setUrlMode((v) => !v)}
                title="Analizza un URL"
                aria-label="Analizza un URL"
                aria-pressed={urlMode}
                className={`rounded-lg border p-2 text-[var(--text-soft)] hover:border-[var(--line-strong)] ${
                  urlMode ? "border-[var(--teal)] text-[var(--teal)]" : "border-[var(--line)]"
                }`}
              >
                <Globe size={15} />
              </button>
            )}
          </div>
          <button
            type="button"
            onClick={onSubmit}
            disabled={disabled || !value.trim()}
            aria-label="Invia messaggio"
            className="rounded-xl bg-[var(--teal)] p-2 text-black disabled:opacity-50"
          >
            <ArrowUp size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
