-- Rollback della 009: perde solo il contatore (lo storico dei valori precedenti resta negli eventi `aggiorna`).
ALTER TABLE public.kbot_fascicolo_voci DROP COLUMN IF EXISTS revisione;
