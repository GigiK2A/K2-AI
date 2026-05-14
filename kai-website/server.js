const http = require('http');
const https = require('https');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { spawn } = require('child_process');
const { createClient } = require('@supabase/supabase-js');
const { Resend } = require('resend');
const Anthropic = require('@anthropic-ai/sdk');

const PORT = process.env.PORT || 4173;
const DIST_DIR = path.join(__dirname, 'dist');
const KBOT_STANDALONE_DIR = process.env.KBOT_STANDALONE_DIR || path.join(__dirname, 'kbot-standalone');
const KBOT_PORT = Number(process.env.KBOT_PORT || 4174);
const REDIRECT_HOST = 'k2-ai.it';
const CANONICAL_HOST = 'www.k2-ai.it';
const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://www.k2-ai.it';
const API_PROXY_BASE = process.env.API_PROXY_BASE || 'https://api.k2-ai.it';
const KBOT_MODEL = process.env.KBOT_MODEL || 'claude-haiku-4-5-20251001';
const REPORT_MODEL = process.env.REPORT_MODEL || 'claude-sonnet-4-6';
const SKILLS_DIR = path.join(__dirname, 'lib', 'skills');
const SUITE_AI_SERVICES = require('./lib/kbot/services-data.json');
const BOARD_REPORT_MOCKS = require('./lib/report/board-report-mocks.json');
const NEWSLETTER_PUBLISH_PATH_TOKEN = 'c7f1b5cb492f8d744b041ce9507f246c8339367313de315a';

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
const SUITE_AI_SERVICE_BY_ID = new Map(SUITE_AI_SERVICES.map(service => [service.id, service]));
const BOARD_REPORT_MOCK_BY_ID = new Map(BOARD_REPORT_MOCKS.map(report => [String(report.id || '').trim().toUpperCase(), report]));
const skillCache = new Map();
const SECURITY_HEADERS = {
  'Content-Security-Policy': "default-src 'self'; base-uri 'self'; frame-ancestors 'self'; form-action 'self' https://*.clerk.accounts.dev https://*.accounts.dev https://*.clerk.com; object-src 'none'; script-src 'self' 'unsafe-inline' https://*.clerk.accounts.dev https://*.accounts.dev https://*.clerk.com https://challenges.cloudflare.com; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data: https://frontend-cdn.perplexity.ai; connect-src 'self' https: wss://*.clerk.accounts.dev wss://*.accounts.dev wss://*.clerk.com; frame-src 'self' https://*.clerk.accounts.dev https://*.accounts.dev https://*.clerk.com https://challenges.cloudflare.com; media-src 'self' data: https:; worker-src 'self' blob:; upgrade-insecure-requests",
  'Referrer-Policy': 'strict-origin-when-cross-origin',
  'X-Content-Type-Options': 'nosniff',
  'X-Frame-Options': 'SAMEORIGIN',
  'Permissions-Policy': 'camera=(), microphone=(), geolocation=(), browsing-topics=()',
};

let kbotProcess = null;
let kbotStandaloneAvailable = false;

function startKbotStandalone() {
  const serverPath = path.join(KBOT_STANDALONE_DIR, 'server.js');
  if (!fs.existsSync(serverPath)) return;

  kbotStandaloneAvailable = true;
  kbotProcess = spawn(process.execPath, [serverPath], {
    cwd: KBOT_STANDALONE_DIR,
    env: {
      ...process.env,
      NODE_ENV: 'production',
      HOSTNAME: '0.0.0.0',
      PORT: String(KBOT_PORT),
    },
    stdio: ['ignore', 'inherit', 'inherit'],
  });

  kbotProcess.on('exit', (code, signal) => {
    kbotProcess = null;
    console.error(`K-BOT standalone exited with code ${code ?? 'null'} signal ${signal ?? 'null'}`);
  });
}

function proxyKbotStandalone(req, res) {
  const target = new URL(req.url || '/', `http://127.0.0.1:${KBOT_PORT}`);
  const proxyReq = http.request({
    hostname: '127.0.0.1',
    port: KBOT_PORT,
    method: req.method,
    path: `${target.pathname}${target.search}`,
    headers: {
      ...req.headers,
      host: `127.0.0.1:${KBOT_PORT}`,
    },
  }, proxyRes => {
    res.writeHead(proxyRes.statusCode || 502, proxyRes.headers);
    proxyRes.pipe(res);
  });

  proxyReq.on('error', err => {
    console.error('K-BOT standalone proxy error:', err);
    if (!res.headersSent) {
      send(res, 502, { 'Content-Type': 'text/plain; charset=utf-8' }, 'K-BOT temporarily unavailable');
    } else {
      res.destroy(err);
    }
  });

  req.pipe(proxyReq);
}

function normalizeHost(req) {
  const xfHost = req.headers['x-forwarded-host'];
  const host = (xfHost || req.headers.host || '').split(',')[0].trim();
  return host.toLowerCase();
}

function shouldRedirect(host) {
  return host === REDIRECT_HOST || host.startsWith(`${REDIRECT_HOST}:`);
}

function applySecurityHeaders(res) {
  Object.entries(SECURITY_HEADERS).forEach(([name, value]) => {
    if (!res.hasHeader(name)) {
      res.setHeader(name, value);
    }
  });

  if (process.env.NODE_ENV === 'production' && !res.hasHeader('Strict-Transport-Security')) {
    res.setHeader('Strict-Transport-Security', 'max-age=31536000; includeSubDomains; preload');
  }
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

function normalizeText(value, maxLen) {
  return String(value || '').trim().slice(0, maxLen);
}

function slugify(value) {
  return String(value || '')
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9\s-]/g, ' ')
    .trim()
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .slice(0, 80);
}

function datePrefix(date = new Date()) {
  return date.toISOString().slice(0, 10);
}

function formatItalianIssueTitle(date) {
  return `Newsletter del ${date.toLocaleDateString('it-IT', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  })}`;
}

function extractInternalApiKeyCandidates(req, body = {}) {
  const auth = String(req.headers.authorization || '');
  const bearer = auth.toLowerCase().startsWith('bearer ') ? auth.slice(7) : '';
  const url = new URL(req.url || '', SITE_URL);
  return [
    req.headers['x-internal-key'],
    req.headers['x-api-key'],
    bearer,
    url.searchParams.get('internal_api_key'),
    url.searchParams.get('key'),
    body.internal_api_key,
    body.internalApiKey,
  ]
    .map(value => String(value || '').trim())
    .filter(Boolean);
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

function normalizeServiceId(value) {
  return String(value || '').trim().toUpperCase();
}

function getSuiteAiService(serviceId) {
  return SUITE_AI_SERVICE_BY_ID.get(normalizeServiceId(serviceId)) || null;
}

function toPublicSuiteAiService(service) {
  if (!service) return null;
  const { skills, ...publicService } = service;
  return publicService;
}

function validateServiceId(serviceId) {
  const normalized = normalizeServiceId(serviceId);
  if (!normalized) return { ok: false, error: 'serviceId obbligatorio' };
  if (!getSuiteAiService(normalized)) return { ok: false, error: 'serviceId non valido' };
  return { ok: true, serviceId: normalized };
}

function resolveKbotSkillNames(sector, serviceId) {
  const service = getSuiteAiService(serviceId);
  if (service && Array.isArray(service.skills) && service.skills.length > 0) return service.skills;
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

function loadKbotSkillBundle(sector, serviceId) {
  const chunks = resolveKbotSkillNames(sector, serviceId)
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

function detectKbotIntent(text, mode = 'report') {
  const value = String(text || '').toLowerCase();
  if (!value.trim()) return 'empty';
  if (/[?？]/.test(value) || /^(come|cosa|quanto|quando|dove|perché|perche|quale|puoi|sapresti|mi spieghi)\b/.test(value)) {
    return 'question';
  }
  if (/\b(preventivo|contatto|call|chiamata|parlare|sentirci|demo|consulenza)\b/.test(value)) return 'contact_request';
  if (/\b(report|pdf|analisi|diagnosi|valutazione|audit|check)\b/.test(value)) return 'report_request';
  if (/\b(allego|file|documento|pdf|excel|csv|bilancio|contratto)\b/.test(value)) return 'document_context';
  if (mode === 'lead') return 'lead_context';
  return 'case_context';
}

function buildDynamicConversationSummary(messages, collectedData = {}, latestIntent = '') {
  const existing = String(collectedData.conversationSummary || collectedData.summary || '').trim();
  const allMessages = Array.isArray(messages) ? messages : [];
  const userMessages = allMessages.filter(message => message.role === 'user').map(message => String(message.content || '').trim()).filter(Boolean);
  const assistantMessages = allMessages.filter(message => message.role === 'assistant').map(message => String(message.content || '').trim()).filter(Boolean);
  const latestUser = userMessages[userMessages.length - 1] || '';
  const firstUser = userMessages[0] || '';
  const serviceId = collectedData.service_id ? `Servizio: ${collectedData.service_id}. ` : '';
  const uploadedFiles = Array.isArray(collectedData.uploaded_files)
    ? collectedData.uploaded_files.map(file => file.name).filter(Boolean)
    : [];

  const facts = [
    serviceId && serviceId.trim(),
    collectedData.businessType ? `Tipo attività: ${collectedData.businessType}.` : '',
    collectedData.problem ? `Problema: ${collectedData.problem}.` : '',
    collectedData.currentProcess ? `Processo attuale: ${collectedData.currentProcess}.` : '',
    collectedData.goal ? `Obiettivo: ${collectedData.goal}.` : '',
    collectedData.urgency ? `Urgenza: ${collectedData.urgency}.` : '',
    collectedData.integrations ? `Strumenti/integrazioni: ${collectedData.integrations}.` : '',
    uploadedFiles.length ? `Allegati: ${uploadedFiles.join(', ')}.` : '',
    firstUser ? `Contesto iniziale: ${firstUser}` : '',
    latestUser && latestUser !== firstUser ? `Ultimo contributo utente: ${latestUser}` : '',
    latestIntent ? `Intent corrente: ${latestIntent}.` : '',
    assistantMessages.length ? `Ultima risposta K-BOT: ${assistantMessages[assistantMessages.length - 1]}` : '',
  ].filter(Boolean);

  const merged = [existing, ...facts].filter(Boolean).join('\n');
  const lines = merged
    .split('\n')
    .map(line => line.trim())
    .filter(Boolean);
  const unique = [];
  const seen = new Set();
  for (const line of lines) {
    const key = line.toLowerCase().replace(/\s+/g, ' ').slice(0, 180);
    if (seen.has(key)) continue;
    seen.add(key);
    unique.push(line);
  }

  return unique.join('\n').slice(-2600);
}

function buildContactPrefillSummary(session, collectedData) {
  const summary = String(collectedData.conversationSummary || collectedData.summary || '').trim();
  const service = getSuiteAiService(collectedData.service_id);
  const messages = Array.isArray(session?.messages) ? session.messages : [];
  const userContext = messages
    .filter(message => message.role === 'user')
    .map(message => String(message.content || '').trim())
    .filter(Boolean)
    .slice(-6)
    .join('\n\n');

  return [
    service ? `Servizio di partenza: ${service.name} (${service.id})` : '',
    collectedData.recommendedTier ? `Tier consigliato: ${collectedData.recommendedTier}` : '',
    summary ? `Sintesi K-BOT:\n${summary}` : '',
    userContext ? `Contesto conversazione:\n${userContext}` : '',
  ].filter(Boolean).join('\n\n').slice(0, 3000);
}

function buildKbotSystemPrompt({ mode, sector, step, session }) {
  const sectorLabel = resolveKbotSectorLabel(sector);
  const serviceId = session?.collected_data?.service_id;
  const service = getSuiteAiService(serviceId);
  const skills = loadKbotSkillBundle(sector, serviceId);
  const conversationSummary = String(session?.collected_data?.conversationSummary || '').trim();
  const currentIntent = String(session?.collected_data?.currentIntent || '').trim();
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
Sei un agente operativo: devi capire l'intento, rispondere alle domande dell'utente quando le fa, mantenere memoria del caso e decidere il prossimo passo sensato. Non sei un modulo rigido.
Settore: ${sectorLabel}
${service ? `Servizio Suite AI selezionato: ${service.id} - ${service.name}` : ''}
Step: ${step}
Intent corrente rilevato: ${currentIntent || 'n/d'}

MEMORIA DINAMICA DELLA CONVERSAZIONE:
${conversationSummary || 'Nessun summary ancora disponibile.'}

Regole generali:
- Una domanda alla volta.
- Tutte le risposte dell'utente sono opzionali: se manca un dato, non bloccare la conversazione.
- Se l'utente fa una domanda, rispondi prima in modo utile e poi, solo se serve, fai una singola domanda successiva.
- Evita duplicazioni: non ripetere domande già coperte nella memoria dinamica.
- Usa tutta la conversazione e la memoria dinamica, non solo l'ultimo messaggio.
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
  if (mode === 'lead' && (text.includes('lead_ready: true') || step >= 8 || collectedData.lead_ready)) {
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
    .replace(/```json[\s\S]*?```/gi, '')
    .replace(/```[\s\S]*?```/gi, '')
    .replace(/\*\*teaser gratuito\*\*[\s\S]*$/i, '')
    .replace(/teaser gratuito[\s\S]*$/i, '')
    .replace(/BRIEF_START[\s\S]*?BRIEF_END/gi, '')
    .replace(/report_ready\s*:\s*true/gi, '')
    .replace(/lead_ready\s*:\s*true/gi, '')
    .replace(/\n{3,}/g, '\n\n')
    .trim() || 'Ricevuto. Dimmi pure un dettaglio in più e procediamo.';
}

function extractJsonFromText(text) {
  const raw = String(text || '').trim();
  if (!raw) return null;
  const fenced = raw.match(/```json\s*([\s\S]*?)\s*```/i);
  const candidate = fenced ? fenced[1] : raw;
  const first = candidate.indexOf('{');
  const last = candidate.lastIndexOf('}');
  if (first === -1 || last === -1 || last <= first) return null;
  try {
    return JSON.parse(candidate.slice(first, last + 1));
  } catch {
    return null;
  }
}

const REPORT_FALLBACK = 'Dato non fornito';

function isPlainObject(value) {
  return Boolean(value && typeof value === 'object' && !Array.isArray(value));
}

function reportText(value) {
  if (typeof value === 'string' && value.trim()) return value.trim();
  if (typeof value === 'number' || typeof value === 'boolean') return String(value);
  return REPORT_FALLBACK;
}

function reportArray(value) {
  return Array.isArray(value)
    ? value.map(item => reportText(item)).filter(item => item !== REPORT_FALLBACK)
    : [];
}

function reportPath(source, pathValue) {
  return pathValue.split('.').reduce((current, key) => {
    if (!isPlainObject(current)) return undefined;
    return current[key];
  }, source);
}

function firstReportValue(source, paths) {
  for (const pathValue of paths) {
    const value = reportPath(source, pathValue);
    if (reportText(value) !== REPORT_FALLBACK || isPlainObject(value) || (Array.isArray(value) && value.length > 0)) {
      return value;
    }
  }
  return undefined;
}

function reportPriorityClass(value) {
  const normalized = String(value || '').trim().toLowerCase();
  if (['high', 'alta', 'alto'].includes(normalized)) return 'high';
  if (['low', 'bassa', 'basso'].includes(normalized)) return 'low';
  return 'medium';
}

function reportPriorityLabel(priorityClass) {
  if (priorityClass === 'high') return 'Alta';
  if (priorityClass === 'low') return 'Bassa';
  return 'Media';
}

function reportUserConversation(messages) {
  const userMessages = Array.isArray(messages)
    ? messages
        .filter(isPlainObject)
        .filter(message => message.role === 'user')
        .map(message => reportText(message.content || message.text))
        .filter(message => message !== REPORT_FALLBACK)
    : [];
  return userMessages.length ? userMessages.join('\n') : REPORT_FALLBACK;
}

function reportDateLabel(value) {
  const candidate = reportText(value) !== REPORT_FALLBACK ? new Date(String(value)) : new Date();
  const date = Number.isNaN(candidate.getTime()) ? new Date() : candidate;
  return date.toLocaleDateString('it-IT', { day: '2-digit', month: 'long', year: 'numeric' });
}

function generateReportData(sessionData) {
  const collectedData = isPlainObject(sessionData?.collected_data) ? sessionData.collected_data : {};
  const extractedData = isPlainObject(sessionData?.extractedData)
    ? sessionData.extractedData
    : isPlainObject(collectedData.extractedData)
      ? collectedData.extractedData
      : {};
  const source = {
    ...(isPlainObject(sessionData) ? sessionData : {}),
    ...collectedData,
    extractedData,
    conversation: reportUserConversation(sessionData?.messages),
  };
  const serviceId = normalizeServiceId(firstReportValue(source, ['serviceId', 'service_id', 'extractedData.recommendedServiceId']) || 'P12');
  const service = isPlainObject(source.selectedService)
    ? source.selectedService
    : SUITE_AI_SERVICE_BY_ID.get(serviceId) || SUITE_AI_SERVICE_BY_ID.get('P12') || {};
  const serviceName = reportText(firstReportValue(source, ['selectedService.name', 'extractedData.recommendedServiceName']) || service.name);
  const recommendedTier = reportText(firstReportValue(source, ['recommendedTier', 'recommended_tier', 'extractedData.recommendedTier']) || service.recommendedTier);
  const conversationSummary = reportText(firstReportValue(source, ['conversationSummary', 'summary', 'extractedData.summary', 'conversation']));
  const problem = reportText(firstReportValue(source, ['problem', 'extractedData.problem']));
  const goal = reportText(firstReportValue(source, ['goal', 'extractedData.goal']));
  const currentProcess = reportText(firstReportValue(source, ['currentProcess', 'extractedData.currentProcess']));
  const businessType = reportText(firstReportValue(source, ['businessType', 'extractedData.businessType', 'client.scope', 'scope']));
  const tags = [serviceName, recommendedTier, ...reportArray(service.tags)].filter(tag => tag !== REPORT_FALLBACK).slice(0, 6);
  const metrics = [
    { value: recommendedTier, label: 'tier consigliato' },
    { value: reportText(firstReportValue(source, ['urgency', 'extractedData.urgency'])), label: 'urgenza dichiarata' },
    { value: reportText(firstReportValue(source, ['budget', 'extractedData.budget'])), label: 'budget indicato' },
  ];
  const problemRows = [{
    area: businessType,
    criticalIssue: problem,
    effect: reportText(firstReportValue(source, ['urgency', 'extractedData.urgency', 'notes', 'extractedData.notes'])),
    priority: 'Media',
    priorityClass: 'medium',
  }];
  const priorityClass = reportPriorityClass(firstReportValue(source, ['priority', 'extractedData.priority']));

  return {
    meta: {
      title: `Report K-BOT - ${serviceName}`,
      subtitle: reportText(service.shortDescription || service.description),
      category: 'Diagnosi operativa K2-AI',
      code: `K2AI-KBOT-${serviceId}`,
      date: reportDateLabel(firstReportValue(source, ['updated_at', 'created_at'])),
      version: '1.0',
    },
    client: {
      name: reportText(firstReportValue(source, ['client.name', 'companyName', 'extractedData.companyName', 'businessType', 'extractedData.businessType'])),
      scope: businessType,
    },
    sections: {
      cover: true,
      executiveSummary: true,
      context: true,
      problem: true,
      analysis: true,
      opportunity: true,
      solution: true,
      roadmap: true,
      priorities: true,
      impact: true,
      recommendedPlan: true,
      nextSteps: true,
      disclaimer: true,
    },
    executiveSummary: {
      title: 'Executive summary',
      text: conversationSummary,
      metrics,
      operationalTakeaway: reportText(firstReportValue(source, ['nextStep', 'extractedData.nextStep', 'goal', 'extractedData.goal'])),
    },
    context: {
      title: 'Contesto aziendale',
      currentScenario: currentProcess,
      reportObjective: goal,
      tags: tags.length ? tags : [REPORT_FALLBACK],
    },
    problem: {
      title: 'Problema rilevato',
      main: problem,
      rows: problemRows,
    },
    analysis: {
      title: 'Analisi operativa',
      intro: conversationSummary,
      cards: [
        { title: 'Processo attuale', description: currentProcess },
        { title: 'Dati disponibili', description: reportText(firstReportValue(source, ['dataAvailable', 'extractedData.dataAvailable'])) },
        { title: 'Note operative', description: reportText(firstReportValue(source, ['notes', 'extractedData.notes', 'conversation'])) },
      ],
      table: [
        { parameter: 'Urgenza', detectedStatus: reportText(firstReportValue(source, ['urgency', 'extractedData.urgency'])), evaluation: recommendedTier, note: 'Dato raccolto da K-BOT.' },
        { parameter: 'Integrazioni', detectedStatus: reportText(firstReportValue(source, ['integrations', 'extractedData.integrations'])), evaluation: REPORT_FALLBACK, note: 'Da validare in fase di scoping.' },
        { parameter: 'Budget', detectedStatus: reportText(firstReportValue(source, ['budget', 'extractedData.budget'])), evaluation: REPORT_FALLBACK, note: 'Da confermare con il cliente.' },
      ],
    },
    opportunity: {
      title: 'Opportunita AI',
      intro: reportText(service.shortDescription || service.description),
      items: (reportArray(service.useCases).length ? reportArray(service.useCases) : [REPORT_FALLBACK]).slice(0, 4).map(useCase => ({
        title: useCase,
        description: goal,
        impact: 'Da stimare',
        effort: 'Da stimare',
      })),
    },
    solution: {
      title: 'Soluzione proposta',
      description: reportText(service.shortDescription || service.description),
      components: [reportText(service.target)],
      expectedResult: goal,
    },
    roadmap: {
      title: 'Roadmap di implementazione',
      items: [
        { phaseTitle: 'Fase 1 - Scoping', timeframe: 'Settimana 1', owner: 'Cliente + K2-AI', phaseDescription: 'Confermare processo, dati disponibili, vincoli e risultato atteso.' },
        { phaseTitle: 'Fase 2 - Prototipo', timeframe: 'Settimane 2-3', owner: 'K2-AI', phaseDescription: 'Preparare un primo flusso operativo sul perimetro selezionato.' },
        { phaseTitle: 'Fase 3 - Validazione', timeframe: 'Settimana 4', owner: 'Cliente + K2-AI', phaseDescription: 'Testare casi reali, raccogliere feedback e misurare gli indicatori principali.' },
      ],
    },
    priorities: {
      title: 'Priorita operative',
      items: [{
        priorityLevel: reportPriorityLabel(priorityClass),
        priorityClass,
        action: goal,
        reason: problem,
        impact: reportText(firstReportValue(source, ['urgency', 'extractedData.urgency'])),
        timing: 'Subito',
      }],
    },
    impact: {
      title: 'Impatto atteso',
      metrics,
      rows: [
        { dimension: 'Tempo', expectedImpact: goal, indicator: 'Ore risparmiate o tempi ciclo ridotti.' },
        { dimension: 'Qualita operativa', expectedImpact: problem, indicator: 'Riduzione errori, rilavorazioni o passaggi manuali.' },
      ],
    },
    recommendedPlan: {
      title: `Piano consigliato - ${recommendedTier}`,
      summary: reportText(firstReportValue(source, ['nextStep', 'extractedData.nextStep']) || service.target),
      steps: [
        { step: '01', activity: 'Validazione dati K-BOT', output: 'Perimetro confermato', owner: 'Cliente + K2-AI' },
        { step: '02', activity: 'Disegno flusso operativo', output: 'Schema soluzione e requisiti', owner: 'K2-AI' },
        { step: '03', activity: 'Prototipo e test', output: 'Demo funzionante su casi reali', owner: 'K2-AI' },
      ],
    },
    nextSteps: {
      title: 'Next step',
      immediateActions: [reportText(firstReportValue(source, ['nextStep', 'extractedData.nextStep']))],
      requiredDecisions: ['Confermare perimetro, dati disponibili e responsabile operativo.'],
      suggestedNextStep: reportText(firstReportValue(source, ['nextStep', 'extractedData.nextStep'])),
    },
    disclaimer: {
      title: 'Disclaimer',
      text: 'Questo report e generato tramite mapping deterministico dei dati raccolti da K-BOT. Le informazioni mancanti sono indicate come "Dato non fornito" e devono essere validate prima di qualsiasi implementazione.',
    },
  };
}

function renderStructuredReportHtml(report, sectorLabel) {
  const safe = report || {};
  const title = escapeHtml(String(safe.title || `Report di analisi - ${sectorLabel}`));
  const summary = escapeHtml(String(safe.executive_summary || 'Analisi completata con i dati disponibili.'));
  const dataPoints = Array.isArray(safe.data_points) ? safe.data_points : [];
  const signals = Array.isArray(safe.signals) ? safe.signals : [];
  const priorities = Array.isArray(safe.priorities) ? safe.priorities : [];
  const checks = Array.isArray(safe.checks) ? safe.checks : [];

  const dataHtml = dataPoints.length
    ? `<ul>${dataPoints.map(item => `<li>${escapeHtml(String(item))}</li>`).join('')}</ul>`
    : '<p>Dati quantitativi non disponibili in forma leggibile nel materiale ricevuto.</p>';

  const signalsHtml = signals.length
    ? signals.map(item => {
      const levelRaw = String(item.level || 'media').toLowerCase();
      const level = ['critica', 'alta', 'media'].includes(levelRaw) ? levelRaw : 'media';
      return `<section class="signal ${level}">
  <h3>${escapeHtml(String(item.title || 'Segnale'))}</h3>
  <p><strong>Sintomo:</strong> ${escapeHtml(String(item.symptom || 'n/d'))}</p>
  <p><strong>Causa strutturale:</strong> ${escapeHtml(String(item.cause || 'n/d'))}</p>
  <p><strong>Impatto operativo:</strong> ${escapeHtml(String(item.impact || 'n/d'))}</p>
</section>`;
    }).join('')
    : '<p>Nessun segnale strutturato disponibile.</p>';

  const prioritiesHtml = priorities.length
    ? `<ol>${priorities.map(item => `<li>${escapeHtml(String(item))}</li>`).join('')}</ol>`
    : '<p>Definire priorita operative dopo verifica dati.</p>';

  const checksHtml = checks.length
    ? `<ul>${checks.map(item => `<li>${escapeHtml(String(item))}</li>`).join('')}</ul>`
    : '<p>Nessun punto aggiuntivo.</p>';

  return `<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${title}</title>
<style>
body{font-family:Inter,Arial,sans-serif;max-width:920px;margin:36px auto;padding:0 18px;line-height:1.6;color:#121212}
h1{font-size:32px;line-height:1.15;margin:0 0 12px}
h2{font-size:22px;margin:28px 0 10px}
h3{font-size:18px;margin:0 0 8px}
.meta{color:#5f6b7a;font-size:13px;margin-bottom:22px}
.box{border:1px solid #e3e7ee;background:#f8fafc;padding:16px}
.signal{border:1px solid #e3e7ee;padding:14px;margin:0 0 12px}
.signal.critica{border-left:4px solid #b42318}
.signal.alta{border-left:4px solid #dd6b20}
.signal.media{border-left:4px solid #1d4ed8}
ul,ol{padding-left:20px}
</style>
</head>
<body>
<h1>${title}</h1>
<p class="meta">Settore: ${escapeHtml(String(sectorLabel))} | Report K-BOT - K2-AI</p>
<section class="box">
  <h2>Executive Summary</h2>
  <p>${summary}</p>
</section>
<h2>Dati Analizzati</h2>
${dataHtml}
<h2>Segnali Identificati</h2>
${signalsHtml}
<h2>Priorita Operative</h2>
${prioritiesHtml}
<h2>Punti da Verificare</h2>
${checksHtml}
</body>
</html>`;
}

function chooseReportTemplateProfile(sector, collectedData, messages) {
  const text = [
    String(collectedData?.problem_description || ''),
    ...((Array.isArray(messages) ? messages : []).map(m => String(m?.content || ''))),
  ].join(' ').toLowerCase();

  if (sector === 'commercialista' || text.includes('bilancio') || text.includes('ebitda') || text.includes('debito')) {
    return 'financial_diagnosis';
  }
  if (sector === 'studio-ingegneria' || sector === 'tlc' || text.includes('commessa') || text.includes('cantier')) {
    return 'operations_commesse';
  }
  if (sector === 'manifatturiero' || text.includes('produzion') || text.includes('magazzino') || text.includes('scorte')) {
    return 'operations_production';
  }
  return 'general_service';
}

function buildPdfAnalysisPrompt({ session, sectorLabel, skills, profile }) {
  const messages = Array.isArray(session?.messages) ? session.messages : [];
  const files = Array.isArray(session?.collected_data?.uploaded_files) ? session.collected_data.uploaded_files : [];
  const compactConversation = compactKbotMessages(messages, 24, 2200);

  return `Produci l'ANALISI COMPLETA JSON per il PDF della Diagnosi AI Operativa.

SETTORE: ${sectorLabel}
PROFILO TEMPLATE DA USARE: ${profile}
DATI RACCOLTI: ${JSON.stringify(session?.collected_data || {}, null, 2)}
CONVERSAZIONE: ${compactConversation.map(m => `${m.role}: ${m.content}`).join('\n')}
ALLEGATI ESTRATTI: ${files.map(f => `${f.name}: ${(String(f.extractedSummary || f.extractedText || '')).slice(0, 2400)}`).join('\n\n')}

Vincoli:
- Produci SOLO JSON valido.
- Struttura allineata alla skill diagnosi-ai-operativa-pmi (analisi completa).
- Minimo 3 sezioni verticali con elementi visivi (includi almeno 1 tabella, 1 grafico barre, 1 gauge).
- Distingui sintomo e causa strutturale.
- NON proporre automazioni come call-to-action commerciale: sezione automazioni solo come lettura analitica interna.
- Nessun testo markdown o prose fuori JSON.

Skill bundle disponibile:
${skills.slice(0, 22000)}`;
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

  const recipientName = typeof body.name === 'string' && body.name.trim() ? body.name.trim().slice(0, 100) : null;
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

async function handleNewsletterPublish(req, res, options = {}) {
  if (req.method === 'OPTIONS') {
    send(res, 204, {
      'Access-Control-Allow-Origin': SITE_URL,
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, x-internal-key',
    }, '');
    return;
  }

  if (req.method !== 'POST') {
    sendJson(res, 405, { error: 'Method not allowed' });
    return;
  }

  let body;
  try {
    body = await readJsonBody(req, 4 * 1024 * 1024);
  } catch {
    sendJson(res, 400, { error: 'Invalid JSON' });
    return;
  }

  const expectedKey = getEnvVar('INTERNAL_API_KEY');
  const providedKeys = extractInternalApiKeyCandidates(req, body);
  const hasValidPathToken = options.pathToken === NEWSLETTER_PUBLISH_PATH_TOKEN;
  if (!hasValidPathToken && (!expectedKey || !providedKeys.includes(expectedKey))) {
    sendJson(res, 401, { error: 'Unauthorized' });
    return;
  }

  if (body.cleanup_tests === true) {
    const supabase = createSupabaseAdminClient();
    const { error } = await supabase
      .from('newsletter_issues')
      .delete()
      .like('slug', '2026-05-08-test-%');

    if (error) {
      console.error('Newsletter cleanup error:', error);
      sendJson(res, 500, { error: 'Cleanup failed' });
      return;
    }

    sendJson(res, 200, { ok: true, cleanup: 'tests' });
    return;
  }

  const originalSubject = normalizeText(body.subject, 220);
  const previewText = normalizeText(body.preview_text, 500);
  const html = String(body.html || '').trim();

  if (!originalSubject) {
    sendJson(res, 400, { error: 'Missing subject' });
    return;
  }
  if (!html) {
    sendJson(res, 400, { error: 'Missing html' });
    return;
  }

  const publishedAt = new Date();
  const displaySubject = formatItalianIssueTitle(publishedAt);
  const customSlug = normalizeText(body.slug, 120);
  const safeBase = slugify(customSlug || originalSubject) || 'newsletter';
  const finalSlug = `${datePrefix(publishedAt)}-${safeBase}`.slice(0, 120);

  const supabase = createSupabaseAdminClient();
  const { data, error } = await supabase
    .from('newsletter_issues')
    .upsert({
      slug: finalSlug,
      subject: displaySubject,
      preview_text: previewText,
      html,
      source: normalizeText(body.source, 120) || 'n8n',
      published_at: publishedAt.toISOString(),
      updated_at: publishedAt.toISOString(),
    }, { onConflict: 'slug' })
    .select('slug, subject, published_at')
    .single();

  if (error || !data) {
    console.error('Newsletter publish error:', error);
    sendJson(res, 500, { error: 'Publish failed' });
    return;
  }

  sendJson(res, 200, {
    ok: true,
    slug: data.slug,
    url: `${SITE_URL}/newsletter-entry?slug=${encodeURIComponent(data.slug)}`,
    published_at: data.published_at,
  });
}

async function handleNewsletterIssues(req, res) {
  if (req.method !== 'GET') {
    sendJson(res, 405, { error: 'Method not allowed' });
    return;
  }

  const url = new URL(req.url || '', SITE_URL);
  const limitRaw = Number(url.searchParams.get('limit') || 100);
  const limit = Number.isFinite(limitRaw) ? Math.min(Math.max(limitRaw, 1), 200) : 100;
  const supabase = createSupabaseAdminClient();

  const { data, error } = await supabase
    .from('newsletter_issues')
    .select('slug,subject,preview_text,published_at')
    .order('published_at', { ascending: false })
    .limit(limit);

  if (error) {
    console.error('Newsletter list error:', error);
    sendJson(res, 500, { error: 'List failed' });
    return;
  }

  sendJson(res, 200, { ok: true, items: data || [] });
}

async function handleNewsletterIssue(req, res) {
  if (req.method !== 'GET') {
    sendJson(res, 405, { error: 'Method not allowed' });
    return;
  }

  const url = new URL(req.url || '', SITE_URL);
  const slug = String(url.searchParams.get('slug') || '').trim();
  if (!slug) {
    sendJson(res, 400, { error: 'Missing slug' });
    return;
  }

  const supabase = createSupabaseAdminClient();
  const { data, error } = await supabase
    .from('newsletter_issues')
    .select('slug,subject,preview_text,html,published_at')
    .eq('slug', slug)
    .single();

  if (error || !data) {
    sendJson(res, 404, { error: 'Not found' });
    return;
  }

  sendJson(res, 200, { ok: true, item: data });
}

async function handleNewsletterCleanupTests(req, res, options = {}) {
  if (req.method !== 'POST') {
    sendJson(res, 405, { error: 'Method not allowed' });
    return;
  }

  if (options.pathToken !== NEWSLETTER_PUBLISH_PATH_TOKEN) {
    sendJson(res, 401, { error: 'Unauthorized' });
    return;
  }

  const supabase = createSupabaseAdminClient();
  const { error } = await supabase
    .from('newsletter_issues')
    .delete()
    .like('slug', '2026-05-08-test-auth-%');

  if (error) {
    console.error('Newsletter cleanup error:', error);
    sendJson(res, 500, { error: 'Cleanup failed' });
    return;
  }

  sendJson(res, 200, { ok: true });
}

function serializeKbotSession(session) {
  const collectedData = session?.collected_data && typeof session.collected_data === 'object'
    ? session.collected_data
    : {};
  const extractedData = collectedData.extractedData && typeof collectedData.extractedData === 'object'
    ? collectedData.extractedData
    : collectedData;

  return {
    id: String(session?.id || ''),
    serviceId: normalizeServiceId(collectedData.service_id),
    messages: Array.isArray(session?.messages) ? session.messages : [],
    extractedData,
    summary: typeof collectedData.summary === 'string' ? collectedData.summary : null,
    recommendedTier: typeof collectedData.recommendedTier === 'string' ? collectedData.recommendedTier : null,
    timestamps: {
      createdAt: typeof session?.created_at === 'string' ? session.created_at : null,
      updatedAt: typeof session?.updated_at === 'string' ? session.updated_at : null,
    },
  };
}

function normalizeIncomingMessages(value) {
  if (!Array.isArray(value)) return [];
  return value
    .map(item => {
      if (!item || typeof item !== 'object') return null;
      const role = item.role === 'assistant' ? 'assistant' : item.role === 'user' ? 'user' : null;
      const content = String(item.content || item.text || '').trim().slice(0, 6000);
      if (!role || !content) return null;
      return { role, content, ts: typeof item.ts === 'string' ? item.ts : new Date().toISOString() };
    })
    .filter(Boolean);
}

function mergeKbotMessages(storedMessages, incomingMessages) {
  const merged = Array.isArray(storedMessages) ? [...storedMessages] : [];
  for (const incoming of incomingMessages) {
    const exists = merged.some(stored =>
      stored.role === incoming.role &&
      stored.content === incoming.content &&
      (!stored.ts || !incoming.ts || stored.ts === incoming.ts),
    );
    if (!exists) merged.push(incoming);
  }
  return merged;
}

function coalesceKbotMessages(messages) {
  const out = [];
  for (const message of Array.isArray(messages) ? messages : []) {
    const role = message.role === 'assistant' ? 'assistant' : 'user';
    const content = String(message.content || '').trim();
    if (!content) continue;
    const last = out[out.length - 1];
    const normalized = content.toLowerCase().replace(/\s+/g, ' ');
    if (last && last.role === role) {
      const lastNormalized = String(last.content || '').toLowerCase().replace(/\s+/g, ' ');
      if (lastNormalized === normalized || lastNormalized.includes(normalized)) continue;
      if (normalized.includes(lastNormalized)) {
        last.content = content;
        last.ts = message.ts || last.ts;
        continue;
      }
      if (role === 'user' && content.length < 900 && String(last.content || '').length < 1800) {
        last.content = `${last.content}\n\n${content}`;
        last.ts = message.ts || last.ts;
        continue;
      }
    }
    out.push({ ...message, role, content });
  }
  return out;
}

function appendKbotUserMessage(messages, message) {
  const content = String(message || '').trim().slice(0, 6000);
  if (!content) return messages;
  const last = messages[messages.length - 1];
  if (last?.role === 'user' && last.content === content) return messages;
  return [...messages, { role: 'user', content, ts: new Date().toISOString() }];
}

function extractKbotSummaryBlock(text) {
  const match = String(text || '').match(/CONSULENZA_SUMMARY_START\s*\n([\s\S]*?)\nCONSULENZA_SUMMARY_END/);
  if (!match) return null;
  try {
    return JSON.parse(match[1].trim());
  } catch {
    return null;
  }
}

function stripKbotSummaryBlock(text) {
  return String(text || '').replace(/\s*CONSULENZA_SUMMARY_START[\s\S]*?CONSULENZA_SUMMARY_END\s*/g, '').trim();
}

function handleSuiteAiServices(req, res, serviceId) {
  if (req.method !== 'GET') return sendJson(res, 405, { error: 'Method not allowed' });
  if (serviceId) {
    const service = getSuiteAiService(serviceId);
    if (!service) return sendJson(res, 404, { error: 'Service not found' });
    return sendJson(res, 200, { service: toPublicSuiteAiService(service) });
  }
  sendJson(res, 200, { services: SUITE_AI_SERVICES.map(toPublicSuiteAiService) });
}

async function handleKbotSession(req, res) {
  if (req.method !== 'POST') return sendJson(res, 405, { error: 'Method not allowed' });

  const body = await readJsonBody(req);
  const explicitServiceId = body.serviceId || body.service_id;
  const serviceValidation = explicitServiceId
    ? validateServiceId(explicitServiceId)
    : { ok: true, serviceId: 'P12' };
  if (!serviceValidation.ok) return sendJson(res, 400, { error: serviceValidation.error });

  const sector = String(body.sector || 'servizi-b2b').trim();
  const mode = String(body.mode || 'report').trim();

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
      collected_data: {
        mode,
        service_id: serviceValidation.serviceId,
        extractedData: {},
      },
    })
    .select('*')
    .single();

  if (error) return sendJson(res, 500, { error: error.message });
  sendJson(res, 200, { session_id: data.id, mode, session: serializeKbotSession(data) });
}

async function handleKbotChat(req, res) {
  if (req.method !== 'POST') return sendJson(res, 405, { error: 'Method not allowed' });

  const body = await readJsonBody(req);
  const sessionId = String(body.session_id || body.sessionId || '').trim();
  const userMessage = String(body.message || '').trim().slice(0, 6000);
  if (!sessionId || (!userMessage && !Array.isArray(body.messages))) {
    return sendJson(res, 400, { error: 'session_id e message obbligatori' });
  }

  const supabase = createSupabaseAdminClient();
  const { data: session, error: sessionError } = await supabase
    .from('kbot_sessions')
    .select('*')
    .eq('id', sessionId)
    .single();

  if (sessionError || !session) return sendJson(res, 404, { error: 'Session not found' });

  const requestedServiceId = body.serviceId || body.service_id || session.collected_data?.service_id;
  const serviceValidation = validateServiceId(requestedServiceId || 'P12');
  if (!serviceValidation.ok) return sendJson(res, 400, { error: serviceValidation.error });

  const mode = session.collected_data?.mode === 'lead' ? 'lead' : 'report';
  const step = Number(session.step || 1);
  const previousMessages = Array.isArray(session.messages) ? session.messages : [];
  const persistedMessages = coalesceKbotMessages(appendKbotUserMessage(
    mergeKbotMessages(previousMessages, normalizeIncomingMessages(body.messages)),
    userMessage,
  ));
  const currentIntent = detectKbotIntent(userMessage || persistedMessages[persistedMessages.length - 1]?.content || '', mode);
  const preAssistantSummary = buildDynamicConversationSummary(persistedMessages, {
    ...(session.collected_data || {}),
    service_id: serviceValidation.serviceId,
    currentIntent,
  }, currentIntent);

  let rawAssistant = '';
  try {
    const anthropic = createAnthropicClient();
    const response = await anthropic.messages.create({
      model: KBOT_MODEL,
      max_tokens: 900,
      system: buildKbotSystemPrompt({
        mode,
        sector: session.sector,
        step,
        session: {
          ...session,
          collected_data: {
            ...(session.collected_data || {}),
            service_id: serviceValidation.serviceId,
            currentIntent,
            conversationSummary: preAssistantSummary,
          },
        },
      }),
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
  const summaryBlock = extractKbotSummaryBlock(rawAssistant);

  let assistantMessage = cleanKbotAssistantMessage(stripKbotSummaryBlock(rawAssistant));
  if (isReportReady) assistantMessage = stripTrailingQuestion(assistantMessage);

  const leadBrief = isLeadReady ? extractLeadBrief(rawAssistant) : '';

  const collectedData = {
    ...(session.collected_data || {}),
    mode,
    service_id: serviceValidation.serviceId,
    currentIntent,
    ...(isReportReady ? { report_ready: true } : {}),
    ...(isLeadReady ? { lead_ready: true } : {}),
    ...(summaryBlock ? {
      ...summaryBlock,
      extractedData: {
        ...((session.collected_data || {}).extractedData || {}),
        ...summaryBlock,
      },
      summary: summaryBlock.summary,
      recommendedTier: summaryBlock.recommendedTier,
    } : {}),
  };
  const nextAction = detectKbotNextAction(mode, step, collectedData, rawAssistant);
  const updatedMessages = [
    ...persistedMessages,
    { role: 'assistant', content: assistantMessage, ts: new Date().toISOString() },
  ];
  collectedData.conversationSummary = buildDynamicConversationSummary(updatedMessages, collectedData, currentIntent);
  collectedData.contactPrefillSummary = buildContactPrefillSummary({ ...session, messages: updatedMessages }, collectedData);

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
    session: { ...serializeKbotSession({ ...session, messages: updatedMessages, collected_data: collectedData, updated_at: new Date().toISOString() }), step: step + 1, mode },
    conversation_summary: collectedData.conversationSummary,
    contact_summary: nextAction === 'show_contact_form'
      ? (collectedData.contactPrefillSummary || leadBrief || assistantMessage)
      : undefined,
    intent: currentIntent,
    ...(summaryBlock ? { v2_summary: summaryBlock, summary: summaryBlock } : {}),
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
  const skills = loadKbotSkillBundle(session.sector);
  const sectorLabel = resolveKbotSectorLabel(session.sector);
  const anthropic = createAnthropicClient();
  const profile = chooseReportTemplateProfile(session.sector, session.collected_data || {}, messages);

  const response = await anthropic.messages.create({
    model: REPORT_MODEL,
    max_tokens: 4096,
    system: 'Sei un analista senior di K2-AI. Restituisci esclusivamente JSON valido.',
    messages: [{
      role: 'user',
      content: buildPdfAnalysisPrompt({
        session,
        sectorLabel,
        skills,
        profile,
      }),
    }],
  });

  const rawReportText = response.content?.[0]?.type === 'text' ? response.content[0].text : '';
  const analysisJson = extractJsonFromText(rawReportText) || {
    meta: {
      settore: sectorLabel,
      skill_attive: resolveKbotSkillNames(session.sector),
      data_generazione: new Date().toISOString(),
      versione_modello: 'fallback-local',
      template_profile: profile,
    },
    executive_summary: 'Analisi completata in fallback con i dati disponibili. Struttura coerente con template di sistema.',
    sezioni: [
      {
        tipo: 'analisi_verticale',
        titolo: 'Contesto raccolto',
        contenuto: `Settore: ${sectorLabel}\nProfilo template: ${profile}\nProblema: ${session?.collected_data?.problem_description || 'non disponibile nel materiale'}`,
        elementi_visivi: [],
      },
      {
        tipo: 'benchmark',
        titolo: 'Segnali principali',
        contenuto: 'Sono emersi punti di attenzione operativi da verificare su base dati completa.',
        elementi_visivi: [],
      },
      {
        tipo: 'roadmap',
        titolo: 'Priorita',
        contenuto: '1. Consolidare dati\n2. Identificare cause strutturali\n3. Definire azioni a 90 giorni',
        elementi_visivi: [],
      },
    ],
    automazioni_consigliate: [],
    prossimo_passo: {
      testo: 'Report generato in modalita fallback.',
      messaggio_precompilato: '',
    },
  };

  const pdfRuntime = require('./lib/pdf/generator.js');
  const generatePdfFn = pdfRuntime.generateDiagnosiPDF || (pdfRuntime.default && pdfRuntime.default.generateDiagnosiPDF);
  if (typeof generatePdfFn !== 'function') {
    return sendJson(res, 500, { error: 'generateDiagnosiPDF non disponibile' });
  }
  const pdfBuffer = await generatePdfFn(analysisJson);

  const REPORTS_BUCKET = 'kbot-reports';
  const fileName = `kbot-${sessionId}-${Date.now()}.pdf`;
  let { error: uploadError } = await supabase.storage
    .from(REPORTS_BUCKET)
    .upload(fileName, pdfBuffer, { contentType: 'application/pdf', upsert: true });

  if (uploadError && uploadError.message && uploadError.message.toLowerCase().includes('bucket not found')) {
    await supabase.storage.createBucket(REPORTS_BUCKET, { public: true });
    const retry = await supabase.storage
      .from(REPORTS_BUCKET)
      .upload(fileName, pdfBuffer, { contentType: 'application/pdf', upsert: true });
    uploadError = retry.error;
  }
  if (uploadError) {
    return sendJson(res, 500, { error: `Upload PDF fallito: ${uploadError.message}` });
  }

  const { data: publicData } = supabase.storage.from(REPORTS_BUCKET).getPublicUrl(fileName);
  const reportUrl = publicData.publicUrl;

  await supabase
    .from('kbot_sessions')
    .update({
      status: 'paid',
      pdf_url: reportUrl,
      collected_data: {
        ...(session.collected_data || {}),
        template_profile: profile,
        report_json: analysisJson,
      },
      updated_at: new Date().toISOString(),
    })
    .eq('id', sessionId);

  sendJson(res, 200, { pdf_url: reportUrl, free: true });
}

async function handleKbotStructuredReport(req, res) {
  if (req.method !== 'POST') return sendJson(res, 405, { error: 'Method not allowed' });

  const body = await readJsonBody(req);
  const sessionId = String(body.session_id || body.sessionId || '').trim();
  if (!sessionId) return sendJson(res, 400, { error: 'sessionId obbligatorio' });

  const supabase = createSupabaseAdminClient();
  const { data: session, error } = await supabase.from('kbot_sessions').select('*').eq('id', sessionId).single();
  if (error || !session) return sendJson(res, 404, { error: 'Session not found' });

  const serviceValidation = validateServiceId(body.serviceId || body.service_id || session.collected_data?.service_id || 'P12');
  if (!serviceValidation.ok) return sendJson(res, 400, { error: serviceValidation.error });

  const service = getSuiteAiService(serviceValidation.serviceId);
  const messages = coalesceKbotMessages(mergeKbotMessages(session.messages || [], normalizeIncomingMessages(body.messages)));
  const collectedData = {
    ...(session.collected_data || {}),
    service_id: serviceValidation.serviceId,
  };
  collectedData.conversationSummary = buildDynamicConversationSummary(messages, collectedData, 'report_request');
  const recommendedTier = collectedData.recommendedTier || collectedData.recommended_tier || service?.recommendedTier || null;
  const reportData = generateReportData({
    ...session,
    messages,
    selectedService: service || serviceValidation.serviceId,
    serviceId: serviceValidation.serviceId,
    recommendedTier,
    conversationSummary: collectedData.conversationSummary || collectedData.summary,
    extractedData: collectedData.extractedData || collectedData,
  });

  const updatedCollectedData = {
    ...collectedData,
    reportData,
    report: reportData,
    summary: reportData.executiveSummary.text,
    conversationSummary: reportData.executiveSummary.text,
    recommendedTier,
    extractedData: collectedData.extractedData || collectedData,
    contactPrefillSummary: buildContactPrefillSummary({ ...session, messages }, {
      ...collectedData,
      summary: reportData.executiveSummary.text,
      recommendedTier,
      extractedData: collectedData.extractedData || collectedData,
    }),
  };

  const { data: updatedSession, error: updateError } = await supabase
    .from('kbot_sessions')
    .update({
      status: 'report_ready',
      messages,
      collected_data: updatedCollectedData,
      updated_at: new Date().toISOString(),
    })
    .eq('id', sessionId)
    .select('*')
    .single();

  if (updateError) return sendJson(res, 500, { error: updateError.message });
  sendJson(res, 200, { reportData, report: reportData, session: serializeKbotSession(updatedSession) });
}

async function handleKbotReport(req, res) {
  if (req.method === 'POST') return handleKbotStructuredReport(req, res);
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

function reportPdfFileName(reportData) {
  const rawCode = String(reportData?.meta?.code || 'report-kbot')
    .toLowerCase()
    .replace(/[^a-z0-9-]+/g, '-')
    .replace(/^-+|-+$/g, '');
  return `${rawCode || 'report-kbot'}.pdf`;
}

function reportDocxFileName(reportData) {
  const rawCode = String(reportData?.meta?.code || 'report-kbot')
    .toLowerCase()
    .replace(/[^a-z0-9-]+/g, '-')
    .replace(/^-+|-+$/g, '');
  return `${rawCode || 'report-kbot'}.docx`;
}

function normalizeBoardMockReportId(value) {
  return String(value || '').trim().toUpperCase();
}

function parseBoardMockCreatedAt(label) {
  const value = String(label || '').trim();
  const match = value.match(/^(\d{2})\/(\d{2})\/(\d{4})(?:\s+(\d{2}):(\d{2}))?$/);
  if (!match) return new Date().toISOString();
  const [, day, month, year, hour = '00', minute = '00'] = match;
  return new Date(`${year}-${month}-${day}T${hour}:${minute}:00`).toISOString();
}

function buildBoardMockReportData(mockReportId) {
  const normalizedId = normalizeBoardMockReportId(mockReportId);
  const mock = BOARD_REPORT_MOCK_BY_ID.get(normalizedId);
  if (!mock) return null;

  const service = getSuiteAiService(mock.serviceId);
  const reportData = generateReportData({
    id: normalizedId,
    serviceId: mock.serviceId,
    service_id: mock.serviceId,
    selectedService: service || {
      id: mock.serviceId,
      name: mock.service,
      shortDescription: mock.summary,
      recommendedTier: mock.tier,
    },
    recommendedTier: mock.tier,
    recommended_tier: mock.tier,
    companyName: mock.client,
    businessType: mock.client,
    summary: mock.summary,
    conversationSummary: mock.summary,
    problem: mock.problem,
    currentProcess: mock.currentProcess,
    created_at: parseBoardMockCreatedAt(mock.createdAtLabel),
    updated_at: parseBoardMockCreatedAt(mock.createdAtLabel),
  });

  reportData.meta.code = normalizedId;
  reportData.meta.date = mock.createdAtLabel.split(' ')[0] || reportData.meta.date;
  reportData.client.name = mock.client;
  reportData.client.scope = mock.currentProcess || reportData.client.scope;
  reportData.executiveSummary.text = mock.summary || reportData.executiveSummary.text;
  reportData.context.currentScenario = mock.currentProcess || reportData.context.currentScenario;
  reportData.problem.main = mock.problem || reportData.problem.main;
  reportData.solution.expectedResult = `Output mock ${mock.statusLabel || 'Pronto'} per anteprima board.`;
  return reportData;
}

async function handleReportPdf(req, res) {
  if (req.method !== 'POST' && req.method !== 'GET') return sendJson(res, 405, { error: 'Method not allowed' });

  const body = req.method === 'POST' ? await readJsonBody(req, 2 * 1024 * 1024) : {};
  const url = new URL(req.url || '/', SITE_URL);
  const mockReportId = body.mockReportId || body.mock_report_id || url.searchParams.get('mock_report_id');
  const mockReportData = mockReportId ? buildBoardMockReportData(mockReportId) : null;
  const reportDataInput = body.reportData || body.report_data || body;
  const reportData = mockReportData || (isPlainObject(reportDataInput) ? reportDataInput : generateReportData({}));
  const pdfRuntime = require('./lib/report/pdf-generator.js');
  const generatePdfFn = pdfRuntime.generatePDF || (pdfRuntime.default && pdfRuntime.default.generatePDF);
  if (typeof generatePdfFn !== 'function') return sendJson(res, 500, { error: 'generatePDF non disponibile' });

  const pdfBuffer = await generatePdfFn(reportData);
  send(res, 200, {
    'Content-Type': 'application/pdf',
    'Content-Disposition': `attachment; filename="${reportPdfFileName(reportData)}"`,
    'Cache-Control': 'no-store',
  }, pdfBuffer);
}

async function handleReportDocx(req, res) {
  if (req.method !== 'POST' && req.method !== 'GET') return sendJson(res, 405, { error: 'Method not allowed' });

  const body = req.method === 'POST' ? await readJsonBody(req, 2 * 1024 * 1024) : {};
  const url = new URL(req.url || '/', SITE_URL);
  const mockReportId = body.mockReportId || body.mock_report_id || url.searchParams.get('mock_report_id');
  const mockReportData = mockReportId ? buildBoardMockReportData(mockReportId) : null;
  const reportDataInput = body.reportData || body.report_data || body;
  const reportData = mockReportData || (isPlainObject(reportDataInput) ? reportDataInput : generateReportData({}));
  const docxRuntime = require('./lib/report/docx-generator.js');
  const generateDocxFn = docxRuntime.generateDocx || (docxRuntime.default && docxRuntime.default.generateDocx);
  if (typeof generateDocxFn !== 'function') return sendJson(res, 500, { error: 'generateDocx non disponibile' });

  const docxBuffer = await generateDocxFn(reportData);
  send(res, 200, {
    'Content-Type': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'Content-Disposition': `attachment; filename="${reportDocxFileName(reportData)}"`,
    'Cache-Control': 'no-store',
  }, docxBuffer);
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
  applySecurityHeaders(res);

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

  if (rawPath === '/api/newsletter/publish' || rawPath.startsWith('/api/newsletter/publish/')) {
    const pathToken = rawPath.startsWith('/api/newsletter/publish/')
      ? rawPath.slice('/api/newsletter/publish/'.length)
      : '';
    handleNewsletterPublish(req, res, { pathToken }).catch(err => {
      console.error('Newsletter publish error:', err);
      sendJson(res, 500, { error: 'Errore pubblicazione newsletter' });
    });
    return;
  }

  if (rawPath === '/api/newsletter/issues') {
    handleNewsletterIssues(req, res).catch(err => {
      console.error('Newsletter issues error:', err);
      sendJson(res, 500, { error: 'Errore archivio newsletter' });
    });
    return;
  }

  if (rawPath === '/api/newsletter/issue') {
    handleNewsletterIssue(req, res).catch(err => {
      console.error('Newsletter issue error:', err);
      sendJson(res, 500, { error: 'Errore newsletter' });
    });
    return;
  }

  if (rawPath.startsWith('/api/newsletter/admin/cleanup-tests/')) {
    const pathToken = rawPath.slice('/api/newsletter/admin/cleanup-tests/'.length);
    handleNewsletterCleanupTests(req, res, { pathToken }).catch(err => {
      console.error('Newsletter cleanup tests error:', err);
      sendJson(res, 500, { error: 'Errore cleanup newsletter' });
    });
    return;
  }

  if (rawPath === '/api/report/pdf') {
    handleReportPdf(req, res).catch(err => {
      console.error('Report PDF API error:', err);
      sendJson(res, 500, { error: 'Errore generazione PDF report' });
    });
    return;
  }

  if (rawPath === '/api/report/docx') {
    handleReportDocx(req, res).catch(err => {
      console.error('Report DOCX API error:', err);
      sendJson(res, 500, { error: 'Errore generazione DOCX report' });
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

  if (rawPath === '/suite-ai/services' || rawPath.startsWith('/suite-ai/services/')) {
    const serviceId = rawPath === '/suite-ai/services'
      ? ''
      : decodeURIComponent(rawPath.replace('/suite-ai/services/', '').split('/')[0] || '');
    handleSuiteAiServices(req, res, serviceId);
    return;
  }

  const cleanKbotApiPath = {
    '/kbot/session': '/api/kbot/session',
    '/kbot/message': '/api/kbot/chat',
    '/kbot/report': '/api/kbot/report',
  }[rawPath];
  if (cleanKbotApiPath) {
    handleKbotApi(req, res, cleanKbotApiPath).catch(err => {
      console.error('K-BOT clean API error:', err);
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

  if (rawPath === '/app' || rawPath.startsWith('/app/')) {
    if (kbotStandaloneAvailable) {
      proxyKbotStandalone(req, res);
      return;
    }

    const appRelPath = rawPath === '/app' ? '/app/index.html' : rawPath;
    const safePath = path.normalize(appRelPath).replace(/^(\.\.[/\\])+/, '');
    let filePath = path.join(DIST_DIR, safePath);
    if (!path.extname(filePath)) {
      filePath = path.join(DIST_DIR, appRelPath, 'index.html');
    }
    serveFile(req, res, filePath);
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

startKbotStandalone();

server.listen(PORT, '0.0.0.0', () => {
  console.log(`K2-AI website listening on ${PORT}`);
});
