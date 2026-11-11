-- Rollback della 011: toglie il trigger e la funzione (nessun dato toccato). Dopo il rollback `has_paid` torna scrivibile dal client.
DROP TRIGGER IF EXISTS kbot_profiles_has_paid_guard ON public.kbot_profiles;
DROP FUNCTION IF EXISTS public.kbot_profiles_proteggi_has_paid();
