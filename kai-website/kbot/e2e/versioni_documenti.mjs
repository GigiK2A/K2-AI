// Test 30B nel browser: una revisione documentale (v2) registrata dalla chat nello STESSO documento logico, versioni conservate,
// citazioni che aprono la versione esatta del PDF (v1 e v2), idempotenza, nessun marcatore grezzo.
// Richiede server_ui.py con UI_LLM_FINTO=1 UI_SEED_VERSIONI=1 (8200) e il frontend (3100). Fascicolo di prova TEST-DOC-VERSIONI-01 (fittizio).
import { chromium } from 'playwright-core';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const QUI = path.dirname(fileURLToPath(import.meta.url));
const V2 = process.env.V2_PDF || path.join(QUI, 'fixtures', 'KBot_Test_04_Riepilogo_Commessa_v2.pdf');
const API = 'http://127.0.0.1:8200/api/kbot';
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
const fascicolo = async () => {
  const l = await (await fetch(API + '/fascicoli')).json();
  const f = l.fascicoli.find((x) => x.codice === 'TEST-DOC-VERSIONI-01');
  return (await (await fetch(API + '/fascicoli/' + f.id)).json());
};
const attendi = async () => { await p.waitForTimeout(3000); for (let i = 0; i < 90; i++) { if (!(await p.getByText('Sto scrivendo').count())) break; await p.waitForTimeout(1000); } await p.waitForTimeout(800); };
const allega = async () => {
  await p.locator('input[type="file"]').first().setInputFiles(V2);
  for (let i = 0; i < 30; i++) { if ((await p.locator('body').innerText()).includes('KBot_Test_04_Riepilogo_Commessa_v2.pdf')) break; await p.waitForTimeout(500); }
  await p.waitForTimeout(1500);
};
const messaggio = async (t) => { const ta = p.locator('textarea').first(); await ta.fill(t); await ta.press('Enter'); await attendi(); };
const ultimaRisposta = async () => (await p.locator('main').first().innerText());

await p.goto('http://localhost:3100/app/', { waitUntil: 'networkidle' }); await p.waitForTimeout(2000);
let f0 = await fascicolo();
ok('V0 partenza: un solo documento (v1) nel fascicolo isolato', f0.documenti.length === 1 && f0.documenti[0].versione === 1, JSON.stringify(f0.documenti.map((d) => [d.versione, d.documento_logico])));
const logico = f0.documenti[0].documento_logico;

// 1) allego la v2 e chiedo di registrarla
await allega();
await messaggio("Sì, registra l'allegato come nuova versione del riepilogo nel fascicolo TEST-DOC-VERSIONI-01, motivo: nuova stima del committente");
const testo1 = await ultimaRisposta();
ok('V1 la risposta riporta l\'esito reale dello strumento (registrata come v2)', /Esito: ok/i.test(testo1) && /v2 del documento/i.test(testo1), testo1.slice(-160).replace(/\n/g, ' '));
const f1 = await fascicolo();
ok('V2 ora ci sono DUE versioni dello stesso documento logico (non un documento indipendente)', f1.documenti.length === 2 && new Set(f1.documenti.map((d) => d.documento_logico)).size === 1 && f1.documenti[0].documento_logico === logico,
  JSON.stringify(f1.documenti.map((d) => [d.versione, d.documento_logico, d.stato])));
const d1 = f1.documenti.find((d) => d.versione === 1), d2 = f1.documenti.find((d) => d.versione === 2);
ok('V3 la v1 è intatta e la v2 ha id diverso, stato «caricato», autore, fonte e motivo', d1 && d2 && d1.doc !== d2.doc && d2.stato === 'caricato' && d2.autore === 'utente' && /chat:/.test(d2.fonte || '') && /stima/.test(d2.motivo || ''), JSON.stringify([d2?.stato, d2?.autore, d2?.fonte, d2?.motivo]));
ok('V4 i record economici NON sono cambiati (registrare ≠ aggiornare)', f1.voci.length === 1 && f1.voci[0].valore === '15.250,00 €' && f1.voci[0].revisione === 1, JSON.stringify(f1.voci.map((v) => [v.valore, v.revisione])));

// 2) confronto: due citazioni, una per versione, che aprono il PDF esatto
await messaggio('Mostra e confronta le versioni del riepilogo nel fascicolo TEST-DOC-VERSIONI-01');
const corpo = await ultimaRisposta();
ok('V5 nessun marcatore grezzo [[fonte…]] nella chat', !/\[\[|fonte\|/i.test(corpo), corpo.match(/.{20}\[\[.{30}/)?.[0] || '');
const nc = await p.locator('[data-testid="citazione"]').count();
ok('V6 le citazioni valide sono cliccabili (v1, v2 e un riferimento alla sola pagina); quella a un documento inesistente è sparita', nc === 3, 'n=' + nc);
const apri = async (i, versione, importo) => {
  await p.locator('[data-testid="citazione"]').nth(i).click();
  await p.waitForSelector('[data-testid="evidenziazione"]', { timeout: 20000 }).catch(() => {});
  const vis = p.locator('[data-testid="visualizzatore"]');
  const testo = await vis.innerText();
  const stato = await vis.locator('[role="status"]').innerText().catch(() => '');
  ok(`V7.${versione} la citazione apre la versione ${versione} del PDF`, new RegExp(`versione ${versione} di 2`).test(testo), testo.slice(0, 110).replace(/\n/g, ' | '));
  ok(`V8.${versione} il passaggio ${importo} è evidenziato nel PDF di quella versione`, (await p.locator('[data-testid="evidenziazione"]').count()) > 0 && stato.includes(importo), stato.slice(0, 100));
  return testo;
};
const t1 = await apri(0, 1, '8.850,00');
ok('V9 la v1 è segnalata come versione PRECEDENTE ma funziona', /versione 1 di 2 \(precedente\)/.test(t1));
await p.screenshot({ path: 'versioni-v1.png' });
await p.locator('[data-testid="chiudi-visualizzatore"]').click(); await p.waitForTimeout(300);
const t2 = await apri(1, 2, '9.250,00');
ok('V10 la v2 non è «precedente»', !/\(precedente\)/.test(t2));
await p.screenshot({ path: 'versioni-v2.png' });
await p.locator('[data-testid="chiudi-visualizzatore"]').click(); await p.waitForTimeout(300);

// 3) idempotenza: stesso allegato in una conversazione NUOVA → nessuna v3
await p.goto('http://localhost:3100/app/', { waitUntil: 'networkidle' }); await p.waitForTimeout(2000);
await allega();
await messaggio("Sì, registra l'allegato come nuova versione del riepilogo nel fascicolo TEST-DOC-VERSIONI-01, motivo: ripeto il caricamento");
const testo3 = await ultimaRisposta();
ok('V11 la ripetizione risponde «idempotente / già registrato»', /idempotente/i.test(testo3) && /già registrat/i.test(testo3), testo3.slice(-200).replace(/\n/g, ' '));
const f3 = await fascicolo();
ok('V12 nessuna v3 e nessun nuovo documento logico', f3.documenti.length === 2 && new Set(f3.documenti.map((d) => d.documento_logico)).size === 1);
await b.close(); console.log(esiti.every(Boolean) ? 'TUTTO OK' : 'CI SONO FALLIMENTI'); process.exit(esiti.every(Boolean) ? 0 : 1);
