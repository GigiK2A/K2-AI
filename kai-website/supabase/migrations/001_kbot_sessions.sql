-- Sessioni K-BOT
CREATE TABLE IF NOT EXISTS kbot_sessions (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),

  -- Dati raccolti
  sector TEXT,                    -- slug settore (es. 'commercialista')
  path TEXT CHECK (path IN ('A', 'B', 'unknown')),
  step INTEGER DEFAULT 1,
  status TEXT DEFAULT 'active',   -- active | teaser_shown | paid | contacted

  -- Conversazione
  messages JSONB DEFAULT '[]',    -- array {role, content, ts}
  collected_data JSONB DEFAULT '{}', -- dati strutturati raccolti

  -- Contatto
  email TEXT,
  nome TEXT,
  disponibilita TEXT,             -- Path B: quando disponibile per call

  -- Pagamento (Path A)
  stripe_session_id TEXT,
  pdf_url TEXT,
  paid_at TIMESTAMPTZ
);

-- Conversioni
CREATE TABLE IF NOT EXISTS kbot_conversions (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  session_id UUID REFERENCES kbot_sessions(id),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  type TEXT CHECK (type IN ('path_a_paid', 'path_b_contact')),
  amount_eur DECIMAL(10,2),
  stripe_session_id TEXT,
  email TEXT
);

-- Indici
CREATE INDEX IF NOT EXISTS idx_kbot_sessions_email ON kbot_sessions(email);
CREATE INDEX IF NOT EXISTS idx_kbot_sessions_status ON kbot_sessions(status);
CREATE INDEX IF NOT EXISTS idx_kbot_sessions_sector ON kbot_sessions(sector);
