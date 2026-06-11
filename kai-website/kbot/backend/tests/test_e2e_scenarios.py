"""End-to-end realistic scenarios for K-BOT Premium.

Goal: probe behaviors NOT covered by existing tests (SSRF / rate-limit / webhook).
Targets: real PDF extraction, prompt assembly with files, size limits,
normalize_assistant_reply truncation/code-fence stripping, cold-start vs picked
service, conversation compaction.

No real Claude / Supabase calls. We monkeypatch:
  - app.lib.supabase_admin.get_admin_client (in-memory fake)
  - anthropic.Anthropic (canned responses)
We also monkeypatch sessions module to keep behaviour deterministic.
"""
from __future__ import annotations

import base64
import io
import os
import uuid
from typing import Any, Dict, List, Optional

import pytest

# Force minimal env BEFORE app import.
os.environ.setdefault("ANTHROPIC_API_KEY", "test-sk-dummy")
os.environ.setdefault("SUPABASE_URL", "https://fake.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "fake-key")

from fastapi.testclient import TestClient  # noqa: E402

from app.lib import sessions as sessions_module  # noqa: E402
from app.lib.prompts import (  # noqa: E402
    build_system_prompt_v2,
    compact_messages,
    extract_summary,
    normalize_assistant_reply,
    strip_summary_block,
)


# ---------------------------------------------------------------------------
# Fake Supabase (in-memory). Mirrors the tiny surface we use.
# ---------------------------------------------------------------------------

class _FakeStorageBucket:
    def __init__(self):
        self.files: Dict[str, bytes] = {}

    def upload(self, path, data, options=None):
        self.files[path] = data
        return {"path": path}

    def get_public_url(self, path):
        return f"https://fake.supabase.co/storage/{path}"


class _FakeStorage:
    def __init__(self):
        self.bucket = _FakeStorageBucket()

    def list_buckets(self):
        return [{"name": "kbot-uploads"}]

    def create_bucket(self, name, options=None):
        return {"name": name}

    def from_(self, name):
        return self.bucket


class _FakeQuery:
    def __init__(self, store: Dict[str, dict], table: str):
        self.store = store
        self.table = table
        self._filter_id: Optional[str] = None
        self._mode: Optional[str] = None
        self._patch: Optional[dict] = None
        self._insert: Optional[dict] = None

    def select(self, *_a, **_k):
        self._mode = "select"
        return self

    def insert(self, row):
        self._mode = "insert"
        self._insert = row
        return self

    def update(self, patch):
        self._mode = "update"
        self._patch = patch
        return self

    def eq(self, key, value):
        if key == "id":
            self._filter_id = value
        return self

    def limit(self, _n):
        return self

    def order(self, *_a, **_k):
        return self

    def execute(self):
        if self._mode == "insert":
            new_id = str(uuid.uuid4())
            row = {"id": new_id, "created_at": "2026-05-17T00:00:00Z", **self._insert}
            self.store[new_id] = row
            return type("R", (), {"data": [row]})()
        if self._mode == "select":
            row = self.store.get(self._filter_id)
            return type("R", (), {"data": [row] if row else []})()
        if self._mode == "update":
            row = self.store.get(self._filter_id)
            if not row:
                return type("R", (), {"data": []})()
            row.update(self._patch)
            return type("R", (), {"data": [row]})()
        return type("R", (), {"data": []})()


class FakeSupabase:
    def __init__(self):
        self._tables: Dict[str, Dict[str, dict]] = {"kbot_sessions": {}}
        self.storage = _FakeStorage()

    def table(self, name):
        self._tables.setdefault(name, {})
        return _FakeQuery(self._tables[name], name)


# ---------------------------------------------------------------------------
# Anthropic mock
# ---------------------------------------------------------------------------

class _FakeUsage:
    input_tokens = 100
    output_tokens = 200


class _FakeBlock:
    def __init__(self, text):
        self.type = "text"
        self.text = text


class _FakeResp:
    def __init__(self, text):
        self.content = [_FakeBlock(text)]
        self.usage = _FakeUsage()


class _FakeMessages:
    def __init__(self, canned: str, capture: list):
        self.canned = canned
        self.capture = capture

    def create(self, **kwargs):
        self.capture.append(kwargs)
        return _FakeResp(self.canned)


class FakeAnthropic:
    canned_text: str = "Va bene, procedo con l'analisi richiesta."
    captured_calls: List[dict] = []

    def __init__(self, *_a, **_k):
        self.messages = _FakeMessages(FakeAnthropic.canned_text, FakeAnthropic.captured_calls)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def fake_db(monkeypatch):
    fake = FakeSupabase()
    # Patch in the places the code actually imports get_admin_client from.
    monkeypatch.setattr("app.lib.supabase_admin.get_admin_client", lambda: fake)
    monkeypatch.setattr("app.lib.sessions.get_admin_client", lambda: fake)
    monkeypatch.setattr("app.api.upload.get_admin_client", lambda: fake)
    # Reset bucket-ready cache so _ensure_bucket runs against fake.
    monkeypatch.setattr("app.api.upload._BUCKET_READY", False, raising=False)
    return fake


@pytest.fixture
def fake_anthropic(monkeypatch):
    FakeAnthropic.captured_calls = []
    FakeAnthropic.canned_text = "Va bene, procedo con l'analisi richiesta."
    # Patch on the module objects the routes already imported.
    import anthropic
    monkeypatch.setattr(anthropic, "Anthropic", FakeAnthropic)
    monkeypatch.setattr("app.api.message.anthropic.Anthropic", FakeAnthropic)
    monkeypatch.setattr("app.api.upload._anthropic.Anthropic", FakeAnthropic)
    return FakeAnthropic


@pytest.fixture
def client(fake_db, fake_anthropic):
    from app.main import app
    return TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_pdf(pages_text: List[str]) -> bytes:
    """Build a real PDF with reportlab. Each list entry is one page."""
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    for txt in pages_text:
        y = h - 50
        for line in txt.split("\n"):
            c.drawString(40, y, line[:110])
            y -= 14
            if y < 50:
                c.showPage()
                y = h - 50
        c.showPage()
    c.save()
    return buf.getvalue()


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode()


def _make_session(client, service_id=None) -> str:
    body = {"service_id": service_id} if service_id else {}
    r = client.post("/api/kbot/session", json=body)
    assert r.status_code == 200, r.text
    return r.json()["session_id"]


# ---------------------------------------------------------------------------
# 1. Long financial PDF — real extraction + prompt verification
# ---------------------------------------------------------------------------

def test_long_financial_pdf_upload_and_extraction(client):
    # 40 pages, each ~250 chars → ~10k chars of financial text
    pages = []
    for i in range(40):
        pages.append(
            f"PAGINA {i+1} BILANCIO 2025\n"
            f"Ricavi netti euro {1_000_000 + i*1000}\n"
            f"Costi operativi euro {600_000 + i*500}\n"
            f"EBITDA margine percento {15 + (i % 5)}\n"
            f"Risultato esercizio euro {200_000 - i*100}\n"
            f"Marker univoco MAGICTOKEN_BILANCIO_{i}\n"
            "Nota integrativa: la societa ha investito in immobilizzazioni.\n"
        )
    pdf = _make_pdf(pages)
    assert len(pdf) > 5000

    sid = _make_session(client)
    r = client.post("/api/kbot/upload", json={
        "session_id": sid,
        "files": [{"name": "bilancio.pdf", "type": "application/pdf",
                   "size": len(pdf), "base64": _b64(pdf)}],
    })
    assert r.status_code == 200, r.text
    files = r.json()["files"]
    assert len(files) == 1
    f = files[0]
    assert f["extractionMethod"] == "pdf-parse", f
    assert len(f["extractedText"]) >= 3000, f"only got {len(f['extractedText'])} chars"
    assert "MAGICTOKEN_BILANCIO_" in f["extractedText"]

    # Session GET → file present.
    r2 = client.get(f"/api/kbot/session/{sid}")
    assert r2.status_code == 200


# ---------------------------------------------------------------------------
# 2. System prompt contains file text, NO P-catalog
# ---------------------------------------------------------------------------

def test_system_prompt_includes_file_text_and_no_service_catalog():
    session = {
        "collected_data": {
            "service_id": "P12",
            "uploaded_files": [
                {"name": "bilancio.pdf",
                 "extractedText": (
                     "Bilancio consolidato al 31 dicembre 2025. Ricavi netti euro 1.234.567. "
                     "EBITDA margin 18.4 percento. Posizione finanziaria netta negativa "
                     "per 450.000 euro. Indice di solidita 0.62. UNIQUE_FILE_MARKER_42. "
                     "Rendiconto finanziario in pareggio. CCN positivo per 320k. "
                     "ROE 11.2 percento. ROI 9.8 percento."
                 )}
            ],
        }
    }
    prompt = build_system_prompt_v2(["analisi-bilancio-pmi"], session)

    assert "UNIQUE_FILE_MARKER_42" in prompt, "extracted text didn't reach prompt"
    assert "<UNTRUSTED_FILE_CONTENT>" in prompt
    assert "</UNTRUSTED_FILE_CONTENT>" in prompt
    # Service catalog (P01..P20 list) should NOT be inlined in this prompt.
    assert "P01 — Agenti AI" not in prompt
    assert "Catalogo servizi K2-AI" not in prompt
    # No-JSON rule must be there.
    assert "MAI" in prompt and "JSON" in prompt
    assert "```code" in prompt or "code blocks" in prompt
    assert len(prompt) > 10_000, f"prompt only {len(prompt)} chars"


# ---------------------------------------------------------------------------
# 3. Size limits: 15MB ok, 25MB rejected
# ---------------------------------------------------------------------------

def test_upload_15mb_accepted(client):
    # Real-ish PDF padded to ~15MB. We just build raw bytes (text decode path
    # not triggered for application/pdf; pdfplumber will fail on garbage and
    # fall through — still 200 with method=none).
    data = b"%PDF-1.4\n" + b"X" * (15 * 1024 * 1024)
    sid = _make_session(client)
    r = client.post("/api/kbot/upload", json={
        "session_id": sid,
        "files": [{"name": "big.pdf", "type": "application/pdf",
                   "size": len(data), "base64": _b64(data)}],
    })
    assert r.status_code == 200, f"15MB should pass, got {r.status_code} {r.text[:200]}"


def test_upload_25mb_rejected(client):
    data = b"X" * (25 * 1024 * 1024)
    sid = _make_session(client)
    r = client.post("/api/kbot/upload", json={
        "session_id": sid,
        "files": [{"name": "huge.bin", "type": "application/octet-stream",
                   "size": len(data), "base64": _b64(data)}],
    })
    assert r.status_code == 413, f"25MB should be rejected, got {r.status_code}"
    # BUG CHECK: upload.py:186 hardcodes "3 MB" in the error string despite
    # MAX_BYTES=20MB. Misleading to users.
    detail = r.json().get("detail", "")
    assert "20" in detail, f"error message lies about cap: {detail!r}"


# ---------------------------------------------------------------------------
# 4. Image-only PDF — fallback (not pdf-parse)
# ---------------------------------------------------------------------------

def test_pdf_without_text_falls_through(client, fake_anthropic):
    # Build a PDF with literally no text content (only an empty drawing).
    # With OCR fallback, this should route to claude-vision-ocr (Vision
    # is mocked to return canned text per page).
    from reportlab.pdfgen import canvas
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    c.showPage()
    c.save()
    data = buf.getvalue()

    fake_anthropic.canned_text = "Pagina scannerizzata: testo OCR ricostruito qui."

    sid = _make_session(client)
    r = client.post("/api/kbot/upload", json={
        "session_id": sid,
        "files": [{"name": "scan.pdf", "type": "application/pdf",
                   "size": len(data), "base64": _b64(data)}],
    })
    assert r.status_code == 200
    f = r.json()["files"][0]
    assert f["extractionMethod"] != "pdf-parse"
    # OCR fallback expected; we still accept "none" if pdfplumber can't render
    # (some sandbox environments lack the imaging dependency).
    assert f["extractionMethod"] in ("none", "claude-vision-ocr"), f["extractionMethod"]


# ---------------------------------------------------------------------------
# 5. CSV upload — text-decode
# ---------------------------------------------------------------------------

def test_csv_upload_text_decode(client):
    csv = b"month,revenue,cost\n2025-01,12000,8000\n2025-02,15000,9500\n"
    sid = _make_session(client)
    r = client.post("/api/kbot/upload", json={
        "session_id": sid,
        "files": [{"name": "kpi.csv", "type": "text/csv",
                   "size": len(csv), "base64": _b64(csv)}],
    })
    assert r.status_code == 200
    f = r.json()["files"][0]
    assert f["extractionMethod"] == "text-decode"
    assert "revenue" in f["extractedText"]


# ---------------------------------------------------------------------------
# 6. PNG upload — Vision path
# ---------------------------------------------------------------------------

def test_png_upload_goes_through_vision(client, fake_anthropic):
    fake_anthropic.canned_text = "Immagine: landing page con titolo 'Test'"
    # Minimal PNG signature (1x1).
    png = bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
        "890000000d49444154789c6300010000000500010d0a2db40000000049454e44"
        "ae426082"
    )
    sid = _make_session(client)
    r = client.post("/api/kbot/upload", json={
        "session_id": sid,
        "files": [{"name": "shot.png", "type": "image/png",
                   "size": len(png), "base64": _b64(png)}],
    })
    assert r.status_code == 200
    f = r.json()["files"][0]
    assert f["extractionMethod"] == "claude-vision"
    assert "Test" in f["extractedSummary"]


# ---------------------------------------------------------------------------
# 7. normalize_assistant_reply — full set
# ---------------------------------------------------------------------------

def test_normalize_does_not_truncate_long_reply():
    text = "Paragrafo di analisi. " * 250  # ~5000 chars
    out = normalize_assistant_reply(text)
    assert len(out) > 4000, f"truncated to {len(out)}"


def test_normalize_strips_closed_json_block():
    raw = "Ecco l'analisi.\n```json\n{\"a\":1,\"b\":2}\n```\nFine."
    out = normalize_assistant_reply(raw)
    assert "json" not in out.lower() or "{" not in out
    assert "{" not in out and "}" not in out


def test_normalize_strips_unclosed_json_block():
    # Bug noted in CLAUDE context: unclosed ```json bypassed strip.
    raw = "Premessa.\n```json\n{\"reportType\":\"bilancio\",\"x\":"
    out = normalize_assistant_reply(raw)
    assert "```" not in out
    assert "reportType" not in out
    assert "Premessa" in out


def test_normalize_strips_bold():
    out = normalize_assistant_reply("Questo è **molto** importante.")
    assert "**" not in out
    assert "molto" in out


def test_normalize_empty_input():
    out = normalize_assistant_reply("")
    assert out and "Ricevuto" in out


def test_normalize_whitespace_only():
    out = normalize_assistant_reply("   \n\n  ")
    assert out and "Ricevuto" in out


# ---------------------------------------------------------------------------
# 8. strip_summary_block / extract_summary
# ---------------------------------------------------------------------------

def test_extract_summary_present():
    raw = (
        "Chiusura.\n\nCONSULENZA_SUMMARY_START\n"
        '{"reportType":"bilancio","objective":"capire margini",'
        '"scope":"esercizio 2024","summary":"x","nextStep":"PDF"}\n'
        "CONSULENZA_SUMMARY_END\n"
    )
    s = extract_summary(raw)
    assert s and s["reportType"] == "bilancio"
    stripped = strip_summary_block(raw)
    assert "CONSULENZA_SUMMARY" not in stripped
    assert "Chiusura." in stripped


def test_extract_summary_absent():
    assert extract_summary("ciao") is None
    assert strip_summary_block("ciao") == "ciao"


def test_extract_summary_invalid_json_returns_none():
    raw = "CONSULENZA_SUMMARY_START\n{not json}\nCONSULENZA_SUMMARY_END"
    assert extract_summary(raw) is None
    # But strip_summary_block still removes the block.
    assert "CONSULENZA_SUMMARY" not in strip_summary_block(raw)


# ---------------------------------------------------------------------------
# 9. Cold-start prompt
# ---------------------------------------------------------------------------

def test_cold_start_prompt_says_no_service_picked():
    p = build_system_prompt_v2([], {"collected_data": {}})
    assert "SERVIZIO NON ANCORA SELEZIONATO" in p
    # Il prompt cold-start chiede che tipo di analisi/deliverable serve (wording
    # aggiornato dalla direzione "deliverable", ex "tipo di analisi").
    assert "analisi" in p.lower() or "deliverable" in p.lower()


def test_picked_service_prompt():
    p = build_system_prompt_v2([], {"collected_data": {"service_id": "P12"}})
    assert "SERVIZIO SELEZIONATO" in p
    assert "P12" in p


# ---------------------------------------------------------------------------
# 10. compact_messages
# ---------------------------------------------------------------------------

def test_compact_messages_keeps_last_n_and_truncates():
    msgs = [{"role": "user", "content": "x" * 2000} for _ in range(20)]
    out = compact_messages(msgs, max_messages=5, max_chars_per_message=500)
    assert len(out) == 5
    for m in out:
        assert len(m["content"]) <= 500


def test_compact_messages_drops_invalid_roles():
    msgs = [
        {"role": "user", "content": "hi"},
        {"role": "system", "content": "ignored"},  # invalid here
        {"role": "assistant", "content": "ciao"},
        {"role": "tool", "content": "ignored2"},
    ]
    out = compact_messages(msgs, max_messages=10, max_chars_per_message=100)
    roles = [m["role"] for m in out]
    assert "system" not in roles and "tool" not in roles
    assert roles == ["user", "assistant"]


# ---------------------------------------------------------------------------
# 11. URL block in prompt
# ---------------------------------------------------------------------------

def test_analyzed_urls_appear_in_prompt():
    session = {"collected_data": {
        "analyzed_urls": [
            {"url": "https://k2-ai.it", "summary": "homepage di K2-AI: AI per PMI italiane"},
        ]
    }}
    p = build_system_prompt_v2([], session)
    assert "<UNTRUSTED_URL_CONTENT>" in p
    assert "</UNTRUSTED_URL_CONTENT>" in p
    assert "K2-AI" in p


# ---------------------------------------------------------------------------
# 12. Multiple files — last 5 enter prompt
# ---------------------------------------------------------------------------

def test_prompt_includes_only_last_five_files():
    files = []
    for i in range(8):
        files.append({
            "name": f"f{i}.pdf",
            "extractedText": f"FILE_MARKER_{i} " + ("x" * 200),
        })
    p = build_system_prompt_v2([], {"collected_data": {"uploaded_files": files}})
    # First 3 dropped, last 5 included.
    for i in range(3):
        assert f"FILE_MARKER_{i}" not in p, f"file {i} should be dropped"
    for i in range(3, 8):
        assert f"FILE_MARKER_{i}" in p, f"file {i} should be in prompt"


def test_prompt_file_budget_per_file_18k_chars():
    big_text = "A" * 25000  # bigger than per-file cap of 18000
    p = build_system_prompt_v2([], {"collected_data": {
        "uploaded_files": [{"name": "big.pdf", "extractedText": big_text}]
    }})
    # Find the file block; it should hold up to 18000 A's, not 25000.
    a_count = p.count("A")
    assert a_count >= 17_000, f"too few As: {a_count}"
    assert a_count < 19_000, f"per-file cap not enforced: {a_count}"


# ---------------------------------------------------------------------------
# 13. /message round-trip with files in session
# ---------------------------------------------------------------------------

def test_message_endpoint_sends_file_text_to_claude(client, fake_anthropic):
    sid = _make_session(client, service_id="P12")

    # Inject a file via upload of a small PDF with marker text.
    pdf = _make_pdf(["MARKER_BILANCIO_XYZ\nRicavi euro 100000\nCosti euro 60000"] * 3)
    r = client.post("/api/kbot/upload", json={
        "session_id": sid,
        "files": [{"name": "b.pdf", "type": "application/pdf",
                   "size": len(pdf), "base64": _b64(pdf)}],
    })
    assert r.status_code == 200

    fake_anthropic.canned_text = "Ho letto il bilancio. Procedo con i margini."
    r = client.post("/api/kbot/message", json={
        "session_id": sid,
        "message": "Analizza il bilancio caricato.",
    })
    assert r.status_code == 200, r.text

    # Verify the system prompt sent to Claude actually contained the file text.
    assert FakeAnthropic.captured_calls, "Claude was never called"
    last_call = FakeAnthropic.captured_calls[-1]
    sys_prompt = last_call.get("system", "")
    assert "MARKER_BILANCIO_XYZ" in sys_prompt, "file text didn't reach Claude"
    # max_tokens generoso, must be >= 4000 (was 1200 bug)
    assert last_call.get("max_tokens", 0) >= 4000, \
        f"max_tokens too small: {last_call.get('max_tokens')}"


def test_message_endpoint_normalizes_unclosed_code_fence(client, fake_anthropic):
    sid = _make_session(client)
    fake_anthropic.canned_text = (
        "Ecco l'analisi.\n```json\n{\"a\":1,"  # unclosed
    )
    r = client.post("/api/kbot/message", json={
        "session_id": sid, "message": "Procedi."
    })
    assert r.status_code == 200
    msg = r.json()["message"]
    assert "```" not in msg
    assert "{" not in msg and "}" not in msg
    assert "Ecco l'analisi" in msg


def test_message_empty_payload_returns_400(client):
    sid = _make_session(client)
    r = client.post("/api/kbot/message", json={"session_id": sid})
    assert r.status_code == 400


# ---------------------------------------------------------------------------
# 14. Long conversation — compact applied
# ---------------------------------------------------------------------------

def test_long_conversation_compacted_history_sent_to_claude(client, fake_anthropic):
    sid = _make_session(client)
    # 15 turns. Each /message persists user + assistant, so after N posts we'll
    # have ≤ 2N msgs. We only need to verify compaction caps history.
    for i in range(15):
        r = client.post("/api/kbot/message", json={
            "session_id": sid,
            "message": f"turno {i} " + ("x" * 1500),
        })
        assert r.status_code == 200

    # Last call's `messages` (history) should be ≤ MAX_HISTORY_MESSAGES (12).
    last = FakeAnthropic.captured_calls[-1]
    hist = last["messages"]
    assert len(hist) <= 12, f"history not capped: {len(hist)}"
    for m in hist:
        assert len(m["content"]) <= 900


# ---------------------------------------------------------------------------
# 15. lead vs report mode in session
# ---------------------------------------------------------------------------

def test_lead_mode_session_keeps_mode(client):
    r = client.post("/api/kbot/session", json={"mode": "lead"})
    sid = r.json()["session_id"]
    r2 = client.get(f"/api/kbot/session/{sid}")
    assert r2.json()["session"]["mode"] == "lead"


def test_report_mode_default(client):
    sid = _make_session(client)
    r = client.get(f"/api/kbot/session/{sid}")
    assert r.json()["session"]["mode"] == "report"


# ---------------------------------------------------------------------------
# 16. OCR fallback — text layer too thin → Vision page-by-page
# ---------------------------------------------------------------------------

def test_ocr_fallback_when_text_layer_below_threshold(client, fake_anthropic):
    """Thin-text-layer PDF should route to claude-vision-ocr."""
    # Tiny PDF with under 120 chars of text → triggers OCR fallback.
    from reportlab.pdfgen import canvas
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    c.drawString(40, 800, "x")  # 1 char on the page; far below 120 threshold
    c.showPage()
    c.save()
    data = buf.getvalue()

    fake_anthropic.canned_text = "OCR_RECOVERED_TEXT_42 valori finanziari ricostruiti."

    sid = _make_session(client)
    r = client.post("/api/kbot/upload", json={
        "session_id": sid,
        "files": [{"name": "scan_bilancio.pdf", "type": "application/pdf",
                   "size": len(data), "base64": _b64(data)}],
    })
    assert r.status_code == 200, r.text
    f = r.json()["files"][0]
    # Accept "none" only if the imaging stack isn't available in this env;
    # otherwise we expect the OCR fallback to fire.
    if f["extractionMethod"] == "none":
        pytest.skip("pdfplumber.to_image not available in this sandbox")
    assert f["extractionMethod"] == "claude-vision-ocr"
    assert "OCR_RECOVERED_TEXT_42" in f["extractedText"]


# ---------------------------------------------------------------------------
# 17. Extraction cache — same hash returns cached row without re-extracting
# ---------------------------------------------------------------------------

def test_extraction_cache_hit_skips_extraction(client, fake_anthropic, monkeypatch):
    """When a cached row exists for the file's sha256, we skip _extract_text."""
    pdf = _make_pdf(["TESTO_CACHED_ABC " * 30])
    # Pre-seed a fake cache hit.
    from app.lib import extraction_cache as ec
    fake_row = {
        "hash": ec.sha256_bytes(pdf),
        "extracted_text": "CACHED_RESULT_MARKER ricavi 100",
        "extracted_summary": "",
        "extraction_method": "pdf-parse",
        "pages_json": [{"n": 1, "text": "CACHED_RESULT_MARKER ricavi 100"}],
    }
    monkeypatch.setattr(ec, "lookup", lambda h: fake_row if h == fake_row["hash"] else None)

    extract_calls = {"n": 0}

    def boom(*_a, **_k):
        extract_calls["n"] += 1
        raise AssertionError("_extract_text must NOT be called on cache hit")

    monkeypatch.setattr("app.api.upload._extract_text", boom)

    sid = _make_session(client)
    r = client.post("/api/kbot/upload", json={
        "session_id": sid,
        "files": [{"name": "b.pdf", "type": "application/pdf",
                   "size": len(pdf), "base64": _b64(pdf)}],
    })
    assert r.status_code == 200, r.text
    f = r.json()["files"][0]
    assert "CACHED_RESULT_MARKER" in f["extractedText"]
    assert f["extractionMethod"] == "pdf-parse"
    assert extract_calls["n"] == 0


# ---------------------------------------------------------------------------
# 18. Diagnostics endpoint — basic shape
# ---------------------------------------------------------------------------

def test_diagnostics_endpoint_shape(client, monkeypatch):
    # Anthropic ping is mocked via FakeAnthropic fixture (already active);
    # supabase ping uses our fake table; the rest are real package imports.
    r = client.get("/api/kbot/diagnostics")
    assert r.status_code == 200, r.text
    body = r.json()
    for key in ("status", "checks", "packages", "env", "runtime", "ts"):
        assert key in body, f"missing key {key}"
    assert body["checks"]["supabase"]["status"] == "ok"
    assert body["checks"]["anthropic"]["status"] == "ok"
    assert body["checks"]["pdfplumber"]["status"] == "ok"
    # Never leak the actual key value.
    assert "ANTHROPIC_API_KEY" in body["env"]
    assert body["env"]["ANTHROPIC_API_KEY"] is True
    serialized = r.text
    assert "test-sk-dummy" not in serialized  # value must never appear


def test_diagnostics_requires_internal_key_when_set(client, monkeypatch):
    monkeypatch.setattr("app.api.diagnostics.INTERNAL_API_KEY", "secret-123")
    r = client.get("/api/kbot/diagnostics")
    assert r.status_code == 401
    r2 = client.get("/api/kbot/diagnostics",
                    headers={"Authorization": "Bearer secret-123"})
    assert r2.status_code == 200
