const http = require('http');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { createClient } = require('@supabase/supabase-js');
const { Resend } = require('resend');

const PORT = process.env.PORT || 4173;
const DIST_DIR = path.join(__dirname, 'dist');
const REDIRECT_HOST = 'k2-ai.it';
const CANONICAL_HOST = 'www.k2-ai.it';
const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://www.k2-ai.it';

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

  const { data: existing } = await supabase
    .from('newsletter_subscribers')
    .select('id, confirmed')
    .eq('email', email)
    .single();

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
    send(res, 302, { Location: '/newsletter-error.html' }, '');
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
    send(res, 302, { Location: '/newsletter-error.html' }, '');
    return;
  }

  send(res, 302, { Location: '/newsletter-ok.html' }, '');
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

  // 301 redirects — URL rename (casi-studio → laboratorio, workshop → suite-ai)
  const REDIRECTS_301 = {
    '/casi-studio.html': '/laboratorio.html',
    '/workshop.html': '/suite-ai.html',
  };
  const rawPath = (req.url || '/').split('?')[0];

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
      send(res, 302, { Location: '/newsletter-error.html' }, '');
    });
    return;
  }

  if (REDIRECTS_301[rawPath]) {
    send(res, 301, { Location: REDIRECTS_301[rawPath] }, '');
    return;
  }

  let urlPath = rawPath;
  if (urlPath === '/') {
    urlPath = '/index.html';
  }

  const safePath = path.normalize(urlPath).replace(/^(\.\.[/\\])+/, '');
  const filePath = path.join(DIST_DIR, safePath);
  serveFile(req, res, filePath);
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`K2-AI website listening on ${PORT}`);
});
