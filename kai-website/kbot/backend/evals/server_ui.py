"""Backend locale con UTENTE FINTO sempre autenticato e database in memoria con filtri veri (conversazioni, profilo):
serve a provare il frontend nel flusso da loggato senza Supabase. Uso: server_ui.py <backend_dir> <porta>"""
import os, sys, uuid
BACKEND = sys.argv[1]; PORTA = int(sys.argv[2]); sys.path.insert(0, BACKEND); sys.path.insert(0, os.path.join(BACKEND, "tests"))
for k, v in {"NEXT_PUBLIC_SUPABASE_URL": "https://locale.invalid", "SUPABASE_SERVICE_ROLE_KEY": "locale", "STRIPE_SECRET_KEY": "sk_test_locale", "STRIPE_WEBHOOK_SECRET": "whsec_locale", "K2A_ENTITLEMENT_SECRET": "locale-secret-32bytes-minimum-length!"}.items(): os.environ.setdefault(k, v)
for k in ("OPENAI_API_KEY", "INTERNAL_API_KEY"): os.environ.pop(k, None)
os.environ.update({"ANTHROPIC_BASE_URL": "http://127.0.0.1:4000", "ANTHROPIC_API_KEY": open(os.path.expanduser("~/.k2a-local/shim_master_key.txt")).read().strip(), "ANTHROPIC_MODEL": "k2a-kbot", "NORMATTIVA_DB_PATH": os.path.expanduser("~/normattiva_ai/normattiva.db"), "KBOT_FREE_MODE": "1", "SLOWAPI_ENABLED": "false", "KBOT_CORS_ORIGINS": "http://localhost:3100"})
from test_e2e_scenarios import _FakeStorage
import datetime
class Q:
    def __init__(s, db, t): s.db, s.t, s.f, s.mode, s.p, s.lim, s.one = db, t, [], "select", None, None, False
    def select(s, *a, **k): s.mode = "select"; return s
    def insert(s, row): s.mode, s.p = "insert", row; return s
    def update(s, p): s.mode, s.p = "update", p; return s
    def upsert(s, row, **k): s.mode, s.p = "upsert", row; return s
    def delete(s): s.mode = "delete"; return s
    def eq(s, k, v): s.f.append(lambda r: str(r.get(k)) == str(v)); return s
    def neq(s, k, v): s.f.append(lambda r: str(r.get(k)) != str(v)); return s
    def is_(s, k, v): s.f.append((lambda r: r.get(k) is None) if v == "null" else (lambda r: r.get(k) is v)); return s
    def in_(s, k, vs): s.f.append(lambda r: r.get(k) in vs); return s
    def order(s, *a, **k): return s
    def limit(s, n): s.lim = n; return s
    def single(s): s.one = True; return s
    maybe_single = single
    def execute(s):
        rows = s.db.tables.setdefault(s.t, []); m = [r for r in rows if all(f(r) for f in s.f)]
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        if s.mode == "insert":
            row = {"id": str(uuid.uuid4()), "created_at": now, **s.p}; rows.append(row); data = [row]
        elif s.mode == "upsert":
            key = "user_id" if "user_id" in s.p else "id"; ex = [r for r in rows if r.get(key) == s.p.get(key)]
            if ex: ex[0].update(s.p); data = [ex[0]]
            else: row = {"id": str(uuid.uuid4()), "created_at": now, **s.p}; rows.append(row); data = [row]
        elif s.mode == "update":
            for r in m: r.update(s.p)
            data = m
        elif s.mode == "delete":
            for r in m: rows.remove(r)
            data = m
        else: data = m[:s.lim] if s.lim else m
        if s.one: data = data[0] if data else None
        return type("R", (), {"data": data, "count": len(m)})()
class DB:
    def __init__(s): s.tables, s.storage = {}, _FakeStorage()
    def table(s, n): return Q(s, n)
db = DB()
import app.lib.supabase_admin as sa, app.lib.sessions as sess, app.lib.storage as stor, app.lib.profile as prof, app.api.conversations as conv
for mod in (sa, sess, stor, prof, conv): mod.get_admin_client = lambda: db
import app.lib.rag as rag
_ch = {}
rag.persist_chunks = lambda rows: [_ch.setdefault(r["session_id"], []).append(r) for r in rows] and None
rag.fetch_chunks = lambda sid, limit=500: list(_ch.get(str(sid), []))[:limit]
from app.main import app
from app.lib.auth import AuthUser, optional_user, require_user
UTENTE = "00000000-0000-4000-8000-000000000001"
def _u(): return AuthUser(id=UTENTE, email="prova@example.com", has_paid=False, raw={"user_metadata": {}})
app.dependency_overrides[optional_user] = _u
app.dependency_overrides[require_user] = _u
import uvicorn
print(f"server_ui su :{PORTA}", flush=True)
uvicorn.run(app, host="127.0.0.1", port=PORTA, log_level="warning")
