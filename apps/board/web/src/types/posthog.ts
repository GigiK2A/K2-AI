export interface PostHogKbotKpis {
  kbot_open: number;
  kbot_message_sent: number;
  kbot_report_requested: number;
  kbot_report_generated: number;
}

export interface PostHogProfileClick {
  profile_id: string;
  count: number;
}

export interface PostHogRecentEvent {
  timestamp: string;
  event: string;
  distinct_id: string;
}

export interface KbotAnalytics {
  configured: boolean;
  error?: string;
  kpis: PostHogKbotKpis;
  profile_clicks: PostHogProfileClick[];
  recent_events: PostHogRecentEvent[];
}
