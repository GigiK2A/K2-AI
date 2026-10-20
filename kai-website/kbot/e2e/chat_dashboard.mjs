import { chromium } from 'playwright-core';
const URL = 'http://localhost:3100/app/';
const exe = process.env.CHROME_PATH || '/usr/bin/chromium-browser';
const b = await chromium.launch({ executablePath: exe, args: ['--no-sandbox'] });
const p = await b.newPage({ viewport: { width: 1360, height: 860 } });
// sessione Supabase FINTA (utente loggato) letta dal client senza rete: chiave sb-<host>-auth-token
await p.addInitScript(() => {
  const exp = Math.floor(Date.now() / 1000) + 86400;
  const b64 = (o) => btoa(JSON.stringify(o)).replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
  const jwt = b64({ alg: 'HS256', typ: 'JWT' }) + '.' + b64({ sub: '00000000-0000-4000-8000-000000000001', exp, aud: 'authenticated', role: 'authenticated', email: 'prova@example.com' }) + '.firma';
  localStorage.setItem('sb-127-auth-token', JSON.stringify({ access_token: jwt, refresh_token: 'rt', expires_in: 86400, expires_at: exp, token_type: 'bearer',
    user: { id: '00000000-0000-4000-8000-000000000001', aud: 'authenticated', role: 'authenticated', email: 'prova@example.com', app_metadata: {}, user_metadata: { first_name: 'Prova' }, created_at: '2026-01-01T00:00:00Z' } }));
});
p.on('pageerror', e => console.log('  [pageerror]', String(e).slice(0, 160)));
await p.goto(URL, { waitUntil: 'networkidle' });
const testo = 'Ho una srl di verniciatura a Foligno con 14 dipendenti: posso assumere un apprendista?';
const ta = p.locator('textarea').first();
await ta.fill(testo);
await ta.press('Enter');
// aspetta la risposta del bot (qualsiasi testo nuovo dopo il messaggio utente) fino a 150 s
const t0 = Date.now();
await p.waitForFunction((t) => document.body.innerText.includes(t.slice(0, 30)), testo, { timeout: 20000 });
// aspetta che la risposta arrivi e si stabilizzi: lunghezza del testo cresciuta di almeno 300 caratteri e ferma per 8 s
{ let ultima = -1, ferma = 0; const base = (await p.evaluate(() => document.body.innerText.length));
  for (let i = 0; i < 160; i++) { await p.waitForTimeout(1000); const l = await p.evaluate(() => document.body.innerText.length);
    if (l === ultima && l > base + 300) { if (++ferma >= 8) break; } else ferma = 0; ultima = l; } }
const prima = await p.evaluate(() => document.body.innerText);
console.log('1) dopo la chat: messaggio utente visibile =', prima.includes('verniciatura a Foligno'), '| lunghezza pagina =', prima.length, '| s =', Math.round((Date.now() - t0) / 1000));
const sid1 = await p.evaluate(() => localStorage.getItem('kbot.session_id'));
console.log('   session_id salvato =', sid1 ? sid1.slice(0, 8) + '…' : null);
// navigazione CLIENT (senza ricaricare) alla dashboard e ritorno
await p.evaluate(() => window.next.router.push('/dashboard/'));
await p.waitForURL('**/dashboard/**', { timeout: 15000 }).catch(() => {});
await p.waitForTimeout(1500);
console.log('2) dashboard raggiunta, url =', p.url().replace(/^https?:\/\/[^/]+/, ''));
await p.evaluate(() => window.next.router.push('/'));
await p.waitForURL((u) => /\/app\/?$/.test(u.pathname), { timeout: 15000 }).catch(() => {});
await p.waitForTimeout(5000);
const dopo = await p.evaluate(() => document.body.innerText);
const sid2 = await p.evaluate(() => localStorage.getItem('kbot.session_id'));
console.log('3) dopo il ritorno: messaggio utente visibile =', dopo.includes('verniciatura a Foligno'), '| session_id =', sid2 ? sid2.slice(0, 8) + '…' : null, '| stesso =', sid1 === sid2);
console.log(dopo.includes('verniciatura a Foligno') ? 'ESITO: la chat è ancora lì' : 'ESITO: CHAT PERSA');
await p.screenshot({ path: process.argv[2] || 'dopo.png' });
await b.close();
