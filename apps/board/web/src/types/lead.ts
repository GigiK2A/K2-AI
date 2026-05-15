export type LeadStatus =
  | "nuovo"
  | "contatto"
  | "proposta"
  | "chiuso_vinto"
  | "chiuso_perso";

export type LeadSource =
  | "k_bot"
  | "contact_form"
  | "newsletter"
  | "referral"
  | "outbound"
  | "other";

export interface Lead {
  id: string;
  contact_id: string | null;
  title: string;
  description: string | null;
  status: LeadStatus;
  source: LeadSource;
  value_eur: number | null;
  probability: number;
  next_action_at: string | null;
  next_action_note: string | null;
  kbot_session_id: string | null;
  created_at: string;
  updated_at: string;
  closed_at: string | null;
}

export interface LeadCreatePayload {
  contact_id?: string | null;
  title: string;
  description?: string | null;
  status?: LeadStatus;
  source?: LeadSource;
  value_eur?: number | null;
  probability?: number;
  next_action_at?: string | null;
  next_action_note?: string | null;
}

export type LeadUpdatePayload = Partial<LeadCreatePayload> & {
  closed_at?: string | null;
};

export interface Contact {
  id: string;
  company: string | null;
  person_name: string | null;
  email: string | null;
  phone: string | null;
  notes: string | null;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface ContactCreatePayload {
  company?: string | null;
  person_name?: string | null;
  email?: string | null;
  phone?: string | null;
  notes?: string | null;
  tags?: string[];
}
