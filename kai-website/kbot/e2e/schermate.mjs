import { chromium } from 'playwright-core';
const b = await chromium.launch({ executablePath: process.env.CHROME_PATH || '/usr/bin/chromium-browser', args: ['--no-sandbox'] });
async function nuova(w, h) {
  const p = await b.newPage({ viewport: { width: w, height: h } });
  await p.addInitScript(() => {
    const exp = Math.floor(Date.now() / 1000) + 86400, enc = (o) => btoa(JSON.stringify(o)).replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
    const jwt = enc({ alg: 'HS256' }) + '.' + enc({ sub: '00000000-0000-4000-8000-000000000001', exp, aud: 'authenticated' }) + '.f';
    localStorage.setItem('sb-127-auth-token', JSON.stringify({ access_token: jwt, refresh_token: 'rt', expires_in: 86400, expires_at: exp, token_type: 'bearer', user: { id: '00000000-0000-4000-8000-000000000001', aud: 'authenticated', email: 'prova@example.com', app_metadata: {}, user_metadata: { first_name: 'Prova' }, created_at: '2026-01-01T00:00:00Z' } }));
  });
  return p;
}
let p = await nuova(1360, 860); await p.goto('http://localhost:3100/app/', { waitUntil: 'networkidle' }); await p.waitForTimeout(2500); await p.screenshot({ path: 'ui-desktop-vuoto.png' });
let m = await nuova(390, 844); await m.goto('http://localhost:3100/app/', { waitUntil: 'networkidle' }); await m.waitForTimeout(2500); await m.screenshot({ path: 'ui-mobile-vuoto.png' });
let d = await nuova(1360, 860); await d.goto('http://localhost:3100/app/dashboard/', { waitUntil: 'networkidle' }); await d.waitForTimeout(3000); await d.screenshot({ path: 'ui-dashboard.png', fullPage: false });
await b.close(); console.log('ok');
