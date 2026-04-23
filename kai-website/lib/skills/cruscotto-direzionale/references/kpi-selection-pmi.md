# Selezione KPI per PMI — Balanced Scorecard adattata (5-50 dipendenti)

## 1. Prospettiva Finanziaria

### 1.1 Fatturato mensile
- **Formula:** Somma ricavi netti del mese (escluse note di credito)
- **Frequenza raccolta:** Mensile
- **Fonte dati tipica PMI:** Registro fatture emesse, gestionale contabile, foglio Excel fatture
- **Target indicativo:** Budget mensile oppure fatturato stesso mese anno precedente + inflazione + crescita attesa
- **Confronti:** vs budget, vs mese precedente, vs stesso mese anno prima

### 1.2 EBITDA mensile
- **Formula:** Fatturato - Costi operativi (materie prime + personale + servizi + affitti + utenze) prima di ammortamenti, interessi e tasse
- **Frequenza raccolta:** Mensile
- **Fonte dati tipica PMI:** Conto economico gestionale mensile, somma costi da prima nota
- **Target indicativo:** 8-15% del fatturato per servizi, 5-10% per produzione (varia per settore)
- **Nota:** Per PMI senza contabilita gestionale mensile, calcolare come Fatturato - Costi diretti comunicati dal titolare

### 1.3 Cash flow operativo
- **Formula:** Incassi del mese - Pagamenti operativi del mese (esclusi investimenti e finanziamenti)
- **Frequenza raccolta:** Mensile
- **Fonte dati tipica PMI:** Estratto conto bancario, registro incassi/pagamenti
- **Target indicativo:** Positivo. Rapporto cash flow/fatturato > 5%
- **Alert critico:** Cash flow negativo per 2+ mesi consecutivi

### 1.4 Giorni medi incasso (DSO)
- **Formula:** (Crediti commerciali a fine mese / Fatturato mese) x 30
- **Frequenza raccolta:** Mensile
- **Fonte dati tipica PMI:** Scadenzario clienti, partitario clienti
- **Target indicativo:** < 60 giorni (media Italia PMI: 67 giorni). Ottimo < 45 giorni
- **Nota:** Indicatore critico per la sopravvivenza della PMI. Il fatturato non conta se non incassi.

### 1.5 Posizione di cassa
- **Formula:** Saldo conti correnti + cassa a fine mese
- **Frequenza raccolta:** Mensile (idealmente settimanale)
- **Fonte dati tipica PMI:** Estratti conto bancari
- **Target indicativo:** >= 2 mesi di costi fissi come buffer minimo
- **Alert critico:** Posizione < 1 mese di costi fissi

---

## 2. Prospettiva Cliente

### 2.1 Numero clienti attivi
- **Formula:** Clienti con almeno una fattura negli ultimi 3 mesi (o 6 mesi per settori con cicli lunghi)
- **Frequenza raccolta:** Mensile
- **Fonte dati tipica PMI:** Anagrafica clienti, CRM, registro fatture
- **Target indicativo:** Stabile o in crescita vs trimestre precedente

### 2.2 Nuovi clienti mese
- **Formula:** Clienti che hanno ricevuto la prima fattura nel mese corrente
- **Frequenza raccolta:** Mensile
- **Fonte dati tipica PMI:** CRM, registro nuove anagrafiche clienti
- **Target indicativo:** Dipende dal settore. Per B2B servizi: 1-3 nuovi/mese. Per B2C retail: analizzare in % sul totale

### 2.3 Clienti persi (churn)
- **Formula:** Clienti attivi nel trimestre precedente che non hanno generato fatturato nel trimestre corrente
- **Frequenza raccolta:** Mensile (calcolo rolling 3 mesi)
- **Fonte dati tipica PMI:** Confronto anagrafica clienti attivi periodo su periodo
- **Target indicativo:** Tasso churn annuale < 10% per B2B, < 20% per B2C
- **Alert:** Churn in aumento per 3 mesi consecutivi

### 2.4 Fatturato medio per cliente
- **Formula:** Fatturato totale mese / Numero clienti attivi
- **Frequenza raccolta:** Mensile
- **Fonte dati tipica PMI:** Derivato da fatturato e numero clienti
- **Target indicativo:** Stabile o in crescita. Diminuzione puo indicare downgrade o perdita clienti premium

### 2.5 NPS o Soddisfazione (se misurato)
- **Formula:** Net Promoter Score = % Promotori (9-10) - % Detrattori (0-6) su scala 0-10
- **Frequenza raccolta:** Trimestrale o semestrale
- **Fonte dati tipica PMI:** Survey clienti (anche semplice email/Google Form)
- **Target indicativo:** NPS > 30 buono, > 50 eccellente
- **Nota:** Molte PMI non lo misurano. Suggerire implementazione graduale.

### 2.6 Concentrazione fatturato top 5 clienti
- **Formula:** (Fatturato top 5 clienti / Fatturato totale) x 100
- **Frequenza raccolta:** Mensile
- **Fonte dati tipica PMI:** Classifica clienti per fatturato
- **Target indicativo:** < 30% ottimo, 30-50% accettabile, > 50% rischio alto
- **Alert critico:** Top 3 clienti > 40% = rischio concentrazione elevato

---

## 3. Prospettiva Processi Interni

### 3.1 Ore fatturabili / Ore totali (per aziende di servizi)
- **Formula:** (Ore direttamente fatturate a clienti / Ore totali lavorate) x 100
- **Frequenza raccolta:** Mensile
- **Fonte dati tipica PMI:** Timesheet, registro presenze, fogli ore
- **Target indicativo:** 65-75% per consulenza, 70-80% per studi professionali
- **Nota:** Sotto il 60% l'azienda brucia margine su attivita non remunerative

### 3.2 Tasso scarti / resi (per aziende di produzione)
- **Formula:** (Pezzi scartati o resi / Pezzi prodotti totali) x 100
- **Frequenza raccolta:** Mensile
- **Fonte dati tipica PMI:** Report produzione, registro resi, gestionale magazzino
- **Target indicativo:** < 2% ottimo, 2-5% accettabile, > 5% critico
- **Nota:** Include sia scarti interni che resi da cliente

### 3.3 Lead time medio
- **Formula:** Giorni medi dall'ordine alla consegna (o dall'incarico al deliverable per servizi)
- **Frequenza raccolta:** Mensile
- **Fonte dati tipica PMI:** Registro ordini con date, gestionale commesse
- **Target indicativo:** Varia per settore. L'obiettivo e stabilita e riduzione progressiva

### 3.4 Reclami ricevuti
- **Formula:** Numero reclami formali e informali ricevuti nel mese
- **Frequenza raccolta:** Mensile
- **Fonte dati tipica PMI:** Email, registro reclami, segnalazioni agenti
- **Target indicativo:** 0 e l'ideale. Tasso reclami/ordini < 1%
- **Nota:** Contare anche i reclami informali (telefonate di lamentela). Sono segnali importanti.

### 3.5 Tempo medio evasione ordine
- **Formula:** Giorni medi dalla conferma ordine alla spedizione/consegna
- **Frequenza raccolta:** Mensile
- **Fonte dati tipica PMI:** Registro ordini/spedizioni, DDT
- **Target indicativo:** Dipende dal settore. Monitorare la stabilita e il trend

---

## 4. Prospettiva Crescita e Apprendimento

### 4.1 Ore formazione
- **Formula:** Ore totali di formazione erogate nel mese (interna + esterna)
- **Frequenza raccolta:** Mensile
- **Fonte dati tipica PMI:** Registro formazione, fatture enti formazione, ore dedicate
- **Target indicativo:** >= 8 ore/dipendente/anno = circa 0.7 ore/dipendente/mese
- **Nota:** Include formazione informale, affiancamento, aggiornamento tecnico

### 4.2 Nuovi prodotti/servizi lanciati
- **Formula:** Numero di nuovi prodotti, servizi o varianti introdotti nel periodo
- **Frequenza raccolta:** Trimestrale (riportato mensilmente come progress)
- **Fonte dati tipica PMI:** Catalogo prodotti, comunicazioni commerciali
- **Target indicativo:** Almeno 1-2 novita/anno per PMI. Dipende dal settore

### 4.3 Investimenti in innovazione
- **Formula:** Spese per R&D, digitalizzazione, nuove tecnologie nel mese
- **Frequenza raccolta:** Mensile
- **Fonte dati tipica PMI:** Fatture fornitori IT/consulenza, acquisti macchinari
- **Target indicativo:** 2-5% del fatturato annuo (ripartito mensilmente)

### 4.4 Turnover dipendenti
- **Formula:** (Dipendenti usciti nel periodo / Organico medio) x 100
- **Frequenza raccolta:** Mensile (analisi rolling 12 mesi)
- **Fonte dati tipica PMI:** Ufficio personale, cedolini, comunicazioni obbligatorie
- **Target indicativo:** < 10% annuo buono, 10-15% nella media, > 15% critico
- **Nota:** Per PMI con 5-10 dipendenti, anche 1 uscita impatta. Monitorare in valore assoluto oltre che in %.

---

## Come scegliere i 10-12 KPI rilevanti

Non tutti i KPI servono a tutte le aziende. La selezione dipende da:

### Per settore

| Settore | KPI prioritari (oltre ai finanziari base) |
|---|---|
| **Servizi professionali** (consulenza, studi) | Ore fatturabili/totali, Fatturato medio/cliente, Lead time, Ore formazione |
| **Produzione/manifattura** | Tasso scarti, Tempo evasione ordine, Reclami, Lead time |
| **Commercio** | Clienti attivi, Nuovi clienti, Churn, Concentrazione fatturato |
| **Edilizia/impiantistica** | Lead time, Reclami, Cash flow (ciclicita), GG medi incasso |
| **Ristorazione/hospitality** | Clienti attivi, Fatturato medio/cliente, Reclami, Turnover |
| **Tech/digitale** | Nuovi clienti, Churn, Investimenti innovazione, Nuovi prodotti |

### Regola pratica di selezione

1. **Sempre presenti (5 KPI fissi):** Fatturato, EBITDA, Cash flow, GG medi incasso, Posizione cassa
2. **Scegliere 2-3 KPI Cliente** in base al modello di business (B2B vs B2C, pochi clienti grandi vs tanti piccoli)
3. **Scegliere 2-3 KPI Processi** in base al tipo di attivita (servizi vs produzione)
4. **Scegliere 1-2 KPI Crescita** in base alla fase aziendale (startup vs matura)

### Revisione periodica
- **Trimestrale:** Verificare se i KPI scelti sono ancora significativi
- **Annuale:** Revisione completa con possibile sostituzione di 1-2 KPI

---

## KPI "sentinella" — I 3-4 indicatori che da soli raccontano lo stato dell'azienda

Per il titolare che ha davvero solo 2 minuti, questi indicatori sintetizzano tutto:

1. **Posizione di cassa** — L'azienda e viva? Ha risorse per andare avanti?
2. **EBITDA mensile** — L'azienda guadagna o perde? Il modello di business funziona?
3. **Giorni medi incasso (DSO)** — L'azienda incassa? Il fatturato si trasforma in liquidita?
4. **Numero clienti attivi** (o churn) — La base clienti e stabile? Il futuro e a rischio?

Questi 4 KPI devono essere i piu visibili nella dashboard (riga top con card grandi) e i primi di cui si parla nell'executive summary.

Se anche uno solo di questi e rosso, l'azienda ha un problema serio che richiede attenzione immediata.
