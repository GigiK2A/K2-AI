# AI Board

Fondamenta del sistema multi-agente per la gestione business.

## Setup

1. Installa le dipendenze con `uv sync`
2. Attiva l'ambiente con `source .venv/bin/activate`
3. Copia `.env.example` in `.env`
4. Compila le variabili reali
5. Esegui `db/migrations/001_initial.sql` su Supabase
6. Avvia con `python main.py`

## Step 1 incluso

- bootstrap applicativo
- connessione Supabase
- seed e cache della memoria condivisa
- classe base `BoardAgent`

## Non incluso in questo step

- agenti specifici
- bot Telegram
- dashboard FastAPI
- scheduler
