-- Migration 006 — tabelle allegati mai create in produzione (audit 6, 10 nov 2026)
-- Idempotente: replica la sezione 2 della 002 (kbot_file_chunks) e la 003 (kbot_extraction_cache).
-- Senza queste tabelle gli allegati non vengono indicizzati: il backend ripiega sul testo
-- estratto tenuto nella sessione (vedi lib/rag.py::chunk_da_file), quindi nulla si rompe,
-- ma la persistenza per chunk con numero di pagina funziona solo dopo questa migrazione.
CREATE TABLE IF NOT EXISTS public.kbot_file_chunks (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id   UUID NOT NULL,
  file_name    TEXT NOT NULL,
  page_number  INT NOT NULL DEFAULT 0,
  chunk_index  INT NOT NULL DEFAULT 0,
  content      TEXT NOT NULL,
  embedding    JSONB,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS kbot_file_chunks_session ON public.kbot_file_chunks (session_id);
ALTER TABLE public.kbot_file_chunks ENABLE ROW LEVEL SECURITY;

CREATE TABLE IF NOT EXISTS public.kbot_extraction_cache (
  hash              TEXT PRIMARY KEY,
  extracted_text    TEXT,
  extracted_summary TEXT,
  extraction_method TEXT NOT NULL,
  pages_json        JSONB,
  bytes_size        BIGINT,
  mime              TEXT,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS kbot_extraction_cache_created_at_idx ON public.kbot_extraction_cache (created_at);
ALTER TABLE public.kbot_extraction_cache ENABLE ROW LEVEL SECURITY;
