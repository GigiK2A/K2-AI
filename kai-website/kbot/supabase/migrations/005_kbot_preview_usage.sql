-- Migration 005 — Gate preview (handoff W8)
-- Applicata su Supabase KAI via MCP il 2026-06-08.
--
-- Contatore preview gratuite per utente/mese (max 2, reset mensile
-- use-it-or-lose-it). Lo stato vive nel K-BOT backend (l'8e resta stateless):
-- il gate decide auth_level=PREVIEW|FULL e l'8e compone di conseguenza.

CREATE TABLE IF NOT EXISTS kbot_preview_usage (
  user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  year_month  TEXT NOT NULL,            -- 'YYYY-MM'
  count       INT  NOT NULL DEFAULT 0,
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (user_id, year_month)
);

ALTER TABLE kbot_preview_usage ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS kbot_preview_usage_select_own ON kbot_preview_usage;
CREATE POLICY kbot_preview_usage_select_own ON kbot_preview_usage
  FOR SELECT USING (auth.uid() = user_id);

-- Incremento atomico con cap. Ritorna il nuovo count se < limite, NULL se la
-- quota è esaurita (il backend interpreta NULL come "invita al documento").
-- Hardening (advisor): search_path fisso + EXECUTE solo a service_role (il
-- backend la chiama; vietata via /rest/v1/rpc ad anon/authenticated, altrimenti
-- un utente potrebbe manipolare il contatore altrui con p_user/p_limit arbitrari).
CREATE OR REPLACE FUNCTION kbot_preview_consume(p_user UUID, p_ym TEXT, p_limit INT)
RETURNS INT
LANGUAGE plpgsql SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE new_count INT;
BEGIN
  INSERT INTO kbot_preview_usage(user_id, year_month, count)
    VALUES (p_user, p_ym, 1)
  ON CONFLICT (user_id, year_month) DO UPDATE
    SET count = kbot_preview_usage.count + 1, updated_at = now()
    WHERE kbot_preview_usage.count < p_limit
  RETURNING count INTO new_count;
  RETURN new_count;
END $$;

REVOKE ALL ON FUNCTION kbot_preview_consume(UUID, TEXT, INT) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION kbot_preview_consume(UUID, TEXT, INT) TO service_role;
