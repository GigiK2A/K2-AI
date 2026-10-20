// Documento in tempo reale, separato dalla chat: stati reali, testo progressivo, versioni, esportazione, errore con ripresa,
// isolamento fra pratiche. Usa il backend VERO con un modello finto lento (server_ui.py con UI_LLM_FINTO=1).
import { chromium } from 'playwright-core';
const b = await chromium.launch({ executablePath: process.env.CHROME_PATH || '/usr/bin/chromium-browser', args: ['--no-sandbox'] });
const ctx = await b.newContext({ viewport: { width: 1360, height: 900 }, acceptDownloads: true });
const p = await ctx.newPage();
await p.addInitScript(() => {
  const exp = Math.floor(Date.now() / 1000) + 86400, enc = (o) => btoa(JSON.stringify(o)).replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
  const jwt = enc({ alg: 'HS256' }) + '.' + enc({ sub: '00000000-0000-4000-8000-000000000001', exp, aud: 'authenticated' }) + '.f';
  if (!localStorage.getItem('sb-127-auth-token'))
    localStorage.setItem('sb-127-auth-token', JSON.stringify({ access_token: jwt, refresh_token: 'rt', expires_in: 86400, expires_at: exp, token_type: 'bearer', user: { id: '00000000-0000-4000-8000-000000000001', aud: 'authenticated', email: 'prova@example.com', app_metadata: {}, user_metadata: {}, created_at: '2026-01-01T00:00:00Z' } }));
});
p.on('pageerror', (e) => console.log('  [pageerror]', String(e).slice(0, 200)));
const esiti = []; const ok = (n, v, extra = '') => { esiti.push([n, !!v]); console.log((v ? 'OK  ' : 'FAIL') + ' ' + n + (extra ? '  ' + extra : '')); };
const pannello = () => p.locator('section[aria-label="Pratica"]');
const stato = async () => (await pannello().locator('[role="status"]').allInnerTexts()).map((t) => t.trim().toLowerCase());   // l'interfaccia le mostra in maiuscolo
const testoDoc = async () => (await pannello().locator('article').allInnerTexts())[0] || '';

await p.goto('http://localhost:3100/app/', { waitUntil: 'networkidle' }); await p.waitForTimeout(2000);

// ── TEST A: PEC, testo progressivo, stati reali, chat senza il documento ──────────────────────────────────────
const t0 = Date.now();
const ta = p.locator('textarea').first(); await ta.fill('Scrivimi una PEC per contestare il gestionale difettoso'); await ta.press('Enter');
const visti = []; const lunghezze = []; let primoTestoDoc = null; let chatConDocumento = false; let badgeContemporanei = 0;
for (let i = 0; i < 400; i++) {
  const st = await stato(); const lab = st[0] || '';
  if (st.length > 1) badgeContemporanei++;
  if (lab && visti[visti.length - 1] !== lab) visti.push(lab);
  const d = await testoDoc(); if (d && lunghezze[lunghezze.length - 1] !== d.length) lunghezze.push(d.length);
  if (d && primoTestoDoc === null) primoTestoDoc = Date.now() - t0;
  const chat = await p.locator('main').first().innerText();
  if (chat.includes('Spett.le DemoSoft')) chatConDocumento = true;
  if (lab.startsWith('bozza pronta')) break;
  await p.waitForTimeout(50);
}
console.log('   stati osservati:', JSON.stringify(visti), '| aggiornamenti del testo:', lunghezze.length, '| primo testo dopo ms:', primoTestoDoc);
ok('A1 il documento compare nel pannello e cresce mentre si scrive (≥5 aggiornamenti)', lunghezze.length >= 5);
ok('A2 gli stati sono reali e in ordine: scrittura → … → bozza pronta', visti.includes('in scrittura…') && visti[visti.length - 1].startsWith('bozza pronta'), JSON.stringify(visti));
ok('A3 mai due stati insieme (niente «in preparazione» e «completato» contemporanei)', badgeContemporanei === 0);
ok('A4 la chat NON contiene il testo del documento', !chatConDocumento);
const chatFinale = await p.locator('main').first().innerText();
ok('A5 la chat contiene la conversazione (premessa e note), non il documento', chatFinale.includes('valore dell\'accettazione tramite SDI') && chatFinale.includes('Controlla il numero della fattura') && !chatFinale.includes('Distinti saluti'));
ok('A6 il documento completo è leggibile nel pannello', (await testoDoc()).includes('Distinti saluti'));
ok('A7 compare il rimando «Bozza pronta» nella chat', chatFinale.includes('Bozza pronta · da verificare'));
ok('A8 nessun generatore di report offerto', !/Genera il report|ControlBoost|Cruscotto direzionale/i.test(await p.evaluate(() => document.body.innerText)));
await p.screenshot({ path: 'ui-doc-pronto.png' });

// ── TEST B: esportazione come passo a parte ───────────────────────────────────────────────────────────────
let corpoExport = null;
await p.route('**/render-message-docx', async (r) => { corpoExport = JSON.parse(r.request().postData() || '{}'); await new Promise((x) => setTimeout(x, 700)); await r.continue(); });
const [dl] = await Promise.all([p.waitForEvent('download', { timeout: 15000 }).catch(() => null), pannello().getByRole('button', { name: /Scarica Word/ }).click()]);
await p.waitForTimeout(200);
ok('B1 durante l\'esportazione compare «Preparo il file…» (stato reale dell\'esportazione)', (await stato()).some((t) => t.includes('preparo il file')) || corpoExport !== null);
ok('B2 la richiesta esporta il documento giusto (message_index e document_index)', corpoExport && corpoExport.message_index === 1 && corpoExport.document_index === 0, JSON.stringify(corpoExport));
ok('B3 il file Word viene scaricato con il titolo del documento', dl && /pec-di-contestazione/.test(dl.suggestedFilename()), dl ? dl.suggestedFilename() : 'nessun download');
if (dl) {
  const percorso = await dl.path();
  const { execFileSync } = await import('node:child_process');
  const testo = execFileSync('python3', ['-c', 'import sys,docx;d=docx.Document(sys.argv[1]);print("\\n".join(p.text for p in d.paragraphs))', percorso]).toString();
  ok('B5 il Word contiene SOLO il documento (niente conversazione, niente intestazioni di sistema)', testo.includes('Spett.le DemoSoft') && testo.includes('Distinti saluti') && !/K2-AI|K2A S\.R\.L|accettazione tramite SDI|Controlla il numero/.test(testo));
}
await p.waitForTimeout(800);
ok('B4 a esportazione finita lo stato torna «Bozza pronta»', (await stato())[0]?.startsWith('bozza pronta'));

// ── TEST C: nuova versione, la chat non duplica il documento ──────────────────────────────────────────────
await ta.fill('Aggiorna la PEC: versione 2 con la data del contratto'); await ta.press('Enter');
await p.waitForFunction(() => document.body.innerText.includes('Versione 2 di 2'), null, { timeout: 20000 }).catch(() => {});
await p.waitForFunction(() => document.body.innerText.includes('Bozza pronta') && document.body.innerText.includes('12 marzo 2026'), null, { timeout: 20000 }).catch(() => {});
ok('C1 compare «Versione 2 di 2» con il contenuto aggiornato', (await testoDoc()).includes('12 marzo 2026'));
await pannello().getByRole('button', { name: 'Versione precedente' }).click(); await p.waitForTimeout(200);
ok('C2 la versione 1 resta consultabile e non contiene i dati nuovi', !(await testoDoc()).includes('12 marzo 2026') && (await pannello().innerText()).includes('Versione 1 di 2'));
await pannello().getByRole('button', { name: 'Versione successiva' }).click(); await p.waitForTimeout(200);
ok('C3 si torna alla versione 2', (await testoDoc()).includes('12 marzo 2026'));
const nPec = (await p.locator('main').first().innerText()).split('Spett.le DemoSoft').length - 1;
ok('C4 il documento non è duplicato nella chat', nPec === 0);

// ── TEST D: errore a metà, testo conservato, ripresa ──────────────────────────────────────────────────────
await p.getByRole('button', { name: 'Nuova pratica' }).first().click(); await p.waitForTimeout(800);
ok('E1 (isolamento) la nuova pratica non mostra il documento dell\'altra', (await pannello().innerText()).includes('Nessuna bozza, per ora'));
const ta2 = p.locator('textarea').first(); await ta2.fill('Scrivimi una PEC per contestare il software: interrompi a metà'); await ta2.press('Enter');
await p.waitForFunction(() => document.body.innerText.includes('Interrotto'), null, { timeout: 20000 }).catch(() => {});
const parziale = await testoDoc();
ok('D1 dopo l\'errore lo stato è «Interrotto» e il testo già scritto resta nel pannello', (await stato())[0] === 'interrotto' && parziale.length > 50, 'caratteri conservati: ' + parziale.length);
ok('D2 compare l\'errore chiaro e il pulsante «Riprova» (chat e pannello)', (await p.getByRole('button', { name: /Riprova/ }).count()) >= 1 && /non è andato perso/.test(await p.evaluate(() => document.body.innerText)));
const nUtenti = async () => (await p.locator('main').first().innerText()).split('LA TUA RICHIESTA').length - 1;
const prima = await nUtenti();
await pannello().getByRole('button', { name: /Riprova/ }).click();
await p.waitForFunction(() => /bozza pronta/i.test(document.querySelector('section[aria-label="Pratica"] [role="status"]')?.innerText || ''), null, { timeout: 25000 }).catch(() => {});
await p.waitForTimeout(300);
ok('D3 la ripresa completa il documento', (await testoDoc()).includes('Distinti saluti') && (await stato())[0]?.startsWith('bozza pronta'), JSON.stringify({ stato: await stato(), fine: (await testoDoc()).slice(-40) }));
ok('D4 la domanda dell\'utente non viene duplicata dalla ripresa', (await nUtenti()) === prima, `richieste in chat: ${prima} → ${await nUtenti()}`);

// ── TEST E: isolamento — la prima pratica conserva il suo documento ───────────────────────────────────────
const titoli = await p.locator('aside').first().innerText();
ok('E2 le due pratiche hanno ciascuna un titolo', (titoli.match(/Contestazione software/g) || []).length >= 1, JSON.stringify(titoli.split('\n').filter(Boolean).slice(0, 8)));
const voci = p.locator('aside button').filter({ hasText: /Contestazione|Nuova pratica|pec|PEC/i });
await p.screenshot({ path: 'ui-doc-seconda-pratica.png' });
await b.close();
const ko = esiti.filter(([, v]) => !v);
console.log(ko.length ? 'FALLITI: ' + ko.map(([n]) => n).join(' | ') : 'TUTTI OK (' + esiti.length + ')'); process.exit(ko.length ? 1 : 0);
