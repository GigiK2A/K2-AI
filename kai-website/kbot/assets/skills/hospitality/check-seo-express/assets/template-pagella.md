# Template Pagella SEO — HTML Self-Contained

Questo file contiene il template HTML da utilizzare per generare la pagella SEO visiva. Sostituire i segnaposto `{{...}}` con i dati reali dell'analisi.

```html
<!DOCTYPE html>
<html lang="it">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Pagella SEO — {{NOME_SITO}}</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }

    body {
      font-family: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
      background: #F8FAFC;
      color: #1E293B;
      line-height: 1.6;
      padding: 20px;
    }

    .container {
      max-width: 800px;
      margin: 0 auto;
    }

    /* Header */
    .header {
      text-align: center;
      padding: 30px 20px;
      border-bottom: 3px solid #E2E8F0;
      margin-bottom: 30px;
    }

    .header .logo-placeholder {
      width: 60px;
      height: 60px;
      background: #E2E8F0;
      border-radius: 12px;
      margin: 0 auto 16px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 24px;
      color: #94A3B8;
    }

    .header h1 {
      font-size: 24px;
      font-weight: 700;
      margin-bottom: 4px;
    }

    .header .subtitle {
      font-size: 14px;
      color: #64748B;
    }

    /* Score Gauge */
    .score-section {
      text-align: center;
      padding: 40px 20px;
      margin-bottom: 30px;
    }

    .gauge-container {
      position: relative;
      width: 200px;
      height: 200px;
      margin: 0 auto 20px;
    }

    .gauge-svg {
      width: 200px;
      height: 200px;
      transform: rotate(-90deg);
    }

    .gauge-bg {
      fill: none;
      stroke: #E2E8F0;
      stroke-width: 12;
    }

    .gauge-fill {
      fill: none;
      stroke: {{COLORE_FASCIA}};
      stroke-width: 12;
      stroke-linecap: round;
      stroke-dasharray: {{DASH_ARRAY}};
      transition: stroke-dasharray 1s ease;
    }

    .gauge-score {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      font-size: 56px;
      font-weight: 800;
      color: {{COLORE_FASCIA}};
    }

    .gauge-label {
      position: absolute;
      bottom: 30px;
      left: 50%;
      transform: translateX(-50%);
      font-size: 14px;
      color: #64748B;
    }

    .fascia-badge {
      display: inline-block;
      padding: 6px 20px;
      border-radius: 20px;
      font-weight: 600;
      font-size: 16px;
      color: white;
      background: {{COLORE_FASCIA}};
      margin-bottom: 12px;
    }

    .fascia-messaggio {
      font-size: 16px;
      color: #475569;
      max-width: 600px;
      margin: 0 auto;
    }

    /* Fattori */
    .fattori-section {
      margin-bottom: 30px;
    }

    .fattori-section h2 {
      font-size: 20px;
      font-weight: 700;
      margin-bottom: 16px;
      padding-bottom: 8px;
      border-bottom: 2px solid #E2E8F0;
    }

    .fattore-item {
      display: flex;
      align-items: center;
      padding: 12px 16px;
      background: white;
      border-radius: 8px;
      margin-bottom: 8px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }

    .semaforo {
      width: 16px;
      height: 16px;
      border-radius: 50%;
      flex-shrink: 0;
      margin-right: 14px;
    }

    .semaforo-verde { background: #22C55E; }
    .semaforo-giallo { background: #EAB308; }
    .semaforo-rosso { background: #EF4444; }

    .fattore-nome {
      font-weight: 600;
      font-size: 15px;
      min-width: 200px;
    }

    .fattore-desc {
      font-size: 14px;
      color: #64748B;
      flex: 1;
    }

    .fattore-score {
      font-weight: 700;
      font-size: 15px;
      margin-left: 12px;
      min-width: 40px;
      text-align: right;
    }

    /* Top 5 criticita */
    .criticita-section {
      background: white;
      border-radius: 12px;
      padding: 24px;
      margin-bottom: 30px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.08);
      border-left: 4px solid #EF4444;
    }

    .criticita-section h2 {
      font-size: 20px;
      font-weight: 700;
      margin-bottom: 16px;
      color: #EF4444;
    }

    .criticita-item {
      padding: 14px 0;
      border-bottom: 1px solid #F1F5F9;
    }

    .criticita-item:last-child {
      border-bottom: none;
      padding-bottom: 0;
    }

    .criticita-num {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 28px;
      height: 28px;
      background: #FEF2F2;
      color: #EF4444;
      border-radius: 50%;
      font-weight: 700;
      font-size: 14px;
      margin-right: 12px;
      vertical-align: middle;
    }

    .criticita-titolo {
      font-weight: 600;
      font-size: 15px;
      vertical-align: middle;
    }

    .criticita-impatto {
      display: block;
      margin: 6px 0 4px 40px;
      font-size: 14px;
      color: #EF4444;
      font-weight: 500;
    }

    .criticita-azione {
      display: block;
      margin-left: 40px;
      font-size: 14px;
      color: #475569;
    }

    /* CTA Footer */
    .cta-section {
      text-align: center;
      background: linear-gradient(135deg, #1E293B 0%, #334155 100%);
      color: white;
      border-radius: 12px;
      padding: 32px 24px;
      margin-bottom: 20px;
    }

    .cta-section h2 {
      font-size: 22px;
      font-weight: 700;
      margin-bottom: 12px;
    }

    .cta-section p {
      font-size: 15px;
      color: #CBD5E1;
      margin-bottom: 20px;
      max-width: 500px;
      margin-left: auto;
      margin-right: auto;
    }

    .cta-button {
      display: inline-block;
      background: #22C55E;
      color: white;
      padding: 14px 32px;
      border-radius: 8px;
      font-weight: 700;
      font-size: 16px;
      text-decoration: none;
      transition: background 0.2s;
    }

    .cta-button:hover {
      background: #16A34A;
    }

    .footer {
      text-align: center;
      font-size: 12px;
      color: #94A3B8;
      padding: 16px;
    }

    /* Responsive */
    @media (max-width: 600px) {
      body { padding: 12px; }
      .header h1 { font-size: 20px; }
      .gauge-container { width: 160px; height: 160px; }
      .gauge-svg { width: 160px; height: 160px; }
      .gauge-score { font-size: 44px; }
      .fattore-item { flex-wrap: wrap; }
      .fattore-nome { min-width: 100%; margin-bottom: 4px; }
      .fattore-desc { margin-left: 30px; }
      .fattore-score { margin-left: 30px; }
    }
  </style>
</head>
<body>
  <div class="container">

    <!-- Header -->
    <div class="header">
      <div class="logo-placeholder">SEO</div>
      <h1>Pagella SEO — {{NOME_SITO}}</h1>
      <div class="subtitle">Analisi generata il {{DATA_GENERAZIONE}} | URL: {{URL_ANALIZZATO}}</div>
    </div>

    <!-- Score Gauge -->
    <div class="score-section">
      <div class="gauge-container">
        <svg class="gauge-svg" viewBox="0 0 200 200">
          <circle class="gauge-bg" cx="100" cy="100" r="85"/>
          <circle class="gauge-fill" cx="100" cy="100" r="85"/>
        </svg>
        <div class="gauge-score">{{SCORE}}</div>
        <div class="gauge-label">su 100</div>
      </div>
      <div class="fascia-badge">{{FASCIA}}</div>
      <p class="fascia-messaggio">{{MESSAGGIO_FASCIA}}</p>
    </div>

    <!-- 10 Fattori -->
    <div class="fattori-section">
      <h2>I 10 fattori analizzati</h2>

      <!-- Ripetere questo blocco per ciascun fattore -->
      {{#FATTORI}}
      <div class="fattore-item">
        <div class="semaforo semaforo-{{SEMAFORO}}"></div>
        <span class="fattore-nome">{{NOME_FATTORE}}</span>
        <span class="fattore-desc">{{DESCRIZIONE_FATTORE}}</span>
        <span class="fattore-score">{{SCORE_FATTORE}}/10</span>
      </div>
      {{/FATTORI}}

    </div>

    <!-- Top 5 Criticita -->
    <div class="criticita-section">
      <h2>Le 5 cose da fare subito</h2>

      <!-- Ripetere per ciascuna criticita -->
      {{#CRITICITA}}
      <div class="criticita-item">
        <span class="criticita-num">{{NUM}}</span>
        <span class="criticita-titolo">{{TITOLO}}</span>
        <span class="criticita-impatto">{{IMPATTO_STIMATO}}</span>
        <span class="criticita-azione">{{AZIONE_SUGGERITA}}</span>
      </div>
      {{/CRITICITA}}

    </div>

    <!-- CTA -->
    <div class="cta-section">
      <h2>Vuoi l'analisi completa?</h2>
      <p>{{CTA_MESSAGGIO}}</p>
      <a href="{{CTA_LINK}}" class="cta-button">Audit SEO Tecnico &rarr;</a>
    </div>

    <div class="footer">
      Pagella SEO generata da check-seo-express | Questo report ha valore indicativo e non sostituisce un'analisi tecnica approfondita.
    </div>

  </div>
</body>
</html>
```

## Note per la compilazione del template

### Segnaposto da sostituire

| Segnaposto | Descrizione | Esempio |
|------------|-------------|---------|
| `{{NOME_SITO}}` | Nome del dominio analizzato | `www.esempio.it` |
| `{{DATA_GENERAZIONE}}` | Data e ora di generazione | `16 aprile 2026, ore 14:30` |
| `{{URL_ANALIZZATO}}` | URL completo analizzato | `https://www.esempio.it` |
| `{{SCORE}}` | Punteggio globale 0-100 | `62` |
| `{{COLORE_FASCIA}}` | Codice colore della fascia | `#EAB308` |
| `{{FASCIA}}` | Nome della fascia | `Sufficiente` |
| `{{MESSAGGIO_FASCIA}}` | Messaggio descrittivo | Vedi scoring-model.md |
| `{{DASH_ARRAY}}` | Valore SVG per l'arco | Calcolare come `(score/100)*534 534` |
| `{{SEMAFORO}}` | Colore semaforo: `verde`, `giallo`, `rosso` | `verde` |
| `{{NOME_FATTORE}}` | Nome del fattore | `HTTPS attivo` |
| `{{DESCRIZIONE_FATTORE}}` | Descrizione breve 1 riga | `Il sito usa connessione sicura` |
| `{{SCORE_FATTORE}}` | Punteggio del fattore 0-10 | `9` |
| `{{NUM}}` | Numero progressivo criticita | `1` |
| `{{TITOLO}}` | Titolo della criticita | `Il sito non si vede bene dal telefono` |
| `{{IMPATTO_STIMATO}}` | Stima impatto qualitativa | `Stai probabilmente perdendo il 40% dei visitatori da mobile` |
| `{{AZIONE_SUGGERITA}}` | Azione da intraprendere | `Chiedi al tuo webmaster di rendere il sito responsive` |
| `{{CTA_MESSAGGIO}}` | Testo CTA dalla fascia | Vedi scoring-model.md |
| `{{CTA_LINK}}` | Link al servizio successivo | `#audit-seo-tecnico` |

### Calcolo DASH_ARRAY per il gauge SVG

La circonferenza del cerchio (raggio 85) e circa 534 pixel.

```
percentuale = score / 100
dash_fill = percentuale * 534
DASH_ARRAY = "{dash_fill} 534"
```

Esempio per score 62: `DASH_ARRAY = "331 534"`
