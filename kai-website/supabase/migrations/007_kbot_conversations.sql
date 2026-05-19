-- Migration 007 — kbot_conversations: sidebar history per utenti loggati.
-- Esegui su Supabase SQL Editor del progetto kai-website. Idempotente.

CREATE TABLE IF NOT EXISTS kbot_conversations (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  title TEXT NOT NULL DEFAULT 'Nuova conversazione',
  mode TEXT NOT NULL DEFAULT 'report' CHECK (mode IN ('report', 'lead')),
  kbot_session_id UUID REFERENCES kbot_sessions(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  deleted_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_kbot_conv_user_id
  ON kbot_conversations(user_id) WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_kbot_conv_session_id
  ON kbot_conversations(kbot_session_id) WHERE kbot_session_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_kbot_conv_created_at
  ON kbot_conversations(created_at DESC);

-- RLS: owner-only access (service-role bypassa).
ALTER TABLE kbot_conversations ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS kbot_conv_owner_select ON kbot_conversations;
CREATE POLICY kbot_conv_owner_select ON kbot_conversations
  FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS kbot_conv_owner_insert ON kbot_conversations;
CREATE POLICY kbot_conv_owner_insert ON kbot_conversations
  FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS kbot_conv_owner_update ON kbot_conversations;
CREATE POLICY kbot_conv_owner_update ON kbot_conversations
  FOR UPDATE USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
