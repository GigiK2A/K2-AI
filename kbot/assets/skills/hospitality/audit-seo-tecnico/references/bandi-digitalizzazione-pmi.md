# Mapping problemi SEO/web → bandi italiani applicabili

Tabella di riferimento per la sezione Bridge Agevolazioni dell'audit. Ogni problema diagnosticato (impatto >30%) viene mappato a strumenti di finanza agevolata applicabili.

## Matrice problema → bando

| Problema SEO/web | Tipo intervento | Bandi applicabili (priorita) |
|---|---|---|
| Sito lento, Core Web Vitals scarsi | Refactoring tecnico, hosting, CDN | Voucher PNRR Digitalizzazione · Punto Impresa Digitale · Sabatini (hardware) |
| Sito non responsive / mobile-first | Redesign mobile-first | Voucher PNRR · Bonus Pubblicita (se include landing) |
| No HTTPS / sicurezza scarsa | SSL, hardening | Voucher PNRR · Punto Impresa Digitale |
| Schema markup assente | Sviluppo custom | Credito R&S/Innovazione (se algoritmico) |
| Sito da rifare ex-novo | Sviluppo CMS + design | Voucher PNRR (max 70%) · Sabatini (parte SW) · Transizione 5.0 (se sostenibile) |
| GBP non gestito, scarse recensioni | Local SEO + reputation mgmt | Bonus Pubblicita · Voucher Camera di Commercio |
| NAP inconsistente su directory | Citation cleanup | Voucher camerali Punto Impresa Digitale |
| Contenuti obsoleti / thin content | Content production | Bonus Pubblicita (se incrementale) · Content marketing in PNRR |
| No e-commerce / piattaforma vendita | Sviluppo e-commerce | Voucher PNRR Export · Sabatini · Transizione 5.0 |
| Marketing automation assente | CRM + tooling | Credito R&S Innovazione · Voucher PNRR |
| App mobile / web app custom | Sviluppo software | Credito R&S/Innovazione · Sabatini · Transizione 5.0 |

## Bandi: schede sintetiche

### Voucher PNRR Digitalizzazione PMI (regionale)
- **Copertura**: 50-70% spese ammissibili
- **Tetto**: 5.000-50.000 EUR a seconda della regione
- **Beneficiari**: PMI 10-249 dipendenti
- **Spese ammissibili**: hardware, software, consulenza, formazione digitale
- **De minimis**: si

### Bonus Pubblicita
- **Copertura**: 75% sull'investimento incrementale
- **Beneficiari**: imprese e lavoratori autonomi
- **Spese ammissibili**: campagne stampa/online (Google Ads, Meta), purche incrementali rispetto anno precedente
- **Soglia minima**: 1% incremento rispetto anno precedente
- **Tetto**: budget annuo nazionale ripartito proporzionalmente

### Credito d'imposta R&S/Innovazione (ex Industria 4.0)
- **Copertura**: 10-25% delle spese (varia per tipo)
- **Beneficiari**: tutte le imprese
- **Spese ammissibili**: sviluppo algoritmi, software custom, sperimentazione
- **Limite**: tetti annuali per tipologia
- **Cumulabile**: con altri incentivi (de minimis a parte)

### Nuova Sabatini
- **Copertura**: contributo in conto interessi su finanziamento bancario
- **Beneficiari**: PMI
- **Spese ammissibili**: investimenti in hardware, software, beni strumentali
- **Importo**: 20.000-4.000.000 EUR di investimento
- **Maggiorazione**: +30% se 4.0/green

### Transizione 5.0
- **Copertura**: 35-45% (variabile per fasce risparmio energetico)
- **Beneficiari**: tutte le imprese
- **Spese ammissibili**: digitalizzazione + risparmio energetico documentato
- **Limite**: 50 mln EUR per progetto
- **Vincolo**: deve dimostrare riduzione consumi >= 3%

### Voucher camerali Punto Impresa Digitale (PID)
- **Copertura**: 50-70% (varia per camera)
- **Tetto**: 5.000-15.000 EUR
- **Beneficiari**: imprese iscritte alla camera
- **Spese ammissibili**: consulenza digitale, sviluppo presenza online

## Procedura di applicazione nell'audit

1. Per ogni problema con impatto > 30%, stima il **costo intervento** (ricerca benchmark + range)
2. Identifica il **bando piu pertinente** dalla matrice sopra
3. Verifica **finestra apertura** corrente (le scadenze cambiano: invoca `matching-bandi-agevolazioni` per dati real-time)
4. Calcola **quota finanziabile** = costo intervento × % copertura, capped al tetto del bando
5. Verifica **plafond de minimis residuo** del cliente (skill `calcolo-de-minimis`) se applicabile
6. Stima conservativa nel report (usa lower bound)

## Tabella output report

Esempio formato finale per la sezione Bridge Agevolazioni:

| Problema | Intervento | Costo stimato | Bando | % | Finanziabile | Note |
|---|---|---|---|---|---|---|
| LCP > 4s | Migrazione hosting + CDN + WebP | 4.500 EUR | Voucher PNRR Lombardia | 50% | 2.250 EUR | Apertura sett 2026 |
| No schema LocalBusiness | Sviluppo schema + microdata | 1.200 EUR | PID camera Milano | 70% | 840 EUR | Sempre aperto |
| GBP non gestito | Setup + 6 mesi gestione | 2.400 EUR | Bonus Pubblicita | 75% (incr.) | 1.800 EUR | Solo se incrementale |
| **TOTALE** |  | **8.100 EUR** |  |  | **4.890 EUR** | **60% recuperato** |

Il numero "TOTALE finanziabile" e la metrica forte per l'executive summary del titolare.
