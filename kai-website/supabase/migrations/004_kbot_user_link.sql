-- Migration 004 — link kbot_sessions to Supabase auth users + cleanup legacy kbot tables.
-- Run on the kai-website Supabase project (SQL Editor).
-- Idempotent: safe to re-run.

-- 1. Add user_id to kbot_sessions (nullable: anonymous sessions still allowed).
ALTER TABLE kbot_sessions
  ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_kbot_sessions_user_id
  ON kbot_sessions(user_id) WHERE user_id IS NOT NULL;

-- 2. Drop legacy tables from the old standalone kbot (Clerk-based).
-- They are not referenced by the new backend.
DROP TABLE IF EXISTS conversations CASCADE;
DROP TABLE IF EXISTS analytics_events CASCADE;
DROP TABLE IF EXISTS feedback CASCADE;
