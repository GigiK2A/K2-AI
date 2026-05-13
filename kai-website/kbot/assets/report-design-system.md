# K2-AI Report Design System

Sistema di design per tutti i report HTML generati da K2-AI. Segui queste specifiche esattamente per garantire coerenza e qualità professionale.

---

## Palette colori (CSS variables — sempre in :root)

```css
:root {
  --primary: #0F2544;
  --primary-light: #1A3A6B;
  --primary-ultra-light: #EEF2F8;
  --accent: #E8A020;
  --accent-light: #FDF3E3;
  --accent-dark: #C07800;
  --green: #1A7A4A;
  --green-bg: #E8F5EE;
  --green-border: #A8D5BC;
  --yellow: #C07A00;
  --yellow-bg: #FFF8E8;
  --yellow-border: #F0C060;
  --red: #B02020;
  --red-bg: #FDF0F0;
  --red-border: #F0A0A0;
  --bg: #F0F2F5;
  --surface: #FFFFFF;
  --surface-2: #F8FAFC;
  --border: #E2E8F0;
  --text: #1A1A2E;
  --text-secondary: #4A5568;
  --text-muted: #8090A8;
  --shadow: 0 2px 12px rgba(15,37,68,0.08);
  --shadow-lg: 0 8px 32px rgba(15,37,68,0.13);
  --radius: 12px;
  --radius-sm: 8px;
}
```

---

## Tipografia

- **Font:** `-apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", Roboto, sans-serif`
- **Body:** 15px, line-height 1.65, color `var(--text)`
- **H1 report title:** 28px, bold, `var(--primary)`
- **H2 section:** 20px, 600, `var(--primary)`, border-bottom 2px `var(--accent)`, padding-bottom 8px, margin-bottom 20px
- **H3 subsection:** 16px, 600, `var(--text)`
- **KPI value (grande):** 40-48px, bold, `var(--primary)`
- **KPI value (medio):** 26-32px, bold
- **Label uppercase:** 11px, letter-spacing 1px, `var(--text-muted)`, text-transform uppercase
- **Caption:** 12px, `var(--text-muted)`

---

## Layout base

```css
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", Roboto, sans-serif;
  background: var(--bg);
  color: var(--text);
  font-size: 15px;
  line-height: 1.65;
}
.page-wrapper {
  max-width: 1100px;
  margin: 0 auto;
  padding: 0 24px 60px;
}
.section {
  background: var(--surface);
  border-radius: var(--radius);
  padding: 32px;
  margin-bottom: 24px;
  box-shadow: var(--shadow);
}
.section-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--primary);
  border-bottom: 2px solid var(--accent);
  padding-bottom: 10px;
  margin-bottom: 24px;
}
```

---

## Componente: Header report

```html
<header style="background: linear-gradient(135deg, #0F2544 0%, #1A3A6B 100%); color: white; padding: 28px 40px; margin-bottom: 0;">
  <div style="max-width:1100px; margin:0 auto; display:flex; justify-content:space-between; align-items:center;">
    <div style="display:flex; align-items:center; gap:16px;">
      <img src="{{K2AI_LOGO}}" alt="K2-AI" style="height:48px; width:auto;">
      <div>
        <div style="font-size:12px; letter-spacing:1.5px; text-transform:uppercase; opacity:0.7;">Report Premium</div>
        <div style="font-size:22px; font-weight:700;">{TITOLO REPORT}</div>
      </div>
    </div>
    <div style="text-align:right; opacity:0.85;">
      <div style="font-size:13px;">{Nome struttura / cliente}</div>
      <div style="font-size:12px; margin-top:4px;">Generato il {data}</div>
      <div style="font-size:11px; margin-top:2px; opacity:0.7;">Codice: {ID report}</div>
    </div>
  </div>
</header>
<!-- Barra accent sotto header -->
<div style="height:4px; background: linear-gradient(90deg, #E8A020, #F0C060);"></div>
```

---

## Componente: Card KPI

```html
<div style="background:var(--surface); border-radius:var(--radius); padding:24px; box-shadow:var(--shadow); border-top:3px solid {COLORE_SEMAFORO};">
  <div style="font-size:11px; letter-spacing:1px; text-transform:uppercase; color:var(--text-muted); margin-bottom:8px;">{LABEL KPI}</div>
  <div style="font-size:44px; font-weight:700; color:var(--primary); line-height:1;">{VALORE}</div>
  <div style="font-size:13px; color:var(--text-secondary); margin-top:6px;">{BENCHMARK o CONFRONTO}</div>
  <div style="margin-top:12px; font-size:14px; color:var(--text-secondary);">{COMMENTO 1 RIGA}</div>
</div>
```

---

## Componente: Tabella professionale

```html
<table style="width:100%; border-collapse:collapse; font-size:14px; margin-top:16px;">
  <thead>
    <tr style="background:var(--primary); color:white;">
      <th style="padding:12px 16px; text-align:left; font-weight:600; font-size:12px; text-transform:uppercase; letter-spacing:0.5px;">{HEADER}</th>
    </tr>
  </thead>
  <tbody>
    <tr style="border-bottom:1px solid var(--border);">
      <td style="padding:11px 16px;">{VALORE}</td>
    </tr>
    <!-- righe zebrate: tr:nth-child(even) background #FAFBFC -->
  </tbody>
</table>
```

---

## Componente: Badge semaforo

```html
<!-- Verde -->
<span style="display:inline-flex; align-items:center; gap:6px; background:var(--green-bg); color:var(--green); border:1px solid var(--green-border); border-radius:20px; padding:4px 12px; font-size:13px; font-weight:600;">
  ● Ottimo
</span>
<!-- Giallo -->
<span style="...background:var(--yellow-bg); color:var(--yellow); border-color:var(--yellow-border)...">⚠ Attenzione</span>
<!-- Rosso -->
<span style="...background:var(--red-bg); color:var(--red); border-color:var(--red-border)...">✕ Critico</span>
```

---

## Componente: Accordion (priorità / azioni)

```html
<details style="border:1px solid var(--border); border-radius:var(--radius-sm); margin-bottom:8px; overflow:hidden;">
  <summary style="padding:16px 20px; cursor:pointer; display:flex; align-items:center; gap:12px; background:var(--surface); list-style:none; font-weight:600;">
    <span style="width:28px; height:28px; border-radius:50%; background:var(--primary); color:white; font-size:13px; font-weight:700; display:flex; align-items:center; justify-content:center; flex-shrink:0;">{N}</span>
    <span>{TITOLO AZIONE}</span>
    <span style="margin-left:auto; font-size:13px; color:var(--text-muted);">{IMPATTO}</span>
  </summary>
  <div style="padding:20px; border-top:1px solid var(--border); background:var(--surface-2);">
    {CONTENUTO ESPANSO}
  </div>
</details>
```

---

## Componente: Gauge SVG (score 0-100)

```html
<svg viewBox="0 0 200 120" width="180" height="108">
  <defs>
    <linearGradient id="gGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#B02020"/>
      <stop offset="50%" stop-color="#C07A00"/>
      <stop offset="100%" stop-color="#1A7A4A"/>
    </linearGradient>
  </defs>
  <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="#E2E8F0" stroke-width="16" stroke-linecap="round"/>
  <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="url(#gGrad)" stroke-width="16"
        stroke-linecap="round" stroke-dasharray="{SCORE/100 * 251.2} 251.2"/>
  <text x="100" y="82" text-anchor="middle" font-size="38" font-weight="700" fill="#0F2544">{SCORE}</text>
  <text x="100" y="100" text-anchor="middle" font-size="12" fill="#8090A8">/ 100</text>
</svg>
```

---

## Componente: Barra progress con marker

```html
<div style="position:relative; height:8px; background:var(--border); border-radius:4px; margin:10px 0;">
  <div style="height:100%; width:{PCT}%; background:var(--accent); border-radius:4px;"></div>
  <div style="position:absolute; top:-4px; left:{MARKER_PCT}%; width:16px; height:16px; border-radius:50%; background:var(--primary); transform:translateX(-50%); border:2px solid white; box-shadow:var(--shadow);"></div>
</div>
<div style="display:flex; justify-content:space-between; font-size:11px; color:var(--text-muted);">
  <span>{LABEL_SINISTRA}</span><span>{LABEL_DESTRA}</span>
</div>
```

---

## Footer obbligatorio

```html
<footer style="background:var(--primary); color:rgba(255,255,255,0.85); padding:24px 40px; margin-top:40px;">
  <div style="max-width:1100px; margin:0 auto; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
    <div>
      <img src="{{K2AI_LOGO}}" alt="K2-AI" style="height:28px; opacity:0.9;">
    </div>
    <div style="font-size:12px; text-align:center;">
      Report generato il {DATA} · Dati forniti dall'utente · Stime basate su dati di mercato pubblici
    </div>
    <div style="font-size:12px; text-align:right;">
      k2-ai.it · info@k2-ai.it
    </div>
  </div>
</footer>
```

---

## Regole qualità OBBLIGATORIE

1. **Ogni numero ha contesto**: mai solo "€45", sempre "€45 (mediana zona: €62)"
2. **Ogni sezione ha almeno un paragrafo descrittivo** oltre ai dati numerici
3. **Ogni raccomandazione ha un impatto economico stimato** in €/anno
4. **Tabelle per confronti**, paragrafi per analisi, accordion per azioni operative
5. **Nessuna sezione vuota, nessun placeholder**, nessun TODO
6. **Disclaimer in footer** sempre presente
7. **Logo K2-AI** in header e footer (usa `{{K2AI_LOGO}}` come src dell'img)
8. **Lunghezza minima**: il report deve essere completo e approfondito — non esiste un "troppo lungo" per un report premium
9. **Stime dichiarate**: quando si stima un valore, indicare "(stima)" ma dare sempre il numero
10. **@media print**: tutti gli accordion espansi, sfondo bianco, page-break puliti dopo ogni sezione principale

---

## Grafici (Chart.js 4.x da CDN)

Usa Chart.js solo quando hai dati numerici reali da visualizzare. CDN: `https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js`

Tipi raccomandati:
- Dati mensili → line chart o bar chart
- Mix percentuali → doughnut/pie
- Confronto scenari → grouped bar
- Trend storico → area line chart

Canvas size: max 400px altezza. Sempre `responsive: true, maintainAspectRatio: false`.

---

## @media print

```css
@media print {
  body { background: white; font-size: 13px; }
  .section { box-shadow: none; border: 1px solid #E2E8F0; page-break-inside: avoid; }
  details { display: block; }
  details > div { display: block !important; }
  header, footer { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  .no-print { display: none; }
}
```
