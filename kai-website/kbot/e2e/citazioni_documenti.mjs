// Markdown (grassetto, tabella) + citazione cliccabile → visualizzatore con il passaggio evidenziato → ritorno alla chat.
// Richiede server_ui.py con UI_LLM_FINTO=1 (8200) e frontend (3100); fixture: e2e/fixtures/Riepilogo economico.pdf
import { chromium } from 'playwright-core';
import { fileURLToPath } from 'node:url';
const b = await chromium.launch({ executablePath: process.env.CHROME_PATH, args: ['--no-sandbox'] });
const ctx = await b.newContext({ viewport: { width: 1360, height: 900 } });
const p = await ctx.newPage();
await p.addInitScript(() => {
  const exp = Math.floor(Date.now() / 1000) + 86400, enc = (o) => btoa(JSON.stringify(o)).replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
  const jwt = enc({ alg: 'HS256' }) + '.' + enc({ sub: '00000000-0000-4000-8000-000000000001', exp, aud: 'authenticated' }) + '.f';
  if (!localStorage.getItem('sb-127-auth-token'))
    localStorage.setItem('sb-127-auth-token', JSON.stringify({ access_token: jwt, refresh_token: 'rt', expires_in: 86400, expires_at: exp, token_type: 'bearer', user: { id: '00000000-0000-4000-8000-000000000001', aud: 'authenticated', email: 'prova@example.com', app_metadata: {}, user_metadata: {}, created_at: '2026-01-01T00:00:00Z' } }));
});
const esiti = []; const ok = (n, v, x = '') => { esiti.push(!!v); console.log((v ? 'OK  ' : 'FAIL') + ' ' + n + (x ? '  ' + x : '')); };
await p.goto('http://localhost:3100/app/', { waitUntil: 'networkidle' }); await p.waitForTimeout(2000);
const [fc] = await Promise.all([p.waitForEvent('filechooser'), p.locator('button[aria-label="Allega file"]').click()]);
await fc.setFiles(fileURLToPath(new URL('./fixtures/Riepilogo economico.pdf', import.meta.url))); await p.waitForTimeout(4000);
const ta = p.locator('textarea').first();
await ta.fill('Controlla il riepilogo economico allegato: le pratiche autorizzative sono calcolate bene? Rispondi con una breve tabella e metti in grassetto l\'importo corretto, citando la fonte.');
await ta.press('Enter');
await p.waitForTimeout(5000);
for (let i = 0; i < 240; i++) { await p.waitForTimeout(1000); if (!(await p.getByText('Sto scrivendo').count())) break; }
await p.waitForTimeout(3000);
const main = p.locator('main').first();
console.log('--- testo ---\n' + (await main.innerText()).slice(-900));
ok('M1 niente asterischi grezzi nella risposta', !/\*\*[^*]+\*\*/.test(await main.innerText()));
ok('M2 grassetto reso (strong)', (await main.locator('strong').count()) > 0);
ok('M3 tabella resa', (await main.locator('table').count()) > 0);
const nc = await p.locator('[data-testid="citazione"]').count();
ok('C1 citazione cliccabile presente', nc > 0, 'n=' + nc);
if (nc) {
  await p.locator('[data-testid="citazione"]').first().click(); await p.waitForSelector('[data-testid="evidenziazione"], [data-testid="visualizzatore"] [role="alert"]', { timeout: 20000 }).catch(() => {});
  ok('C2 si apre il visualizzatore', await p.locator('[data-testid="visualizzatore"]').isVisible());
  ok('C3 documento nella pagina citata', /Pagina 1 di 2/.test(await p.locator('[data-testid="visualizzatore"]').innerText()));
  ok('C4 passaggio evidenziato', (await p.locator('[data-testid="evidenziazione"]').count()) > 0);
  await p.screenshot({ path: 'citazione.png' });
  await p.locator('[data-testid="chiudi-visualizzatore"]').click(); await p.waitForTimeout(500);
  ok('C5 si torna alla chat con la conversazione intatta', !(await p.locator('[data-testid="visualizzatore"]').count()) && (await main.innerText()).includes('Controlla il riepilogo'));
}
await b.close(); process.exit(esiti.every(Boolean) ? 0 : 1);
