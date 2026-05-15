export type LeadStatus =
  | "nuovo"
  | "contatto"
  | "proposta"
  | "chiuso_vinto"
  | "chiuso_perso";

export interface HighValueLead {
  id: string;
  title: string;
  status: LeadStatus;
  value_eur: number;
  probability: number;
}

export interface NextMeeting {
  id: string;
  title: string;
  starts_at: string;
  meet_link?: string | null;
}

export type AlertKind =
  | "overdue_task"
  | "stale_lead"
  | "pending_approval"
  | string;

export type AlertSeverity = "high" | "medium" | "low";

export interface OverviewAlert {
  kind: AlertKind;
  title: string;
  ref_id?: string | null;
  severity: AlertSeverity;
}

export interface OverviewResponse {
  generated_at: string;
  leads: {
    active: number;
    by_status: Partial<Record<LeadStatus, number>>;
    stale_count: number;
    high_value: HighValueLead[];
  };
  tasks: {
    overdue: number;
    today: number;
    this_week: number;
  };
  approvals_pending: number;
  revenue_mtd_cents: number;
  next_meeting: NextMeeting | null;
  alerts: OverviewAlert[];
}
