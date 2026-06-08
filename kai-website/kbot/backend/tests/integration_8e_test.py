"""Integrazione end-to-end K-BOT backend ↔ 8e (senza dati prod).

Avvia un 8e reale (subprocess) con segreto entitlement condiviso, poi guida i
veri endpoint del K-BOT (deliverables/preview/form) via TestClient con auth e
sessione stubbate (no Supabase). Valida la catena:
  form → preview(gate quota) → full(entitlement JWT mint+verify) → render.

Run:  K2A_8E_PORT=8831 python tests/integration_8e_test.py
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import httpx

BE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BE))
EIGHTE = BE.parent.parent / "k2a-8e"
PORT = os.environ.get("K2A_8E_PORT", "8831")
SECRET = "integration-secret-32bytes-minimum!"


def start_8e() -> subprocess.Popen:
    env = {**os.environ, "K2A_8E_API_KEY": "dev-key",
           "K2A_ENTITLEMENT_SECRET": SECRET, "K2A_8E_OUT_DIR": "/tmp/8e-int-out"}
    env.pop("ANTHROPIC_API_KEY", None)  # offline → veloce, no costo
    venv_uvicorn = EIGHTE / ".venv" / "bin" / "uvicorn"
    p = subprocess.Popen([str(venv_uvicorn), "app.main:app", "--port", PORT],
                         cwd=str(EIGHTE), env=env,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(60):
        try:
            if httpx.get(f"http://localhost:{PORT}/health", timeout=1).status_code == 200:
                return p
        except Exception:
            pass
        time.sleep(0.5)
    raise RuntimeError("8e non parte")


def main() -> int:
    proc = start_8e()
    try:
        # env per il K-BOT: punta all'8e reale, stesso segreto entitlement
        os.environ["K2A_8E_BASE_URL"] = f"http://localhost:{PORT}"
        os.environ["K2A_8E_API_KEY"] = "dev-key"
        os.environ["K2A_ENTITLEMENT_SECRET"] = SECRET

        from fastapi.testclient import TestClient
        from app.main import app
        from app.lib.auth import AuthUser, require_user, optional_user
        from app.lib import sessions

        # stub auth + sessione paid (no Supabase, no dati prod)
        fake_user = AuthUser(id="00000000-0000-0000-0000-000000000001", email="t@t.it",
                             has_paid=True, raw={})
        app.dependency_overrides[require_user] = lambda: fake_user
        app.dependency_overrides[optional_user] = lambda: fake_user
        paid = {"id": "11111111-1111-1111-1111-111111111111", "status": "paid",
                "user_id": fake_user.id, "collected_data": {}}
        sessions.get_session = lambda sid: paid                      # type: ignore
        sessions.update_session = lambda sid, patch: paid            # type: ignore
        # contatore preview → consuma sempre ok (no DB)
        import app.api.deliverables as D

        class _RPC:
            data = 1
        class _Admin:
            def rpc(self, *a, **k): return self
            def execute(self): return _RPC()
        D.get_admin_client = lambda: _Admin()                       # type: ignore

        c = TestClient(app)
        ok = 0; tot = 0

        def chk(name, cond):
            nonlocal ok, tot
            tot += 1; ok += bool(cond)
            print(f"  [{'PASS' if cond else 'FAIL'}] {name}")

        SID = "11111111-1111-1111-1111-111111111111"
        SERV = "primo_parere_legale"

        # 1. form
        r = c.get(f"/api/kbot/deliverables/form/{SERV}")
        chk("form 200 con campi", r.status_code == 200 and len(r.json()["campi"]) > 0)

        # 2. preview (gate quota stub) → job → rendered con preview, no PDF
        r = c.post("/api/kbot/preview", json={"session_id": SID, "servizio_id": SERV,
                                              "inputs": {"forma_giuridica": "srl"}})
        chk("preview 200", r.status_code == 200)
        if r.status_code == 200:
            jid = r.json()["job_id"]
            d = {}
            for _ in range(30):
                d = c.get(f"/api/kbot/deliverables/{jid}").json()
                if d["status"] in ("rendered", "refused", "error"): break
                time.sleep(0.3)
            prev = (d.get("outputs") or {}).get("preview")
            chk("preview rendered + assaggio", d["status"] == "rendered" and prev is not None)
            chk("preview senza PDF (no leak)", not (d.get("outputs") or {}).get("pdf_url"))

        # 3. full (entitlement JWT mint dal K-BOT, verify dall'8e) → rendered + PDF
        r = c.post("/api/kbot/deliverables", json={"session_id": SID, "servizio_id": SERV,
                                                   "inputs": {"forma_giuridica": "srl",
                                                              "settore_ateco": "62.01", "n_dipendenti": 5}})
        chk("full create ok (200/202)", r.status_code in (200, 202))
        if r.status_code in (200, 202):
            jid = r.json()["job_id"]
            d = {}
            for _ in range(40):
                d = c.get(f"/api/kbot/deliverables/{jid}").json()
                if d["status"] in ("rendered", "refused", "error"): break
                time.sleep(0.3)
            chk("full rendered (entitlement JWT verificato dall'8e)", d["status"] == "rendered")
            chk("full validation L1/L2/output-schema", d.get("validation", {}).get("output_schema") == "PASS")
            chk("full ha PDF", bool((d.get("outputs") or {}).get("pdf_path")))

        print(f"\n{ok}/{tot} check integrazione superati")
        return 0 if ok == tot else 1
    finally:
        proc.terminate()


if __name__ == "__main__":
    sys.exit(main())
