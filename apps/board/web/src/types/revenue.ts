export interface RevenueEvent {
  id: string;
  external_id: string;
  customer_email: string | null;
  customer_id: string | null;
  amount_cents: number;
  currency: string;
  description: string | null;
  status: string;
  occurred_at: string;
  lead_id: string | null;
  raw: unknown;
  created_at: string;
}
