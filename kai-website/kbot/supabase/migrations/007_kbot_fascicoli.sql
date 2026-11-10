-- Migration 007 — memoria aziendale: fascicoli persistenti (commesse, clienti, contratti…), voci tracciate e documenti.
-- Isolamento: ogni riga porta user_id (l'azienda/utente); il backend filtra SEMPRE per user_id (service role) e le tabelle
-- hanno RLS attiva senza policy: nessun accesso diretto dal browser. Idempotente.
CREATE TABLE IF NOT EXISTS public.kbot_fascicoli (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID NOT NULL,
  tipo        TEXT NOT NULL DEFAULT 'commessa',   -- commessa|cliente|fornitore|contratto|controversia|consulenza|progetto|investimento
  codice      TEXT,
  titolo      TEXT NOT NULL,
  stato       TEXT NOT NULL DEFAULT 'aperto',     -- aperto|in_corso|chiuso
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at  TIMESTAMPTZ
);
CREATE UNIQUE INDEX IF NOT EXISTS kbot_fascicoli_user_codice ON public.kbot_fascicoli (user_id, tipo, codice) WHERE codice IS NOT NULL AND deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS kbot_fascicoli_user ON public.kbot_fascicoli (user_id, updated_at DESC);
ALTER TABLE public.kbot_fascicoli ENABLE ROW LEVEL SECURITY;

CREATE TABLE IF NOT EXISTS public.kbot_fascicolo_voci (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  fascicolo_id  UUID NOT NULL REFERENCES public.kbot_fascicoli(id) ON DELETE CASCADE,
  user_id       UUID NOT NULL,
  tipo          TEXT NOT NULL DEFAULT 'dato',     -- dato|decisione|scadenza|analisi|anomalia|nota|attivita
  chiave        TEXT,                              -- es. imponibile_dichiarato: serve a riconoscere un dato contraddittorio
  testo         TEXT NOT NULL,
  valore        TEXT,
  fonte         JSONB,                             -- {origine, session_id, doc, pag, quote}
  verifica      TEXT NOT NULL DEFAULT 'non_verificato',   -- confermato|non_verificato|contraddittorio
  data_verifica TIMESTAMPTZ,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at    TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS kbot_fascicolo_voci_fasc ON public.kbot_fascicolo_voci (fascicolo_id, created_at DESC);
ALTER TABLE public.kbot_fascicolo_voci ENABLE ROW LEVEL SECURITY;

CREATE TABLE IF NOT EXISTS public.kbot_fascicolo_documenti (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  fascicolo_id   UUID NOT NULL REFERENCES public.kbot_fascicoli(id) ON DELETE CASCADE,
  user_id        UUID NOT NULL,
  name           TEXT NOT NULL,
  type           TEXT,
  size           BIGINT,
  path           TEXT NOT NULL,                    -- percorso nello Storage privato (mai un link pubblico)
  extracted_text TEXT,
  extraction_method TEXT,
  source_session UUID,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at     TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS kbot_fascicolo_documenti_fasc ON public.kbot_fascicolo_documenti (fascicolo_id);
ALTER TABLE public.kbot_fascicolo_documenti ENABLE ROW LEVEL SECURITY;
