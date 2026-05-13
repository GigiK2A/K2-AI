# Integrazione piattaforma SaaS — HostBoost

Guida di riferimento per l'esecuzione della skill in due modalita: consulenziale diretta (Cowork / Claude Code oggi) e piattaforma SaaS (Agent SDK con tool custom, domani).

## 1. Doppia modalita

La skill deve comportarsi in modo coerente in entrambi gli scenari, degradando gracefully dove i tool non sono disponibili.

### Modalita consulenziale diretta
- Contesto: utente in chat (Cowork desktop o Claude Code CLI).
- Input: file caricati dall'utente (PDF, XLSX, CSV da PMS) o dati dichiarati conversazionalmente.
- Output: file creati in `/mnt/outputs/` e consegnati via `mcp__cowork__present_files`.
- Calcoli: eseguiti dalla skill in ragionamento + eventuali tool nativi Claude Code (xlsx, docx).

### Modalita piattaforma SaaS
- Contesto: backend Python/Node con Agent SDK, la skill gira dentro un agente servito da API.
- Input: acquisiti via form multi-step nel frontend K2-AI oppure via upload file in tenant storage.
- Output: file salvati in tenant storage, URL firmati restituiti al frontend che li visualizza in dashboard o li offre al download.
- Calcoli: eseguiti da tool custom esposti come funzioni (definiti sotto).

## 2. Tool custom attesi in modalita piattaforma

Lo scheletro di interfaccia che la piattaforma dovra esporre per far girare HostBoost. La skill, quando tool custom non esistono, simula il comportamento in ragionamento.

### `parse_pms_export(file_url, format) -> dati_struttura_json`
Parsa un export PMS (CSV, XLSX) di piattaforme comuni (Octorate, Hotel Runner, Wubook, Ericsoft, Scrigno, Beddy, Simplebooking) e restituisce un JSON normalizzato con notti vendute, ADR, ricavi per mese e canale.

Input previsto:
- `file_url`: URL firmato per il file caricato dal cliente.
- `format`: "octorate" | "hotelrunner" | "wubook" | "generic_xlsx" | "generic_csv".

Output previsto:
```json
{
  "periodo": { "inizio": "2024-01-01", "fine": "2024-12-31" },
  "camere_totali": 10,
  "giorni_apertura": 280,
  "mensile": [
    {
      "mese": "2024-06",
      "notti_disponibili": 300,
      "notti_vendute": 245,
      "ricavi_camera": 24500,
      "adr": 100,
      "occupancy": 0.817,
      "revpar": 81.67,
      "canali": {
        "diretto": { "notti": 45, "ricavi": 4950 },
        "booking": { "notti": 140, "ricavi": 13300 },
        "expedia": { "notti": 35, "ricavi": 3850 },
        "airbnb": { "notti": 25, "ricavi": 2400 }
      }
    }
  ]
}
```

### `scrape_booking_pricing(compset_ids, dates) -> prezzi_compset`
Scraping prezzi Booking.com per un compset di 3-5 strutture su date future. Usa API o scraping gentile con rate limit.

Input previsto:
- `compset_ids`: array di hotel_id Booking.com.
- `dates`: array di date ISO (20-30 date campione distribuite sulla stagione).

Output previsto:
```json
{
  "compset": [
    {
      "hotel_id": "123456",
      "nome": "Agriturismo Le Querce",
      "rating": 8.9,
      "prezzi": [
        { "data": "2025-07-15", "adr_base": 145, "camera": "Standard" },
        { "data": "2025-07-22", "adr_base": 165, "camera": "Standard" }
      ]
    }
  ]
}
```

### `calcola_kpi_ricettivi(dati_struttura_json) -> kpi_json`
Calcola tutti i KPI (ADR, Occupancy, RevPAR, TRevPAR, GOPPAR se dati costi disponibili, ALOS, booking window, cancellation rate) con breakdown mensile e annuale.

### `benchmark_revpar_zona(regione, tipologia, categoria) -> benchmark_json`
Restituisce i valori di riferimento da `references/benchmark-ricettive-italia.md`. In piattaforma SaaS questi benchmark sono in database aggiornato trimestralmente.

### `analisi_recensioni(struttura_id, piattaforme) -> recensioni_json`
Estrae e classifica recensioni da Booking.com, TripAdvisor, Google, Airbnb. Esegue sentiment e theme analysis sulle ultime 30-50 recensioni.

Output previsto:
```json
{
  "rating": {
    "booking": 8.7,
    "tripadvisor": 4.5,
    "google": 4.6,
    "airbnb": 4.8
  },
  "temi_positivi": [
    { "tema": "colazione", "frequenza": 0.42 },
    { "tema": "posizione", "frequenza": 0.38 }
  ],
  "temi_negativi": [
    { "tema": "wifi", "frequenza": 0.18 },
    { "tema": "parcheggio", "frequenza": 0.12 }
  ]
}
```

### `genera_calendario_pricing(parametri, scenario) -> calendario_json`
Genera un calendario pricing dinamico 12 mesi con BAR suggerito per giorno, minimum stay, offerte applicabili, flag eventi.

Input previsto:
- `parametri`: dati struttura (tipologia, camere, zona, stagionalita).
- `scenario`: "base" | "ottimistico" | "pessimistico".

Output previsto: array di 365 oggetti giorno con BAR, DBI, minimum stay, flag eventi.

### `save_to_tenant_storage(tenant_id, files) -> urls_firmati`
Salva i file generati (DOCX, XLSX, HTML, JSON) nello storage tenant e restituisce URL firmati a scadenza temporizzata.

### `update_job_progress(job_id, pct, message)`
Aggiorna la progress bar del frontend durante l'esecuzione.

## 3. Graceful degradation

Quando un tool non esiste o fallisce, la skill sopperisce come segue:

| Tool mancante | Fallback |
|---|---|
| `parse_pms_export` | Chiedere all'utente di compilare tabella mensile. Annotare "dati raccolti manualmente, possibile imprecisione". |
| `scrape_booking_pricing` | Chiedere all'utente 3-5 nomi di competitor, suggerire di verificare 10 date campione a mano. |
| `calcola_kpi_ricettivi` | Calcolo manuale in ragionamento con formule esplicite nel report. |
| `benchmark_revpar_zona` | Valori hardcoded dal reference `benchmark-ricettive-italia.md`. |
| `analisi_recensioni` | Chiedere al cliente rating di ciascuna piattaforma e copia-incolla di 20-30 recensioni testuali. |
| `genera_calendario_pricing` | Calendario semplificato per stagione (alta/media/bassa/spalla) invece di 365 giorni. |
| `save_to_tenant_storage` | Salvare in `/mnt/outputs/` e presentare con `present_files`. |

## 4. Naming convenzione file

I file consegnati devono seguire una naming standard per facilitare il download multiplo.

```
hostboost-{slug_struttura}-{YYYYMMDD}-report.docx
hostboost-{slug_struttura}-{YYYYMMDD}-cruscotto.xlsx
hostboost-{slug_struttura}-{YYYYMMDD}-dashboard.html
hostboost-{slug_struttura}-{YYYYMMDD}-output.json
```

Lo `slug_struttura` e generato dal nome struttura lowercase, solo ASCII, spazi in trattino, max 40 caratteri.

Esempio: `hostboost-agriturismo-le-querce-20260418-report.docx`.

## 5. Progressi e timing attesi

In piattaforma SaaS il job async ha queste tappe tipiche (total: 8-15 minuti per 12 mesi di dati).

| Step | % | Messaggio |
|---|---|---|
| 1. Parsing input | 10% | "Acquisisco i dati della struttura..." |
| 2. Calcolo KPI core | 25% | "Calcolo RevPAR, ADR, occupancy..." |
| 3. Benchmark zona | 35% | "Confronto con ricettive della tua zona..." |
| 4. Analisi canali | 50% | "Analizzo distribuzione e commissioni..." |
| 5. Analisi pricing e compset | 65% | "Verifico pricing vs competitor..." |
| 6. Analisi recensioni | 75% | "Estraggo i temi delle recensioni..." |
| 7. Piano ricavi 12 mesi | 88% | "Costruisco il calendario pricing..." |
| 8. Generazione deliverable | 100% | "Preparo i documenti finali..." |
