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
  tagPillar?: string | null;
  boostSuggerito?: string | null;
  boostSuggeritoLabel?: string | null;
  deliverableLabel?: string | null;
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
  linkToken?: string | null;
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
  tagPillar?: string | null;
  mode?: Mode;
  authToken?: string | null;
} = {}): Promise<KbotSession> {
  const res = await fetch(`${API_BASE}/api/kbot/session`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders(opts.authToken) },
    body: JSON.stringify({
      service_id: opts.serviceId,
      tag_pillar: opts.tagPillar ?? undefined,
      mode: opts.mode ?? "report",
    }),
  });
  if (!res.ok) await parseErr(res, "Errore creazione sessione");
  const data = await res.json();
  const session = data.session as KbotSession;
  // Backend emette link_token solo per sessioni anonime — serve per claim post-login.
  if (data.link_token) session.linkToken = data.link_token as string;
  return session;
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

/* -----------------------------------------------------------------
 * Dati azienda dell'account (dashboard / signup): impostati una volta,
 * presi dall'account e iniettati nel prompt → non da reinserire in ogni chat.
 * ----------------------------------------------------------------- */
export type CompanyProfile = {
  ragione_sociale?: string;
  partita_iva?: string;
  codice_ateco?: string;
  forma_giuridica?: string;
  settore?: string;
  dipendenti?: string;
  fatturato?: string;
  citta?: string;
};

export async function getCompanyProfile(authToken: string): Promise<CompanyProfile> {
  const res = await fetch(`${API_BASE}/api/kbot/profile`, {
    headers: { ...authHeaders(authToken) },
    cache: "no-store",
  });
  if (!res.ok) return {};
  const data = await res.json();
  return (data.profile as CompanyProfile) ?? {};
}

export async function saveCompanyProfile(
  profile: CompanyProfile,
  authToken: string,
): Promise<CompanyProfile> {
  const res = await fetch(`${API_BASE}/api/kbot/profile`, {
    method: "PUT",
    headers: { "Content-Type": "application/json", ...authHeaders(authToken) },
    body: JSON.stringify(profile),
  });
  if (!res.ok) await parseErr(res, "Errore salvataggio dati azienda");
  const data = await res.json();
  return (data.profile as CompanyProfile) ?? {};
}

export async function linkSessionToUser(
  sessionId: string,
  authToken: string,
  linkToken?: string | null,
): Promise<KbotSession> {
  const res = await fetch(`${API_BASE}/api/kbot/session/${sessionId}/link-user`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders(authToken) },
    body: JSON.stringify({ linkToken: linkToken ?? null }),
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

/**
 * Download the full PAID deliverable (the generated report) as an Excel file.
 * Re-renders the analysis JSON persisted by generate-pdf — data tables and
 * editorial calendars become real spreadsheet sheets. Gated: paid or test_mode.
 */
export async function downloadDeliverableXlsx(
  sessionId: string,
  opts: { authToken?: string | null; testMode?: boolean } = {},
): Promise<void> {
  const res = await fetch(`${API_BASE}/api/kbot/render-deliverable-xlsx`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders(opts.authToken) },
    body: JSON.stringify({ session_id: sessionId, test_mode: opts.testMode ?? false }),
  });
  if (!res.ok) await parseErr(res, "Errore export Excel");
  const blob = await res.blob();
  const disposition = res.headers.get("Content-Disposition") || "";
  const match = /filename="?([^"]+)"?/.exec(disposition);
  const filename = match?.[1] ?? `k2ai-report-${sessionId.slice(0, 8)}.xlsx`;
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

/** Streaming SSE: emette stage+progress real-time, restituisce pdf_url finale. */
export async function generatePdfStream(
  sessionId: string,
  opts: {
    authToken?: string | null;
    testMode?: boolean;
    onProgress?: (e: { stage: string; progress: number }) => void;
  } = {},
): Promise<{ pdfUrl: string; session?: KbotSession }> {
  const res = await fetch(`${API_BASE}/api/kbot/generate-pdf/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders(opts.authToken) },
    body: JSON.stringify({ session_id: sessionId, test_mode: opts.testMode ?? false }),
  });
  if (!res.ok || !res.body) await parseErr(res, "Errore generazione PDF");
  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let pdfUrl: string | null = null;
  let session: KbotSession | undefined;
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let sep: number;
    while ((sep = buffer.indexOf("\n\n")) >= 0) {
      const raw = buffer.slice(0, sep);
      buffer = buffer.slice(sep + 2);
      const data = raw.split("\n").filter((l) => l.startsWith("data:")).map((l) => l.slice(5).trimStart()).join("\n");
      if (!data) continue;
      try {
        const evt = JSON.parse(data) as { stage?: string; progress?: number; pdf_url?: string; session?: KbotSession; error?: string };
        if (evt.error) throw new Error(evt.error);
        if (typeof evt.stage === "string" && typeof evt.progress === "number") {
          opts.onProgress?.({ stage: evt.stage, progress: evt.progress });
        }
        if (evt.pdf_url) {
          pdfUrl = evt.pdf_url;
          session = evt.session;
        }
      } catch (err) {
        if (err instanceof Error) throw err;
      }
    }
  }
  if (!pdfUrl) throw new Error("Stream chiuso senza pdf_url");
  return { pdfUrl, session };
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

/* -----------------------------------------------------------------
 * Deliverable 8e (Boost) — instrada al motore 8e e polla lo stato.
 * Vedi docs/interfaccia-kbot-8e.md + api/deliverables.py.
 * ----------------------------------------------------------------- */

export type DeliverableStatus =
  | "routed" | "running" | "validating" | "rendered" | "refused" | "error";

export interface DeliverablePreview {
  score?: number;
  criticita_1?: { area?: string; descrizione?: string; gravita?: string };
  altre_aree?: string[];
  cta?: string;
}

export interface DeliverableJob {
  job_id: string;
  status: DeliverableStatus;
  outputs?: {
    html_url?: string; pdf_url?: string; html_path?: string; pdf_path?: string;
    bundle?: { type: string; url?: string }[];
    preview?: DeliverablePreview;
  } | null;
  validation?: Record<string, unknown> | null;
  citazioni?: { campo?: string; fonte?: string; vigenza?: string }[];
  refusal_reason?: string | null;
  error?: string | null;
  meta?: Record<string, unknown> | null;
}

export async function createDeliverable(
  sessionId: string,
  servizioId: string,
  inputs: Record<string, unknown>,
  authToken?: string | null,
): Promise<{ job_id: string; status: string }> {
  const res = await fetch(`${API_BASE}/api/kbot/deliverables`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders(authToken) },
    body: JSON.stringify({ session_id: sessionId, servizio_id: servizioId, inputs }),
  });
  if (!res.ok) await parseErr(res, "Errore creazione deliverable");
  return res.json();
}

/** Checkout per un Boost: prezzo dal catalogo (non i 19€ del report). */
export async function startBoostCheckout(
  sessionId: string,
  servizioId: string,
  authToken?: string | null,
  email?: string,
): Promise<string> {
  const res = await fetch(`${API_BASE}/api/kbot/checkout/boost`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders(authToken) },
    body: JSON.stringify({ session_id: sessionId, servizio_id: servizioId, email }),
  });
  if (!res.ok) await parseErr(res, "Errore checkout boost");
  const data = await res.json();
  return data.checkout_url as string;
}

/** Rientro post-redirect Stripe: scambia il success_token opaco (querystring ?t=)
 * con il session_id + stato, così il frontend riprende generazione e polling. */
export async function exchangeToken(
  token: string,
): Promise<{ session_id: string; status: string | null; paid: boolean; pdf_url: string | null } | null> {
  const res = await fetch(`${API_BASE}/api/kbot/checkout/exchange`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token }),
  });
  if (res.status === 404) return null;
  if (!res.ok) await parseErr(res, "Errore scambio token");
  return (await res.json()) as { session_id: string; status: string | null; paid: boolean; pdf_url: string | null };
}

/** DEMO — pagamento simulato (nessun Stripe, nessun addebito). Attivo solo se il
 * backend ha KBOT_FAKE_PAYMENT=1. Marca la sessione `paid` e ritorna il prezzo
 * applicato: il chiamante poi ri-lancia la generazione (ora la sessione è pagata). */
export const KBOT_FAKE_PAYMENT =
  (process.env.NEXT_PUBLIC_KBOT_FAKE_PAYMENT ?? "0").toLowerCase() === "1" ||
  (process.env.NEXT_PUBLIC_KBOT_FAKE_PAYMENT ?? "").toLowerCase() === "true";

export async function demoPayBoost(
  sessionId: string,
  servizioId: string,
  authToken?: string | null,
): Promise<{ ok: boolean; prezzo_eur?: number }> {
  const res = await fetch(`${API_BASE}/api/kbot/checkout/boost/demo`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders(authToken) },
    body: JSON.stringify({ session_id: sessionId, servizio_id: servizioId }),
  });
  if (!res.ok) await parseErr(res, "Errore pagamento demo");
  return (await res.json()) as { ok: boolean; prezzo_eur?: number };
}

// ===== Billing: abbonamenti + crediti =====
export interface BillingStatus {
  plan: "free" | "pro" | "business";
  label: string;
  crediti: number;
  crediti_mese: number;
  sconto_boost_pct: number;
  servizi_eseguibili: boolean;
}

export async function getBilling(authToken: string): Promise<BillingStatus> {
  const res = await fetch(`${API_BASE}/api/kbot/billing/me`, {
    headers: { ...authHeaders(authToken) },
  });
  if (!res.ok) await parseErr(res, "Errore stato abbonamento");
  return (await res.json()) as BillingStatus;
}

export async function startSubscriptionCheckout(
  plan: "pro" | "business",
  authToken: string,
  email?: string,
): Promise<string> {
  const res = await fetch(`${API_BASE}/api/kbot/checkout/subscription`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders(authToken) },
    body: JSON.stringify({ plan, email }),
  });
  if (!res.ok) await parseErr(res, "Errore checkout abbonamento");
  return (await res.json()).checkout_url as string;
}

export async function startCreditsCheckout(
  prezzoEur: 49 | 199 | 499,
  authToken: string,
  email?: string,
): Promise<string> {
  const res = await fetch(`${API_BASE}/api/kbot/checkout/credits`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders(authToken) },
    body: JSON.stringify({ prezzo_eur: prezzoEur, email }),
  });
  if (!res.ok) await parseErr(res, "Errore acquisto crediti");
  return (await res.json()).checkout_url as string;
}

export async function consumeCredits(
  servizioId: string,
  authToken: string,
): Promise<{ ok: boolean; saldo: number; costo: number }> {
  const res = await fetch(`${API_BASE}/api/kbot/billing/consume`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders(authToken) },
    body: JSON.stringify({ servizio_id: servizioId }),
  });
  if (!res.ok) await parseErr(res, "Crediti insufficienti");
  return await res.json();
}

// ---- Check express (strato Consumo, calcolo deterministico) ----------------

export interface CheckMeta {
  service_id: string;
  tool: string;
  module: string;
  input_schema: Record<string, unknown>;
}

/** Elenco dei Check express disponibili (calcolo locale, gate crediti). */
export async function listChecks(authToken: string): Promise<{ checks: CheckMeta[]; count: number }> {
  const res = await fetch(`${API_BASE}/api/kbot/checks`, {
    headers: { ...authHeaders(authToken) },
    cache: "no-store",
  });
  if (!res.ok) await parseErr(res, "Impossibile leggere i check");
  return await res.json();
}

/** Esegue un Check express → risultato strutturato (consuma crediti). */
export async function runCheck(
  serviceId: string,
  inputs: Record<string, unknown>,
  authToken: string,
): Promise<{ service_id: string; result: unknown; saldo_crediti: number }> {
  const res = await fetch(`${API_BASE}/api/kbot/check/${encodeURIComponent(serviceId)}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders(authToken) },
    body: JSON.stringify({ inputs }),
  });
  if (!res.ok) await parseErr(res, "Check non riuscito");
  return await res.json();
}

/** Esegue un Check express e scarica il PDF D1 (consuma crediti). */
export async function getCheckDocument(
  serviceId: string,
  inputs: Record<string, unknown>,
  authToken: string,
): Promise<Blob> {
  const res = await fetch(`${API_BASE}/api/kbot/check/${encodeURIComponent(serviceId)}/document`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders(authToken) },
    body: JSON.stringify({ inputs }),
  });
  if (!res.ok) await parseErr(res, "Generazione documento non riuscita");
  return await res.blob();
}

/** Catalogo dei tool a calcolo dell'ecosistema (auth richiesta). */
export async function listComputeTools(
  authToken: string,
  dominio?: string,
): Promise<{ tools: { tool_id: string; dominio: string; tool: string }[]; count: number }> {
  const url = new URL(`${API_BASE}/api/kbot/tools`);
  if (dominio) url.searchParams.set("dominio", dominio);
  const res = await fetch(url.toString(), { headers: { ...authHeaders(authToken) }, cache: "no-store" });
  if (!res.ok) await parseErr(res, "Impossibile leggere i tool");
  return await res.json();
}

/** Esegue un tool a calcolo deterministico dell'ecosistema. */
export async function runComputeTool(
  toolId: string,
  inputs: Record<string, unknown>,
  authToken: string,
): Promise<{ tool_id: string; result: unknown }> {
  const res = await fetch(`${API_BASE}/api/kbot/tool/${toolId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders(authToken) },
    body: JSON.stringify({ inputs }),
  });
  if (!res.ok) await parseErr(res, "Calcolo non riuscito");
  return await res.json();
}

export interface DeliverableFormField {
  id: string;
  label: string;
  tipo?: string;
  enum?: string[] | null;
  items_enum?: string[] | null;
  obbligatorio?: boolean;
}

/** Campi che il deliverable richiede (dal blueprint form.json via 8e). */
export async function getDeliverableForm(
  servizioId: string,
): Promise<{ service_id: string; title?: string; campi: DeliverableFormField[] }> {
  const res = await fetch(`${API_BASE}/api/kbot/deliverables/form/${encodeURIComponent(servizioId)}`, {
    cache: "no-store",
  });
  if (!res.ok) await parseErr(res, "Errore form deliverable");
  return res.json();
}

export interface BoostCatalogItem {
  id: string;
  label: string;
  ambito?: string;
}

/** Elenco dei documenti (boost) generabili via 8e — per il selettore nel pannello. */
export async function listBoostCatalog(): Promise<BoostCatalogItem[]> {
  const res = await fetch(`${API_BASE}/api/kbot/boost-catalog`, { cache: "no-store" });
  if (!res.ok) return [];
  const j = await res.json().catch(() => ({ servizi: [] }));
  return j.servizi ?? [];
}

/** Anteprima gratuita (gate W8): richiede login, consuma 1 delle 2 preview/mese.
 *  409 con reason "preview_quota_exhausted" se quota finita. */
export async function createPreview(
  sessionId: string,
  servizioId: string,
  inputs: Record<string, unknown>,
  authToken?: string | null,
): Promise<{ job_id: string; status: string; preview_count?: number; preview_limit?: number }> {
  const res = await fetch(`${API_BASE}/api/kbot/preview`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders(authToken) },
    body: JSON.stringify({ session_id: sessionId, servizio_id: servizioId, inputs }),
  });
  if (res.status === 409) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body?.detail?.message || "Anteprime gratuite esaurite per il mese.");
  }
  if (!res.ok) await parseErr(res, "Errore anteprima");
  return res.json();
}

export async function getDeliverable(jobId: string): Promise<DeliverableJob> {
  const res = await fetch(`${API_BASE}/api/kbot/deliverables/${encodeURIComponent(jobId)}`, {
    cache: "no-store",
  });
  if (!res.ok) await parseErr(res, "Errore stato deliverable");
  return res.json();
}

export type AutoGenResult =
  | { kind: "job"; job_id: string; servizio_id?: string; label?: string }
  | { kind: "checkout"; servizio_id?: string; label?: string; prezzo_eur?: number }
  | { kind: "unavailable"; message: string }
  // OUTPUT ALIGNMENT CHECKER: il backend ha giudicato il boost instradato non adatto
  // e propone quello giusto dal catalogo → il chiamante rigenera con servizio_suggerito.
  | { kind: "reroute"; servizio_suggerito: string; suggested_label?: string; message: string };

/** Genera il documento SENZA form: il backend sceglie il boost (instradato dalla
 * chat) e AUTO-COMPILA gli input dalla conversazione + file caricati.
 * 402 → serve pagamento (kind:"checkout"); 409 non_vendibile → kind:"unavailable";
 * 409 misaligned_deliverable → kind:"reroute" (rigenerare con servizio_suggerito).
 * `servizioId` forza un servizio esplicito (usato dal retry di reroute). */
export async function autoGenerateDeliverable(
  sessionId: string,
  authToken?: string | null,
  servizioId?: string,
): Promise<AutoGenResult> {
  const res = await fetch(`${API_BASE}/api/kbot/deliverables/auto`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders(authToken) },
    body: JSON.stringify({ session_id: sessionId, ...(servizioId ? { servizio_id: servizioId } : {}) }),
  });
  if (res.status === 402) {
    const d = ((await res.json().catch(() => ({}))).detail ?? {}) as Record<string, unknown>;
    return {
      kind: "checkout",
      servizio_id: d.servizio_id as string | undefined,
      label: d.label as string | undefined,
      prezzo_eur: d.prezzo_eur as number | undefined,
    };
  }
  if (res.status === 409) {
    const d = (await res.json().catch(() => ({}))).detail as Record<string, unknown> | undefined;
    // non_vendibile → documento non ancora disponibile; needs_input → mancano campi
    // obbligatori del boost (pre-flight): in entrambi i casi mostriamo il messaggio
    // (che NOMINA cosa manca) e fermiamo, invece di un errore generico.
    if (d && typeof d === "object" && d.reason === "misaligned_deliverable" && d.servizio_suggerito) {
      return {
        kind: "reroute",
        servizio_suggerito: d.servizio_suggerito as string,
        suggested_label: d.suggested_label as string | undefined,
        message: (d.message as string) ?? "Documento più adatto individuato.",
      };
    }
    if (d && typeof d === "object" && (d.reason === "non_vendibile" || d.reason === "needs_input")) {
      return { kind: "unavailable", message: (d.message as string) ?? "Documento non disponibile." };
    }
  }
  if (!res.ok) await parseErr(res, "Errore generazione documento");
  const data = await res.json();
  return { kind: "job", job_id: data.job_id, servizio_id: data.servizio_id, label: data.label };
}

/** Rende duraturo il deliverable: lo carica su Storage e lo lega alla sessione
 * (→ compare in dashboard/storico). Ritorna l'URL durevole del PDF. */
export async function saveDeliverable(
  sessionId: string,
  jobId: string,
  authToken?: string | null,
): Promise<string | null> {
  const res = await fetch(`${API_BASE}/api/kbot/deliverables/save`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders(authToken) },
    body: JSON.stringify({ session_id: sessionId, job_id: jobId }),
  });
  if (!res.ok) return null; // best-effort: il download dal /pdf resta comunque
  const j = await res.json().catch(() => ({}));
  return j.pdf_url ?? null;
}

/** Polla finché rendered/refused/error o timeout. onTick per aggiornare la UI. */
export async function pollDeliverable(
  jobId: string,
  onTick?: (job: DeliverableJob) => void,
  opts: { intervalMs?: number; timeoutMs?: number } = {},
): Promise<DeliverableJob> {
  const interval = opts.intervalMs ?? 4000;
  // La generazione 8e profonda (16 pagine, per-sezione) su modello LOCALE (gpt-oss)
  // dura MOLTI minuti. Timeout allineato al JOB_TIMEOUT dell'8e (~45 min) così il
  // polling NON "fallisce" mentre il job è ancora in corso lato server. Il chiamante
  // distingue il timeout (error === "timeout") da un refuse/errore reale.
  const timeout = opts.timeoutMs ?? 2_700_000;
  const start = Date.now();
  let lastJob: DeliverableJob | null = null;
  for (;;) {
    try {
      const job = await getDeliverable(jobId);
      lastJob = job;
      onTick?.(job);
      if (["rendered", "refused", "error"].includes(job.status)) return job;
    } catch {
      // Errore transitorio (429 rate-limit, blip di rete): NON fatale durante il
      // polling. La generazione 8e dura minuti → riprova fino al timeout.
    }
    if (Date.now() - start > timeout) {
      return lastJob
        ? { ...lastJob, status: "error", error: "timeout" }
        : ({ job_id: jobId, status: "error", error: "timeout" } as DeliverableJob);
    }
    await new Promise((r) => setTimeout(r, interval));
  }
}
