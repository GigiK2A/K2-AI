// Il report NON parte da solo: con un boost già suggerito dal routing (dal 3° turno), né al ricaricamento né alla domanda
// successiva («ricontrolla i calcoli») deve partire POST /deliverables/auto. Regressione del 20/10/2026.
import { chromium } from 'playwright-core';
const SID = '22222222-2222-4222-8222-222222222222';
const sessione = (extra = {}) => ({ id: SID, mode: 'report', status: 'active', hasUser: true, summary: null, pdfUrl: null,
  boostSuggerito: 'checkup_fiscale', boostSuggeritoLabel: 'Check-up fiscale',
  extractedData: { used_skills: ['diagnosi-ai-operativa-pmi', 'fiscale-tributario-italiano'] }, schedaCliente: {}, timestamps: {},
  messages: [
    { role: 'user', content: 'Siamo una SRL, abbiamo comprato un computer da 2.500 euro. Come funziona l\'ammortamento?' },
    { role: 'assistant', content: 'Si ammortizza con il coefficiente della tabella ministeriale.' },
    { role: 'user', content: 'Calcolami IVA, IRES e quota del primo anno.' },
    { role: 'assistant', content: 'IVA 550 euro, quota primo anno 250 euro.' },
    { role: 'user', content: 'E per i mesi?' },
    { role: 'assistant', content: 'Dipende dal mese di entrata in funzione.' },
  ], ...extra });
const b = await chromium.launch({ executablePath: process.env.CHROME_PATH || '/usr/bin/chromium-browser', args: ['--no-sandbox'] });
const p = await b.newPage({ viewport: { width: 1360, height: 860 } });
await p.addInitScript((sid) => {
  const exp = Math.floor(Date.now() / 1000) + 86400, enc = (o) => btoa(JSON.stringify(o)).replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
  const jwt = enc({ alg: 'HS256' }) + '.' + enc({ sub: '00000000-0000-4000-8000-000000000001', exp, aud: 'authenticated' }) + '.f';
  localStorage.setItem('sb-127-auth-token', JSON.stringify({ access_token: jwt, refresh_token: 'rt', expires_in: 86400, expires_at: exp, token_type: 'bearer', user: { id: '00000000-0000-4000-8000-000000000001', aud: 'authenticated', email: 'prova@example.com', app_metadata: {}, user_metadata: {}, created_at: '2026-01-01T00:00:00Z' } }));
  localStorage.setItem('kbot.session_id', sid);
}, SID);
let chiamateAuto = 0; const corpi = [];
await p.route('**/api/kbot/deliverables/auto', (r) => { chiamateAuto++; corpi.push(r.request().postData()); r.fulfill({ status: 409, json: { detail: { reason: 'needs_input', message: 'prova' } } }); });
await p.route('**/api/kbot/session/' + SID, (r) => r.fulfill({ json: { session: sessione() } }));
await p.route('**/api/kbot/title', (r) => r.fulfill({ json: { title: 'Ammortamento computer' } }));
await p.route('**/api/kbot/message/stream', async (r) => {
  const ev = (o) => 'data: ' + JSON.stringify(o) + '\n\n';
  await new Promise((x) => setTimeout(x, 800));
  r.fulfill({ status: 200, headers: { 'Content-Type': 'text/event-stream' }, body: ev({ delta: 'Ricontrollo: ' }) + ev({ delta: 'la quota del primo anno è 250 euro.' }) +
    ev({ done: true, message: 'Ricontrollo: la quota del primo anno è 250 euro.', nextAction: 'continue', session: sessione() }) });
});
const esiti = []; const ok = (n, v) => { esiti.push([n, !!v]); console.log((v ? 'OK  ' : 'FAIL') + ' ' + n); };
p.on('pageerror', (e) => console.log('  [pageerror]', String(e).slice(0, 160)));
await p.goto('http://localhost:3100/app/', { waitUntil: 'networkidle' }); await p.waitForTimeout(3500);
ok('al ricaricamento NON parte nessun report', chiamateAuto === 0);
const ta = p.locator('textarea').first(); await ta.fill('Ricontrolla i calcoli, mi sembrano sbagliati.'); await ta.press('Enter');
await p.waitForFunction(() => document.body.innerText.includes('la quota del primo anno è 250 euro'), null, { timeout: 8000 }).catch(() => {});
await p.waitForTimeout(1500);
ok('inviando «ricontrolla i calcoli» NON parte nessun report', chiamateAuto === 0);
ok('la risposta compare in chat', (await p.evaluate(() => document.body.innerText)).includes('la quota del primo anno è 250 euro'));
ok('nessun «Genera il documento» né «Generazione in corso» a schermo', !/Generazione in corso|Genera il documento|In coda…/i.test(await p.evaluate(() => document.body.innerText)));
console.log('   chiamate /deliverables/auto:', chiamateAuto, corpi.length ? corpi[0] : '');
// CASO LEGITTIMO: il bot emette il riepilogo (nextAction=show_summary) → il generatore parte, come avvio automatico (explicit:false).
const p2 = await b.newPage({ viewport: { width: 1360, height: 860 } });
await p2.addInitScript(() => localStorage.setItem('kbot.session_id', '22222222-2222-4222-8222-222222222222'));
let auto2 = []; 
await p2.route('**/api/kbot/deliverables/auto', (r) => { auto2.push(JSON.parse(r.request().postData() || '{}')); r.fulfill({ status: 409, json: { detail: { reason: 'needs_input', message: 'prova' } } }); });
await p2.route('**/api/kbot/session/' + SID, (r) => r.fulfill({ json: { session: sessione() } }));
await p2.route('**/api/kbot/title', (r) => r.fulfill({ json: { title: 'Ammortamento computer' } }));
await p2.route('**/api/kbot/message/stream', async (r) => {
  const ev = (o) => 'data: ' + JSON.stringify(o) + '\n\n';
  await new Promise((x) => setTimeout(x, 400));
  const sess = sessione({ extractedData: { used_skills: ['diagnosi-ai-operativa-pmi'], generation: { requested: true } } });
  r.fulfill({ status: 200, headers: { 'Content-Type': 'text/event-stream' }, body: ev({ delta: 'Preparo il report.' }) + ev({ done: true, message: 'Preparo il report.', nextAction: 'show_summary', summary: { reportType: 'x' }, session: sess }) });
});
await p2.addInitScript(() => {
  const exp = Math.floor(Date.now() / 1000) + 86400, enc = (o) => btoa(JSON.stringify(o)).replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
  const jwt = enc({ alg: 'HS256' }) + '.' + enc({ sub: '00000000-0000-4000-8000-000000000001', exp, aud: 'authenticated' }) + '.f';
  localStorage.setItem('sb-127-auth-token', JSON.stringify({ access_token: jwt, refresh_token: 'rt', expires_in: 86400, expires_at: exp, token_type: 'bearer', user: { id: '00000000-0000-4000-8000-000000000001', aud: 'authenticated', email: 'prova@example.com', app_metadata: {}, user_metadata: {}, created_at: '2026-01-01T00:00:00Z' } }));
});
await p2.goto('http://localhost:3100/app/', { waitUntil: 'networkidle' }); await p2.waitForTimeout(3000);
ok('(legittimo) al ricaricamento ancora nessun avvio automatico', auto2.length === 0);
const ta2 = p2.locator('textarea').first(); await ta2.fill('Va bene, fai il report.'); await ta2.press('Enter');
await p2.waitForTimeout(4500);
ok('(legittimo) quando il bot emette il riepilogo il report parte, una sola volta, come avvio automatico', auto2.length === 1 && auto2[0].explicit === false);
await b.close();
const ko = esiti.filter(([, v]) => !v);
console.log(ko.length ? 'FALLITI: ' + ko.map(([n]) => n).join(' | ') : 'TUTTI OK (' + esiti.length + ')'); process.exit(ko.length ? 1 : 0);
