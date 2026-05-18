import type { UploadedFile as ApiUploadedFile } from "@/lib/api";

export type Mode = "lead" | "report";

export type SkillSummary = {
  id: string;
  name: string;
};

/** Re-export for legacy components that imported UploadedFile from "@/types/chat". */
export type UploadedFile = ApiUploadedFile;

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  ts: number;
  attachments?: ApiUploadedFile[];
  /** Set true when the assistant emitted the V2 summary block — UI shows the "Scarica PDF" CTA. */
  reportReady?: boolean;
  /** Server-side kbot_sessions.id, attached to assistant messages once known. */
  sessionId?: string;
  /** Pre-generated PDF URL (if backend returned it inline). Usually null until checkout. */
  reportPdfUrl?: string | null;
  hasPaid?: boolean;
};

export type Conversation = {
  id: string;
  title: string;
  mode: Mode;
  messages: ChatMessage[];
  /** Backend kbot_sessions.id — null until first ensureSession in this conv. */
  kbotSessionId?: string | null;
  /** Backend kbot_conversations.id — null per anon, valorizzato dopo POST /conversations. */
  remoteId?: string | null;
};
