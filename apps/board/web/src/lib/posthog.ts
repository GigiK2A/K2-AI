// Server-side PostHog HogQL query helper.
// IMPORTANT: never expose POSTHOG_PERSONAL_API_KEY to the client.

import type {
  KbotAnalytics,
  PostHogKbotKpis,
  PostHogProfileClick,
  PostHogRecentEvent,
} from "@/types/posthog";

const DEFAULT_HOST = "https://eu.i.posthog.com";
const DEFAULT_PROJECT_ID = "179781";

interface HogQLResponse {
  results?: unknown[][];
  columns?: string[];
}

async function runHogQL(
  host: string,
  projectId: string,
  apiKey: string,
  query: string,
): Promise<HogQLResponse> {
  const res = await fetch(`${host}/api/projects/${projectId}/query/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify({ query: { kind: "HogQLQuery", query } }),
    cache: "no-store",
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`PostHog ${res.status}: ${text.slice(0, 200)}`);
  }
  return (await res.json()) as HogQLResponse;
}

function asNumber(v: unknown): number {
  if (typeof v === "number") return v;
  if (typeof v === "string") {
    const n = Number(v);
    return Number.isFinite(n) ? n : 0;
  }
  return 0;
}

function asString(v: unknown): string {
  if (v == null) return "";
  if (typeof v === "string") return v;
  return String(v);
}

export async function fetchKbotAnalytics(): Promise<KbotAnalytics> {
  const apiKey = process.env.POSTHOG_PERSONAL_API_KEY;
  const host = process.env.POSTHOG_HOST || DEFAULT_HOST;
  const projectId = process.env.POSTHOG_PROJECT_ID || DEFAULT_PROJECT_ID;

  const emptyKpis: PostHogKbotKpis = {
    kbot_open: 0,
    kbot_message_sent: 0,
    kbot_report_requested: 0,
    kbot_report_generated: 0,
  };

  if (!apiKey) {
    return {
      configured: false,
      kpis: emptyKpis,
      profile_clicks: [],
      recent_events: [],
    };
  }

  try {
    const kpiQuery = `
      SELECT
        countIf(event = 'kbot_open') AS kbot_open,
        countIf(event = 'kbot_message_sent') AS kbot_message_sent,
        countIf(event = 'kbot_report_requested') AS kbot_report_requested,
        countIf(event = 'kbot_report_generated') AS kbot_report_generated
      FROM events
      WHERE timestamp >= now() - INTERVAL 30 DAY
    `;

    const clicksQuery = `
      SELECT
        coalesce(toString(properties.profile_id), 'unknown') AS profile_id,
        count() AS c
      FROM events
      WHERE event = 'profile_click'
        AND timestamp >= now() - INTERVAL 30 DAY
      GROUP BY profile_id
      ORDER BY c DESC
      LIMIT 10
    `;

    const recentQuery = `
      SELECT timestamp, event, distinct_id
      FROM events
      WHERE event IN ('kbot_open', 'kbot_message_sent', 'kbot_report_requested', 'kbot_report_generated', 'profile_click')
        AND timestamp >= now() - INTERVAL 30 DAY
      ORDER BY timestamp DESC
      LIMIT 50
    `;

    const [kpiRes, clicksRes, recentRes] = await Promise.all([
      runHogQL(host, projectId, apiKey, kpiQuery),
      runHogQL(host, projectId, apiKey, clicksQuery),
      runHogQL(host, projectId, apiKey, recentQuery),
    ]);

    const kpiRow = kpiRes.results?.[0] ?? [];
    const kpis: PostHogKbotKpis = {
      kbot_open: asNumber(kpiRow[0]),
      kbot_message_sent: asNumber(kpiRow[1]),
      kbot_report_requested: asNumber(kpiRow[2]),
      kbot_report_generated: asNumber(kpiRow[3]),
    };

    const profile_clicks: PostHogProfileClick[] = (clicksRes.results ?? []).map(
      (row) => ({
        profile_id: asString(row[0]) || "unknown",
        count: asNumber(row[1]),
      }),
    );

    const recent_events: PostHogRecentEvent[] = (recentRes.results ?? []).map(
      (row) => ({
        timestamp: asString(row[0]),
        event: asString(row[1]),
        distinct_id: asString(row[2]),
      }),
    );

    return {
      configured: true,
      kpis,
      profile_clicks,
      recent_events,
    };
  } catch (err) {
    return {
      configured: true,
      error: err instanceof Error ? err.message : "Errore PostHog",
      kpis: emptyKpis,
      profile_clicks: [],
      recent_events: [],
    };
  }
}
