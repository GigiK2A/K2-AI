// Prova della UI «pratica per caso»: sessione finta con messaggi, bozza, fonti e fatti; schermate desktop/telefono + controlli.
import { chromium } from 'playwright-core';
const SID = '11111111-1111-4111-8111-111111111111';
const BOZZA = 'Oggetto: diffida di pagamento fattura n. 42/2026\n\nSpett.le Gamma Srl,\nvi invitiamo a versare entro 15 giorni dal ricevimento della presente la somma di € 18.400,00, relativa alla fattura n. 42/2026 scaduta il 10 agosto 2026, oltre agli interessi di mora previsti dal D.Lgs. 231/2002. In mancanza adiremo le vie legali senza ulteriore avviso.\n\nCordiali saluti\nVerniciature Rossi Srl\n\nFonti: D.Lgs. 231/2002 art. 4; c.c. art. 1219.';
const sessione = { id: SID, serviceId: null, mode: 'report', status: 'active', hasUser: true, summary: null, pdfUrl: null,
  extractedData: { used_skills: ['diagnosi-ai-operativa-pmi', 'diritto-italiano'] },
  schedaCliente: { citta: 'Foligno', dipendenti: '14', importo_fattura: '18.400 €', cliente_moroso: 'Gamma Srl' },
  timestamps: { createdAt: '2026-10-14T10:00:00Z', updatedAt: '2026-10-20T10:00:00Z' },
  messages: [
    { role: 'user', content: 'Gamma Srl non paga una fattura di 18.400 € scaduta da 70 giorni. Siamo a Foligno, 14 dipendenti. Scrivi la diffida.' },
    { role: 'assistant', content: BOZZA },
  ] };
const b = await chromium.launch({ executablePath: process.env.CHROME_PATH || '/usr/bin/chromium-browser', args: ['--no-sandbox'] });
const esiti = [];
const ok = (nome, v) => { esiti.push([nome, !!v]); console.log((v ? 'OK  ' : 'FAIL') + ' ' + nome); };
async function nuova(w, h) {
  const p = await b.newPage({ viewport: { width: w, height: h } });
  await p.addInitScript((sid) => {
    const exp = Math.floor(Date.now() / 1000) + 86400, enc = (o) => btoa(JSON.stringify(o)).replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
    const jwt = enc({ alg: 'HS256' }) + '.' + enc({ sub: '00000000-0000-4000-8000-000000000001', exp, aud: 'authenticated' }) + '.f';
    localStorage.setItem('sb-127-auth-token', JSON.stringify({ access_token: jwt, refresh_token: 'rt', expires_in: 86400, expires_at: exp, token_type: 'bearer', user: { id: '00000000-0000-4000-8000-000000000001', aud: 'authenticated', email: 'prova@example.com', app_metadata: {}, user_metadata: { first_name: 'Prova' }, created_at: '2026-01-01T00:00:00Z' } }));
    localStorage.setItem('kbot.session_id', sid);
  }, SID);
  await p.route('**/api/kbot/session/' + SID, (r) => r.fulfill({ json: { session: sessione } }));
  p.on('pageerror', (e) => console.log('  [pageerror]', String(e).slice(0, 160)));
  await p.goto('http://localhost:3100/app/', { waitUntil: 'networkidle' });
  await p.waitForTimeout(2500);
  return p;
}
// DESKTOP
let p = await nuova(1360, 860);
await p.screenshot({ path: 'ui-b-desktop.png' });
let t = await p.evaluate(() => document.body.innerText);
ok('desktop: pratiche a sinistra', t.includes('Nuova pratica') && t.includes('Le tue pratiche'));
ok('desktop: bozza visibile nel pannello', /bozza pronta/i.test(t) && t.includes('€ 18.400,00'));
ok('desktop: niente testi vecchi', !/Insight Panel|Report Premium|calendario editoriale/i.test(t));
await p.getByRole('tab', { name: /Fatti/ }).click(); t = await p.evaluate(() => document.body.innerText);
ok('desktop: Fatti mostra Foligno e 14', t.includes('Foligno') && t.includes('Gamma Srl'));
await p.screenshot({ path: 'ui-b-desktop-fatti.png' });
await p.getByRole('tab', { name: /Fonti/ }).click(); t = await p.evaluate(() => document.body.innerText);
ok('desktop: Fonti mostra le norme e le competenze', t.includes('D.Lgs. 231/2002 art. 4') && t.includes('diritto-italiano'));
ok('desktop: rimando alla bozza nella chat (anche per i messaggi senza marcatori)', await p.getByRole('button', { name: /Bozza pronta/ }).count() > 0);
ok('desktop: la chat c\'è dopo il ritorno (messaggio utente)', t.includes('Gamma Srl non paga'));
// ANDATA E RITORNO DALLA DASHBOARD (difetto «chat persa»)
await p.evaluate(() => window.next.router.push('/dashboard/'));
await p.waitForURL('**/dashboard/**', { timeout: 15000 }).catch(() => {});
await p.waitForTimeout(1500);
await p.evaluate(() => window.next.router.push('/'));
await p.waitForURL((u) => /\/app\/?$/.test(u.pathname), { timeout: 15000 }).catch(() => {});
await p.waitForTimeout(4000);
t = await p.evaluate(() => document.body.innerText);
ok('ritorno dalla dashboard: chat, bozza e fatti ci sono ancora', t.includes('Gamma Srl non paga') && /bozza pronta/i.test(t));
// TELEFONO
let m = await nuova(390, 844);
await m.screenshot({ path: 'ui-b-mobile-chat.png' });
t = await m.evaluate(() => document.body.innerText);
ok('telefono: chat visibile, pannello nascosto', t.includes('Gamma Srl non paga') && !(await m.locator('section[aria-label="Pratica"]').isVisible()));
await m.getByRole('button', { name: 'Apri le pratiche' }).click(); await m.waitForTimeout(400);
await m.screenshot({ path: 'ui-b-mobile-menu.png' });
ok('telefono: menu pratiche si apre', (await m.evaluate(() => document.body.innerText)).includes('Nuova pratica'));
await m.getByRole('button', { name: 'Chiudi il menu' }).click(); await m.waitForTimeout(400);
await m.getByRole('button', { name: /Pratica/ }).first().click(); await m.waitForTimeout(400);
await m.screenshot({ path: 'ui-b-mobile-pratica.png' });
ok('telefono: la pratica si apre a tutto schermo con la bozza', (await m.locator('section[aria-label="Pratica"]').isVisible()) && /bozza pronta/i.test(await m.locator('section[aria-label="Pratica"]').innerText()));
await m.getByRole('button', { name: 'Torna alla chat' }).click(); await m.waitForTimeout(300);
ok('telefono: si torna alla chat', !(await m.locator('section[aria-label="Pratica"]').isVisible()));
const sc = await m.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1);
ok('telefono: nessuno scroll orizzontale', sc);
const compos = await m.evaluate(() => { const r = document.querySelector('textarea')?.getBoundingClientRect(); return r && r.bottom <= window.innerHeight && r.top >= 0; });
ok('telefono: il campo di scrittura è raggiungibile senza scorrere', compos);
// PORTATILE 1100: pannello come schermata
let l = await nuova(1100, 760);
await l.screenshot({ path: 'ui-b-1100.png' });
ok('1100: pratiche fisse e pulsante Pratica', (await l.getByRole('button', { name: /Pratica/ }).count()) > 0);
await b.close();
const ko = esiti.filter(([, v]) => !v);
console.log(ko.length ? 'FALLITI: ' + ko.map(([n]) => n).join(' | ') : 'TUTTI OK (' + esiti.length + ')');
process.exit(ko.length ? 1 : 0);
