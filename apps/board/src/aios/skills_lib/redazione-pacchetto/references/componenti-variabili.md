# Componenti Variabili — Ricerche Web Obbligatorie

Questo file elenca tutti i componenti del pacchetto autorizzativo che possono variare nel tempo e che devono essere verificati tramite ricerca web all'avvio di ogni sessione di redazione.

---

## 1. PEC Destinatari

### Roma Capitale

| Destinatario | Query di ricerca | Valore noto (fallback) |
|-------------|-----------------|----------------------|
| DPU — Dip. Programmazione e Attuazione Urbanistica | `"DPU Roma Capitale" PEC 2024 2025 2026` | protocollo.urbanistica@pec.comune.roma.it |
| SUAP Roma Capitale | `"SUAP Roma Capitale" PEC` | suap.roma@pec.comune.roma.it |
| Titolare Poteri Sostitutivi | `"poteri sostitutivi Roma Capitale" PEC telecomunicazioni` | — |
| Municipio [N] Roma | `"Municipio [N] Roma" PEC` | (varia per municipio) |
| ARPA Lazio — Sede Provinciale Roma | `"ARPA Lazio" "sede provinciale Roma" PEC` | protocollo.roma@pec.arpalazio.it |

### Comuni fuori Roma

| Destinatario | Query di ricerca |
|-------------|-----------------|
| SUAP del Comune | `"SUAP [nome comune]" PEC` oppure `"Comune di [nome]" SUAP PEC` |
| ARPA Lazio — Sede Provinciale competente | `"ARPA Lazio" "sede provinciale [provincia]" PEC` |

**Se la ricerca non restituisce risultati certi:** usare il valore di fallback e segnare: ⚠️ **PEC da verificare manualmente — ultimo aggiornamento noto: [data]**

---

## 2. Aggiornamenti Normativi

| Norma | Query di ricerca | Cosa cercare |
|-------|-----------------|-------------|
| Art. 45 D.Lgs. 259/2003 | `"art. 45" "D.Lgs. 259" modifica 2024 2025 2026` | Eventuali modifiche alla procedura SCIA telecomunicazioni |
| L. 214/2023 — limiti EM | `"legge 214/2023" "limiti elettromagnetici" DPCM attuativo` | Nuovi DPCM che modificano i limiti di 6 V/m → eventuale innalzamento |
| D.M. 2/12/2014 — α24h | `"decreto 2 dicembre 2014" alpha24h modifica aggiornamento` | Eventuali modifiche alle linee guida sul coefficiente α24h |
| DPCM 8/7/2003 — limiti esposizione | `"DPCM 8 luglio 2003" limiti esposizione modifica 2024 2025` | Aggiornamento dei limiti di esposizione (20 V/m, 6 V/m) |

**Se trovato aggiornamento:** segnalare all'utente e adeguare i riferimenti nei documenti.
**Se nessun aggiornamento trovato:** proseguire con i riferimenti normativi vigenti.

---

## 3. Tariffe ARPA Lazio

| Componente | Query di ricerca | Cosa cercare |
|-----------|-----------------|-------------|
| Tariffe art. 45 | `"ARPA Lazio" tariffe "art. 45" telecomunicazioni 2024 2025 2026` | Importo aggiornato per l'impegno al pagamento |
| Delibera tariffaria | `"ARPA Lazio" delibera tariffe pareri preventivi` | Nuova delibera che aggiorna le tariffe |

**Fallback:** usare il wording generico "tariffe vigenti ai sensi dell'art. 45" senza indicare un importo specifico.

---

## 4. PRG / PTPR del Sito

| Componente | Query / Strumento | Note |
|-----------|-------------------|------|
| PRG Roma — Tavole | `site:urbanistica.comune.roma.it PRG tavola [indirizzo]` oppure WebGIS Roma Capitale | Le tavole (3, 4, G1) sono divise in quadranti (es. 3_10, 3_11). Identificare il quadrante corretto dall'indirizzo |
| PTPR Lazio — Tavole | `site:regione.lazio.it PTPR tavola [comune]` oppure Geoportale Regione Lazio | Tavole A (sistemi), B (beni paesaggistici), C (beni culturali) |

**ATTENZIONE:** Non riutilizzare le tavole PRG di una preesistenza se il sito è in una zona diversa della città.

---

## 5. Validità Procura Iliad

| Componente | Valore attuale | Verifica |
|-----------|---------------|----------|
| Procuratore | Andrea Longari | Verificare se risultano nuove procure iliad |
| Data procura | 10/04/2024 | Verificare validità — segnalare se > 2 anni dalla data |
| Notaio | Dott. Luca Amato, Roma | — |
| Rep. | 63403/18598 | — |

Query: `"iliad italia" "procura speciale" "Andrea Longari" 2025 2026`

**Se la procura risulta scaduta o sostituita:** BLOCCARE la redazione e avvisare l'utente.

---

## 6. Nulla Osta Cellnex (solo siti in ospitalità)

| Componente | Query di ricerca | Note |
|-----------|-----------------|------|
| Formato NO Cellnex | `"Cellnex" "nulla osta" "ospitalità" modello 2024 2025` | Verificare se il formato del NO è cambiato |
| Referente Cellnex | Da preesistenza o utente | — |

---

## Gestione Risultati Incerti

Per ogni ricerca che non restituisce risultati certi o aggiornati:

1. Usare il **valore di fallback** (colonna "Valore noto")
2. Aggiungere il tag: `⚠️ verifica manuale consigliata`
3. Indicare: "Ultimo aggiornamento verificato: [data ricerca]"
4. Proseguire con la redazione senza bloccarsi

**NON bloccare mai la redazione** per una ricerca web infruttuosa — segnalare e proseguire.
