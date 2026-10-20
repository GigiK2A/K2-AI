// «Cerca sul web»: il pulsante esiste, è distinto da «Analizza una pagina», la scelta dell'utente arriva al backend e resta salvata.
import { chromium } from 'playwright-core';
const b = await chromium.launch({ executablePath: process.env.CHROME_PATH || '/usr/bin/chromium-browser', args: ['--no-sandbox'] });
const p = await b.newPage({ viewport: { width: 1360, height: 860 } });
await p.addInitScript(() => {
  const exp = Math.floor(Date.now() / 1000) + 86400, enc = (o) => btoa(JSON.stringify(o)).replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
  const jwt = enc({ alg: 'HS256' }) + '.' + enc({ sub: '00000000-0000-4000-8000-000000000001', exp, aud: 'authenticated' }) + '.f';
  if (!localStorage.getItem('sb-127-auth-token'))
    localStorage.setItem('sb-127-auth-token', JSON.stringify({ access_token: jwt, refresh_token: 'rt', expires_in: 86400, expires_at: exp, token_type: 'bearer', user: { id: '00000000-0000-4000-8000-000000000001', aud: 'authenticated', email: 'prova@example.com', app_metadata: {}, user_metadata: {}, created_at: '2026-01-01T00:00:00Z' } }));
});
const corpi = [];
await p.route('**/api/kbot/message/stream', async (r) => {
  corpi.push(JSON.parse(r.request().postData() || '{}'));
  const ev = (o) => 'data: ' + JSON.stringify(o) + '\n\n';
  r.fulfill({ status: 200, headers: { 'Content-Type': 'text/event-stream' }, body: ev({ delta: 'Risposta.' }) + ev({ done: true, message: 'Risposta.', nextAction: 'continue', session: { id: 'x', mode: 'report', messages: [], extractedData: {}, timestamps: {} } }) });
});
const esiti = []; const ok = (n, v, e = '') => { esiti.push([n, !!v]); console.log((v ? 'OK  ' : 'FAIL') + ' ' + n + (e ? '  ' + e : '')); };
await p.goto('http://localhost:3100/app/', { waitUntil: 'networkidle' }); await p.waitForTimeout(1500);
const bottoneRicerca = p.getByRole('button', { name: 'Cerca sul web' });
const bottoneLink = p.getByRole('button', { name: /Analizza una pagina/ });
ok('1 esistono due pulsanti distinti: «Cerca sul web» e «Analizza una pagina da un link»', (await bottoneRicerca.count()) === 1 && (await bottoneLink.count()) === 1);
ok('2 di default la ricerca web NON è forzata (decide il sistema)', (await bottoneRicerca.getAttribute('aria-pressed')) === 'false');
const ta = p.locator('textarea').first();
await ta.fill('Quanto vale oggi il tasso di mora tra imprese?'); await ta.press('Enter'); await p.waitForTimeout(1500);
ok('3 con la ricerca spenta il messaggio parte senza forzatura', corpi.length === 1 && !('web_search' in corpi[0]) || corpi[0]?.web_search == null, JSON.stringify(corpi[0]));
await bottoneRicerca.click();
ok('4 acceso: il pulsante lo mostra (aria-pressed e etichetta visibile)', (await bottoneRicerca.getAttribute('aria-pressed')) === 'true' && (await p.getByText('Cerca sul web', { exact: true }).count()) >= 1);
await ta.fill('Verifica la norma italiana aggiornata sul tasso di mora'); await ta.press('Enter'); await p.waitForTimeout(1500);
ok('5 acceso: il backend riceve web_search=force', corpi.length === 2 && corpi[1].web_search === 'force', JSON.stringify(corpi[1]));
await ta.fill('E per i consumatori?'); await ta.press('Enter'); await p.waitForTimeout(1500);
ok('6 la scelta dell\'utente non viene cambiata dal sistema: resta accesa al messaggio dopo', corpi.length === 3 && corpi[2].web_search === 'force');
await p.reload({ waitUntil: 'networkidle' }); await p.waitForTimeout(1500);
ok('7 la preferenza resta dopo il ricaricamento', (await p.getByRole('button', { name: 'Cerca sul web' }).getAttribute('aria-pressed')) === 'true');
await p.getByRole('button', { name: 'Cerca sul web' }).click();
ok('8 si può spegnere', (await p.getByRole('button', { name: 'Cerca sul web' }).getAttribute('aria-pressed')) === 'false');
await b.close();
const ko = esiti.filter(([, v]) => !v);
console.log(ko.length ? 'FALLITI: ' + ko.map(([n]) => n).join(' | ') : 'TUTTI OK (' + esiti.length + ')'); process.exit(ko.length ? 1 : 0);
