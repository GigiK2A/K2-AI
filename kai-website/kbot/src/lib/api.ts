/**
 * Client SDK for the new session-based K-BOT backend (FastAPI).
 *
 * Endpoint set (all under `/api/kbot/`):
 *   POST   /session                       create a session (anon or user-linked)
 *   GET    /session/{id}                  fetch a session
 *   POST   /session/{id}/link-user        link an anonymous session to the auth user
 *   POST   /message                       chat turn against a session
 *   POST   /upload                        upload files into a session (base64)
 *   POST   /report                        deterministic ReportData transformer
 *   POST   /checkout                      Stripe Checkout Session
 *   POST   /generate-pdf                  LLM → HTML → PDF (gated: paid or test_mode)
 *   GET    /status?id=...                 polling
 *
 * Auth is sent as `Authorization: Bearer <supabase_access_token>` and is
 * optional on every endpoint except link-user. Anonymous sessions are first
 * class — the UI starts chatting without login.
 */

export type Mode = "lead" | "report";

export interface KbotSession {
  id: string;
  serviceId: string | null;
  mode: Mode;
  messages: KbotMessage[];
  extractedData: Record<string, unknown>;
  summary: string | null;
  recommendedServiceId: string | null;
  recommendedServiceName: string | null;
  recommendedTier: string | null;
  status: string | null;
  pdfUrl: string | null;
  hasUser: boolean;
  timestamps: { createdAt: string; updatedAt: string };
}

export interface KbotMessage {
  role: "user" | "assistant";
  content: string;
  ts?: string;
}

export interface UploadedFile {
  name: string;
  type: string;
  size: number;
  path: string;
  publicUrl: string;
  extractedText: string;
  extractedSummary: string;
  extractionMethod: "text-decode" | "pdf-parse" | "claude-summary" | "none" | string;
}

export interface AnalyzedUrl {
  url: string;
  title: string;
  summary: string;
  cached: boolean;
}

export interface SendMessageResult {
  message: string;
  summary: Record<string, unknown> | null;
  nextAction: "show_summary" | "continue" | string;
  session: KbotSession;
}

function resolveApiBase(): string {
  const configured = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";
  // If we're not on localhost but the configured URL is, ignore it.
  if (
    typeof window !== "undefined" &&
    window.location.hostname !== "localhost" &&
    /^https?:\/\/(localhost|127\.0\.0\.1|192\.168\.)/i.test(configured)
  ) {
    return "";
  }
  return configured;
}

export const API_BASE = resolveApiBase();

function authHeaders(token?: string | null): Record<string, string> {
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function parseErr(res: Response, fallback: string): Promise<never> {
  let detail = fallback;
  try {
    const data = await res.json();
    detail = (data?.detail as string) || (data?.message as string) || fallback;
  } catch {
    /* ignore */
  }
  throw new Error(detail);
}

/* -----------------------------------------------------------------
 * Sessions
 * ----------------------------------------------------------------- */

export async function createSession(opts: {
  serviceId?: string;
  mode?: Mode;
  authToken?: string | null;
} = {}): Promise<KbotSession> {
  const res = await fetch(`${API_BASE}/api/kbot/session`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders(opts.authToken) },
    body: JSON.stringify({
      service_id: opts.serviceId,
      mode: opts.mode ?? "report",
    }),
  });
  if (!res.ok) await parseErr(res, "Errore creazione sessione");
  const data = await res.json();
  return data.session as KbotSession;
}

export async function getSession(
  sessionId: string,
  authToken?: string | null,
): Promise<KbotSession> {
  const res = await fetch(`${API_BASE}/api/kbot/session/${sessionId}`, {
    headers: { ...authHeaders(authToken) },
    cache: "no-store",
  });
  if (!res.ok) await parseErr(res, "Sessione non trovata");
  const data = await res.json();
  return data.session as KbotSession;
}

export interface DashboardPayload {
  sessions: KbotSession[];
  stats: { total: number; paid: number; with_pdf: number };
  account: { email: string | null; has_paid: boolean };
}

export async function fetchUserSessions(authToken: string): Promise<DashboardPayload> {
  const res = await fetch(`${API_BASE}/api/kbot/sessions`, {
    headers: { ...authHeaders(authToken) },
    cache: "no-store",
  });
  if (!res.ok) await parseErr(res, "Errore caricamento sessioni");
  return res.json();
}

export async function linkSessionToUser(
  sessionId: string,
  authToken: string,
): Promise<KbotSession> {
  const res = await fetch(`${API_BASE}/api/kbot/session/${sessionId}/link-user`, {
    method: "POST",
    headers: { ...authHeaders(authToken) },
  });
  if (!res.ok) await parseErr(res, "Errore collegamento sessione");
  const data = await res.json();
  return data.session as KbotSession;
}

/* -----------------------------------------------------------------
 * Chat turn
 * ----------------------------------------------------------------- */

export class RateLimitError extends Error {
  retryAfter: number;
  constructor(retryAfter: number, message = "Rate limit") {
    super(message);
    this.name = "RateLimitError";
    this.retryAfter = retryAfter;
  }
}

export async function sendMessage(
  sessionId: string,
  message: string,
  opts: { serviceId?: string; authToken?: string | null; forcedSkills?: string[] } = {},
): Promise<SendMessageResult> {
  const res = await fetch(`${API_BASE}/api/kbot/message`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders(opts.authToken) },
    body: JSON.stringify({
      session_id: sessionId,
      service_id: opts.serviceId,
      message,
      forced_skills: opts.forcedSkills,
    }),
  });
  if (res.status === 429) {
    const ra = parseInt(res.headers.get("retry-after") || "30", 10);
    throw new RateLimitError(Number.isFinite(ra) && ra > 0 ? ra : 30, "Troppe richieste");
  }
  if (!res.ok) await parseErr(res, "Errore invio messaggio");
  return res.json() as Promise<SendMessageResult>;
}

/* -----------------------------------------------------------------
 * Context (remove a file/URL from session)
 * ----------------------------------------------------------------- */

export async function removeContextItem(
  sessionId: string,
  type: "file" | "url",
  idOrName: string,
  authToken?: string | null,
): Promise<void> {
  const res = await fetch(`${API_BASE}/api/kbot/context/remove`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders(authToken) },
    body: JSON.stringify({ session_id: sessionId, type, id_or_name: idOrName }),
  });
  if (!res.ok) await parseErr(res, "Errore rimozione contesto");
}

/* -----------------------------------------------------------------
 * Skills registry
 * ----------------------------------------------------------------- */

export interface AvailableSkill {
  name: string;
  description: string;
}

export async function listSkills(): Promise<AvailableSkill[]> {
  const res = await fetch(`${API_BASE}/api/kbot/skills`, { cache: "no-store" });
  if (!res.ok) await parseErr(res, "Errore caricamento skill");
  const data = await res.json();
  return (data.skills as AvailableSkill[]) ?? [];
}

/* -----------------------------------------------------------------
 * Follow-up suggestions (after long assistant reports)
 * ----------------------------------------------------------------- */

export async function fetchFollowUps(
  sessionId: string,
  authToken?: string | null,
): Promise<string[]> {
  const res = await fetch(`${API_BASE}/api/kbot/followups`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders(authToken) },
    body: JSON.stringify({ session_id: sessionId }),
  });
  if (!res.ok) return [];
  const data = await res.json();
  return (data.followups as string[]) ?? [];
}

/* -----------------------------------------------------------------
 * Streaming chat turn (SSE)
 * ----------------------------------------------------------------- */

export interface StreamCallbacks {
  onDelta: (chunk: string) => void;
  onDone: (result: SendMessageResult) => void;
  onError?: (error: string) => void;
  signal?: AbortSignal;
}

/**
 * Stream a chat turn via Server-Sent Events.
 *
 * Falls back gracefully: if the response is not `text/event-stream` (e.g. an
 * error JSON), the body is parsed once and surfaced via `onError`.
 */
export async function streamMessage(
  sessionId: string,
  message: string,
  opts: { serviceId?: string; authToken?: string | null; forcedSkills?: string[] } & StreamCallbacks,
): Promise<void> {
  const res = await fetch(`${API_BASE}/api/kbot/message/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders(opts.authToken) },
    body: JSON.stringify({
      session_id: sessionId,
      service_id: opts.serviceId,
      message,
      forced_skills: opts.forcedSkills,
    }),
    signal: opts.signal,
  });

  if (!res.ok || !res.body) {
    let detail = "Errore invio messaggio";
    try {
      const data = await res.json();
      detail = (data?.detail as string) || (data?.message as string) || detail;
    } catch {
      /* ignore */
    }
    opts.onError?.(detail);
    throw new Error(detail);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let finalPayload: SendMessageResult | null = null;
  let sawError: string | null = null;

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    // Parse complete SSE events (delimited by blank line).
    let sepIdx: number;
    while ((sepIdx = buffer.indexOf("\n\n")) >= 0) {
      const rawEvent = buffer.slice(0, sepIdx);
      buffer = buffer.slice(sepIdx + 2);
      const dataLines = rawEvent
        .split("\n")
        .filter((l) => l.startsWith("data:"))
        .map((l) => l.slice(5).trimStart());
      if (!dataLines.length) continue;
      const dataStr = dataLines.join("\n");
      try {
        const evt = JSON.parse(dataStr) as {
          delta?: string;
          done?: boolean;
          error?: string;
          message?: string;
          summary?: Record<string, unknown> | null;
          nextAction?: string;
          session?: KbotSession;
        };
        if (evt.error) {
          sawError = evt.error;
          opts.onError?.(evt.error);
          continue;
        }
        if (typeof evt.delta === "string") {
          opts.onDelta(evt.delta);
        }
        if (evt.done && evt.session && typeof evt.message === "string") {
          finalPayload = {
            message: evt.message,
            summary: evt.summary ?? null,
            nextAction: evt.nextAction ?? "continue",
            session: evt.session,
          };
        }
      } catch {
        // ignore malformed chunk
      }
    }
  }

  if (sawError && !finalPayload) {
    throw new Error(sawError);
  }
  if (!finalPayload) {
    throw new Error("Stream chiuso senza payload finale");
  }
  opts.onDone(finalPayload);
}

/* -----------------------------------------------------------------
 * Export a single message (PDF / DOCX). Markdown is purely client-side.
 * ----------------------------------------------------------------- */

export type MessageExportFormat = "pdf" | "docx";

export async function downloadMessageExport(
  sessionId: string,
  format: MessageExportFormat,
  opts: { messageIndex?: number; messageId?: string; authToken?: string | null } = {},
): Promise<void> {
  const endpoint = format === "pdf" ? "render-message-pdf" : "render-message-docx";
  const res = await fetch(`${API_BASE}/api/kbot/${endpoint}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders(opts.authToken) },
    body: JSON.stringify({
      session_id: sessionId,
      message_index: opts.messageIndex,
      message_id: opts.messageId,
    }),
  });
  if (!res.ok) await parseErr(res, "Errore export");
  const blob = await res.blob();
  const disposition = res.headers.get("Content-Disposition") || "";
  const match = /filename="?([^"]+)"?/.exec(disposition);
  const filename =
    match?.[1] ?? `k2ai-report-${sessionId.slice(0, 8)}.${format}`;
  triggerBlobDownload(blob, filename);
}

export function downloadMarkdown(sessionId: string, content: string): void {
  const stamp = new Date()
    .toISOString()
    .replace(/[-:]/g, "")
    .replace(/\..+/, "")
    .replace("T", "-");
  const filename = `k2ai-report-${sessionId.slice(0, 8)}-${stamp}.md`;
  const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
  triggerBlobDownload(blob, filename);
}

function triggerBlobDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 0);
}

/* -----------------------------------------------------------------
 * Upload (base64 payload, multi-file)
 * ----------------------------------------------------------------- */

async function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = String(reader.result);
      const idx = result.indexOf(",");
      resolve(idx >= 0 ? result.slice(idx + 1) : result);
    };
    reader.onerror = () => reject(reader.error || new Error("read failed"));
    reader.readAsDataURL(file);
  });
}

export async function uploadFiles(
  sessionId: string,
  files: File[],
  authToken?: string | null,
): Promise<UploadedFile[]> {
  if (!files.length) return [];
  const payload = await Promise.all(
    files.map(async (f) => ({
      name: f.name,
      type: f.type,
      size: f.size,
      base64: await fileToBase64(f),
    })),
  );
  const res = await fetch(`${API_BASE}/api/kbot/upload`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders(authToken) },
    body: JSON.stringify({ session_id: sessionId, files: payload }),
  });
  if (!res.ok) await parseErr(res, "Errore upload");
  const data = await res.json();
  return (data.files as UploadedFile[]) ?? [];
}

/* -----------------------------------------------------------------
 * URL fetching and analysis
 * ----------------------------------------------------------------- */

export async function fetchUrl(
  sessionId: string,
  url: string,
  token?: string | null,
): Promise<AnalyzedUrl> {
  const res = await fetch(`${API_BASE}/api/kbot/fetch-url`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(token),
    },
    body: JSON.stringify({ session_id: sessionId, url }),
  });
  if (!res.ok) await parseErr(res, "Errore analisi URL");
  return res.json();
}

/* -----------------------------------------------------------------
 * Report (deterministic skeleton) — phase 2 stub on backend
 * ----------------------------------------------------------------- */

export interface ReportData {
  serviceId: string | null;
  summary: string | null;
  recommendedTier: string | null;
  extractedData: Record<string, unknown>;
}

export async function buildReport(
  sessionId: string,
  authToken?: string | null,
): Promise<{ reportData: ReportData; session: KbotSession }> {
  const res = await fetch(`${API_BASE}/api/kbot/report`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders(authToken) },
    body: JSON.stringify({ session_id: sessionId }),
  });
  if (!res.ok) await parseErr(res, "Errore generazione report");
  return res.json();
}

/* -----------------------------------------------------------------
 * Stripe checkout
 * ----------------------------------------------------------------- */

export async function startCheckout(
  sessionId: string,
  authToken: string,
  email?: string,
): Promise<string> {
  const res = await fetch(`${API_BASE}/api/kbot/checkout`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders(authToken) },
    body: JSON.stringify({ session_id: sessionId, email }),
  });
  if (!res.ok) await parseErr(res, "Errore checkout");
  const data = await res.json();
  return data.checkout_url as string;
}

/* -----------------------------------------------------------------
 * PDF generation (post-payment or test_mode)
 * ----------------------------------------------------------------- */

export async function generatePdf(
  sessionId: string,
  authToken?: string | null,
  testMode = false,
): Promise<{ pdfUrl: string; session?: KbotSession }> {
  const res = await fetch(`${API_BASE}/api/kbot/generate-pdf`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders(authToken) },
    body: JSON.stringify({ session_id: sessionId, test_mode: testMode }),
  });
  if (!res.ok) await parseErr(res, "Errore generazione PDF");
  const data = await res.json();
  return { pdfUrl: data.pdf_url as string, session: data.session };
}

/* -----------------------------------------------------------------
 * Conversations history (persisted server-side for authed users)
 * ----------------------------------------------------------------- */

export interface RemoteConversation {
  id: string;
  title: string;
  mode: Mode;
  kbotSessionId: string | null;
  createdAt: string;
  updatedAt: string;
}

export async function listConversations(authToken: string): Promise<RemoteConversation[]> {
  const res = await fetch(`${API_BASE}/api/kbot/conversations`, {
    headers: { ...authHeaders(authToken) },
    cache: "no-store",
  });
  if (!res.ok) await parseErr(res, "Errore caricamento conversazioni");
  const data = await res.json();
  return (data.conversations as RemoteConversation[]) ?? [];
}

export async function createRemoteConversation(
  authToken: string,
  payload: { title?: string; mode?: Mode; kbotSessionId?: string | null },
): Promise<RemoteConversation> {
  const res = await fetch(`${API_BASE}/api/kbot/conversations`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders(authToken) },
    body: JSON.stringify({
      title: payload.title,
      mode: payload.mode ?? "report",
      kbotSessionId: payload.kbotSessionId,
    }),
  });
  if (!res.ok) await parseErr(res, "Errore creazione conversazione");
  const data = await res.json();
  return data.conversation as RemoteConversation;
}

export async function updateRemoteConversation(
  authToken: string,
  convId: string,
  patch: { title?: string; kbotSessionId?: string | null },
): Promise<RemoteConversation> {
  const res = await fetch(`${API_BASE}/api/kbot/conversations/${convId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json", ...authHeaders(authToken) },
    body: JSON.stringify(patch),
  });
  if (!res.ok) await parseErr(res, "Errore aggiornamento conversazione");
  const data = await res.json();
  return data.conversation as RemoteConversation;
}

export async function deleteRemoteConversation(authToken: string, convId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/kbot/conversations/${convId}`, {
    method: "DELETE",
    headers: { ...authHeaders(authToken) },
  });
  if (!res.ok) await parseErr(res, "Errore eliminazione conversazione");
}

/* -----------------------------------------------------------------
 * Status polling (used after Stripe redirect)
 * ----------------------------------------------------------------- */

export async function getStatus(
  sessionId: string,
): Promise<{ status: string; pdf_url: string | null }> {
  const res = await fetch(`${API_BASE}/api/kbot/status?id=${encodeURIComponent(sessionId)}`, {
    cache: "no-store",
  });
  if (!res.ok) await parseErr(res, "Errore stato");
  return res.json();
}
