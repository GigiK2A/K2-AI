export interface MeetingAttendee {
  email?: string;
  name?: string;
  status?: string;
}

export interface Meeting {
  id: string;
  external_id: string | null;
  title: string;
  description: string | null;
  starts_at: string;
  ends_at: string;
  location: string | null;
  meet_link: string | null;
  attendees: MeetingAttendee[];
  contact_id: string | null;
  lead_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface MeetingCreatePayload {
  title: string;
  description?: string | null;
  starts_at: string;
  ends_at: string;
  location?: string | null;
  meet_link?: string | null;
  attendees?: MeetingAttendee[];
  contact_id?: string | null;
  lead_id?: string | null;
}

export type MeetingUpdatePayload = Partial<MeetingCreatePayload>;
