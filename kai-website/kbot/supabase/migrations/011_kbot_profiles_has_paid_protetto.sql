-- Migration 011 — `kbot_profiles.has_paid` modificabile solo da processi autorizzati (service role, migrazioni, webhook di pagamento).
-- Motivo (test 31): la policy «Users can update own kbot profile» + il grant UPDATE su tutte le colonne permettono a un utente autenticato di
-- eseguire `update kbot_profiles set has_paid = true where id = auth.uid()` dal client. Nessun trigger lo impediva.
-- ADDITIVA e reversibile (011_rollback.sql): una funzione e un trigger; nessun dato modificato. Le altre colonne restano scrivibili
-- come prima (consensi, anagrafica): non si cambia il comportamento delle schermate esistenti.
CREATE OR REPLACE FUNCTION public.kbot_profiles_proteggi_has_paid() RETURNS trigger
LANGUAGE plpgsql SECURITY INVOKER SET search_path = public, pg_temp AS $$
DECLARE ruolo text := coalesce(nullif(current_setting('request.jwt.claim.role', true), ''),
                               nullif(current_setting('request.jwt.claims', true), '')::jsonb ->> 'role', current_user);
BEGIN
  IF ruolo IN ('anon', 'authenticated') THEN                       -- richiesta arrivata dal client (PostgREST con la chiave pubblica)
    IF TG_OP = 'INSERT' AND coalesce(NEW.has_paid, false) THEN
      RAISE EXCEPTION 'has_paid non impostabile dal client' USING ERRCODE = '42501';
    ELSIF TG_OP = 'UPDATE' AND NEW.has_paid IS DISTINCT FROM OLD.has_paid THEN
      RAISE EXCEPTION 'has_paid non modificabile dal client' USING ERRCODE = '42501';
    END IF;
  END IF;
  RETURN NEW;
END $$;

DROP TRIGGER IF EXISTS kbot_profiles_has_paid_guard ON public.kbot_profiles;
CREATE TRIGGER kbot_profiles_has_paid_guard BEFORE INSERT OR UPDATE ON public.kbot_profiles
  FOR EACH ROW EXECUTE FUNCTION public.kbot_profiles_proteggi_has_paid();
