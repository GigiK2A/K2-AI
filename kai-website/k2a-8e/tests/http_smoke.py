"""HTTP smoke — contro il server 8e REALE (non TestClient in-process).

Prova la catena come la userà il K-BOT in produzione: HTTP + Bearer + polling.
Avviare prima il server:  uvicorn app.main:app --port 8810
Uso:  K2A_8E_URL=http://localhost:8810 python tests/http_smoke.py
"""
from __future__ import annotations

import os
import sys
import time

import httpx

BASE = os.environ.get("K2A_8E_URL", "http://localhost:8810")
H = {"Authorization": "Bearer dev-key"}


def main() -> int:
    c = httpx.Client(timeout=30.0)

    h = c.get(f"{BASE}/health").json()
    print("health:", h)
    assert h["status"] == "ok"

    cat = c.get(f"{BASE}/v1/catalog", headers=H).json()
    print("catalog: engine", cat["engine_version"], "snapshot", cat["grounding_snapshot_version"],
          "services", [s["service_id"] for s in cat["services"]])

    # service ignoto → 422 out_of_catalog
    r = c.post(f"{BASE}/v1/deliverables", headers=H,
               json={"service_id": "non-esiste", "entitlement_token": "x"})
    assert r.status_code == 422 and r.json()["reason"] == "out_of_catalog", r.text
    print("refuse out_of_catalog ok")

    # happy path: primo_parere_legale (manifest → LegalBoost)
    r = c.post(f"{BASE}/v1/deliverables", headers=H, json={
        "service_id": "primo_parere_legale", "tier": "servizio",
        "inputs": {"ragione_sociale": "Acme SRL", "tipo_contratto": "fornitura"},
        "entitlement_token": "phase1-test",
    })
    assert r.status_code == 202, r.text
    job = r.json()["job_id"]
    print("job:", job, "blueprint:", r.json()["routed_blueprint"])

    data = {}
    for _ in range(40):
        data = c.get(f"{BASE}/v1/deliverables/{job}", headers=H).json()
        if data["status"] in ("rendered", "refused", "error"):
            break
        time.sleep(0.3)
    print("status:", data["status"], "| validation:", data.get("validation"), "| meta:", data.get("meta"))
    assert data["status"] == "rendered", data
    assert data["citazioni"] and data["citazioni"][0]["fonte"], "citazione mancante"

    # scarica il PDF reale via il path (server locale lo serve da _out)
    pdf_path = data["outputs"]["pdf_path"]
    size = os.path.getsize(pdf_path) if os.path.exists(pdf_path) else 0
    print(f"PDF: {pdf_path} ({size} bytes)")
    assert size > 1000, "PDF troppo piccolo"

    print("\nHTTP SMOKE PASS ✅")
    return 0


if __name__ == "__main__":
    sys.exit(main())
