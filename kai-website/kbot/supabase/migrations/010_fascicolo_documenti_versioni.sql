-- Migration 010 — documenti dei fascicoli: documento LOGICO stabile + versioni con autore, fonte e motivazione.
-- SOLO ADDITIVA: colonne nuove (tutte NULL-abili) e due indici univoci PARZIALI. Nessun dato esistente viene modificato
-- (i documenti già presenti restano con documento_id NULL: il codice li tratta come radice della propria catena `sostituisce_doc`).
-- Rollback: 010_rollback.sql. Idempotente.
ALTER TABLE public.kbot_fascicolo_documenti
  ADD COLUMN IF NOT EXISTS documento_id UUID,     -- identificativo STABILE del documento logico (uguale in tutte le sue versioni); `id` resta quello della singola versione
  ADD COLUMN IF NOT EXISTS motivo       TEXT,     -- perché si registra questa versione
  ADD COLUMN IF NOT EXISTS autore       TEXT,     -- utente|modello|sistema: chi l'ha registrata (la conferma è dell'utente, verificata nel codice)
  ADD COLUMN IF NOT EXISTS fonte        TEXT;     -- da dove arriva (es. «chat:<sessione>:<nome file>»)

CREATE INDEX IF NOT EXISTS kbot_fascicolo_documenti_logico ON public.kbot_fascicolo_documenti (fascicolo_id, documento_id);

-- Difesa contro il caricamento ripetuto anche con due richieste in contemporanea: stessa versione e stesso contenuto nello stesso documento logico = una riga sola.
CREATE UNIQUE INDEX IF NOT EXISTS kbot_fascicolo_documenti_uq_versione
  ON public.kbot_fascicolo_documenti (documento_id, versione) WHERE documento_id IS NOT NULL AND deleted_at IS NULL;
CREATE UNIQUE INDEX IF NOT EXISTS kbot_fascicolo_documenti_uq_contenuto
  ON public.kbot_fascicolo_documenti (documento_id, sha256) WHERE documento_id IS NOT NULL AND sha256 IS NOT NULL AND deleted_at IS NULL;
