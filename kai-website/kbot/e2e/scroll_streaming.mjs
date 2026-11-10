// Scroll libero durante lo streaming: se l'utente sale, la posizione resta ferma mentre arrivano i token;
// «Vai alla risposta in corso» riporta in fondo e riattiva l'inseguimento. Richiede server_ui.py con UI_LLM_FINTO=1 (8200) e frontend (3100).
import { chromium } from 'playwright-core';
const b = await chromium.launch({ executablePath: process.env.CHROME_PATH || '/usr/bin/chromium-browser', args: ['--no-sandbox'] });
const ctx = await b.newContext({ viewport: { width: 1360, height: 800 } });
const p = await ctx.newPage();
await p.addInitScript(() => {
  const exp = Math.floor(Date.now() / 1000) + 86400, enc = (o) => btoa(JSON.stringify(o)).replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
  const jwt = enc({ alg: 'HS256' }) + '.' + enc({ sub: '00000000-0000-4000-8000-000000000001', exp, aud: 'authenticated' }) + '.f';
  if (!localStorage.getItem('sb-127-auth-token'))
    localStorage.setItem('sb-127-auth-token', JSON.stringify({ access_token: jwt, refresh_token: 'rt', expires_in: 86400, expires_at: exp, token_type: 'bearer', user: { id: '00000000-0000-4000-8000-000000000001', aud: 'authenticated', email: 'prova@example.com', app_metadata: {}, user_metadata: {}, created_at: '2026-01-01T00:00:00Z' } }));
});
const esiti = []; const ok = (n, v, x = '') => { esiti.push(!!v); console.log((v ? 'OK  ' : 'FAIL') + ' ' + n + (x ? '  ' + x : '')); };
await p.goto('http://localhost:3100/app/', { waitUntil: 'networkidle' }); await p.waitForTimeout(1500);
const m = () => p.evaluate(() => { const e = document.querySelector('main'); return { top: e.scrollTop, h: e.scrollHeight, c: e.clientHeight, dist: e.scrollHeight - e.scrollTop - e.clientHeight }; });
const ta = p.locator('textarea').first(); await ta.fill('Controlla il riepilogo'); await ta.press('Enter');
// 1) in fondo, la chat segue la generazione
await p.waitForFunction(() => { const e = document.querySelector('main'); return e.scrollHeight > e.clientHeight + 400; }, null, { timeout: 30000 });
await p.waitForTimeout(800);
let s1 = await m(); ok('S1 in fondo la chat segue i token', s1.dist < 70, JSON.stringify(s1));
// 2) l'utente sale con la rotella
await p.mouse.move(700, 400); await p.mouse.wheel(0, -4000); await p.waitForTimeout(300);
const fermo = await m();
await p.waitForTimeout(3500);
const dopo = await m();
ok('S2 salendo, la posizione resta ferma mentre arrivano token', Math.abs(dopo.top - fermo.top) <= 2 && dopo.h > fermo.h, `top ${fermo.top}→${dopo.top} altezza ${fermo.h}→${dopo.h}`);
ok('S3 compare «Vai alla risposta in corso»', await p.locator('[data-testid="vai-in-fondo"]').isVisible());
// 3) un'altra salita/discesa piccola non riattiva il follow finché si è lontani
await p.mouse.wheel(0, 200); await p.waitForTimeout(1500);
const lontano = await m();
ok('S4 a metà pagina il follow resta sospeso', lontano.dist > 150, JSON.stringify(lontano));
// 4) torna in fondo col pulsante: riprende a seguire
await p.locator('[data-testid="vai-in-fondo"]').click(); await p.waitForTimeout(1500);
const s5 = await m();
ok('S5 il pulsante riporta in fondo', s5.dist < 70, JSON.stringify(s5));
const hPrima = s5.h; await p.waitForTimeout(2500); const s6 = await m();
ok('S6 la chat segue di nuovo (altezza cresciuta, ancora in fondo)', s6.h > hPrima && s6.dist < 70, JSON.stringify(s6));
ok('S7 il pulsante sparisce', !(await p.locator('[data-testid="vai-in-fondo"]').isVisible()));
// 5) scendendo a mano fino in fondo il follow si riattiva da solo
await p.mouse.wheel(0, -3000); await p.waitForTimeout(400); await p.mouse.wheel(0, 20000); await p.waitForTimeout(1200);
const s8h = (await m()).h; await p.waitForTimeout(2500); const s8 = await m();
ok('S8 tornando spontaneamente in fondo il follow riprende', s8.h >= s8h && s8.dist < 70, JSON.stringify(s8));
await b.close(); console.log(esiti.every(Boolean) ? 'TUTTO OK' : 'CI SONO FALLIMENTI'); process.exit(esiti.every(Boolean) ? 0 : 1);
