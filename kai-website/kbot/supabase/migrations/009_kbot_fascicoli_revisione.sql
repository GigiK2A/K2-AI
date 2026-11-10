-- Migration 009 — contatore di revisione dei record (aggiornamento per ID con controllo di concorrenza e idempotenza).
-- Additiva: una colonna con default. Rollback: 009_rollback.sql. Idempotente.
ALTER TABLE public.kbot_fascicolo_voci ADD COLUMN IF NOT EXISTS revisione INT NOT NULL DEFAULT 1;
