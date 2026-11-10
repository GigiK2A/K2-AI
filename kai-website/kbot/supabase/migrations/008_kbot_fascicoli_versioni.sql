-- Migration 008 — fascicoli: versionamento dei record, stato temporale ≠ verifica ≠ origine, storico, versioni dei documenti.
-- SOLO ADDITIVA: colonne nuove con default, una tabella nuova, indici. Nessun dato esistente viene modificato o cancellato
-- (il backfill scrive solo nelle colonne nuove). Rollback: 008_rollback.sql. Idempotente.
ALTER TABLE public.kbot_fascicolo_voci
  ADD COLUMN IF NOT EXISTS stato_record   TEXT NOT NULL DEFAULT 'attuale',      -- attuale|da_verificare|superata|contestata|archiviata
  ADD COLUMN IF NOT EXISTS origine        TEXT,                                  -- letto_da_documento|dichiarato_utente|calcolato|verificato_esterno|confermato_autorizzato
  ADD COLUMN IF NOT EXISTS unita          TEXT,
  ADD COLUMN IF NOT EXISTS periodo        TEXT,
  ADD COLUMN IF NOT EXISTS contesto       TEXT,                                  -- prestazione / voce contrattuale di riferimento
  ADD COLUMN IF NOT EXISTS doc_versione   TEXT,
  ADD COLUMN IF NOT EXISTS data_efficacia DATE,
  ADD COLUMN IF NOT EXISTS valido_dal     TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS valido_fino    TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS sostituisce    UUID,
  ADD COLUMN IF NOT EXISTS sostituita_da  UUID,
  ADD COLUMN IF NOT EXISTS motivo         TEXT,
  ADD COLUMN IF NOT EXISTS modificato_da  TEXT,
  ADD COLUMN IF NOT EXISTS updated_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  ADD COLUMN IF NOT EXISTS fonti          JSONB NOT NULL DEFAULT '[]'::jsonb,   -- tutte le fonti che sostengono il record
  ADD COLUMN IF NOT EXISTS firma          TEXT;                                  -- chiave di deduplicazione calcolata dal backend
CREATE INDEX IF NOT EXISTS kbot_fascicolo_voci_stato ON public.kbot_fascicolo_voci (fascicolo_id, stato_record);
CREATE INDEX IF NOT EXISTS kbot_fascicolo_voci_firma ON public.kbot_fascicolo_voci (fascicolo_id, firma);

-- backfill SOLO delle colonne nuove (la colonna `verifica` non si tocca)
UPDATE public.kbot_fascicolo_voci SET valido_dal = created_at WHERE valido_dal IS NULL;
UPDATE public.kbot_fascicolo_voci SET fonti = jsonb_build_array(fonte) WHERE fonte IS NOT NULL AND fonti = '[]'::jsonb;
UPDATE public.kbot_fascicolo_voci SET origine = CASE
    WHEN testo ILIKE 'CALCOLATO%' THEN 'calcolato'
    WHEN fonte->>'origine' = 'utente' THEN 'dichiarato_utente'
    WHEN fonte->>'origine' = 'documento' THEN 'letto_da_documento'
    ELSE 'dichiarato_utente' END WHERE origine IS NULL;
UPDATE public.kbot_fascicolo_voci SET stato_record = 'contestata' WHERE verifica = 'contraddittorio' AND stato_record = 'attuale';
UPDATE public.kbot_fascicolo_voci SET stato_record = 'da_verificare' WHERE testo ILIKE 'DA CONFERMARE%' AND stato_record = 'attuale';

ALTER TABLE public.kbot_fascicolo_documenti
  ADD COLUMN IF NOT EXISTS versione        INT NOT NULL DEFAULT 1,
  ADD COLUMN IF NOT EXISTS serie           TEXT,                       -- stessa serie = versioni dello stesso documento
  ADD COLUMN IF NOT EXISTS sha256          TEXT,
  ADD COLUMN IF NOT EXISTS stato           TEXT NOT NULL DEFAULT 'caricato',   -- caricato|verificato|approvato
  ADD COLUMN IF NOT EXISTS sostituisce_doc UUID;
CREATE INDEX IF NOT EXISTS kbot_fascicolo_documenti_serie ON public.kbot_fascicolo_documenti (fascicolo_id, serie);

CREATE TABLE IF NOT EXISTS public.kbot_fascicolo_eventi (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  fascicolo_id UUID NOT NULL REFERENCES public.kbot_fascicoli(id) ON DELETE CASCADE,
  user_id      UUID NOT NULL,
  voce_id      UUID,
  azione       TEXT NOT NULL,     -- crea|aggiunge_fonte|propone|sostituisce|contesta|archivia|conferma|verifica_esterna|consolida|annulla|documento
  prima        JSONB,
  dopo         JSONB,
  motivo       TEXT,
  attore       TEXT NOT NULL DEFAULT 'sistema',   -- utente|modello|sistema
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS kbot_fascicolo_eventi_fasc ON public.kbot_fascicolo_eventi (fascicolo_id, created_at DESC);
CREATE INDEX IF NOT EXISTS kbot_fascicolo_eventi_voce ON public.kbot_fascicolo_eventi (voce_id);
ALTER TABLE public.kbot_fascicolo_eventi ENABLE ROW LEVEL SECURITY;
