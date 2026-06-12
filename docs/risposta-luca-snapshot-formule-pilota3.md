# Per Luca — i 2 dati che chiedevi + go pilota-3

Tutto allineato sulla tua risposta. Endorso **pilota-3 adesso**. Ecco i dati.

## §1 — Snapshot canonico (committato nel repo)
```
snapshot_version : 1.0.0
generated_at     : 2026-06-07T09:25:53Z
coverage         : 55 / 57  (gap: revpar_zona, keyword_dataset — benchmark)
```
Confronta col tuo locale: se combacia → Fisco chiuso, nessun refresh (era falso-positivo sano, come dici). Se il tuo è più vecchio → ti allinei a questo.

## §6 — Formule calc-boost da validare (16)
Sono standard da manuale; la tua validazione dovrebbe essere una conferma rapida (eventuale golden-test numerico lato Code).

**Finance (9):**
```
ROE           = utile_netto / patrimonio_netto
ROI           = reddito_operativo / capitale_investito
ROS           = reddito_operativo / ricavi
EBITDA_margin = EBITDA / ricavi
current_ratio = attivo_corrente / passivo_corrente
quick_ratio   = (attivo_corrente - rimanenze) / passivo_corrente
D/E           = debiti_finanziari / patrimonio_netto
CCN           = attivo_corrente - passivo_corrente
CCC           = DSO + giorni_magazzino - DPO
```
**Control (5):**
```
EBITDA            = fatturato - costi_operativi
cashflow_operativo= incassi - pagamenti
DSO               = crediti / fatturato * giorni
churn             = clienti_persi / clienti_attivi_iniziali
scostamento_pct   = (valore - target) / target
```
**Advisor (2):**
```
WACC   = E/V*Ke + D/V*Kd*(1-t)
EV_DCF = somma(FCF_t / (1+WACC)^t) + TV
```
**Strategy**: confermo model-only (framework qualitativi). Vincolo accettato: se cita un numero di mercato, va groundato.

## Sui 6 punti — allineato su tutto
- (1) Build → aspetto RCA MCP + finding KB. Gate soft intanto.
- (2) benchmark → d'accordo sulla priorità: multipli_ev/benchmark_settore (Advisor/Finance) da fonte datata prima del loro paid; revpar/keyword → gap dichiarato, dopo.
- (3) Agevolazioni → fuori prima onda, architettura time-bound D-047. Concordo.
- (4) date CONSOLIDATED nel gate → quando me le dai per entry, le cablo (oggi il gate usa i marker testuali; aggiungo il confronto-data).
- (5) MCP fix → aspetto RCA.
- (6) formule → sopra.

## Conferme A/B — palla a Gigi
- (A) Prezzi pilota: servono i 3 → Legal __€ · Fisco __€ · Safety __€ (li decide Gigi; dal catalogo v1.0.0 se confermati).
- (B) Disclaimer → d'accordo con te: validazione di Gigi/avvocato, non auto-approvata. Requisiti minimi che indichi (AI-assisted, non sostitutivo di consulenza, verifica da professionista, norme alla data snapshot) li recepisco nel template.

## Go
**Pilota-3 parte appena Gigi conferma A (3 prezzi) + B (disclaimer).** Tutto il resto è parallelo e non blocca. Da me lato codice è pronto: manca solo l'URL 8e a deploy.
