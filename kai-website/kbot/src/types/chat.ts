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
  /** Cached follow-up question suggestions (3 chips) for long assistant reports. */
  followUps?: string[];
  /** Fase reale del turno in corso (evento del server); assente a turno concluso. */
  fase?: "fonti" | "generazione" | "verifica";
  /** Messaggio d'errore se il turno si è interrotto: il testo già prodotto resta e si può riprovare. */
  errore?: string;
  /** Messaggio creato solo nel browser (non salvato dal server): non conta nell'indice dei messaggi del backend. */
  local?: boolean;
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
