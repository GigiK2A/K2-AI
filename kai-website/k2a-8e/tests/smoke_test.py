"""Smoke test 8e Phase-1 (offline, no rete). Run: python tests/smoke_test.py

ASSERT (dal PROMPT_8e_Phase1 §6):
- PDF prodotto
- L1 = PASS, L2 = PASS
- almeno una citazione con fonte + vigenza
- service_id ignoto → refused: out_of_catalog
- entitlement assente → 402
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402

H = {"Authorization": "Bearer dev-key"}
client = TestClient(app)


def _fail(msg: str):
    print(f"FAIL: {msg}")
    sys.exit(1)


def main():
    # health
    r = client.get("/health")
    assert r.status_code == 200, _fail("health")
    print("health:", r.json())

    # no auth → 401
    assert client.get("/v1/catalog").status_code == 401, _fail("auth non applicata")

    # entitlement assente → 402
    r = client.post("/v1/deliverables", headers=H,
                    json={"service_id": "flusso-legalboost-pmi", "inputs": {}})
    assert r.status_code == 402, _fail(f"atteso 402, ricevuto {r.status_code}")
    print("no-entitlement → 402 ok")

    # service ignoto → refused out_of_catalog
    r = client.post("/v1/deliverables", headers=H,
                    json={"service_id": "non-esiste", "inputs": {}, "entitlement_token": "x"})
    assert r.status_code == 422 and r.json().get("reason") == "out_of_catalog", \
        _fail(f"atteso refuse out_of_catalog, ricevuto {r.status_code} {r.json()}")
    print("service ignoto → refused out_of_catalog ok")

    # happy path LegalBoost (service_id reale dal manifest)
    r = client.post("/v1/deliverables", headers=H, json={
        "service_id": "primo_parere_legale", "tier": "boost",
        "inputs": {"ragione_sociale": "Acme SRL", "tipo_contratto": "fornitura"},
        "entitlement_token": "x",
    })
    assert r.status_code == 202, _fail(f"create {r.status_code} {r.text}")
    job_id = r.json()["job_id"]
    print("job creato:", job_id, "blueprint:", r.json()["routed_blueprint"])

    # poll (BackgroundTask con TestClient gira sincrono, ma poll per sicurezza)
    status, data = None, {}
    for _ in range(30):
        data = client.get(f"/v1/deliverables/{job_id}", headers=H).json()
        status = data["status"]
        if status in ("rendered", "refused", "error"):
            break
        time.sleep(0.2)
    print("status finale:", status, "| meta:", data.get("meta"))

    assert status == "rendered", _fail(f"atteso rendered, ricevuto {status} ({data.get('error')})")
    assert data["validation"]["L1"] == "PASS", _fail("L1 non PASS")
    assert data["validation"]["L2"] == "PASS", _fail("L2 non PASS")
    cits = data.get("citazioni", [])
    assert cits and cits[0].get("fonte") and cits[0].get("vigenza"), _fail("citazione senza fonte/vigenza")
    pdf = Path(data["outputs"]["pdf_path"])
    assert pdf.exists() and pdf.stat().st_size > 500, _fail("PDF mancante/vuoto")
    print(f"PDF: {pdf} ({pdf.stat().st_size} bytes)")
    print(f"citazioni: {len(cits)} | prima fonte: {cits[0]['fonte']}")

    print("\nSMOKE TEST PASS ✅")


if __name__ == "__main__":
    main()
