# K2-AI Bot Engine

Frontend in Next.js + backend completamente Python (FastAPI).

## 1) Backend Python

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# compila ANTHROPIC_API_KEY (obbligatorio)
uvicorn app.main:app --reload --port 8000
```

## 2) Frontend Next.js

In root progetto:

```bash
cp .env.example .env.local
npm install
npm run dev
```

## Endpoint backend (Python)

- `POST /api/chat` `{ input, mode: "lead"|"report", paid }`
- `GET /api/skills`
- `POST /api/leads`
- `GET /api/report-access`
- `GET /health`

## Note

- Le skill vengono caricate da: `assets/skills/skills sito k2-ai 2`
- I lead vengono salvati in: `data/leads.jsonl`
- Per report premium imposta `REPORT_PAYMENT_LINK` nel backend
