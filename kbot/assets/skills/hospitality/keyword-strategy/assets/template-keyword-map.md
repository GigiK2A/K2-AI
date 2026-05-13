# Template Keyword Map — XLSX (4 Tab)

Struttura del file XLSX generato dalla skill `keyword-strategy`. Il file viene creato tramite la skill `xlsx`.

---

## Tab 1 — Keyword Master

Elenco completo di tutte le keyword analizzate e selezionate.

| Colonna | Tipo | Descrizione |
|---------|------|-------------|
| keyword | testo | La keyword esatta come cercata su Google |
| volume | numero | Volume di ricerca mensile stimato (Italia) |
| difficulty | numero (0-100) | Difficolta di posizionamento stimata |
| intent | testo (I/N/C/T) | Intent primario: Informazionale, Navigazionale, Commerciale, Transazionale |
| cluster | testo | Nome del cluster tematico di appartenenza |
| pagina_target | testo | URL pagina esistente o "DA CREARE: [tipo]" |
| priorita | numero (1-5) | 1 = massima priorita, 5 = minima |
| note | testo | Note operative (es. "stagionale", "competitor forte", "quick win") |

**Ordinamento**: per priorita (1 prima), poi per volume (decrescente).

**Formattazione condizionale suggerita:**
- Priorita 1: sfondo verde
- Priorita 2: sfondo verde chiaro
- Priorita 3: sfondo giallo
- Priorita 4: sfondo arancione
- Priorita 5: sfondo rosso chiaro
- Intent T: testo grassetto
- Intent C: testo grassetto corsivo

**Esempio riga:**

| keyword | volume | difficulty | intent | cluster | pagina_target | priorita | note |
|---------|--------|------------|--------|---------|--------------|----------|------|
| idraulico urgente milano | 720 | 25 | T | pronto intervento | /pronto-intervento/ | 1 | Quick win - pagina gia esistente |
| come sturare lavandino | 2400 | 15 | I | manutenzione fai-da-te | DA CREARE: blog post | 3 | Alto volume, porta traffico TOFU |
| miglior idraulico zona 3 milano | 110 | 18 | C | zona milano | /zona-3-milano/ | 2 | Gap vs competitor |

---

## Tab 2 — Cluster Tematici

Vista aggregata per pillar topic e cluster.

| Colonna | Tipo | Descrizione |
|---------|------|-------------|
| pillar | testo | Nome del pillar topic (macro-argomento) |
| cluster | testo | Nome del cluster (sotto-argomento) |
| keyword_correlate | testo | Lista keyword del cluster separate da virgola |
| pagina_pillar | testo | URL o titolo della pagina pillar |
| pagine_cluster | testo | URL o titoli delle pagine cluster (separate da virgola) |
| volume_totale_cluster | numero | Somma dei volumi di tutte le keyword del cluster |

**Ordinamento**: per pillar (alfabetico), poi per volume_totale_cluster (decrescente).

**Esempio riga:**

| pillar | cluster | keyword_correlate | pagina_pillar | pagine_cluster | volume_totale_cluster |
|--------|---------|-------------------|---------------|----------------|----------------------|
| Pronto intervento | Emergenze idrauliche | idraulico urgente milano, pronto intervento idraulico, idraulico 24 ore milano, emergenza acqua | /servizi/pronto-intervento/ | /pronto-intervento/perdite/, /pronto-intervento/allagamento/ | 1850 |
| Manutenzione caldaie | Caldaie a condensazione | caldaia condensazione milano, sostituzione caldaia, installazione caldaia condensazione | /servizi/caldaie/ | /caldaie/condensazione/, /caldaie/manutenzione-annuale/ | 980 |

---

## Tab 3 — Competitor Gap

Matrice comparativa: per ogni keyword, posizione del cliente vs competitor.

| Colonna | Tipo | Descrizione |
|---------|------|-------------|
| keyword | testo | La keyword analizzata |
| volume | numero | Volume di ricerca mensile |
| intent | testo (I/N/C/T) | Intent primario |
| tuo_sito_posizione | numero o testo | Posizione in SERP (1-100) o "assente" |
| competitor_1_posizione | numero o testo | Posizione competitor 1 o "assente" |
| competitor_2_posizione | numero o testo | Posizione competitor 2 o "assente" |
| competitor_3_posizione | numero o testo | Posizione competitor 3 o "assente" |
| opportunita | testo (si/no) | "si" se almeno un competitor e presente e il cliente e assente o in posizione peggiore |

**Nota**: le colonne competitor si adattano al numero di competitor forniti (1-3). I nomi dei competitor vanno usati come intestazione colonna.

**Ordinamento**: opportunita "si" prima, poi per volume (decrescente).

**Formattazione condizionale suggerita:**
- Posizione 1-3: sfondo verde scuro, testo bianco
- Posizione 4-10: sfondo verde chiaro
- Posizione 11-20: sfondo giallo
- Posizione 21-50: sfondo arancione
- Posizione 51-100: sfondo rosso chiaro
- "assente": sfondo rosso, testo bianco

**Esempio riga:**

| keyword | volume | intent | tuo_sito_posizione | idraulicobianchi.it | termoidraulicaverdi.it | opportunita |
|---------|--------|--------|-------------------|--------------------|-----------------------|-------------|
| idraulico urgente zona 3 | 210 | T | assente | 3 | 7 | si |
| riparazione caldaia milano | 480 | T | 18 | 5 | 2 | si |
| pronto intervento idraulico | 1200 | T | 8 | 6 | 4 | si |

---

## Tab 4 — Piano Assegnazione

Mappa operativa: quale keyword va su quale pagina, con stato e azioni.

| Colonna | Tipo | Descrizione |
|---------|------|-------------|
| pagina | testo | URL della pagina (esistente) o titolo proposto (da creare) |
| keyword_primaria | testo | La keyword primaria per cui ottimizzare la pagina |
| keyword_secondarie | testo | 2-5 keyword secondarie separate da virgola |
| intent | testo (I/N/C/T) | Intent delle keyword assegnate |
| stato | testo | "esistente" / "da creare" / "da ottimizzare" |
| priorita | numero (1-5) | Priorita di intervento |

**Ordinamento**: per priorita (1 prima), poi per stato ("da ottimizzare" prima di "da creare").

**Formattazione condizionale suggerita:**
- Stato "da ottimizzare": sfondo giallo (intervento su pagina esistente, sforzo medio)
- Stato "da creare": sfondo arancione (pagina nuova, sforzo alto)
- Stato "esistente": sfondo verde (pagina gia ok, verificare periodicamente)

**Esempio riga:**

| pagina | keyword_primaria | keyword_secondarie | intent | stato | priorita |
|--------|-----------------|-------------------|--------|-------|----------|
| /pronto-intervento/ | idraulico urgente milano | pronto intervento idraulico milano, idraulico emergenza milano, idraulico 24 ore | T | da ottimizzare | 1 |
| DA CREARE: Blog post | come sturare il lavandino | sturare lavandino rimedi, lavandino intasato cosa fare, sturare scarico cucina | I | da creare | 3 |
| /servizi/caldaie/ | installazione caldaia milano | sostituzione caldaia milano, caldaia condensazione prezzo, cambio caldaia | T | da ottimizzare | 1 |

---

## Note operative per la generazione XLSX

- Usare la skill `xlsx` per generare il file
- Ogni tab deve avere intestazioni in grassetto con filtri automatici attivati
- Larghezza colonne auto-fit al contenuto
- Congelare la prima riga (intestazioni) in ogni tab
- Applicare formattazione condizionale come descritto sopra
- Aggiungere un commento in cella A1 di ogni tab con la data di generazione
- Nome file suggerito: `keyword-map-[dominio]-[data].xlsx`
