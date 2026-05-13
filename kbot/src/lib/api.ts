import { ChatApiResponse, Mode, SkillSummary, UploadedFile } from "@/types/chat";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export async function fetchSkills(): Promise<SkillSummary[]> {
  const res = await fetch(`${API_BASE}/api/skills`, { cache: "no-store" });
  if (!res.ok) throw new Error("Skills non disponibili");
  const data = await res.json();
  return data.skills ?? [];
}

export async function matchSkills(input: string, conversationId: string, contextFiles: string[]): Promise<SkillSummary[]> {
  const res = await fetch(`${API_BASE}/api/skills/match`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      input,
      conversation_id: conversationId,
      context_files: contextFiles,
      limit: 6,
    }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Match skill non disponibile");
  }
  const data = await res.json();
  return data.skills ?? [];
}

export async function fetchReportAccess(): Promise<{ enabled: boolean; paymentLink: string | null }> {
  const res = await fetch(`${API_BASE}/api/report-access`, { cache: "no-store" });
  if (!res.ok) throw new Error("Report access non disponibile");
  const data = await res.json();
  return { enabled: Boolean(data.enabled), paymentLink: data.paymentLink ?? null };
}

export async function sendChat(
  input: string,
  mode: Mode,
  paid: boolean,
  conversationId: string,
  contextFiles: string[],
  authToken?: string | null,
): Promise<{
  answer: string;
  usedSkills: string[];
  reportPdfUrl: string | null;
  reportPdfDownloadUrl: string | null;
  reportPdfFilename: string | null;
  reportHtmlUrl: string | null;
  reportHtmlDownloadUrl: string | null;
}> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (authToken) headers["Authorization"] = `Bearer ${authToken}`;
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      input,
      mode,
      paid,
      conversation_id: conversationId,
      context_files: contextFiles,
    }),
  });

  const data = (await res.json()) as ChatApiResponse;

  if (!res.ok) {
    throw new Error(data.detail || "Errore backend");
  }

  return {
    answer: data.answer ?? "",
    usedSkills: data.usedSkills ?? [],
    reportPdfUrl: data.reportPdfUrl ?? null,
    reportPdfDownloadUrl: data.reportPdfDownloadUrl ?? null,
    reportPdfFilename: data.reportPdfFilename ?? null,
    reportHtmlUrl: data.reportHtmlUrl ?? null,
    reportHtmlDownloadUrl: data.reportHtmlDownloadUrl ?? null,
  };
}

export async function uploadContextFiles(files: File[]): Promise<UploadedFile[]> {
  if (!files.length) return [];
  const body = new FormData();
  files.forEach((f) => body.append("files", f));

  const res = await fetch(`${API_BASE}/api/upload`, {
    method: "POST",
    body,
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Errore upload file");
  }
  const data = await res.json();
  return data.files ?? [];
}

export async function saveLead(payload: { name: string; email: string; need: string; company?: string }) {
  const res = await fetch(`${API_BASE}/api/leads`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Errore salvataggio lead");
  }
}

export async function startCheckout(authToken: string): Promise<string> {
  const res = await fetch(`${API_BASE}/api/stripe/checkout`, {
    method: "POST",
    headers: { "Authorization": `Bearer ${authToken}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Errore checkout");
  return data.url as string;
}

export interface DashboardReport {
  id: string;
  title: string;
  filename: string;
  created_at: string;
  has_html: boolean;
  url: string;
  download_url: string;
  html_url: string | null;
}

export interface DashboardData {
  reports: DashboardReport[];
  stats: { total_reports: number; last_report_at: string | null };
  account: { has_paid: boolean; clerk_user_id: string };
}

export async function fetchDashboard(authToken: string): Promise<DashboardData> {
  const res = await fetch(`${API_BASE}/api/dashboard`, {
    headers: { Authorization: `Bearer ${authToken}` },
    cache: "no-store",
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Errore dashboard");
  }
  return res.json() as Promise<DashboardData>;
}

export async function submitFeedback(
  reportId: string,
  rating: number,
  comment: string,
  authToken: string,
): Promise<void> {
  await fetch(`${API_BASE}/api/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "Authorization": `Bearer ${authToken}` },
    body: JSON.stringify({ report_id: reportId, rating, comment }),
  });
}
