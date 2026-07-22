"""Output Quality Engine (review "AI Proof"): l'utente non vede mai HTML, template,
placeholder, artefatti tecnici, markdown rotto o tipografia sporca. Polish deterministico,
idempotente, fail-open — agganciato al choke point del testo visibile della chat.
"""
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

for _name, _attrs in (("dotenv", {"load_dotenv": lambda *a, **k: False}),):
    if _name not in sys.modules:
        _m = types.ModuleType(_name)
        [setattr(_m, k, v) for k, v in _attrs.items()]
        sys.modules[_name] = _m
try:  # pragma: no cover
    from supabase import Client as _ProbeClient  # noqa: F401
except Exception:  # pragma: no cover
    _m = types.ModuleType("supabase")
    _m.Client, _m.create_client = object, (lambda *a, **k: None)
    sys.modules["supabase"] = _m

from app.lib import output_quality as OQ  # noqa: E402


# ── HTML: mai tag, contenuto conservato, entità decodificate ─────────────────────────────
def test_html_converted_never_shown():
    out = OQ.polish("Piano:<br><p>Fase 1</p><ul><li>uno</li><li>due</li></ul>"
                    "<strong>chiave</strong><script>alert(1)</script><!-- nota -->")
    assert "<" not in out and ">" not in out
    assert "Fase 1" in out and "- uno" in out and "chiave" in out
    assert "alert" not in out and "nota" not in out


def test_html_entities_decoded_without_tags():
    out = OQ.polish("Il margine &egrave; basso &amp; il DSO cresce")
    assert "è" in out and "&" in out and "&egrave;" not in out and "&amp;" not in out


# ── Placeholder / template: mai {{}}, ${}, [INSERIRE], TODO, lorem, N/D ──────────────────
def test_placeholders_removed():
    out = OQ.polish("Report per {{azienda}} con budget ${budget}. [INSERIRE dettaglio] "
                    "TODO: rifinire. Lorem ipsum dolor sit amet. Margine: N/D.")
    for bad in ("{{", "${", "INSERIRE", "TODO", "orem ipsum", "N/D"):
        assert bad not in out, bad
    assert "da definire" in out            # N/D → dichiarato, non nascosto


def test_ellipsis_preserved():
    assert "..." in OQ.polish("Vediamo... direi di sì.")


# ── Artefatti tecnici: marker, stack trace, UUID, frammenti SSE ──────────────────────────
def test_technical_artifacts_removed():
    out = OQ.polish("Ok.\nNUOVO_BLOCCO_START {\"a\":1} NUOVO_BLOCCO_END\n"
                    "Traceback (most recent call last):\n  File \"x.py\", line 1\nBoom\n"
                    "1c5847f5-c23d-4f7a-86cd-5dec816384bb\n"
                    "data: {\"delta\": \"x\"}\nFine.")
    for bad in ("_START", "_END", "Traceback", "File \"", "1c5847f5", "data:"):
        assert bad not in out, bad
    assert "Ok." in out and "Fine." in out


# ── Tipografia + liste + dedup ───────────────────────────────────────────────────────────
def test_typography_normalized():
    out = OQ.polish("Troppi  spazi , “virgolette” e trattino‑esotico")
    assert "  " not in out and " ," not in out
    assert "«virgolette»" in out and "‑" not in out


def test_lists_uniform():
    out = OQ.polish("• uno\n* due\n– tre\n- quattro")
    assert out.count("- ") == 4 and "•" not in out and "*" not in out and "–" not in out


def test_consecutive_duplicates_removed():
    out = OQ.polish("Questa frase è ripetuta identica.\nQuesta frase è ripetuta identica.\nAltra.")
    assert out.count("ripetuta identica") == 1


# ── proprietà della pipeline ─────────────────────────────────────────────────────────────
def test_idempotent_and_fail_open():
    dirty = "Testo <b>x</b> {{y}} N/D\n\n\n\nfine"
    once = OQ.polish(dirty)
    assert OQ.polish(once) == once          # idempotente
    assert OQ.polish("") == ""              # vuoto → vuoto, mai eccezioni
    assert OQ.polish(None) is None          # fail-open sul non-testo


def test_clean_text_untouched():
    clean = "Il DSO è salito a 128 giorni: conviene rivedere gli incassi.\n- azione uno\n- azione due"
    assert OQ.polish(clean) == clean


def test_final_checks_telemetry():
    assert OQ.final_checks("Testo pulito.") == []
    failed = OQ.final_checks("resta <div> e {{x}} e N/D e ```")
    assert set(failed) >= {"html_tag", "template_var", "nd_placeholder", "unclosed_fence"}


# ── wiring: il testo visibile della chat passa dal polish ────────────────────────────────
def test_visible_chat_text_polished():
    from app.api.message import _extract_gated_summary
    raw = ("Ecco l'analisi:<br><strong>margine in calo</strong> per {{azienda}}.\n"
           "Serve una verifica sugli incassi.\n"
           "DIAGNOSI_STATO_START {\"fase\":\"diagnosi\",\"ipotesi\":[{\"t\":\"x\",\"s\":\"aperta\"}],"
           "\"manca\":null,\"confidenza\":\"media\"} DIAGNOSI_STATO_END")
    merged = [{"role": "user", "content": "com'è il margine?"},
              {"role": "assistant", "content": "ciao"},
              {"role": "user", "content": "dimmi"}]
    visible, summary, diagnosi = _extract_gated_summary(raw, merged, {})
    assert "<" not in visible and "{{" not in visible
    assert "margine in calo" in visible
    assert "DIAGNOSI_STATO" not in visible
