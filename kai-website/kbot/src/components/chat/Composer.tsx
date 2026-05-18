"use client";

import { useEffect, useRef, useState } from "react";
import { ArrowUp, Globe, Loader2, Mic, MicOff, Paperclip, X } from "lucide-react";
import { UploadedFile, AnalyzedUrl } from "@/lib/api";

const URL_RE = /https?:\/\/[^\s<>"']{6,}/i;

type ActiveContext =
  | { kind: "file"; key: string; label: string; idOrName: string }
  | { kind: "url"; key: string; label: string; idOrName: string };

/** Web Speech API typing helpers (kept loose; not all browsers expose them). */
interface SpeechRecognitionResultLike {
  isFinal: boolean;
  0: { transcript: string };
}
interface SpeechRecognitionEventLike {
  resultIndex: number;
  results: ArrayLike<SpeechRecognitionResultLike>;
}
interface SpeechRecognitionInstance {
  lang: string;
  interimResults: boolean;
  continuous: boolean;
  onresult: ((e: SpeechRecognitionEventLike) => void) | null;
  onerror: ((e: unknown) => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
  abort: () => void;
}
type SpeechRecognitionCtor = new () => SpeechRecognitionInstance;

function getSpeechRecognitionCtor(): SpeechRecognitionCtor | null {
  if (typeof window === "undefined") return null;
  const w = window as unknown as {
    SpeechRecognition?: SpeechRecognitionCtor;
    webkitSpeechRecognition?: SpeechRecognitionCtor;
  };
  return w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null;
}

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
  analyzedUrls = [],
  onRemoveContext,
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
  analyzedUrls?: AnalyzedUrl[];
  onRemoveContext?: (item: { type: "file" | "url"; idOrName: string }) => void;
}) {
  const ref = useRef<HTMLTextAreaElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const [urlMode, setUrlMode] = useState(false);
  const [urlInput, setUrlInput] = useState("");
  const urlRef = useRef<HTMLInputElement>(null);

  // Voice input ----------------------------------------------------------
  const recognitionRef = useRef<SpeechRecognitionInstance | null>(null);
  const baseValueRef = useRef("");
  const [voiceSupported, setVoiceSupported] = useState(false);
  const [recording, setRecording] = useState(false);

  useEffect(() => {
    setVoiceSupported(getSpeechRecognitionCtor() !== null);
  }, []);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "0px";
    el.style.height = `${Math.min(el.scrollHeight, 170)}px`;
  }, [value]);

  useEffect(() => {
    if (urlMode) urlRef.current?.focus();
  }, [urlMode]);

  // Stop recognition on unmount.
  useEffect(() => {
    return () => {
      try {
        recognitionRef.current?.abort();
      } catch {
        /* ignore */
      }
    };
  }, []);

  function toggleVoice() {
    if (recording) {
      recognitionRef.current?.stop();
      return;
    }
    const Ctor = getSpeechRecognitionCtor();
    if (!Ctor) return;
    const rec = new Ctor();
    rec.lang = "it-IT";
    rec.interimResults = true;
    rec.continuous = true;
    baseValueRef.current = value ? value.replace(/\s+$/, "") + " " : "";
    rec.onresult = (e: SpeechRecognitionEventLike) => {
      let finalChunk = "";
      let interim = "";
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const r = e.results[i];
        if (r.isFinal) finalChunk += r[0].transcript;
        else interim += r[0].transcript;
      }
      if (finalChunk) {
        baseValueRef.current = (baseValueRef.current + finalChunk).replace(/\s+/g, " ");
      }
      onChange((baseValueRef.current + interim).trim());
    };
    rec.onerror = () => setRecording(false);
    rec.onend = () => setRecording(false);
    try {
      rec.start();
      recognitionRef.current = rec;
      setRecording(true);
    } catch {
      setRecording(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      if (!disabled && value.trim()) onSubmit();
    }
  }

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

  // Build the "Contesto attivo" list (files + URLs).
  const activeContext: ActiveContext[] = [
    ...files.map((f) => ({
      kind: "file" as const,
      key: `f-${f.path}`,
      label: f.name,
      idOrName: f.path || f.name,
    })),
    ...analyzedUrls.map((u) => {
      let host = u.url;
      try {
        host = new URL(u.url).hostname.replace(/^www\./, "");
      } catch {
        /* keep raw */
      }
      return {
        kind: "url" as const,
        key: `u-${u.url}`,
        label: host,
        idOrName: u.url,
      };
    }),
  ];

  return (
    <div className="sticky bottom-0 mt-4 border-t border-[var(--line)] bg-[var(--bg-0)]/95 pt-3 backdrop-blur">
      {activeContext.length > 0 && (
        <div className="mb-2 flex flex-wrap items-center gap-1.5 rounded-lg border border-[var(--line)] bg-[var(--bg-1)] px-2 py-1.5">
          <span className="text-[10px] uppercase tracking-wider text-[var(--text-muted)]">
            Contesto attivo
          </span>
          {activeContext.map((ctx) => (
            <span
              key={ctx.key}
              className="inline-flex max-w-[220px] items-center gap-1 rounded-full border border-[var(--teal)]/40 bg-[var(--teal-soft)] px-2 py-0.5 text-xs text-[var(--text-soft)]"
            >
              <span aria-hidden>{ctx.kind === "file" ? "📎" : "🌐"}</span>
              <span className="truncate">{ctx.label}</span>
              {onRemoveContext && (
                <button
                  type="button"
                  onClick={() =>
                    onRemoveContext({ type: ctx.kind, idOrName: ctx.idOrName })
                  }
                  aria-label={`Rimuovi ${ctx.label} dal contesto`}
                  className="ml-0.5 rounded-full p-0.5 hover:bg-red-500/15 hover:text-red-400"
                >
                  <X size={10} />
                </button>
              )}
            </span>
          ))}
        </div>
      )}

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
        <div className="mb-2 flex items-center gap-2 rounded-xl border border-[var(--line)] bg-[var(--bg-1)] px-3 py-2">
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
            {files.map((f) => {
              const isImage = (f.type || "").startsWith("image/") ||
                /\.(jpe?g|png|gif|webp)$/i.test(f.name);
              return (
                <span
                  key={f.path}
                  className="inline-flex items-center gap-1.5 rounded-full border border-[var(--line)] py-1 pl-1 pr-2 text-xs text-[var(--text-soft)]"
                >
                  {isImage && f.publicUrl ? (
                    // eslint-disable-next-line @next/next/no-img-element -- thumb, no Next image overhead
                    <img
                      src={f.publicUrl}
                      alt={f.name}
                      className="h-5 w-5 rounded-full object-cover"
                    />
                  ) : (
                    <Paperclip size={11} className="ml-1 text-[var(--teal)]" />
                  )}
                  <span className="truncate max-w-[160px]">{f.name}</span>
                </span>
              );
            })}
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
          onKeyDown={handleKeyDown}
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
            <button
              type="button"
              onClick={toggleVoice}
              disabled={!voiceSupported}
              aria-pressed={recording}
              aria-label={recording ? "Ferma dettatura" : "Avvia dettatura vocale"}
              title={
                voiceSupported
                  ? recording
                    ? "Ferma dettatura"
                    : "Dettatura vocale (it-IT)"
                  : "Voce non supportata in questo browser"
              }
              className={`rounded-lg border p-2 text-[var(--text-soft)] hover:border-[var(--line-strong)] disabled:cursor-not-allowed disabled:opacity-40 ${
                recording
                  ? "k2-mic-recording border-red-500/60 text-red-400"
                  : "border-[var(--line)]"
              }`}
            >
              {recording ? <Mic size={15} /> : voiceSupported ? <Mic size={15} /> : <MicOff size={15} />}
            </button>
          </div>
          <button
            type="button"
            onClick={() => onSubmit()}
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
