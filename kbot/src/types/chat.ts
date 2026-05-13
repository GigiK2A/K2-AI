export type Mode = "lead" | "report";

export type SkillSummary = {
  id: string;
  name: string;
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  ts: number;
  attachments?: UploadedFile[];
  reportPdfUrl?: string | null;
  reportPdfDownloadUrl?: string | null;
  reportPdfFilename?: string | null;
  reportHtmlUrl?: string | null;
  reportHtmlDownloadUrl?: string | null;
  hasPaid?: boolean;
};

export type UploadedFile = {
  fileId: string;
  name: string;
  mimeType: string;
  size: number;
  preview: string;
};

export type Conversation = {
  id: string;
  title: string;
  mode: Mode;
  messages: ChatMessage[];
};

export type ChatApiResponse = {
  answer?: string;
  usedSkills?: string[];
  reportPdfUrl?: string | null;
  reportPdfDownloadUrl?: string | null;
  reportPdfFilename?: string | null;
  reportHtmlUrl?: string | null;
  reportHtmlDownloadUrl?: string | null;
  detail?: string;
};

export type FeedbackPayload = {
  reportId: string;
  rating: number;
  comment: string;
};
