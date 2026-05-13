# Documenti Richiesti — Pacchetto Autorizzativo Iliad SCIA art. 45

## Elenco Documenti Obbligatori

| N. | Nome documento | Tipo file | Note |
|----|----------------|-----------|------|
| 1 | SCIA art. 45 | .docx / .pdf | Firmato digitalmente (p7m) nella cartella PROT |
| 2 | Delega alla presentazione | .docx / .pdf | Firma Andrea Longari + firma del tecnico incaricato |
| 3 | MISE-PROCURA (Procura Longari-Rossi) | .pdf | Documento fisso, Notaio Luca Amato 10/04/2024 Rep. n. 63403/18598 |
| 4 | RT — Relazione Tecnico Illustrativa | .docx / .pdf | |
| 5 | PDM — Piano di Misurazione | .pdf | Fornito da ARPA Lazio |
| 6 | ASSEVERAZIONI | .docx / .pdf | Più asseverazioni del tecnico incaricato |
| 7 | B40/RELAIE — Analisi Impatto Elettromagnetico | .docx / .pdf | Documento tecnico principale |
| 8 | Impegno al pagamento ARPA Roma | .doc / .pdf | |
| 9 | DICH. SOSTITUTIVA ALPHA24 | .docx / .pdf | Dichiarazione sostitutiva atto di notorietà |
| 10 | Atto d'obbligo | .docx / .pdf | |

## Documenti Condizionali

| N. | Nome documento | Quando richiesto |
|----|----------------|-----------------|
| 11 | Diagrammi Angolari | Se presenti studi direzionali o settori particolari |
| 12 | TX+MSI.rar | File dati antenne (pattern MSI) per simulazione EM |
| 13 | Nulla Osta Ospitalità / Assenso UPG Cellnex | Se il sito è su infrastruttura Cellnex (tower sharing) |
| — | FILETX.xlsx | File dati per software RELAIE — non oggetto di presentazione ma necessario per il B40 |

## Struttura Cartelle Attesa

```
[CODICE_SITO]_[NOME_SITO]/
├── COMUNE/                         ← Documenti editabili (.docx, .doc)
│   ├── 1.[CODICE]_[NOME]_Scia art. 45.docx
│   ├── 2.[CODICE]_[NOME]_Delega alla presentazione.docx
│   ├── 3.MISE-PROCURA-LONGARI-ROSSI.pdf
│   ├── 4.[CODICE]_[NOME]_RT.docx
│   ├── 5.[CODICE]_PDM_[DATA].pdf
│   ├── 6.[CODICE]_[NOME]_ASSEVERAZIONI.docx
│   ├── 7.[CODICE]_[NOME]_B40_RELAIE.docx
│   ├── 8.[CODICE]_[NOME]_Impegno al pagamento art. 45 singolo operatore_Arpa Roma.doc
│   ├── 9.[CODICE]_[NOME]_DICH. SOSTITUTIVA ALPHA24.docx
│   ├── 10.[CODICE]_[NOME]_Atto d'obbligo.docx
│   ├── [CODICE]_[NOME]_FILETX.xlsx
│   ├── PROT/                       ← Versioni firmate digitalmente (.pdf.p7m)
│   │   ├── 1.[...].pdf.p7m
│   │   └── ...
│   └── [CODICE]_msi/               ← File pattern antenne (.txt)
└── MSI/                            ← Alternativo per i file pattern antenne
```

## Destinatari per Comune di Roma (Municipio competente)

La SCIA va intestata a:
1. **Roma Capitale — DPU** (Dipartimento Programmazione Urbanistica, Ufficio SRB)
   - Viale della Civiltà del Lavoro, 10 — 00144 Roma
   - PEC: protocollo.programmazioneurbanistica@pec.comune.roma.it
2. **Roma Capitale — SUAP** (Direzione Sviluppo Economico)
   - Via dei Cerchi, 6 — 00186 Roma
   - PEC: protocollo.attivitaproduttive@pec.comune.roma.it
3. **Dott. Francesco Paciello** (Poteri sostitutivi SUAP)
   - PEC: potsostitutivi.attivitaproduttive@comune.roma.it
4. **Municipio competente** (variabile per sito — vedi tabella sotto)
   - Nota: inoltrato a cura del DPU
5. **ARPA Lazio** — Sede Provinciale di Roma, Area Agenti Fisici
   - Via Saredo, n. 52 — 00173 Roma
   - PEC: sedediroma@arpalazio.legalmailpa.it

### Tabella PEC Municipi di Roma

| Municipio | Indirizzo | PEC |
|-----------|-----------|-----|
| I | Piazza della Croce Rossa, 1 | protocollo.municipioroma1@pec.comune.roma.it |
| II | Via Dire Daua, 13 | protocollo.municipioroma2@pec.comune.roma.it |
| III | Via Duilio Cambellotti, 11 | protocollo.municipioroma3@pec.comune.roma.it |
| IV | Via Tiburtina, 1163 | protocollo.municipioroma4@pec.comune.roma.it |
| V | Via Ignazio Pettinengo, 50 | protocollo.municipioroma5@pec.comune.roma.it |
| VI | Via Duilio Cambellotti, 11 | protocollo.municipioroma6@pec.comune.roma.it |
| VII | Via Benedetto Croce, 60 | protocollo.municipioroma7@pec.comune.roma.it |
| VIII | Via Benedetto Croce, 60 | protocollo.municipioroma8@pec.comune.roma.it |
| IX | Via Carlo Avolio, 1 | protocollo.municipioroma9@pec.comune.roma.it |
| X | Via Claudio Allegrini, 25 | protocollo.municipioroma10@pec.comune.roma.it |
| XI | Via Fabiola, 14 | protocollo.municipioroma11@pec.comune.roma.it |
| XII | Via Fabiola, 14 | protocollo.municipioroma12@pec.comune.roma.it |
| XIII | Via della Pescaia, 1 | protocollo.municipioroma13@pec.comune.roma.it |
| XIV (ex XIX) | Piazza Santa Maria della Pietà, 5 | protocollo.municipioroma14@pec.comune.roma.it |
| XV | Via Flaminia, 872 | protocollo.municipioroma15@pec.comune.roma.it |

## Destinatari per Comuni della Provincia RM (fuori Roma Capitale)

La SCIA va intestata a:
1. **Comune [NOME]** con indirizzo e PEC del Comune specifico
2. **ARPA Lazio** — stessa sede di Roma

Nota: per i comuni fuori Roma non ci sono DPU, SUAP o Municipio. Il destinatario è il SUAP del comune specifico (se esistente) o l'Ufficio Tecnico comunale.

## Tecnici Incaricati K2A s.r.l.s.

| Tecnico | CF | Ordine | N. Iscrizione |
|---------|-----|--------|---------------|
| Ing. Luca Rossi | RSSLCU73A23H501U | Ordine Ingegneri Perugia | A2212 |
| Ing. Jessica Romanelli | RMNJSC87T50D653J | Ordine Ingegneri Perugia | A3537 |

Sede K2A s.r.l.s.: Via Alessandro Manzoni, n. 84 — Perugia (PG)

## Dati Fissi Iliad Italia S.p.A.

| Campo | Valore |
|-------|--------|
| Ragione sociale | ILIAD ITALIA S.p.A. a Socio Unico |
| Sede legale | Viale Francesco Restelli 1/A, Milano (MI) 20124 |
| CF e P. IVA | 13970161009 |
| REA | MI-2126511 |
| Procuratore speciale | Andrea Longari, nato a Roma il 27/04/1974 |
| Procura notarile | Notaio Luca Amato, Roma, 10/04/2024, Rep. n. 63403/18598 |
| Registrazione procura | Agenzia Entrate Roma 5, 10/04/2024, n. 3697 Serie 1T |
| PEC Iliad | svilupporete.iliaditalia@legalmail.it |
| Permit Coordinator | Arch. Antonella Tiroli — atiroli@it.iliad.com |
| Autorizzazione MISE | 25.07.2016 (MNO - Mobile Network Operator) |
