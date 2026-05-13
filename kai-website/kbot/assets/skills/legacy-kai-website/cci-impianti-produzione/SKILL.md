---
name: cci-impianti-produzione
description: >-
  CCI (Corrispettivo per la Capacità di Interrompibilità) per impianti FV ed
  eolici MT: delibera ARERA 385/2025/R/eel, RIGEDI, obbligo interrompibilità,
  soglie potenza, modulistica GSE, calcolo corrispettivo, adempimenti.
---

# CCI — Impianti FV ed Eolici MT

## Cos'è il CCI

Il **Corrispettivo per la Capacità di Interrompibilità (CCI)** è un incentivo riconosciuto agli impianti di produzione da fonti rinnovabili che si rendono disponibili a ridurre/interrompere la produzione su richiesta di Terna (TSO italiano) per esigenze di bilanciamento della rete.

**Base normativa**: Delibera ARERA 385/2025/R/eel (aggiornamento 2025) e Codice di Rete Terna (RIGEDI — Regolamento per l'Interrompibilità Graduale della produzione Eolica e fotovoltaica per i servizi DI bilanciamento).

## Chi è soggetto all'obbligo

Impianti FV e eolici connessi in **Media Tensione (MT)** con:
- **Potenza installata ≥ 200 kW** per FV
- **Potenza installata ≥ 100 kW** per eolico

**Attenzione**: soglie riviste con delibera 385/2025 (precedentemente 100 kW per FV). Verificare versione normativa vigente.

## Come funziona il meccanismo

```
1. Terna invia segnale di interrompibilità (RIGEDI) via telecontrollo
2. Impianto riduce produzione entro il tempo risposta previsto (tipico 5 min)
3. Riduzione mantenuta per durata segnale
4. Terna registra riduzione effettiva e attiva pagamento CCI
5. Produttore riceve corrispettivo mensile sul conto energy
```

## Requisiti tecnici impianto

Per accedere al CCI l'impianto deve avere:
- **Sistema di telecontrollo** compatibile con protocollo Terna (IEC 61850 o conforme)
- **Interfaccia di rete** abilitata alla ricezione segnali RIGEDI
- **Misure di produzione** certificate con contatore AMM classe B
- **Piano di messa in servizio** aggiornato con funzionalità interrompibilità

## Calcolo corrispettivo CCI

```
CCI annuo = C_u × P_disp × h_disponibilità

C_u = corrispettivo unitario (€/MW/ora) fissato da ARERA (aggiornato annualmente)
P_disp = potenza resa disponibile per interrompibilità (MW)
h_disponibilità = ore di disponibilità dichiarate (tipico 8.760 ore/anno per impianti FV)

Esempio (valori indicativi):
P_disp = 0.5 MW
C_u = 15.000 €/MW/anno (verifica valore ARERA aggiornato)
CCI = 0.5 × 15.000 = 7.500 €/anno
```

**Nota**: i valori C_u variano con ogni delibera ARERA. Sempre verificare l'atto deliberativo più recente.

## Procedura di accesso

```
1. Verifica requisiti tecnici impianto
2. Adeguamento telecontrollo (se necessario)
3. Presentazione domanda su portale GSE con:
   - Documentazione tecnica impianto
   - Schema elettrico con sistema telecontrollo
   - Dichiarazione conformità RIGEDI
4. GSE/Terna effettua verifiche tecniche
5. Abilitazione impianto al CCI
6. Firma contratto con Terna
7. Attivazione corrispettivo mensile
```

## Interazione con altri incentivi

| Incentivo | Compatibilità CCI |
|-----------|-------------------|
| Conto Energia (vecchie tariffe) | Verificare singolo decreto |
| FER1/FER2 incentivi | ✓ Compatibile |
| Ritiro dedicato (RD) | ✓ Compatibile |
| Scambio sul posto (SSP) | Solo per impianti in autoconsumo |
| Transizione 5.0 (se abbinato a BESS) | ✓ |

## Adempimenti annuali

- **Dichiarazione disponibilità**: comunicazione annuale a Terna della potenza disponibile
- **Test di interrompibilità**: verifica funzionale periodica (frequenza da RIGEDI)
- **Manutenzione telecontrollo**: attestazione funzionamento sistema
- **Rendicontazione GSE**: dati produzione/interrompibilità per liquidazione CCI

## Segnali RIGEDI — struttura

Il segnale RIGEDI trasmesso da Terna contiene:
- Setpoint di potenza (valore assoluto in kW o % della potenza nominale)
- Rampa di discesa (gradiente MW/min)
- Durata prevista riduzione
- Tipo segnale (graduale vs emergenza)

L'impianto deve rispondere entro 5 minuti per segnali graduali, 1 minuto per emergenza.
