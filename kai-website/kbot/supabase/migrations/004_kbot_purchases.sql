-- Migration 004 — Acquisti (multi-prodotto: Check, tappe, Boost)
-- Run via Supabase SQL Editor o `supabase db push`.
--
-- Traccia ogni acquisto di un servizio del catalogo (oltre al report 19€ legacy
-- gestito su kbot_sessions). Necessaria per:
--   * percorsi a tappe (verifica ordine + sconto completamento)
--   * versioning end-to-end (riproducibilità report per reclamo — vedi
--     docs/interfaccia-kbot-8e.md §4): logga la terna catalog/blueprint/snapshot
--     + versione motore 8e con cui il deliverable è stato generato.
-- RLS: l'utente vede solo i propri acquisti.

CREATE TABLE IF NOT EXISTS kbot_purchases (
  id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id                     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  kbot_session_id             UUID,

  -- Cosa è stato comprato (riferimenti al catalog.json)
  servizio_id                 TEXT NOT NULL,
  servizio_tipo               TEXT NOT NULL CHECK (servizio_tipo IN ('consumo','tappa','servizio','retainer')),
  percorso_id                 TEXT,

  -- Pagamento
  prezzo_pagato_cents         INT NOT NULL,
  stripe_session_id           TEXT,

  -- Generazione deliverable (8e)
  job_id                      TEXT,                  -- id job 8e
  deliverable_url             TEXT,                  -- PDF su Supabase Storage del K-BOT
  status                      TEXT NOT NULL DEFAULT 'paid'
                                CHECK (status IN ('paid','generating','delivered','refused','error','refunded')),

  -- Versioning end-to-end (riproducibilità) — vedi membrana §4
  catalog_version             TEXT,
  blueprint_version           TEXT,
  grounding_snapshot_version  TEXT,
  engine_version              TEXT,

  created_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at                  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS kbot_purchases_user_path
  ON kbot_purchases (user_id, percorso_id, created_at DESC);

CREATE INDEX IF NOT EXISTS kbot_purchases_user_servizio
  ON kbot_purchases (user_id, servizio_id);

CREATE UNIQUE INDEX IF NOT EXISTS kbot_purchases_stripe_session
  ON kbot_purchases (stripe_session_id)
  WHERE stripe_session_id IS NOT NULL;

ALTER TABLE kbot_purchases ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS kbot_purchases_select_own ON kbot_purchases;
CREATE POLICY kbot_purchases_select_own ON kbot_purchases
  FOR SELECT USING (auth.uid() = user_id);

-- INSERT/UPDATE solo da service_role (webhook Stripe + generate). Nessuna policy
-- per anon/authenticated: il client non scrive acquisti direttamente.
