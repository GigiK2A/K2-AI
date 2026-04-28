const http = require('http');
const https = require('https');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { createClient } = require('@supabase/supabase-js');
const { Resend } = require('resend');
const Anthropic = require('@anthropic-ai/sdk');

const PORT = process.env.PORT || 4173;
const DIST_DIR = path.join(__dirname, 'dist');
const REDIRECT_HOST = 'k2-ai.it';
const CANONICAL_HOST = 'www.k2-ai.it';
const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://www.k2-ai.it';
const API_PROXY_BASE = process.env.API_PROXY_BASE || 'https://api.k2-ai.it';
const KBOT_MODEL = process.env.KBOT_MODEL || 'claude-haiku-4-5-20251001';
const REPORT_MODEL = process.env.REPORT_MODEL || 'claude-sonnet-4-6';
const SKILLS_DIR = path.join(__dirname, 'lib', 'skills');

const MIME_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
  '.mp4': 'video/mp4',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
  '.ttf': 'font/ttf',
  '.map': 'application/octet-stream'
};

const SECTOR_LABELS = {
  'studio-ingegneria': 'Studio di ingegneria / architettura',
  'commercialista': 'Studio commercialista / CdL',
  'manifatturiero': 'Manifatturiero / produzione',
  'servizi-b2b': 'Servizi B2B / consulenza',
  'hospitality': 'Hospitality / ricettivo',
  'commercio-ecommerce': 'Commercio / e-commerce',
  'tlc': 'TLC / infrastrutture',
  'studio-legale': 'Studio legale',
  'pubblica-amministrazione': 'Pubblica Amministrazione',
};

const SECTOR_BUNDLES = {
  'studio-ingegneria': ['diagnosi-ai-operativa-pmi', 'progettista-strutturale', 'progettazione-architettonica', 'direzione-lavori'],
  'commercialista': ['diagnosi-ai-operativa-pmi', 'contabilita-bilancio', 'fiscale-tributario-italiano', 'analisi-bilancio-pmi', 'budget-forecast-pmi'],
  'manifatturiero': ['diagnosi-ai-operativa-pmi', 'programmazione-controllo', 'strategia-competitiva', 'analisi-settore-pmi'],
  'servizi-b2b': ['diagnosi-ai-operativa-pmi', 'strategia-competitiva', 'marketing-strategico', 'crm-customer-experience'],
  'hospitality': ['diagnosi-ai-operativa-pmi', 'flusso-hostboost-ricettive', 'marketing-strategico', 'pricing-optimizer'],
  'commercio-ecommerce': ['diagnosi-ai-operativa-pmi', 'ecommerce-marketing-pmi', 'audit-seo-tecnico', 'crm-customer-experience'],
  'tlc': ['diagnosi-ai-operativa-pmi', 'verifica-pe-terzi', 'progettista-strutturale', 'cse-coordinatore-sicurezza'],
  'studio-legale': ['diagnosi-ai-operativa-pmi', 'diritto-italiano', 'diritto-societario-italiano', 'it-law-privacy-ai'],
  'pubblica-amministrazione': ['diagnosi-ai-operativa-pmi', 'consulente-pa-operativa', 'consulente-finanza-pubblica', 'it-law-privacy-ai'],
};

const VALID_KBOT_SECTORS = new Set(Object.keys(SECTOR_LABELS));
const VALID_KBOT_MODES = new Set(['report', 'lead']);
const skillCache = new Map();

function normalizeHost(req) {
  const xfHost = req.headers['x-forwarded-host'];
  const host = (xfHost || req.headers.host || '').split(',')[0].trim();
  return host.toLowerCase();
}

function shouldRedirect(host) {
  return host === REDIRECT_HOST || host.startsWith(`${REDIRECT_HOST}:`);
}

function send(res, status, headers, body) {
  res.writeHead(status, headers);
  res.end(body);
}

function sendJson(res, status, payload) {
  send(res, status, { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' }, JSON.stringify(payload));
}

function escapeHtml(value) {
  return String(value || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function getEnvVar(name, fallbacks = []) {
  for (const key of [name, ...fallbacks]) {
    if (process.env[key]) return process.env[key];
  }
  return '';
}

function createSupabaseAdminClient() {
  const supabaseUrl = getEnvVar('NEXT_PUBLIC_SUPABASE_URL', ['SUPABASE_URL']);
  const serviceRoleKey = getEnvVar('SUPABASE_SERVICE_ROLE_KEY', ['SUPABASE_SERVICE_KEY', 'SUPABASE_KEY']);

  if (!supabaseUrl || !serviceRoleKey) {
    throw new Error('Missing Supabase newsletter env vars');
  }

  return createClient(supabaseUrl, serviceRoleKey, {
    auth: { persistSession: false },
  });
}

function createAnthropicClient() {
  const apiKey = getEnvVar('ANTHROPIC_API_KEY');
  if (!apiKey) {
    throw new Error('Missing ANTHROPIC_API_KEY');
  }
  return new Anthropic({ apiKey });
}

function resolveKbotSectorLabel(sector) {
  return SECTOR_LABELS[sector] || 'PMI italiana';
}

function resolveKbotSkillNames(sector) {
  return SECTOR_BUNDLES[sector] || ['diagnosi-ai-operativa-pmi'];
}

function readSkill(skillName, maxChars = 5200) {
  const cacheKey = `${skillName}:${maxChars}`;
  if (skillCache.has(cacheKey)) return skillCache.get(cacheKey);

  const skillPath = path.join(SKILLS_DIR, skillName, 'SKILL.md');
  if (!fs.existsSync(skillPath)) return '';

  const raw = fs.readFileSync(skillPath, 'utf8');
  const content = raw.length > maxChars ? `${raw.slice(0, maxChars)}\n\n[skill troncata]` : raw;
  skillCache.set(cacheKey, content);
  return content;
}

function loadKbotSkillBundle(sector) {
  const chunks = resolveKbotSkillNames(sector)
    .map(skillName => {
      const content = readSkill(skillName);
      return content ? `\n\n# SKILL: ${skillName}\n${content}` : '';
    })
    .filter(Boolean);

  return chunks.join('\n').slice(0, 26000);
}

function compactKbotMessages(messages, maxMessages = 14, maxChars = 1100) {
  return (Array.isArray(messages) ? messages : [])
    .slice(-maxMessages)
    .map(message => ({
      role: message.role === 'assistant' ? 'assistant' : 'user',
      content: String(message.content || '').slice(0, maxChars),
      ts: message.ts,
    }));
}

function buildKbotSystemPrompt({ mode, sector, step, session }) {
  const sectorLabel = resolveKbotSectorLabel(sector);
  const skills = loadKbotSkillBundle(sector);
  const files = Array.isArray(session?.collected_data?.uploaded_files)
    ? session.collected_data.uploaded_files
    : [];
  const fileContext = files.length
    ? `\nAllegati disponibili:\n${files.slice(-4).map(file => `- ${file.name}: ${String(file.extractedSummary || '').slice(0, 1200)}`).join('\n')}`
    : '\nNessun allegato ancora disponibile.';

  const reportRules = `
Modalità REPORT.
Obiettivo: analizzare documenti, dati o un caso specifico usando le skill interne al livello di una consulenza professionale reale.

RACCOLTA DATI (massima economia):
- Se l'utente ha allegato materiale o descritto il caso in dettaglio: NON fare domande. Procedi subito verso l'analisi.
- Se manca UN'informazione critica (es. settore ATECO, anno di riferimento): fai UNA sola domanda, non un elenco.
- MAI spezzare una singola esigenza in più sotto-domande consecutive.
- Dopo al massimo 1-2 scambi, chiudi la raccolta.
- Considera il modello di business tipico del settore: commessa per ingegneria/architettura, parcella per studi legali/commercialisti, abbonamento/canone per SaaS/TLC, ciclo produzione-magazzino per manifatturiero.

QUALITÀ ANALISI:
- Distingui SEMPRE tra sintomo (cosa appare nei dati) e causa strutturale (perché accade, nel contesto operativo del settore).
- Usa le skill interne per applicare indici, framework e benchmark corretti — non fare letture generiche da "Excel allarmista".
- Contestualizza ogni segnale: un crediti/ricavi alto in uno studio a commessa è normale; in un'azienda prodotto è un problema.
- Non inventare numeri non presenti nel materiale. Se un dato manca, indicalo esplicitamente.

CHIUSURA RACCOLTA — REGOLA ASSOLUTA:
- Quando hai abbastanza materiale, scrivi una frase di chiusura dichiarativa e includi esattamente: report_ready: true
- L'ULTIMO messaggio NON deve MAI contenere un punto interrogativo.
- L'ultimo messaggio è UNA SOLA FRASE DICHIARATIVA tipo: "Ho abbastanza materiale per procedere con l'analisi." oppure "Il documento è chiaro, procedo con la lettura strutturata."
- Anche se hai dubbi, dichiara che procedi: i dubbi li gestisce il report.
- VIETATO scrivere domande nel messaggio che contiene report_ready: true.`;

  const leadRules = `
Modalità CONTATTO.
Obiettivo: capire contesto, problema, urgenza e fit commerciale in modo naturale.
Conversazione naturale: una domanda alla volta, basata sulla risposta precedente. Niente script rigido.
NON chiedere mai email, telefono, disponibilità o dati di contatto: ci pensa il form dopo.

Quando hai processo, attrito, obiettivo e urgenza (bastano 3-5 scambi), produci il messaggio finale con questa struttura ESATTA:

[2-3 frasi dichiarative per l'utente: conferma che hai capito il quadro e che stai mandando il brief al team. NESSUNA domanda.]

BRIEF_START
Settore/ruolo: [settore e ruolo dell'utente]
Processo attuale: [descrizione del workflow o processo che costa tempo/qualità oggi]
Problema principale: [il collo di bottiglia o attrito emerso dalla conversazione]
Obiettivo: [cosa vuole costruire, automatizzare o migliorare]
Urgenza: [se emersa, altrimenti ometti]
BRIEF_END

lead_ready: true

REGOLE OBBLIGATORIE per il messaggio finale:
- Il testo PRIMA di BRIEF_START non deve MAI terminare con una domanda.
- Il BRIEF deve essere scritto come testo continuativo leggibile da un operatore umano.
- Il BRIEF deve basarsi sull'INTERA conversazione, non solo sull'ultimo messaggio.`;

  return `
Sei K-BOT di K2-AI. Parli in italiano, tono umano, diretto, normale.
Settore: ${sectorLabel}
Step: ${step}

Regole generali:
- Una domanda alla volta.
- Massimo 3 frasi per turno, salvo quando stai chiudendo.
- Niente markdown pesante, tabelle o JSON in chat.
- Non inventare numeri o conclusioni da documenti non leggibili.
- Se l'utente risponde in modo vago, chiedi un chiarimento concreto invece di seguire uno schema fisso.

${mode === 'lead' ? leadRules : reportRules}
${fileContext}

Skill interne disponibili:
${skills}
`.slice(0, 32000);
}

function detectKbotNextAction(mode, step, collectedData, assistantMessage) {
  const text = String(assistantMessage || '').toLowerCase();
  if (mode === 'report' && (text.includes('report_ready: true') || step >= 4 || collectedData.report_ready)) {
    return 'show_report';
  }
  if (mode === 'lead' && (text.includes('lead_ready: true') || step >= 5 || collectedData.lead_ready)) {
    return 'show_contact_form';
  }
  return 'continue';
}

function extractLeadBrief(raw) {
  const match = String(raw || '').match(/BRIEF_START\s*([\s\S]*?)\s*BRIEF_END/i);
  if (!match) return '';
  return match[1]
    .replace(/^Settore\/ruolo:\s*/im, 'Settore: ')
    .trim();
}

function cleanKbotAssistantMessage(message) {
  return String(message || '')
    .replace(/BRIEF_START[\s\S]*?BRIEF_END/gi, '')
    .replace(/report_ready\s*:\s*true/gi, '')
    .replace(/lead_ready\s*:\s*true/gi, '')
    .replace(/\n{3,}/g, '\n\n')
    .trim() || 'Ricevuto. Dimmi pure un dettaglio in più e procediamo.';
}

function stripTrailingQuestion(text) {
  const t = String(text || '').trimEnd();
  if (!t.endsWith('?')) return t;
  // Remove the last sentence that ends with ?
  const lastSentenceEnd = Math.max(
    t.lastIndexOf('.', t.length - 2),
    t.lastIndexOf('!', t.length - 2),
    t.lastIndexOf('\n', t.length - 2),
  );
  if (lastSentenceEnd > 0) return t.slice(0, lastSentenceEnd + 1).trim();
  return 'Ho abbastanza materiale. Procedo con l\'analisi.';
}

function readJsonBody(req, maxBytes = 16 * 1024) {
  return new Promise((resolve, reject) => {
    let data = '';
    req.on('data', chunk => {
      data += chunk.toString();
      if (data.length > maxBytes) {
        req.destroy();
        reject(new Error('Body too large'));
      }
    });
    req.on('end', () => {
      try {
        resolve(data ? JSON.parse(data) : {});
      } catch {
        reject(new Error('Invalid JSON'));
      }
    });
    req.on('error', reject);
  });
}

function readRawBody(req, maxBytes = 8 * 1024 * 1024) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    let total = 0;
    req.on('data', chunk => {
      total += chunk.length;
      if (total > maxBytes) {
        req.destroy();
        reject(new Error('Body too large'));
        return;
      }
      chunks.push(chunk);
    });
    req.on('end', () => resolve(Buffer.concat(chunks)));
    req.on('error', reject);
  });
}

function shouldForwardRequestHeader(name) {
  const lower = String(name || '').toLowerCase();
  if (!lower) return false;
  if (lower === 'host') return false;
  if (lower === 'connection') return false;
  if (lower === 'content-length') return false;
  if (lower === 'accept-encoding') return false;
  if (lower === 'x-forwarded-host' || lower === 'x-forwarded-proto' || lower === 'x-forwarded-for') return false;
  return true;
}

function shouldForwardResponseHeader(name) {
  const lower = String(name || '').toLowerCase();
  if (!lower) return false;
  if (lower === 'connection') return false;
  if (lower === 'transfer-encoding') return false;
  if (lower === 'content-length') return false;
  if (lower === 'www-authenticate') return false;
  if (lower === 'proxy-authenticate') return false;
  return true;
}

async function proxyApiRequest(req, res, rawPath, rawQuery) {
  const upstreamUrl = `${API_PROXY_BASE}${rawPath}${rawQuery}`;
  const method = (req.method || 'GET').toUpperCase();

  const forwardedHeaders = {};
  Object.entries(req.headers || {}).forEach(([name, value]) => {
    if (!shouldForwardRequestHeader(name) || value == null) return;
    forwardedHeaders[name] = value;
  });
  forwardedHeaders['x-forwarded-host'] = CANONICAL_HOST;
  forwardedHeaders['x-forwarded-proto'] = 'https';

  let bodyBuffer = null;
  if (!['GET', 'HEAD'].includes(method)) {
    bodyBuffer = await readRawBody(req);
    if (bodyBuffer.length > 0) {
      forwardedHeaders['content-length'] = String(bodyBuffer.length);
    }
  }

  const upstreamReq = https.request(upstreamUrl, {
    method,
    headers: forwardedHeaders,
  }, upstreamRes => {
    const statusCode = upstreamRes.statusCode || 502;

    if (rawPath.startsWith('/api/kbot/') && statusCode === 401) {
      upstreamRes.resume();
      sendJson(res, 503, { error: 'K-BOT temporaneamente non disponibile' });
      return;
    }

    const responseHeaders = {};
    Object.entries(upstreamRes.headers || {}).forEach(([name, value]) => {
      if (!shouldForwardResponseHeader(name) || value == null) return;
      responseHeaders[name] = value;
    });

    if (rawPath.startsWith('/api/workshop/')) {
      responseHeaders['Cache-Control'] = 'no-store';
    }

    res.writeHead(statusCode, responseHeaders);
    upstreamRes.pipe(res);
  });

  upstreamReq.on('error', err => {
    console.error('API proxy error:', err);
    sendJson(res, 502, { error: 'Upstream API non disponibile' });
  });

  if (bodyBuffer && bodyBuffer.length > 0) {
    upstreamReq.write(bodyBuffer);
  }
  upstreamReq.end();
}

function generateToken() {
  return crypto.randomBytes(32).toString('hex');
}

async function sendConfirmationEmail(email, token) {
  const resendApiKey = getEnvVar('RESEND_API_KEY');
  if (!resendApiKey) return;

  const confirmUrl = `${SITE_URL}/api/newsletter/confirm?token=${token}`;
  const resend = new Resend(resendApiKey);

  await resend.emails.send({
    from: 'K2-AI <noreply@k2-ai.it>',
    to: [email],
    subject: 'Conferma iscrizione alla newsletter K2-AI',
    html: `
      <div style="font-family:Inter,sans-serif;max-width:560px;margin:0 auto;color:#212529">
        <h2 style="margin-bottom:8px;color:#0d1117">Conferma la tua iscrizione</h2>
        <p>Hai richiesto di ricevere aggiornamenti da K2-AI sull'intelligenza artificiale.</p>
        <p>Clicca il pulsante per confermare:</p>
        <a href="${escapeHtml(confirmUrl)}"
           style="display:inline-block;margin:16px 0;padding:12px 24px;background:#0d1117;color:#fff;text-decoration:none;border-radius:6px;font-weight:600">
          Conferma iscrizione
        </a>
        <p style="font-size:13px;color:#6c757d">Se non hai fatto questa richiesta, ignora questa email.</p>
        <hr style="border:none;border-top:1px solid #DEE2E6;margin:20px 0"/>
        <p style="font-size:11px;color:#adb5bd">K2A S.R.L.S. - P.IVA IT03655920548</p>
      </div>
    `,
  });
}

async function sendWelcomeEmail(email) {
  const resendApiKey = getEnvVar('RESEND_API_KEY');
  if (!resendApiKey) return;

  const resend = new Resend(resendApiKey);

  await resend.emails.send({
    from: 'K2-AI <noreply@k2-ai.it>',
    to: [email],
    subject: 'Iscrizione confermata alla newsletter K2-AI',
    html: `
      <div style="font-family:Inter,sans-serif;max-width:560px;margin:0 auto;color:#212529">
        <h2 style="margin-bottom:8px;color:#0d1117">Iscrizione confermata</h2>
        <p>Sei dentro: da ora riceverai il briefing K2-AI con le novità più utili dal mondo dell'intelligenza artificiale.</p>
        <p>La newsletter è pensata per essere semplice: poche notizie, spiegate bene, con attenzione a creator, PMI e team operativi.</p>
        <a href="${escapeHtml(SITE_URL)}/contatti"
           style="display:inline-block;margin:16px 0;padding:12px 24px;background:#0d1117;color:#fff;text-decoration:none;border-radius:6px;font-weight:600">
          Visita K2-AI
        </a>
        <hr style="border:none;border-top:1px solid #DEE2E6;margin:20px 0"/>
        <p style="font-size:11px;color:#adb5bd">K2A S.R.L.S. - P.IVA IT03655920548</p>
      </div>
    `,
  });
}

async function handleNewsletterSubscribe(req, res) {
  if (req.method === 'OPTIONS') {
    send(res, 204, {
      'Access-Control-Allow-Origin': SITE_URL,
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    }, '');
    return;
  }

  if (req.method !== 'POST') {
    sendJson(res, 405, { error: 'Method not allowed' });
    return;
  }

  let body;
  try {
    body = await readJsonBody(req);
  } catch {
    sendJson(res, 400, { error: 'Invalid JSON' });
    return;
  }

  const email = typeof body.email === 'string' ? body.email.trim().toLowerCase() : '';
  const source = typeof body.source === 'string' ? body.source.trim().slice(0, 100) : 'website';

  if (!email || !isValidEmail(email)) {
    sendJson(res, 400, { error: 'Email non valida' });
    return;
  }

  // Il workflow n8n usa "name" come destinatario Outlook, quindi qui salviamo la mail.
  const recipientName = email;
  const supabase = createSupabaseAdminClient();

  const { data: existing, error: existingError } = await supabase
    .from('newsletter_subscribers')
    .select('id, confirmed')
    .eq('email', email)
    .single();

  // `single()` returns PGRST116 when no rows are found: that case is expected.
  // Any other error is logged for diagnostics and we continue with insert fallback.
  if (existingError && existingError.code !== 'PGRST116') {
    console.warn('Newsletter lookup warning:', existingError);
  }

  if (existing) {
    if (existing.confirmed) {
      sendJson(res, 200, { ok: true, already: true });
      return;
    }

    const token = generateToken();
    await supabase
      .from('newsletter_subscribers')
      .update({ name: recipientName, confirm_token: token, updated_at: new Date().toISOString() })
      .eq('email', email);

    await sendConfirmationEmail(email, token);
    sendJson(res, 200, { ok: true, resent: true });
    return;
  }

  const token = generateToken();
  const { error } = await supabase.from('newsletter_subscribers').insert({
    email,
    name: recipientName,
    confirmed: false,
    confirm_token: token,
    source,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  });

  if (error) {
    const rawErrorText = [
      error.code,
      error.message,
      error.details,
      error.hint,
      error.constraint,
    ]
      .filter(Boolean)
      .join(' ')
      .toLowerCase();

    // If we cannot read existing rows (permissions/policies) and hit a duplicate
    // on insert, degrade gracefully as "already subscribed".
    const isDuplicate =
      error.code === '23505' ||
      /duplicate key|unique constraint|already exists|email_key|newsletter_subscribers_email_key/.test(rawErrorText);

    if (isDuplicate) {
      sendJson(res, 200, { ok: true, already: true });
      return;
    }

    console.error('Newsletter insert error:', error);
    sendJson(res, 500, { error: 'Errore salvataggio' });
    return;
  }

  await sendConfirmationEmail(email, token);
  sendJson(res, 200, { ok: true });
}

async function handleNewsletterConfirm(req, res) {
  const url = new URL(req.url || '', SITE_URL);
  const token = url.searchParams.get('token') || '';

  if (!token || token.length < 32) {
    send(res, 302, { Location: '/newsletter-error' }, '');
    return;
  }

  const supabase = createSupabaseAdminClient();
  const { data, error } = await supabase
    .from('newsletter_subscribers')
    .update({
      confirmed: true,
      confirmed_at: new Date().toISOString(),
      confirm_token: null,
      updated_at: new Date().toISOString(),
    })
    .eq('confirm_token', token)
    .eq('confirmed', false)
    .select('email')
    .single();

  if (error || !data) {
    send(res, 302, { Location: '/newsletter-error' }, '');
    return;
  }

  await sendWelcomeEmail(data.email);
  send(res, 302, { Location: '/newsletter-ok' }, '');
}

async function handleKbotSession(req, res) {
  if (req.method !== 'POST') return sendJson(res, 405, { error: 'Method not allowed' });

  const body = await readJsonBody(req);
  const sector = String(body.sector || '').trim();
  const mode = String(body.mode || '').trim();

  if (!VALID_KBOT_SECTORS.has(sector)) return sendJson(res, 400, { error: 'Settore non valido' });
  if (!VALID_KBOT_MODES.has(mode)) return sendJson(res, 400, { error: 'Modalità non valida' });

  const supabase = createSupabaseAdminClient();
  const { data, error } = await supabase
    .from('kbot_sessions')
    .insert({
      sector,
      path: mode === 'lead' ? 'B' : 'A',
      status: 'active',
      step: 1,
      messages: [],
      collected_data: { mode },
    })
    .select('id')
    .single();

  if (error) return sendJson(res, 500, { error: error.message });
  sendJson(res, 200, { session_id: data.id, mode });
}

async function handleKbotChat(req, res) {
  if (req.method !== 'POST') return sendJson(res, 405, { error: 'Method not allowed' });

  const body = await readJsonBody(req);
  const sessionId = String(body.session_id || '').trim();
  const userMessage = String(body.message || '').trim().slice(0, 6000);
  if (!sessionId || !userMessage) return sendJson(res, 400, { error: 'session_id e message obbligatori' });

  const supabase = createSupabaseAdminClient();
  const { data: session, error: sessionError } = await supabase
    .from('kbot_sessions')
    .select('*')
    .eq('id', sessionId)
    .single();

  if (sessionError || !session) return sendJson(res, 404, { error: 'Session not found' });

  const mode = session.collected_data?.mode === 'lead' ? 'lead' : 'report';
  const step = Number(session.step || 1);
  const previousMessages = Array.isArray(session.messages) ? session.messages : [];
  const persistedMessages = [
    ...previousMessages,
    { role: 'user', content: userMessage, ts: new Date().toISOString() },
  ];

  let rawAssistant = '';
  try {
    const anthropic = createAnthropicClient();
    const response = await anthropic.messages.create({
      model: KBOT_MODEL,
      max_tokens: 900,
      system: buildKbotSystemPrompt({ mode, sector: session.sector, step, session }),
      messages: compactKbotMessages(persistedMessages).map(message => ({
        role: message.role,
        content: message.content,
      })),
    });
    rawAssistant = response.content?.[0]?.type === 'text' ? response.content[0].text : '';
  } catch (aiErr) {
    console.error('Anthropic API error in handleKbotChat:', aiErr);
    return sendJson(res, 500, { error: `Errore AI: ${aiErr instanceof Error ? aiErr.message : String(aiErr)}` });
  }

  const isReportReady = /report_ready\s*:\s*true/i.test(rawAssistant);
  const isLeadReady = /lead_ready\s*:\s*true/i.test(rawAssistant);

  let assistantMessage = cleanKbotAssistantMessage(rawAssistant);
  if (isReportReady) assistantMessage = stripTrailingQuestion(assistantMessage);

  const leadBrief = isLeadReady ? extractLeadBrief(rawAssistant) : '';

  const collectedData = {
    ...(session.collected_data || {}),
    mode,
    ...(isReportReady ? { report_ready: true } : {}),
    ...(isLeadReady ? { lead_ready: true } : {}),
  };
  const nextAction = detectKbotNextAction(mode, step, collectedData, rawAssistant);
  const updatedMessages = [
    ...persistedMessages,
    { role: 'assistant', content: assistantMessage, ts: new Date().toISOString() },
  ];

  await supabase
    .from('kbot_sessions')
    .update({
      messages: updatedMessages,
      step: step + 1,
      path: mode === 'lead' ? 'B' : 'A',
      collected_data: collectedData,
      updated_at: new Date().toISOString(),
    })
    .eq('id', sessionId);

  sendJson(res, 200, {
    message: assistantMessage,
    mode,
    path: mode === 'lead' ? 'B' : 'A',
    next_action: nextAction,
    session: { step: step + 1, mode },
    ...(nextAction === 'show_contact_form' ? { contact_summary: leadBrief || assistantMessage } : {}),
  });
}

function sanitizeKbotFileName(name) {
  return String(name || 'file').replace(/[^a-zA-Z0-9._-]/g, '_').slice(0, 120);
}

function decodeKbotText(buffer) {
  return buffer.toString('utf8').replace(/\u0000/g, '').replace(/\r\n/g, '\n').trim();
}

function isTextLikeFile(mime, name) {
  const lower = String(name || '').toLowerCase();
  return String(mime || '').startsWith('text/') || /\.(txt|md|csv|json|xml)$/i.test(lower);
}

async function summarizeKbotPdf(base64, fileName) {
  const anthropic = createAnthropicClient();
  const response = await anthropic.messages.create({
    model: KBOT_MODEL,
    max_tokens: 900,
    messages: [
      {
        role: 'user',
        content: [
          { type: 'text', text: `Leggi il PDF "${fileName}" e restituisci una sintesi analitica in italiano: tipo documento, elementi importanti, dati leggibili, rischi o punti da verificare. Non proporre automazioni.` },
          { type: 'document', source: { type: 'base64', media_type: 'application/pdf', data: base64 } },
        ],
      },
    ],
  });
  return response.content?.[0]?.type === 'text' ? response.content[0].text.trim() : '';
}

async function handleKbotUpload(req, res) {
  if (req.method !== 'POST') return sendJson(res, 405, { error: 'Method not allowed' });

  const body = await readJsonBody(req, 24 * 1024 * 1024);
  const sessionId = String(body.session_id || '').trim();
  const files = Array.isArray(body.files) ? body.files.slice(0, 5) : [];
  if (!sessionId || files.length === 0) return sendJson(res, 400, { error: 'session_id e files obbligatori' });

  const supabase = createSupabaseAdminClient();
  const out = [];

  for (const file of files) {
    const name = sanitizeKbotFileName(file.name);
    const mime = String(file.type || 'application/octet-stream');
    const raw = String(file.base64 || '').replace(/^data:.*;base64,/, '');
    const buffer = Buffer.from(raw, 'base64');
    if (buffer.length > 4 * 1024 * 1024) return sendJson(res, 413, { error: `File troppo grande: ${name}` });

    let extractedSummary = '';
    let extractedText = '';
    let extractionMethod = 'none';

    if (isTextLikeFile(mime, name)) {
      extractedText = decodeKbotText(buffer).slice(0, 30000);
      extractedSummary = extractedText.slice(0, 3000);
      extractionMethod = 'text-decode';
    } else if (mime === 'application/pdf' || name.toLowerCase().endsWith('.pdf')) {
      extractedSummary = await summarizeKbotPdf(raw, name);
      extractionMethod = extractedSummary ? 'claude-summary' : 'none';
    }

    out.push({
      name,
      type: mime,
      size: Number(file.size || buffer.length),
      publicUrl: '',
      path: '',
      extractedSummary: extractedSummary || 'Documento ricevuto, ma il testo non è leggibile in modo affidabile.',
      extractedText,
      extractionMethod,
    });
  }

  const { data: session } = await supabase
    .from('kbot_sessions')
    .select('collected_data')
    .eq('id', sessionId)
    .single();

  const prevFiles = Array.isArray(session?.collected_data?.uploaded_files)
    ? session.collected_data.uploaded_files
    : [];

  await supabase
    .from('kbot_sessions')
    .update({
      collected_data: {
        ...(session?.collected_data || {}),
        uploaded_files: [...prevFiles, ...out],
      },
      updated_at: new Date().toISOString(),
    })
    .eq('id', sessionId);

  sendJson(res, 200, { files: out });
}

async function handleKbotTeaser(req, res) {
  if (req.method !== 'POST') return sendJson(res, 405, { error: 'Method not allowed' });

  const body = await readJsonBody(req);
  const sessionId = String(body.session_id || '').trim();
  const supabase = createSupabaseAdminClient();
  const { data: session, error } = await supabase.from('kbot_sessions').select('*').eq('id', sessionId).single();
  if (error || !session) return sendJson(res, 404, { error: 'Session not found' });

  const messages = Array.isArray(session.messages) ? session.messages : [];
  const files = Array.isArray(session.collected_data?.uploaded_files) ? session.collected_data.uploaded_files : [];
  const skills = loadKbotSkillBundle(session.sector);
  const anthropic = createAnthropicClient();
  const response = await anthropic.messages.create({
    model: REPORT_MODEL,
    max_tokens: 1600,
    system: `Sei un analista senior di K2-AI. Produci un teaser di analisi professionale in formato JSON valido.

OBIETTIVO: identificare i 3 segnali più rilevanti del caso, distinguendo sintomi da cause strutturali.

REGOLE ANALISI:
- Ogni segnale deve avere una causa strutturale plausibile nel contesto del settore (non solo la lettura numerica).
- priorita: usa "critica" solo per rischi immediati di liquidità/insolvenza o violazioni normative; "alta" per inefficienze strutturali significative; "media" per opportunità di miglioramento.
- anteprima_analisi: 1-2 frasi tecniche che mostrano la profondità dell'analisi completa — non marketing, non allarmismo generico.
- hook_pdf: frase che descrive cosa trova l'utente nel report completo (strutturato, con indici, benchmark, azioni).
- NON proporre automazioni AI nel teaser.
- Usa le skill interne disponibili per applicare i framework corretti al settore.

OUTPUT: JSON con questa struttura esatta:
{
  "settore": "label settore",
  "skill_attive": ["skill1", "skill2"],
  "segnali": [
    {
      "priorita": "critica|alta|media",
      "titolo": "titolo breve del segnale",
      "sintesi": "1-2 frasi: cosa emerge dai dati",
      "causa_strutturale": "perché accade, nel contesto operativo del settore",
      "anteprima_analisi": "cosa approfondisce il report completo"
    }
  ],
  "hook_pdf": "frase descrittiva del report completo"
}

SKILL INTERNE DISPONIBILI:
${skills.slice(0, 18000)}`,
    messages: [{
      role: 'user',
      content: `Settore: ${resolveKbotSectorLabel(session.sector)}\n\nConversazione:\n${messages.map(m => `${m.role}: ${m.content}`).join('\n')}\n\nAllegati:\n${files.map(f => `${f.name}:\n${String(f.extractedSummary || f.extractedText || '').slice(0, 3000)}`).join('\n\n')}`,
    }],
  });

  let teaser;
  try {
    teaser = JSON.parse(String(response.content?.[0]?.text || '{}').replace(/```json|```/g, '').trim());
  } catch {
    teaser = {
      settore: resolveKbotSectorLabel(session.sector),
      skill_attive: resolveKbotSkillNames(session.sector),
      segnali: [{ priorita: 'media', titolo: 'Analisi in elaborazione', sintesi: 'Il materiale è stato acquisito e richiede una lettura strutturata.', causa_strutturale: 'Da definire nel report completo.', anteprima_analisi: 'Il report include lettura tecnica, indici di settore e priorità di verifica.' }],
      hook_pdf: 'Il report struttura lettura tecnica, segnali con cause, benchmark di settore e azioni prioritarie.',
    };
  }

  await supabase
    .from('kbot_sessions')
    .update({ status: 'teaser_shown', collected_data: { ...(session.collected_data || {}), teaser }, updated_at: new Date().toISOString() })
    .eq('id', sessionId);

  sendJson(res, 200, { teaser });
}

async function handleKbotContact(req, res) {
  if (req.method !== 'POST') return sendJson(res, 405, { error: 'Method not allowed' });
  const body = await readJsonBody(req);
  const sessionId = String(body.session_id || '').trim();
  const email = String(body.email || '').trim();
  const disponibilita = String(body.disponibilita || '').trim();
  if (!sessionId) return sendJson(res, 400, { error: 'session_id obbligatorio' });

  const supabase = createSupabaseAdminClient();
  await supabase
    .from('kbot_sessions')
    .update({ status: 'contacted', email: email || null, disponibilita: disponibilita || null, updated_at: new Date().toISOString() })
    .eq('id', sessionId);

  sendJson(res, 200, { ok: true });
}

async function handleKbotGenerateReport(req, res) {
  if (req.method !== 'POST') return sendJson(res, 405, { error: 'Method not allowed' });
  const body = await readJsonBody(req);
  const sessionId = String(body.session_id || '').trim();
  const supabase = createSupabaseAdminClient();
  const { data: session, error } = await supabase.from('kbot_sessions').select('*').eq('id', sessionId).single();
  if (error || !session) return sendJson(res, 404, { error: 'Session not found' });

  const messages = Array.isArray(session.messages) ? session.messages : [];
  const files = Array.isArray(session.collected_data?.uploaded_files) ? session.collected_data.uploaded_files : [];
  const skills = loadKbotSkillBundle(session.sector);
  const sectorLabel = resolveKbotSectorLabel(session.sector);
  const anthropic = createAnthropicClient();

  const reportSystemPrompt = `Sei un analista senior di K2-AI. Produci un report di analisi professionale in HTML.

OBIETTIVO: report conclusivo, strutturato, al livello di una consulenza professionale reale. Non un riassunto della conversazione, non marketing.

TEMPLATE OBBLIGATORIO — usa esattamente questa struttura HTML:

<h1>[Titolo specifico — es. "Analisi Bilancio 2024 — EagleProjects S.p.A."]</h1>
<p class="meta">Settore: ${sectorLabel} | Report K-BOT — K2-AI</p>

<div class="executive-summary">
<h2>Executive Summary</h2>
<p>[3-5 frasi: situazione complessiva, segnali principali, orientamento. Nessuna domanda. Nessun allarmismo generico. Conclusivo.]</p>
</div>

<h2>Dati Analizzati</h2>
[Tabella o elenco strutturato con i valori chiave estratti dal materiale. Se disponibili: ricavi, costi, margini, indici. Se non disponibili per un dato: indica "non disponibile nel materiale" — non inventare.]

<h2>Segnali Identificati</h2>
[Per ogni segnale (massimo 5):
<div class="signal [critica|alta|media]">
  <span class="badge [critica|alta|media]">[CRITICA|ALTA|MEDIA]</span>
  <h3>[Titolo segnale]</h3>
  <p><strong>Sintomo:</strong> [cosa si vede nei dati — con numeri se disponibili]</p>
  <p><strong>Causa strutturale:</strong> [perché accade, nel contesto operativo del settore — es. per uno studio a commessa, crediti alti sono normali ma se superano X mesi sono un problema di governance contrattuale]</p>
  <p><strong>Impatto operativo:</strong> [effetto concreto sull'azienda]</p>
</div>]

<h2>Analisi di Dettaglio</h2>
[Sezione tecnica: indici calcolati, confronti anno su anno, benchmark di settore dove disponibili. Usa i framework delle skill interne. Per bilanci: ROE/ROI/ROS, liquidità corrente, D/E, CCC. Per altri settori: metriche rilevanti dal contesto.]

<h2>Azioni Prioritarie</h2>
[3-5 azioni specifiche e realizzabili, con orizzonte temporale (immediato/3 mesi/6 mesi). Concrete, non generiche.]

<h2>Punti da Approfondire</h2>
[2-3 informazioni aggiuntive che permetterebbero un'analisi più precisa — non domande all'utente, ma indicazioni per chi usa il report.]

REGOLE QUALITÀ:
- Distingui SEMPRE sintomi da cause strutturali.
- Contestualizza nel modello di business del settore.
- Non usare "potrebbe", "forse", "si potrebbe valutare" — sii diretto.
- Non terminare il report con domande.
- Non proporre automazioni AI.
- Se un dato numerico non è nel materiale, NON inventarlo.

SKILL INTERNE DISPONIBILI (usa i framework, gli indici e i benchmark pertinenti):
${skills.slice(0, 22000)}`;

  const response = await anthropic.messages.create({
    model: REPORT_MODEL,
    max_tokens: 4096,
    system: reportSystemPrompt,
    messages: [{
      role: 'user',
      content: `Produci il report finale.\n\nConversazione:\n${messages.map(m => `${m.role}: ${m.content}`).join('\n')}\n\nAllegati:\n${files.map(f => `${f.name}:\n${String(f.extractedSummary || f.extractedText || '').slice(0, 4000)}`).join('\n\n')}`,
    }],
  });

  const reportBody = response.content?.[0]?.type === 'text' ? response.content[0].text : '<p>Report non disponibile.</p>';
  const html = `<!doctype html>
<html lang="it">
<head><meta charset="utf-8"><title>Report K-BOT — K2-AI</title>
<style>
  body{font-family:'Helvetica Neue',Arial,sans-serif;max-width:860px;margin:40px auto;line-height:1.65;color:#1a202c;padding:0 24px}
  h1{font-size:26px;color:#0d1b2a;border-bottom:2px solid #e2e8f0;padding-bottom:12px;margin-bottom:6px}
  h2{font-size:19px;color:#1a365d;margin-top:36px;border-left:4px solid #3182ce;padding-left:12px}
  h3{font-size:15px;color:#2d3748;margin:12px 0 6px}
  .meta{color:#718096;font-size:13px;margin-bottom:28px}
  .executive-summary{background:#f7fafc;border:1px solid #e2e8f0;padding:20px 24px;margin:20px 0 32px;border-radius:4px}
  .executive-summary h2{border-left:none;padding-left:0;margin-top:0}
  .signal{border:1px solid #e2e8f0;padding:16px;margin-bottom:14px;border-radius:4px}
  .signal.critica{border-left:4px solid #e53e3e}
  .signal.alta{border-left:4px solid #dd6b20}
  .signal.media{border-left:4px solid #d69e2e}
  .badge{display:inline-block;font-size:11px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;padding:2px 8px;border-radius:2px;margin-bottom:8px}
  .badge.critica{background:#fed7d7;color:#c53030}
  .badge.alta{background:#feebc8;color:#c05621}
  .badge.media{background:#fefcbf;color:#b7791f}
  table{width:100%;border-collapse:collapse;margin:14px 0;font-size:14px}
  th{background:#edf2f7;padding:8px 12px;text-align:left;font-weight:600;border:1px solid #e2e8f0}
  td{padding:8px 12px;border:1px solid #e2e8f0}
  strong{color:#2d3748}
  p{margin:8px 0}
</style>
</head>
<body>
${reportBody}
<hr style="margin:40px 0;border:none;border-top:1px solid #e2e8f0">
<p style="font-size:12px;color:#a0aec0">Report generato da K-BOT · K2-AI · ${new Date().toLocaleDateString('it-IT')}</p>
</body></html>`;
  const reportUrl = `/api/kbot/report?id=${encodeURIComponent(sessionId)}`;

  await supabase
    .from('kbot_sessions')
    .update({
      status: 'paid',
      pdf_url: reportUrl,
      collected_data: { ...(session.collected_data || {}), report_html: html },
      updated_at: new Date().toISOString(),
    })
    .eq('id', sessionId);

  sendJson(res, 200, { pdf_url: reportUrl, free: true });
}

async function handleKbotReport(req, res) {
  if (req.method !== 'GET') return sendJson(res, 405, { error: 'Method not allowed' });
  const url = new URL(req.url || '/', SITE_URL);
  const id = url.searchParams.get('id');
  if (!id) return send(res, 400, { 'Content-Type': 'text/plain; charset=utf-8' }, 'id obbligatorio');

  const supabase = createSupabaseAdminClient();
  const { data, error } = await supabase.from('kbot_sessions').select('collected_data').eq('id', id).single();
  const html = data?.collected_data?.report_html;
  if (error || !html) return send(res, 404, { 'Content-Type': 'text/plain; charset=utf-8' }, 'Report non trovato');

  send(res, 200, {
    'Content-Type': 'text/html; charset=utf-8',
    'Cache-Control': 'no-store',
  }, html);
}

async function handleKbotStatus(req, res) {
  if (req.method !== 'GET') return sendJson(res, 405, { error: 'Method not allowed' });
  const url = new URL(req.url || '/', SITE_URL);
  const id = url.searchParams.get('id');
  if (!id) return sendJson(res, 400, { error: 'id obbligatorio' });

  const supabase = createSupabaseAdminClient();
  const { data, error } = await supabase.from('kbot_sessions').select('status, pdf_url').eq('id', id).single();
  if (error || !data) return sendJson(res, 404, { error: 'Session not found' });
  sendJson(res, 200, { status: data.status, pdf_url: data.pdf_url || null });
}

async function handleKbotApi(req, res, rawPath) {
  if (rawPath === '/api/kbot/session') return handleKbotSession(req, res);
  if (rawPath === '/api/kbot/chat') return handleKbotChat(req, res);
  if (rawPath === '/api/kbot/upload') return handleKbotUpload(req, res);
  if (rawPath === '/api/kbot/teaser') return handleKbotTeaser(req, res);
  if (rawPath === '/api/kbot/contact') return handleKbotContact(req, res);
  if (rawPath === '/api/kbot/generate-pdf') return handleKbotGenerateReport(req, res);
  if (rawPath === '/api/kbot/report') return handleKbotReport(req, res);
  if (rawPath === '/api/kbot/status') return handleKbotStatus(req, res);
  return sendJson(res, 404, { error: 'K-BOT endpoint not found' });
}

function serveFile(req, res, filePath) {
  fs.stat(filePath, (statErr, stats) => {
    if (statErr || !stats.isFile()) {
      send(res, 404, { 'Content-Type': 'text/plain; charset=utf-8' }, 'Not found');
      return;
    }

    const ext = path.extname(filePath).toLowerCase();
    const contentType = MIME_TYPES[ext] || 'application/octet-stream';
    const range = req.headers.range;

    if (range) {
      const match = range.match(/bytes=(\d*)-(\d*)/);
      const start = match && match[1] ? parseInt(match[1], 10) : 0;
      const end = match && match[2] ? parseInt(match[2], 10) : stats.size - 1;

      if (!match || start >= stats.size || end >= stats.size || start > end) {
        send(res, 416, { 'Content-Range': `bytes */${stats.size}` }, '');
        return;
      }

      res.writeHead(206, {
        'Content-Type': contentType,
        'Content-Length': String(end - start + 1),
        'Content-Range': `bytes ${start}-${end}/${stats.size}`,
        'Accept-Ranges': 'bytes'
      });
      fs.createReadStream(filePath, { start, end }).pipe(res);
      return;
    }

    fs.readFile(filePath, (err, data) => {
    if (err) {
      send(res, 404, { 'Content-Type': 'text/plain; charset=utf-8' }, 'Not found');
      return;
    }
      // HTML: rivalidazione obbligatoria ad ogni richiesta (no CDN cache)
      // Asset con hash nel nome: cache immutabile 1 anno
      const isHtml = ext === '.html';
      const hasHash = /\-[a-zA-Z0-9_]{8,}\.[a-z]+$/.test(filePath);
      const cacheControl = isHtml
        ? 'no-cache, no-store, must-revalidate'
        : hasHash
          ? 'public, max-age=31536000, immutable'
          : 'public, max-age=3600';

      send(res, 200, {
        'Content-Type': contentType,
        'Content-Length': String(stats.size),
        'Accept-Ranges': 'bytes',
        'Cache-Control': cacheControl,
      }, data);
    });
  });
}

const server = http.createServer((req, res) => {
  const host = normalizeHost(req);
  if (shouldRedirect(host)) {
    const location = `https://${CANONICAL_HOST}${req.url || '/'}`;
    send(res, 301, { Location: location }, '');
    return;
  }

  // 301 redirects - URL rename and clean URLs.
  const REDIRECTS_301 = {
    '/casi-studio': '/laboratorio',
    '/casi-studio.html': '/laboratorio',
    '/workshop': '/suite-ai',
    '/workshop.html': '/suite-ai',
  };
  const rawPath = (req.url || '/').split('?')[0];
  const rawQuery = (req.url || '').includes('?') ? `?${(req.url || '').split('?').slice(1).join('?')}` : '';

  if (rawPath === '/api/newsletter/subscribe') {
    handleNewsletterSubscribe(req, res).catch(err => {
      console.error('Newsletter subscribe error:', err);
      sendJson(res, 500, { error: 'Errore temporaneo' });
    });
    return;
  }

  if (rawPath === '/api/newsletter/confirm') {
    handleNewsletterConfirm(req, res).catch(err => {
      console.error('Newsletter confirm error:', err);
      send(res, 302, { Location: '/newsletter-error' }, '');
    });
    return;
  }

  if (rawPath.startsWith('/api/kbot/')) {
    handleKbotApi(req, res, rawPath).catch(err => {
      console.error('K-BOT API error:', err);
      sendJson(res, 500, { error: 'Errore temporaneo K-BOT' });
    });
    return;
  }

  if (rawPath.startsWith('/api/')) {
    proxyApiRequest(req, res, rawPath, rawQuery).catch(err => {
      console.error('API proxy failure:', err);
      sendJson(res, 502, { error: 'Errore proxy API' });
    });
    return;
  }

  if (REDIRECTS_301[rawPath]) {
    send(res, 301, { Location: `${REDIRECTS_301[rawPath]}${rawQuery}` }, '');
    return;
  }

  if (rawPath !== '/index.html' && rawPath.endsWith('.html')) {
    send(res, 301, { Location: `${rawPath.slice(0, -5)}${rawQuery}` }, '');
    return;
  }

  let urlPath = rawPath;
  if (urlPath === '/') {
    urlPath = '/index.html';
  }

  const safePath = path.normalize(urlPath).replace(/^(\.\.[/\\])+/, '');
  let filePath = path.join(DIST_DIR, safePath);
  if (!path.extname(filePath)) {
    filePath = `${filePath}.html`;
  }
  serveFile(req, res, filePath);
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`K2-AI website listening on ${PORT}`);
});
