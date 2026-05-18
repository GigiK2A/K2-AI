-- Migration 002 — Conversazioni persistenti + chunk RAG
-- Run via Supabase SQL Editor or `supabase db push`.
--
-- Aggiunge:
--   * kbot_conversations: lista conv lato sidebar legate all'utente loggato.
--     Anon mantiene comportamento in-memory (no row).
--   * kbot_file_chunks: chunk testuali per file con page_number per citazioni
--     e per retrieval BM25 lato backend (no embeddings — vedi report).
-- RLS: solo owner accede ai propri record.

-- =========================================
-- 1) kbot_conversations
-- =========================================
CREATE TABLE IF NOT EXISTS kbot_conversations (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id           UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  title             TEXT NOT NULL DEFAULT 'Nuova conversazione',
  mode              TEXT NOT NULL DEFAULT 'report',
  kbot_session_id   UUID,
  deleted_at        TIMESTAMPTZ,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS kbot_conversations_user_created
  ON kbot_conversations (user_id, created_at DESC)
  WHERE deleted_at IS NULL;

ALTER TABLE kbot_conversations ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS kbot_conv_select_own ON kbot_conversations;
CREATE POLICY kbot_conv_select_own ON kbot_conversations
  FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS kbot_conv_insert_own ON kbot_conversations;
CREATE POLICY kbot_conv_insert_own ON kbot_conversations
  FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS kbot_conv_update_own ON kbot_conversations;
CREATE POLICY kbot_conv_update_own ON kbot_conversations
  FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS kbot_conv_delete_own ON kbot_conversations;
CREATE POLICY kbot_conv_delete_own ON kbot_conversations
  FOR DELETE USING (auth.uid() = user_id);

-- =========================================
-- 2) kbot_file_chunks  (RAG / citazioni)
-- =========================================
-- Niente pgvector: l'MVP usa BM25 in-memory lato backend (vedi prompts.py).
-- Lasciamo `embedding` come jsonb opzionale per upgrade futuro senza migration.
CREATE TABLE IF NOT EXISTS kbot_file_chunks (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id   UUID NOT NULL,
  file_name    TEXT NOT NULL,
  page_number  INT NOT NULL DEFAULT 0,
  chunk_index  INT NOT NULL DEFAULT 0,
  content      TEXT NOT NULL,
  embedding    JSONB,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS kbot_file_chunks_session
  ON kbot_file_chunks (session_id);

-- Accesso ai chunk: passa sempre via service-role lato backend.
-- RLS abilitata + nessuna policy = nessuno legge direttamente. OK.
ALTER TABLE kbot_file_chunks ENABLE ROW LEVEL SECURITY;
