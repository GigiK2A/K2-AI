# Pattern di generazione contenuti — WebBoost

Usa questo file durante lo **Step 6** quando generi i 2 articoli pronti e il piano editoriale. Il file descrive i pattern che distinguono un articolo SEO vero da uno "generato a caso che suona da AI".

---

## 1. Struttura canonica di un articolo SEO per PMI

Ogni articolo deve rispettare questa struttura. Non è opzionale.

```
[H1 — title con keyword primaria]
  
  [Lead paragraph 60–100 parole]
  - Risponde al search intent nelle prime 2 righe (utile per featured snippet)
  - Menziona 1–2 pain point del lettore target
  - Anticipa cosa troverà nell'articolo
  - Keyword primaria naturale nel primo paragrafo

  [Paragrafo sintesi / TL;DR — opzionale ma consigliato per articoli >1200 parole]
  - 3–5 bullet con i punti chiave
  - Serve per lettori scanner
  
[H2 — Sezione 1 — una keyword correlata]
  [200–400 parole]
  [Può contenere H3 se la sezione è articolata]
  [Esempio concreto o caso reale]
  
[H2 — Sezione 2 — altra keyword correlata]
  [200–400 parole]
  [Uso elenchi puntati dove la lista aggiunge valore, non solo per spezzare]
  
[H2 — Sezione 3 — topic complementare]
  ...
  
[H2 — Domande frequenti]
  [3–5 FAQ con domanda come H3 e risposta 40–80 parole]
  [Ottimo per featured snippet e People Also Ask]
  [Marcare con schema FAQPage quando possibile]
  
[H2 — Conclusione / Next step]
  [CTA chiara e unica: contatto, lead magnet, prodotto]
  [Internal link a 1–2 pagine rilevanti del sito]

[Meta description pronta: 140–160 car, con keyword + CTA]
```

---

## 2. Cosa rende un articolo buono (segnali di qualità che Google premia)

**Expertise visibile.** Non dire "l'azienda X offre servizi di...". Dillo come lo direbbe un esperto di quel settore, con dati, numeri, nomi di norme, esempi concreti. Se scrivi per un commercialista, cita articoli del TUIR. Se scrivi per un serramentista, parla di trasmittanza termica Uf/Ug e detrazioni 50% o 65%.

**Punto di vista.** Un articolo buono ha un'opinione. "Le 5 cose da fare" è mediocre. "Perché il 90% delle PMI sbaglia il primo passo, e come evitarlo" è un articolo con angolo.

**Specificità italiana.** Menziona la normativa italiana, usi casi aziendali italiani, cita fonti italiane autorevoli (Il Sole 24 Ore, Altroconsumo, associazioni di categoria, Agenzia Entrate). Gli articoli tradotti dall'inglese si riconoscono da mille km.

**Call-to-action coerente.** L'articolo non è un annuncio, ma ha un obiettivo. Per WebBoost tipicamente: generare un contatto, scaricare un lead magnet, prenotare una consulenza gratuita, iscriversi alla newsletter. Mai più di 1 CTA dominante per articolo.

---

## 3. Cosa NON fare mai

Lista degli errori che marchiano un articolo come "AI slop" e uccidono credibilità + SEO:

1. **Iniziare con "Nel mondo di oggi..."** o altre frasi vuote.
2. **Scrivere "in un'era digitale in cui..."** o varianti.
3. **Usare "fondamentale", "cruciale", "imprescindibile"** più di 1 volta per articolo.
4. **Bullet list di 7 punti dove ogni punto è una frase generica senza esempio concreto.**
5. **Frasi tipo "ogni azienda è unica"** (ovvio, non aggiunge nulla).
6. **Chiudere con "In conclusione, è importante considerare..."** — piattezza.
7. **Non menzionare mai dati, numeri, percentuali concrete.**
8. **Usare lo stesso aggettivo 3 volte nel pezzo** ("efficace", "efficiente", "ottimale").
9. **Scrivere in terza persona impersonale tutto il tempo** — alterna "tu" quando parli al lettore.
10. **Non avere un punto di vista.**

---

## 4. Pattern per articolo pillar vs cluster

**Pillar page** (guida completa, evergreen):
- Lunghezza: 2000–3500 parole
- Obiettivo: rankare su keyword ampia e generica del settore (es. "gestione contabilità PMI")
- Struttura: introduttiva → panoramica delle sotto-aree → link a cluster article di dettaglio → conclusione strategica
- Aggiornata ogni 6–12 mesi
- Template title: "Guida completa [topic] per PMI italiane", "[Topic]: tutto quello che devi sapere nel [anno]"

**Cluster article** (topic specifico, supporta la pillar):
- Lunghezza: 800–1500 parole
- Obiettivo: rankare su long-tail specifica (es. "come calcolare iva compensazione credito")
- Struttura: pain/pregunta → risposta breve → approfondimento → esempio concreto → link interno alla pillar page
- Template title: "Come [azione] in [tempo specifico]", "[Numero] errori da evitare quando [situazione]", "[Domanda specifica che il cliente si fa]"

---

## 5. Workflow interno per generare un articolo

Quando devi generare uno dei 2 articoli pronti:

1. **Ricevi dalla skill**: keyword target, intent, pillar/cluster, pagina del sito a cui deve linkare internamente, brand voice estratta.
2. **Ricerca SERP mentale**: che cosa sta già rankando? Che angolo manca? Non imitare, differenziati con valore aggiunto concreto (esempio italiano, calcolo, checklist scaricabile, template).
3. **Outline**: scrivi prima la struttura H2/H3 e il punto di vista in 2 righe.
4. **Scrittura**: usa la brand voice dichiarata. Non farti prendere dal ritmo generico AI.
5. **Ottimizzazione SEO post-scrittura**:
   - Title con keyword primaria, <60 car
   - Meta description con keyword + CTA, 140–160 car
   - Keyword primaria nel primo paragrafo
   - 2–3 varianti/sinonimi nei H2
   - Almeno 2 internal link suggeriti
   - 1 external link a fonte autorevole (dà credibilità)
   - Alt text descrittivo per immagini suggerite
6. **Check finale anti-slop**: rileggi e rimuovi ogni frase della lista "non fare mai" sopra.

---

## 6. Template prompt per generazione articoli (modalità piattaforma)

Quando la skill gira in piattaforma e deve chiamare un sub-agente dedicato alla scrittura:

```
Sei un copywriter SEO senior specializzato in [settore del cliente].
Scrivi un articolo per il sito di [nome cliente], che è [descrizione 1 riga].

Target lettore: [persona del target, 1–2 righe]

Keyword primaria: [keyword]
Keyword correlate da usare naturalmente: [3–5 keyword]
Intent: [informativo / transazionale / commerciale]

Brand voice:
- Tono: [3 attributi]
- Parole da usare: [5 esempi]
- Parole da evitare: [5 esempi]
- Esempio di frase on-brand: "[frase reale dal sito]"

Struttura richiesta:
- Lunghezza 1000–1400 parole
- 1 H1 con keyword primaria
- 4–6 H2, ciascuno con 200–300 parole di contenuto
- 1 sezione FAQ finale con 3 domande
- CTA finale verso [URL specifica]
- Almeno 2 internal link verso: [URL1, URL2]

Regole:
- Niente intro vuote tipo "nel mondo digitale di oggi"
- Ogni affermazione deve avere esempio, numero o riferimento concreto
- Usa "tu" per parlare direttamente al lettore in almeno 2 sezioni
- Includi 1 dato italiano verificabile (associazione di categoria, Istat, Agenzia Entrate...)
- Concludi con CTA unica e chiara

Output atteso:
- Title (con variante alternativa)
- Meta description
- Articolo completo in Markdown
- Alt text per 2 immagini suggerite
```

---

## 7. Qualità del piano editoriale (Step 6 parte 1)

Un piano editoriale di qualità per una PMI deve avere queste caratteristiche:

- **Bilanciamento intent**: 50% informativi (SEO evergreen), 30% commerciali (lead gen), 20% brand/autorevolezza.
- **Bilanciamento fase funnel**: 40% TOFU (awareness), 40% MOFU (consideration), 20% BOFU (decision).
- **Cadenza sostenibile**: 2–4 articoli/mese per PMI piccole. Non 12, non 1.
- **Pillar-cluster logic**: ogni 4–6 cluster, una pillar che li raccoglie.
- **Stagionalità**: se il settore ha stagionalità (ristorazione, turismo, bilanci a marzo/giugno, Black Friday, ecc.), il calendario la riflette.
- **Keyword con opportunità reale**: non tutte keyword ad altissimo volume (impossibili) né a zero volume (inutili). Sweet spot: volume stimato 50–1000, difficulty medio-basso.
