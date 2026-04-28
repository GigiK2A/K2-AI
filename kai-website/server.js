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
Obiettivo: analizzare documenti, dati o un caso specifico usando le skill interne. Non vendere automazioni e non trasformare il report in una richiesta di progetto.
Conversazione naturale: fai domande mirate solo quando servono davvero per interpretare il materiale. Evita domande statiche.
Dopo 1-2 turni utili, se hai abbastanza contesto, chiudi con una frase breve e includi esattamente: report_ready: true
Il report finale deve descrivere cosa emerge dall'analisi: segnali, rischi, punti da verificare, lettura tecnica e priorità informative.`;

  const leadRules = `
Modalità CONTATTO.
Obiettivo: capire contesto, problema, urgenza e fit commerciale, poi portare verso /contatti.html.
Conversazione naturale: una domanda alla volta, basata sulla risposta precedente. Niente script rigido.
Quando hai processo, attrito, obiettivo e urgenza, sintetizza il caso e includi esattamente: lead_ready: true`;

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

function cleanKbotAssistantMessage(message) {
  return String(message || '')
    .replace(/report_ready\s*:\s*true/gi, '')
    .replace(/lead_ready\s*:\s*true/gi, '')
    .replace(/\n{3,}/g, '\n\n')
    .trim() || 'Ricevuto. Dimmi pure un dettaglio in più e procediamo.';
}

function readJsonBody(req) {
  return new Promise((resolve, reject) => {
    let data = '';
    req.on('data', chunk => {
      data += chunk.toString();
      if (data.length > 16 * 1024) {
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
      max_tokens: 700,
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

  const assistantMessage = cleanKbotAssistantMessage(rawAssistant);
  const collectedData = {
    ...(session.collected_data || {}),
    mode,
    ...(mode === 'report' && /report_ready\s*:\s*true/i.test(rawAssistant) ? { report_ready: true } : {}),
    ...(mode === 'lead' && /lead_ready\s*:\s*true/i.test(rawAssistant) ? { lead_ready: true } : {}),
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

  const body = await readJsonBody(req);
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
  const anthropic = createAnthropicClient();
  const response = await anthropic.messages.create({
    model: KBOT_MODEL,
    max_tokens: 1200,
    system: `Sei K-BOT. Produci solo JSON valido per un teaser di report analitico, non commerciale. Usa skill e contesto, non proporre automazioni. Campi: settore, skill_attive array, segnali array massimo 3 con priorita/titolo/sintesi/anteprima_analisi, hook_pdf.`,
    messages: [{
      role: 'user',
      content: `Settore: ${resolveKbotSectorLabel(session.sector)}\nConversazione:\n${messages.map(m => `${m.role}: ${m.content}`).join('\n')}\nAllegati:\n${files.map(f => `${f.name}: ${f.extractedSummary}`).join('\n\n')}`,
    }],
  });

  let teaser;
  try {
    teaser = JSON.parse(String(response.content?.[0]?.text || '{}').replace(/```json|```/g, '').trim());
  } catch {
    teaser = {
      settore: resolveKbotSectorLabel(session.sector),
      skill_attive: resolveKbotSkillNames(session.sector),
      segnali: [{ priorita: 'rilevante', titolo: 'Punto da verificare', sintesi: 'Il materiale richiede una lettura strutturata.', anteprima_analisi: 'Nel report completo trovi la lettura dei segnali principali.' }],
      hook_pdf: 'Il report gratuito raccoglie lettura tecnica, punti aperti e priorità di verifica.',
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
  const anthropic = createAnthropicClient();
  const response = await anthropic.messages.create({
    model: KBOT_MODEL,
    max_tokens: 2600,
    system: `${buildKbotSystemPrompt({ mode: 'report', sector: session.sector, step: session.step || 1, session })}\n\nOra produci un report finale in HTML semplice. Deve essere analitico, gratuito per test, basato sulle skill interne e sui documenti. Non vendere automazioni e non usare script.`,
    messages: [{
      role: 'user',
      content: `Crea il report finale.\nConversazione:\n${messages.map(m => `${m.role}: ${m.content}`).join('\n')}\nAllegati:\n${files.map(f => `${f.name}: ${f.extractedSummary}`).join('\n\n')}`,
    }],
  });

  const reportBody = response.content?.[0]?.type === 'text' ? response.content[0].text : '<p>Report non disponibile.</p>';
  const html = `<!doctype html><html lang="it"><meta charset="utf-8"><title>Report K-BOT</title><body style="font-family:Inter,Arial,sans-serif;max-width:820px;margin:40px auto;line-height:1.55;color:#111"><h1>Report K-BOT</h1>${reportBody}</body></html>`;
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
