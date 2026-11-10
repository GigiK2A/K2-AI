// Trascinamento di un file nella chat: riquadro visibile, il browser NON apre il file, il file viene caricato
// (endpoint /upload vero), compare il chip con il nome, formati non ammessi rifiutati con messaggio chiaro,
// il pulsante «Allega file» continua a funzionare. Richiede server_ui.py (8200) e il frontend (3100).
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
let navigato = false; p.on('framenavigated', (f) => { if (f === p.mainFrame() && f.url().startsWith('file:')) navigato = true; });
const uploads = []; p.on('request', (r) => { if (r.url().includes('/api/kbot/upload')) uploads.push(r.postData()?.length || 0); });
await p.goto('http://localhost:3100/app/', { waitUntil: 'networkidle' }); await p.waitForTimeout(2000);

// helper: simula un drag di file veri (DataTransfer) sulla pagina
async function trascina(nome, tipo, contenuto, fase) {
  return p.evaluate(async ({ nome, tipo, contenuto, fase }) => {
    const dt = new DataTransfer(); dt.items.add(new File([contenuto], nome, { type: tipo }));
    const t = document.querySelector('textarea');
    const ev = (n) => { const e = new DragEvent(n, { bubbles: true, cancelable: true, dataTransfer: dt }); t.dispatchEvent(e); return e.defaultPrevented; };
    if (fase === 'entra') return ev('dragenter') && ev('dragover');
    return ev('drop');
  }, { nome, tipo, contenuto, fase });
}
const pdf = '%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Count 0/Kids[]>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF';
const prevenuto = await trascina('contratto.pdf', 'application/pdf', pdf, 'entra');
ok('D1 durante il trascinamento il browser non apre il file (dragover annullato)', prevenuto);
ok('D2 compare il riquadro «Rilascia qui»', await p.locator('[data-testid="drop-zone"]').isVisible());
await trascina('contratto.pdf', 'application/pdf', pdf, 'rilascia');
await p.waitForTimeout(2500);
ok('D3 rilasciato il file parte il caricamento (/upload)', uploads.length === 1, JSON.stringify(uploads));
ok('D4 il riquadro sparisce', !(await p.locator('[data-testid="drop-zone"]').isVisible()));
ok('D5 il file compare tra gli allegati con il suo nome', (await p.locator('main').first().innerText()).includes('contratto.pdf') || (await p.locator('body').innerText()).includes('contratto.pdf'));
ok('D6 la pagina non è stata sostituita dal file', !navigato);

// formato non ammesso: nessun upload, messaggio chiaro
await trascina('virus.exe', 'application/x-msdownload', 'MZ', 'entra');
await trascina('virus.exe', 'application/x-msdownload', 'MZ', 'rilascia');
await p.waitForTimeout(800);
ok('D7 un .exe non viene caricato', uploads.length === 1);
ok('D8 messaggio di errore chiaro', /formato non supportato/i.test(await p.locator('body').innerText()));

// pulsante «Allega file» ancora funzionante
const [fc] = await Promise.all([p.waitForEvent('filechooser'), p.locator('button[aria-label="Allega file"]').click()]);
await fc.setFiles({ name: 'nota.txt', mimeType: 'text/plain', buffer: Buffer.from('Fornitore Rossi srl, fattura 120/2026 da 1.500 euro, scadenza 30 giorni') });
await p.waitForTimeout(2500);
ok('D9 il pulsante Allega file carica ancora', uploads.length === 2 && (await p.locator('body').innerText()).includes('nota.txt'));
await b.close();
console.log(esiti.every(Boolean) ? 'TUTTO OK' : 'CI SONO FALLIMENTI'); process.exit(esiti.every(Boolean) ? 0 : 1);
