// Fascicolo persistente dall'interfaccia: strumenti chiamati dal modello (finto), documento aperto dal fascicolo, citazione cliccabile,
// visualizzatore con il passaggio evidenziato, e fascicolo grande recuperato a pagine senza troncamenti silenziosi.
// Richiede server_ui.py con UI_LLM_FINTO=1 UI_SEED_FASCICOLO=1 (8200) e il frontend (3100). Fascicolo di prova DEMO-001 (non reale).
import { chromium } from 'playwright-core';
const b = await chromium.launch({ executablePath: process.env.CHROME_PATH || '/usr/bin/chromium-browser', args: ['--no-sandbox'] });
const ctx = await b.newContext({ viewport: { width: 1360, height: 900 } });
const p = await ctx.newPage();
await p.addInitScript(() => {
  const exp = Math.floor(Date.now() / 1000) + 86400, enc = (o) => btoa(JSON.stringify(o)).replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
  const jwt = enc({ alg: 'HS256' }) + '.' + enc({ sub: '00000000-0000-4000-8000-000000000001', exp, aud: 'authenticated' }) + '.f';
  if (!localStorage.getItem('sb-127-auth-token'))
    localStorage.setItem('sb-127-auth-token', JSON.stringify({ access_token: jwt, refresh_token: 'rt', expires_in: 86400, expires_at: exp, token_type: 'bearer', user: { id: '00000000-0000-4000-8000-000000000001', aud: 'authenticated', email: 'prova@example.com', app_metadata: {}, user_metadata: {}, created_at: '2026-01-01T00:00:00Z' } }));
});
const esiti = []; const ok = (n, v, x = '') => { esiti.push(!!v); console.log((v ? 'OK  ' : 'FAIL') + ' ' + n + (x ? '  ' + x : '')); };
await p.goto('http://localhost:3100/app/', { waitUntil: 'networkidle' }); await p.waitForTimeout(1500);
const attendi = async () => { await p.waitForTimeout(3000); for (let i = 0; i < 90; i++) { if (!(await p.getByText('Sto scrivendo').count())) break; await p.waitForTimeout(1000); } await p.waitForTimeout(800); };
const ta = p.locator('textarea').first();
// 1) fascicolo grande: il modello apre il fascicolo, il sistema dice «PARZIALE» (non tronca in silenzio)
await ta.fill('Apri il fascicolo DEMO-001'); await ta.press('Enter'); await attendi();
const t1 = await p.locator('main').first().innerText();
ok('F1 il fascicolo grande viene dichiarato parziale al modello (non troncato in silenzio)', /parziale/i.test(t1));
// 2) il modello apre il documento dal fascicolo e lo cita: la citazione è cliccabile
await ta.fill('Apri il documento Riepilogo del fascicolo DEMO-001: quanto resta da liquidare?'); await ta.press('Enter'); await attendi();
const nc = await p.locator('[data-testid="citazione"]').count();
ok('F2 la citazione del documento persistente è un riferimento cliccabile', nc > 0, 'n=' + nc);
if (nc) {
  await p.locator('[data-testid="citazione"]').last().click();
  await p.waitForSelector('[data-testid="evidenziazione"], [data-testid="visualizzatore"] [role="alert"]', { timeout: 20000 }).catch(() => {});
  ok('F3 si apre il PDF originale del fascicolo nel visualizzatore', await p.locator('[data-testid="visualizzatore"]').isVisible());
  ok('F4 il passaggio citato è evidenziato', (await p.locator('[data-testid="evidenziazione"]').count()) > 0, (await p.locator('[data-testid="visualizzatore"]').innerText()).slice(0, 80).replace(/\n/g, ' | '));
  const stato = await p.locator('[data-testid="visualizzatore"] [role="status"]').innerText().catch(() => '');
  ok('F4b il visualizzatore NON dice «evidenziazione non disponibile» e riporta il passaggio citato', !/non disponibile/i.test(stato) && /8\.850,00/.test(stato), stato.slice(0, 90));
  ok('F4c il riquadro cade sulla riga giusta (area alta della pagina, larghezza > 0)', await p.evaluate(() => { const e = document.querySelector('[data-testid="evidenziazione"]'); if (!e) return false; const r = e.getBoundingClientRect(); const pg = e.parentElement.getBoundingClientRect(); return r.width > 20 && r.height > 3 && (r.top - pg.top) / pg.height < 0.3; }));
  await p.screenshot({ path: 'fascicolo-citazione.png' });
  await p.locator('[data-testid="chiudi-visualizzatore"]').click(); await p.waitForTimeout(400);
  ok('F5 si torna alla conversazione', !(await p.locator('[data-testid="visualizzatore"]').count()) && (await p.locator('main').first().innerText()).includes('Apri il documento Riepilogo'));
}
await b.close(); console.log(esiti.every(Boolean) ? 'TUTTO OK' : 'CI SONO FALLIMENTI'); process.exit(esiti.every(Boolean) ? 0 : 1);
