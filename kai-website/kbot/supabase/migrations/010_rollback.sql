-- Rollback della 010: perde solo i metadati di versionamento nuovi (documento logico, motivo, autore, fonte). I documenti e i loro file restano.
DROP INDEX IF EXISTS public.kbot_fascicolo_documenti_uq_contenuto;
DROP INDEX IF EXISTS public.kbot_fascicolo_documenti_uq_versione;
DROP INDEX IF EXISTS public.kbot_fascicolo_documenti_logico;
ALTER TABLE public.kbot_fascicolo_documenti
  DROP COLUMN IF EXISTS fonte, DROP COLUMN IF EXISTS autore, DROP COLUMN IF EXISTS motivo, DROP COLUMN IF EXISTS documento_id;
