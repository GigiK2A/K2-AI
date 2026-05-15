export type ApprovalKind = "email" | "proposta" | "post" | "reply" | "altro";

export type ApprovalStatus =
  | "pending"
  | "approved"
  | "rejected"
  | "edited_and_sent";

export interface Approval {
  id: string;
  kind: ApprovalKind;
  title: string;
  body: string;
  rationale: string | null;
  lead_id: string | null;
  contact_id: string | null;
  status: ApprovalStatus;
  decision_note: string | null;
  created_at: string;
  decided_at: string | null;
}

export interface ApprovalCreatePayload {
  kind: ApprovalKind;
  title: string;
  body: string;
  rationale?: string | null;
  lead_id?: string | null;
  contact_id?: string | null;
}

export interface ApprovalUpdatePayload {
  kind?: ApprovalKind;
  title?: string;
  body?: string;
  rationale?: string | null;
  lead_id?: string | null;
  contact_id?: string | null;
  status?: ApprovalStatus;
  decision_note?: string | null;
  decided_at?: string | null;
}
