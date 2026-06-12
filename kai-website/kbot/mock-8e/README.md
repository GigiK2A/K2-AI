# MOCK 8e

Finto motore di generazione deliverable. Implementa il contratto
`docs/interfaccia-kbot-8e.md §1` per sbloccare lo sviluppo del client 8e,
dell'UI percorsi e dell'upsell **prima** che l'8e reale (di Luca) esista.

Non genera niente di reale: niente skill, niente grounding, niente Claude.
Restituisce un PDF placeholder e simula la macchina a stati del job.

## Run

```bash
cd kbot/mock-8e
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8800
# veloce (stati in 3s invece di 9s):  MOCK_8E_FAST=1 uvicorn main:app --port 8800
```

Il backend K-BOT lo usa via env `K2A_8E_BASE_URL=http://localhost:8800` +
`K2A_8E_API_KEY=dev-key` (vedi `settings.py`).

## Endpoint (contratto membrana)

| Metodo | Path | Note |
|---|---|---|
| GET | `/health` | liveness, no auth |
| GET | `/v1/catalog` | Bearer · versioni motore/snapshot/catalog + blueprint noti |
| POST | `/v1/deliverables` | Bearer · crea job → `202 {job_id, status:routed, confidence}` |
| GET | `/v1/deliverables/{job_id}` | Bearer · stato job + outputs quando `rendered` |
| GET | `/v1/deliverables/{job_id}/download?fmt=pdf\|html\|json` | scarica il placeholder |

## Auth

`Authorization: Bearer <MOCK_8E_API_KEY>` (default `dev-key`).

## Macchina a stati

`routed → running → validating → rendered` in base al tempo trascorso
(default 0→3→6→9s; con `MOCK_8E_FAST=1` → 0→1→2→3s).

## Trigger di test (edge case dal client)

| Come | Effetto |
|---|---|
| `service_id="force-refuse"` | `422 refused / out_of_catalog` |
| `inputs.force="low_confidence"` | `422 refused / low_confidence` |
| `inputs.force="validation_failed"` | job va in `status:refused` (L2 FAIL) |
| `entitlement_token` assente | `402 payment_required` |

## Esempio curl

```bash
# crea job
curl -s -X POST localhost:8800/v1/deliverables \
  -H "Authorization: Bearer dev-key" -H "Content-Type: application/json" \
  -d '{"service_id":"flusso-legalboost-pmi","tier":"boost","inputs":{},"entitlement_token":"x"}'

# polla stato (ripeti finché status=rendered)
curl -s localhost:8800/v1/deliverables/<job_id> -H "Authorization: Bearer dev-key"

# scarica pdf placeholder
curl -s "localhost:8800/v1/deliverables/<job_id>/download?fmt=pdf" -o mock.pdf
```

## Quando arriva l'8e reale

Swap senza toccare il client K-BOT: cambia `K2A_8E_BASE_URL` →
URL Railway dell'8e reale + `K2A_8E_API_KEY` reale. Il contratto è lo stesso.
Prima del cutover, chiudere i gap `docs/interfaccia-kbot-8e.md §9` (entitlement
JWT, storage cross-service, versioni, ecc.).
