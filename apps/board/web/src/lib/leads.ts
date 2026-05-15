import type { Lead, LeadSource, LeadStatus } from "@/types/lead";

export const LEAD_STATUS_ORDER: LeadStatus[] = [
  "nuovo",
  "contatto",
  "proposta",
  "chiuso_vinto",
  "chiuso_perso",
];

export const LEAD_STATUS_LABELS: Record<LeadStatus, string> = {
  nuovo: "Nuovo",
  contatto: "Contatto",
  proposta: "Proposta",
  chiuso_vinto: "Chiuso vinto",
  chiuso_perso: "Chiuso perso",
};

export const LEAD_STATUS_COLORS: Record<LeadStatus, string> = {
  nuovo: "bg-[color:var(--color-teal)]",
  contatto: "bg-sky-500",
  proposta: "bg-amber-500",
  chiuso_vinto: "bg-[color:var(--color-success)]",
  chiuso_perso: "bg-[color:var(--color-danger)]",
};

export const SOURCE_LABELS: Record<LeadSource, string> = {
  k_bot: "K-BOT",
  contact_form: "Form contatti",
  newsletter: "Newsletter",
  referral: "Referral",
  outbound: "Outbound",
  other: "Altro",
};

const EURO_FMT = new Intl.NumberFormat("it-IT", {
  style: "currency",
  currency: "EUR",
  maximumFractionDigits: 0,
});

export function formatLeadValue(lead: Pick<Lead, "value_eur">): string {
  if (lead.value_eur === null || lead.value_eur === undefined) return "—";
  return EURO_FMT.format(lead.value_eur);
}

export function formatProbability(p: number): string {
  return `${Math.round(p)}%`;
}

export function isLeadStatus(value: string): value is LeadStatus {
  return (LEAD_STATUS_ORDER as string[]).includes(value);
}
