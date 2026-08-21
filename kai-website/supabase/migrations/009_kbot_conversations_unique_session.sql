-- Migration 009 — una sessione K-BOT non può comparire due volte in cronologia.
-- Esegui su Supabase SQL Editor del progetto kai-website. Idempotente.
--
-- PERCHÉ: il recupero delle sessioni orfane (lib/conversations_index.py) fa read-then-insert.
-- La 007 crea solo un indice NON unico su kbot_session_id, quindi due richieste
-- GET /api/kbot/conversations sovrapposte dello stesso utente possono materializzare la
-- stessa sessione due volte, in modo permanente: due righe identiche in sidebar.
-- Con l'indice unico il secondo insert fallisce con 23505 e il codice lo ignora.

-- 1. Ripulisci eventuali duplicati già presenti, tenendo la riga più vecchia (è quella
--    che l'utente ha effettivamente visto e magari già rinominato).
WITH ranked AS (
  SELECT id,
         ROW_NUMBER() OVER (
           PARTITION BY kbot_session_id
           ORDER BY created_at ASC, id ASC
         ) AS rn
  FROM kbot_conversations
  WHERE kbot_session_id IS NOT NULL
)
DELETE FROM kbot_conversations
WHERE id IN (SELECT id FROM ranked WHERE rn > 1);

-- 2. Una conversazione per sessione. Parziale: `kbot_session_id` è NULL sulle conversazioni
--    create dal frontend prima che la sessione backend esista, e quelle non vanno vincolate.
CREATE UNIQUE INDEX IF NOT EXISTS idx_kbot_conv_session_unique
  ON kbot_conversations(kbot_session_id)
  WHERE kbot_session_id IS NOT NULL;
