# Framework AdvisorBoost — quadro metodologico

Questo documento codifica i framework analitici applicati in sequenza da AdvisorBoost. Va letto come supporto di `SKILL.md`, non come istruzione operativa autonoma.

## Principio guida

AdvisorBoost non e "fare tutto". E scegliere **cosa guardare**, **in quale ordine**, e **come connettere** i livelli (finanziario ↔ strategico ↔ operativo). Il valore della skill e proprio il ponte tra i tre livelli, che raramente e fatto bene dai consulenti single-track.

## Architettura a 3 livelli

```
Livello 1 — FINANZA
  Bilancio 3 anni, indici, rendiconto, proiezione 36 mesi, enterprise value
      |
      v
Livello 2 — STRATEGIA
  Settore (5 forze), posizionamento (VRIO, catena valore), opzioni (Ansoff)
      |
      v
Livello 3 — OPERATIVITA
  5-8 azioni prioritarie, milestones, KPI mensili, responsabilita, costi
```

Ogni livello rimanda all'altro:
- La finanza da i **vincoli** (quanto posso investire, quanto produce margine).
- La strategia da il **dove andare** (quale posizionamento, quale mercato).
- L'operativita da il **come e quando** (chi fa cosa, entro quando, con quale budget).

## Livello 1 — Framework finanziari

### Riclassificazione obbligatoria
- **SP a liquidita/esigibilita**: attivo ordinato per liquidita crescente, passivo per esigibilita crescente. Output: CCN operativo, capitale investito netto, PFN.
- **SP funzionale**: attivo per destinazione (caratteristico/patrimoniale/finanziario). Output: ROI, ROS, rotazione attivo.
- **CE a valore aggiunto**: valore della produzione - consumi esterni - costi del lavoro - ammortamenti = EBIT. Output: EBITDA, EBITDA margin.
- **CE a costo del venduto**: solo per aziende con magazzino rilevante. Output: margine lordo, gross margin %.

### Indici minimi da calcolare (25)
1. ROE = Utile netto / PN medio
2. ROI = EBIT / Capitale investito
3. ROS = EBIT / Ricavi
4. ROA = Utile netto / Totale attivo
5. Rotazione capitale investito = Ricavi / CI
6. Leverage = CI / PN
7. Spread = ROI - i (costo medio debito)
8. D/E = Debiti finanziari / PN
9. PFN/EBITDA
10. Copertura oneri finanziari = EBIT / OF
11. Quoziente di struttura = PN / Immobilizzazioni
12. Copertura immobilizzazioni = (PN + Passivita consolidate) / Immobilizzazioni
13. Current ratio = Attivo corrente / Passivo corrente
14. Quick ratio = (Attivo corrente - Magazzino) / Passivo corrente
15. Giorni clienti = (Crediti commerciali / Ricavi) × 365
16. Giorni fornitori = (Debiti commerciali / Costi) × 365
17. Giorni magazzino = (Magazzino / Costo venduto) × 365
18. CCC = Giorni clienti + Giorni magazzino - Giorni fornitori
19. Incidenza OF = OF / Ricavi
20. Tax rate effettivo = Imposte / Utile lordo
21. Self-financing = Utile netto + Ammortamenti - Dividendi
22. Capex / Ammortamenti (intensita investimenti)
23. Working capital / Ricavi
24. CAGR fatturato 3 anni
25. CAGR EBITDA 3 anni

### Alert CCII (Codice della Crisi d'Impresa e Insolvenza)
Segnalare come **rosso** se:
- Patrimonio netto < 0 oppure < 1/3 del capitale sociale versato.
- DSCR prospettico 12 mesi < 1.
- Ritardi superiori a 90 giorni nel pagamento di retribuzioni o fornitori abituali.
- PFN / EBITDA > 6.
- Capitale circolante netto < 0 persistente.

Se 2+ alert: inserire paragrafo esplicito "Soglie allerta CCII attive — valutare consulenza di composizione negoziata".

### Enterprise value
Triangolare 3 metodi:
1. **Multipli EBITDA**: benchmark settoriale da `benchmark-italia-business` (tipicamente 4x-7x per PMI italiane settore industriale/servizi).
2. **DCF unlevered**: proiezione FCFF 5 anni + terminal value con g perpetuo (1.5-2%) + WACC (tipicamente 8-11% per PMI italiane).
3. **Patrimoniale rettificato**: PN contabile + rivalutazione immobili + avviamento stimato.

Valore raccomandato: mediana dei 3. Se spread tra metodi > 30% discutere ragioni (bilancio sottostimato? multiplo gonfiato? capex intensivi non riflessi?).

## Livello 2 — Framework strategici

### Porter 5 forze (scoring 1-5)
| Forza | Variabili da valutare |
|---|---|
| Rivalita interna | Numero competitor, concentrazione, crescita settore, differenziazione, costi uscita |
| Minaccia entranti | Barriere ingresso (capitali, economie scala, brand, switching), ritorsione attesa |
| Minaccia sostituti | Rapporto prezzo/prestazione sostituti, propensione switch |
| Potere fornitori | Concentrazione, switching cost, minaccia integrazione avanti |
| Potere clienti | Concentrazione, info disponibili, switching cost, minaccia integrazione indietro |

Score: 1 (debole) - 5 (fortissima). Attrattivita settore = 20 - somma scores. 

### VRIO
Per ogni risorsa/competenza:
- **Valore**: crea valore per il cliente? si/no
- **Rarita**: la posseggono pochi competitor? si/no
- **Inimitabilita**: difficile da copiare (storia, complessita sociale, ambiguita causale)? si/no
- **Organizzazione**: l'azienda e organizzata per sfruttarla? si/no

Output tipi:
- VRIO tutti si → vantaggio competitivo sostenibile
- V + R + I ma no O → vantaggio inutilizzato (potenziale)
- V + R, no I → vantaggio temporaneo
- Solo V → parita competitiva
- No V → svantaggio

### Ansoff 2×2 per opzioni crescita
|  | Mercati esistenti | Mercati nuovi |
|---|---|---|
| Prodotti esistenti | Penetrazione | Sviluppo mercato |
| Prodotti nuovi | Sviluppo prodotto | Diversificazione |

Per PMI italiane privilegiare penetrazione e sviluppo prodotto (rischio contenuto). Diversificazione solo con risorse solide e core competencies trasferibili.

### Make / Buy / Ally
Per ogni opzione strategica, valutare:
- Risorse interne sufficienti e tempi compatibili → **Make**
- Risorse non replicabili o tempi urgenti → **Buy** (acquisizione mirata)
- Sinergie con partner esistente, rischio basso → **Ally** (alleanza, JV, rete d'impresa)

## Livello 3 — Framework operativi

### Selezione azioni prioritarie
Filtro a 3 criteri:
1. **Impatto EBITDA o fatturato** stimato 12-24 mesi: > 5% per essere considerata.
2. **Fattibilita**: risorse e competenze presenti o acquisibili entro 6 mesi.
3. **Rischio**: irreversibilita limitata, opzioni di exit.

Scoring combinato: `Priorita = (Impatto × Fattibilita) / Rischio`.

### Struttura azione
Ogni azione deve contenere:
- Titolo imperativo (es: "Riposizionare listino categoria B").
- Descrizione 2-3 righe.
- KPI di successo (es: "Margine categoria B da 18% a 24% entro 12 mesi").
- Milestone 30-60-90 giorni.
- Budget una tantum e ricorrente.
- Responsabile interno + eventuale consulente/fornitore esterno.
- Rischi principali e mitigazione.

### Cruscotto KPI mensile (consigliato per retainer)
10 KPI mensili con target e semaforo:
1. Fatturato mese vs target
2. EBITDA mese vs target
3. Ordini acquisiti
4. Pipeline commerciale
5. DSO (giorni incasso medio)
6. DPO (giorni pagamento medio)
7. Rotazione magazzino
8. Nuovi clienti acquisiti
9. Tasso di fidelizzazione (retention)
10. KPI specifico settore (es: ore fatturate per studio professionale, tasso riempimento per ricettivo)

## Regole di sintesi executive

L'executive summary deve rispondere a 3 domande, in questo ordine:
1. **Stiamo sopravvivendo?** (diagnosi finanziaria + allerta CCII)
2. **Abbiamo un vantaggio competitivo?** (VRIO + quote di mercato + benchmark)
3. **Dove andiamo nei prossimi 36 mesi?** (Ansoff + azioni prioritarie + scenario economico)

Se la risposta alla 1 e "marginalmente" o "no", le domande 2 e 3 passano in secondo piano e si raccomanda turnaround prima di sviluppo.

## Relazione con il commercialista

AdvisorBoost non sostituisce il commercialista ma lo integra. Delineare nell'executive:
- "Il tuo commercialista tiene la contabilita e gli adempimenti fiscali. Noi ti diamo la chiave di lettura strategica."
- "Le voci di bilancio qui analizzate sono quelle del tuo bilancio ufficiale firmato dal commercialista."
- "Per pianificazione fiscale avanzata (IRES anticipata, ACE, bonus R&S) coinvolgi il tuo commercialista insieme a noi."

## Disclaimer standard

Ogni deliverable deve contenere:
> "La presente analisi strategico-finanziaria costituisce supporto decisionale per l'imprenditore. Non rappresenta servizio di revisione legale dei conti, attestazione o consulenza fiscale in senso tecnico. Le proiezioni economico-finanziarie sono stime basate sui dati forniti dal cliente e sulle ipotesi dichiarate; scostamenti rispetto alla realizzazione effettiva sono normali. K2-AI non garantisce rendimenti ne risultati specifici."
