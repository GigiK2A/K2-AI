-- Migration 008 — kbot_client_memory: memoria-profilo cross-sessione del cliente.
-- Esegui su Supabase SQL Editor del progetto kai-website. Idempotente.
--
-- PERCHÉ ESISTE QUESTA MIGRATION: la tabella era usata da backend/app/lib/profile.py da
-- mesi senza essere mai versionata qui. `profile.load()` è fail-open (logga e ritorna None),
-- quindi se la tabella non esiste in un ambiente la memoria cross-sessione è un NO-OP
-- SILENZIOSO: il bot richiede ogni volta dati che l'utente ha già dato, e nessun errore lo
-- segnala. Verifica lo stato reale con GET /api/kbot/diagnostics (campo `client_memory`).

CREATE TABLE IF NOT EXISTS kbot_client_memory (
  user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  profile JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_kbot_client_memory_updated_at
  ON kbot_client_memory(updated_at DESC);

-- RLS: owner-only (il service-role del backend bypassa). L'utente deve poter LEGGERE ciò
-- che K-BOT ricorda di lui (GDPR art. 15) e correggerlo (art. 16).
ALTER TABLE kbot_client_memory ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS kbot_client_memory_owner_select ON kbot_client_memory;
CREATE POLICY kbot_client_memory_owner_select ON kbot_client_memory
  FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS kbot_client_memory_owner_insert ON kbot_client_memory;
CREATE POLICY kbot_client_memory_owner_insert ON kbot_client_memory
  FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS kbot_client_memory_owner_update ON kbot_client_memory;
CREATE POLICY kbot_client_memory_owner_update ON kbot_client_memory
  FOR UPDATE USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS kbot_client_memory_owner_delete ON kbot_client_memory;
CREATE POLICY kbot_client_memory_owner_delete ON kbot_client_memory
  FOR DELETE USING (auth.uid() = user_id);
