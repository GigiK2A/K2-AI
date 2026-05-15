export interface Memo {
  id: string;
  subject: string;
  body: string;
  tags: string[];
  contact_id: string | null;
  lead_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface MemoCreatePayload {
  subject: string;
  body: string;
  tags?: string[];
  contact_id?: string | null;
  lead_id?: string | null;
}

export type MemoUpdatePayload = Partial<MemoCreatePayload>;
