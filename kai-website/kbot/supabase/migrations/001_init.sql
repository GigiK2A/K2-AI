-- Run this in Supabase Dashboard → SQL Editor
-- Or via: supabase db push (if CLI configured)

-- Memoria conversazioni report premium (per utenti Clerk loggati)
CREATE TABLE IF NOT EXISTS conversations (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clerk_user_id   TEXT NOT NULL,
  conversation_id TEXT NOT NULL,
  role            TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
  content         TEXT NOT NULL,
  context_files   JSONB DEFAULT '[]',
  ts              TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS conversations_user_conv_ts
  ON conversations (clerk_user_id, conversation_id, ts);

-- Analytics eventi
CREATE TABLE IF NOT EXISTS analytics_events (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_type    TEXT NOT NULL,
  clerk_user_id TEXT,
  session_id    TEXT,
  payload       JSONB DEFAULT '{}',
  ts            TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS analytics_events_type_ts
  ON analytics_events (event_type, ts);

-- Feedback report
CREATE TABLE IF NOT EXISTS feedback (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clerk_user_id TEXT,
  report_id     TEXT,
  rating        INT CHECK (rating BETWEEN 1 AND 5),
  comment       TEXT,
  ts            TIMESTAMPTZ DEFAULT now()
);
