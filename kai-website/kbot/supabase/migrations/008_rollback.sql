-- Rollback della 008: toglie solo ciò che la 008 ha aggiunto. I dati delle colonne originali non sono mai stati modificati.
-- ATTENZIONE: perde lo storico/le versioni scritti dopo la 008 (le voci restano, ma senza stati, fonti multiple e cronologia).
-- Prima di eseguirlo, se serve conservarli: COPY (SELECT * FROM kbot_fascicolo_eventi) e SELECT id, stato_record, fonti, sostituisce FROM kbot_fascicolo_voci.
DROP TABLE IF EXISTS public.kbot_fascicolo_eventi;
DROP INDEX IF EXISTS public.kbot_fascicolo_voci_stato, public.kbot_fascicolo_voci_firma, public.kbot_fascicolo_documenti_serie;
ALTER TABLE public.kbot_fascicolo_voci
  DROP COLUMN IF EXISTS stato_record, DROP COLUMN IF EXISTS origine, DROP COLUMN IF EXISTS unita, DROP COLUMN IF EXISTS periodo,
  DROP COLUMN IF EXISTS contesto, DROP COLUMN IF EXISTS doc_versione, DROP COLUMN IF EXISTS data_efficacia, DROP COLUMN IF EXISTS valido_dal,
  DROP COLUMN IF EXISTS valido_fino, DROP COLUMN IF EXISTS sostituisce, DROP COLUMN IF EXISTS sostituita_da, DROP COLUMN IF EXISTS motivo,
  DROP COLUMN IF EXISTS modificato_da, DROP COLUMN IF EXISTS updated_at, DROP COLUMN IF EXISTS fonti, DROP COLUMN IF EXISTS firma;
ALTER TABLE public.kbot_fascicolo_documenti
  DROP COLUMN IF EXISTS versione, DROP COLUMN IF EXISTS serie, DROP COLUMN IF EXISTS sha256, DROP COLUMN IF EXISTS stato, DROP COLUMN IF EXISTS sostituisce_doc;
