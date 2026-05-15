import type { ApprovalKind, ApprovalStatus } from "@/types/approval";

export const APPROVAL_KIND_ORDER: ApprovalKind[] = [
  "email",
  "proposta",
  "post",
  "reply",
  "altro",
];

export const APPROVAL_KIND_LABELS: Record<ApprovalKind, string> = {
  email: "Email",
  proposta: "Proposta",
  post: "Post",
  reply: "Reply",
  altro: "Altro",
};

// Tailwind classes for the kind badge (background + text)
export const APPROVAL_KIND_COLORS: Record<ApprovalKind, string> = {
  email: "bg-sky-500/15 text-sky-300 border border-sky-500/30",
  proposta: "bg-amber-500/15 text-amber-300 border border-amber-500/30",
  post: "bg-fuchsia-500/15 text-fuchsia-300 border border-fuchsia-500/30",
  reply: "bg-emerald-500/15 text-emerald-300 border border-emerald-500/30",
  altro: "bg-slate-500/15 text-slate-300 border border-slate-500/30",
};

export const APPROVAL_STATUS_LABELS: Record<ApprovalStatus, string> = {
  pending: "In attesa",
  approved: "Approvato",
  rejected: "Rifiutato",
  edited_and_sent: "Modificato e inviato",
};

const RTF = new Intl.RelativeTimeFormat("it", { numeric: "auto" });

export function formatRelativeTime(iso: string | null | undefined): string {
  if (!iso) return "—";
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "—";
  const diffSec = Math.round((then - Date.now()) / 1000);
  const abs = Math.abs(diffSec);

  if (abs < 60) return RTF.format(diffSec, "second");
  const diffMin = Math.round(diffSec / 60);
  if (Math.abs(diffMin) < 60) return RTF.format(diffMin, "minute");
  const diffH = Math.round(diffMin / 60);
  if (Math.abs(diffH) < 24) return RTF.format(diffH, "hour");
  const diffD = Math.round(diffH / 24);
  if (Math.abs(diffD) < 30) return RTF.format(diffD, "day");
  const diffMo = Math.round(diffD / 30);
  if (Math.abs(diffMo) < 12) return RTF.format(diffMo, "month");
  const diffY = Math.round(diffMo / 12);
  return RTF.format(diffY, "year");
}

export function isApprovalKind(value: string): value is ApprovalKind {
  return (APPROVAL_KIND_ORDER as string[]).includes(value);
}
