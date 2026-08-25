"""Regressioni dei fix di sicurezza dell'audit K-BOT (ago 2026).

Ogni test qui corrisponde a un buco chiuso: se torna verde per il motivo
sbagliato (perché qualcuno ha rimosso il controllo) il test deve fallire.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("NEXT_PUBLIC_SUPABASE_URL", "https://x.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "x")
os.environ.setdefault("ANTHROPIC_API_KEY", "x")

from app.lib import email as email_lib  # noqa: E402
from app.lib import skills  # noqa: E402
from app.api.upload import _storage_content_type  # noqa: E402


# --- email: il titolo del report è output LLM, non markup ----------------------

def test_titolo_report_non_inietta_html_nella_mail(monkeypatch):
    """`report_title` viene da analysis.meta.title (modello, quindi guidabile da
    conversazione e file caricati) e finiva grezzo dentro l'HTML di un'email
    firmata DKIM da noreply@k2-ai.it, con l'operatore in BCC."""
    sent = {}

    class _Resp:
        status_code = 200
        text = "ok"

    def _fake_post(url, headers=None, json=None, timeout=None):
        sent.update(json or {})
        return _Resp()

    monkeypatch.setattr(email_lib, "RESEND_API_KEY", "re_test")
    monkeypatch.setattr(email_lib.httpx, "post", _fake_post)

    payload_title = 'X</strong><a href="https://evil.example">Scarica</a><strong>'
    ok = email_lib.send_report_ready_email(
        to_email="cliente@example.com",
        report_url="https://proj.supabase.co/storage/v1/object/sign/x.pdf?token=t",
        report_title=payload_title,
    )
    assert ok is True
    # Il payload resta visibile come TESTO ma non come markup: nessun link nuovo.
    assert '<a href="https://evil.example"' not in sent["html"]
    assert "&lt;/strong&gt;" in sent["html"]  # il markup è stato neutralizzato
    # Gli unici due <a> sono i nostri: il bottone al report e il link ai contatti.
    assert sent["html"].count("<a href=") == 2


def test_report_url_non_https_non_viene_spedito(monkeypatch):
    monkeypatch.setattr(email_lib, "RESEND_API_KEY", "re_test")

    def _explode(*a, **kw):  # pragma: no cover - non deve essere chiamata
        raise AssertionError("nessuna email deve partire con un URL non valido")

    monkeypatch.setattr(email_lib.httpx, "post", _explode)
    assert email_lib.send_report_ready_email(
        to_email="cliente@example.com",
        report_url="javascript:alert(1)",
        report_title="Report",
    ) is False


# --- skills: il nome è una directory, non un path ------------------------------

def test_skill_name_non_esce_da_skills_dir():
    """`forced_skills` arriva dal body di /api/kbot/message e finiva in
    `SKILLS_DIR / name` senza validazione: `..` esce dalla base e un path
    assoluto la scarta del tutto (semantica di pathlib)."""
    for bad in ("../../etc", "/opt/config", "..", "a/b", "x\x00y", ""):
        assert skills._skill_root(bad) is None
        assert skills.load_skill(bad) is None


def test_skill_name_valido_resta_valido():
    root = skills._skill_root("brand-voice")
    assert root is not None and root.name == "brand-voice"


# --- upload: il content-type servito lo decide il server -----------------------

def test_content_type_upload_ignora_quello_dichiarato():
    """`{"name":"nota.txt","type":"text/html"}` superava la whitelist (l'estensione
    è ammessa) e l'oggetto veniva salvato come text/html: HTML attivo servito
    dall'origin dello storage."""
    assert _storage_content_type("nota.txt", "text/html") == "text/plain"
    assert _storage_content_type("dati.csv", "image/svg+xml") == "text/csv"
    assert _storage_content_type("bilancio.pdf", "text/html") == "application/pdf"
    assert _storage_content_type("mappa.xml", "text/html") == "text/plain"
