// Titoli brevi delle pratiche: la prima frase NON diventa il titolo; arriva quello breve del backend, si salva e sopravvive al ricaricamento.
import { chromium } from 'playwright-core';
const b = await chromium.launch({ executablePath: process.env.CHROME_PATH || '/usr/bin/chromium-browser', args: ['--no-sandbox'] });
const p = await b.newPage({ viewport: { width: 1360, height: 860 } });
await p.addInitScript(() => {
  const exp = Math.floor(Date.now() / 1000) + 86400, enc = (o) => btoa(JSON.stringify(o)).replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
  const jwt = enc({ alg: 'HS256' }) + '.' + enc({ sub: '00000000-0000-4000-8000-000000000001', exp, aud: 'authenticated' }) + '.f';
  if (!localStorage.getItem('sb-127-auth-token'))
    localStorage.setItem('sb-127-auth-token', JSON.stringify({ access_token: jwt, refresh_token: 'rt', expires_in: 86400, expires_at: exp, token_type: 'bearer', user: { id: '00000000-0000-4000-8000-000000000001', aud: 'authenticated', email: 'prova@example.com', app_metadata: {}, user_metadata: {}, created_at: '2026-01-01T00:00:00Z' } }));
});
let chiamateTitolo = 0;
await p.route('**/api/kbot/title', async (r) => { chiamateTitolo++; await new Promise((x) => setTimeout(x, 700)); r.fulfill({ json: { title: 'Ammortamento computer' } }); });
await p.route('**/api/kbot/message/stream', async (r) => {
  const body = JSON.parse(r.request().postData() || '{}');
  const sess = { id: body.session_id || body.sessionId || 'x', mode: 'report', messages: [], extractedData: { used_skills: ['diagnosi-ai-operativa-pmi', 'fiscale-tributario-italiano'] }, schedaCliente: { importo: '2.500 euro' }, timestamps: {} };
  const ev = (o) => 'data: ' + JSON.stringify(o) + '\n\n';
  await new Promise((x) => setTimeout(x, 1200));
  r.fulfill({ status: 200, headers: { 'Content-Type': 'text/event-stream' }, body: ev({ delta: 'Sotto i 516,46 euro ' }) + ev({ delta: 'è deducibile subito; sopra si ammortizza.' }) + ev({ done: true, message: 'Sotto i 516,46 euro è deducibile subito; sopra si ammortizza.', nextAction: 'continue', session: sess }) });
});
const esiti = []; const ok = (n, v) => { esiti.push([n, !!v]); console.log((v ? 'OK  ' : 'FAIL') + ' ' + n); };
p.on('pageerror', (e) => console.log('  [pageerror]', String(e).slice(0, 160)));
await p.goto('http://localhost:3100/app/', { waitUntil: 'networkidle' }); await p.waitForTimeout(2000);
const testo = "Abbiamo comprato un computer da 2.500 euro per l'azienda. Conviene scaricarlo tutto subito oppure ammortizzarlo negli anni? Come funziona?";
const ta = p.locator('textarea').first(); await ta.fill(testo); await ta.press('Enter');
await p.waitForTimeout(250);
let side = await p.locator('aside').innerText();
ok('titolo provvisorio breve (non la frase tagliata)', !/Abbiamo comprato un computer da 2\.500 euro per l/.test(side) && /Comprato computer/.test(side));
await p.waitForFunction(() => document.body.innerText.includes('516,46'), null, { timeout: 8000 }).catch(() => {});
ok('LA RISPOSTA compare in chat (la pratica cambia id mentre arriva)', (await p.evaluate(() => document.body.innerText)).includes('Sotto i 516,46 euro è deducibile subito'));
await p.waitForFunction(() => document.querySelector('aside')?.innerText.includes('Ammortamento computer'), null, { timeout: 8000 }).catch(() => {});
side = await p.locator('aside').innerText();
ok('titolo del backend nella lista pratiche', side.includes('Ammortamento computer'));
const head = await p.locator('header').first().innerText();
ok('titolo nella testata', head.includes('Ammortamento computer'));
ok('una sola chiamata di titolo', chiamateTitolo === 1);
await p.waitForTimeout(1500);
const ta2 = p.locator('textarea').first(); await ta2.fill('E se il computer costasse 400 euro?'); await ta2.press('Enter'); await p.waitForTimeout(1200);
console.log('   DEBUG dopo 2° messaggio: chiamate', chiamateTitolo, '| aside =', JSON.stringify(await p.locator('aside').innerText()));
ok('un secondo messaggio non rigenera il titolo', chiamateTitolo === 1 && (await p.locator('aside').innerText()).includes('Ammortamento computer'));
await p.getByRole('tab', { name: /Fonti/ }).click();
ok('le competenze usate arrivano nel pannello', (await p.locator('section[aria-label="Pratica"]').innerText()).includes('fiscale-tributario-italiano'));
await p.reload({ waitUntil: 'networkidle' }); await p.waitForTimeout(3000);
side = await p.locator('aside').innerText();
console.log('   DEBUG dopo reload: aside =', JSON.stringify(side));
ok('dopo il ricaricamento il titolo resta (salvato sulla conversazione)', side.includes('Ammortamento computer'));
await b.close();
const ko = esiti.filter(([, v]) => !v);
console.log(ko.length ? 'FALLITI: ' + ko.map(([n]) => n).join(' | ') : 'TUTTI OK (' + esiti.length + ')'); process.exit(ko.length ? 1 : 0);
