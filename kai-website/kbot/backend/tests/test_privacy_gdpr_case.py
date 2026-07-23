"""Review GDPR/privacy/AI su immagini (test reale "app outfit"): niente checklist meccanica
foto=biometria=art.9=consenso; basi giuridiche per finalità; DPIA a scoring non a keyword;
ruoli corretti nel data breach (72h = titolare→Garante); server UE ≠ niente trasferimenti;
certificazioni = evidenze non obblighi; provider = prodotto specifico; conclusioni
condizionate con livelli di affidabilità. Macro: qualificazione del caso prima di rispondere.
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

from app.lib import privacy_case  # noqa: E402

_OUTFIT = ("ho creato una nuova applicazione che genera outfit. inserisci le tue foto, una AI "
           "analizza come sei e genera outfit col tuo viso e la tua forma fisica. vorrei "
           "capire se secondo il GDPR è tutto in regola")


# ── rilevazione del caso privacy/AI su immagini ──────────────────────────────────────────
def test_outfit_case_detected():
    assert privacy_case.is_privacy_ai_case(_OUTFIT)
    assert privacy_case.is_privacy_ai_case(
        "per il fatto che le foto vanno su server extra UE è un problema per la privacy?")
    assert privacy_case.is_privacy_ai_case(
        "usiamo il riconoscimento facciale per l'accesso, serve il consenso esplicito?")


def test_non_visual_or_non_privacy_not_detected():
    # privacy senza dati visivi → il modulo immagini NON scatta
    assert not privacy_case.is_privacy_ai_case("devo aggiornare l'informativa privacy del sito?")
    # dati visivi senza tema privacy → non scatta
    assert not privacy_case.is_privacy_ai_case("che foto metto sul profilo Instagram aziendale?")
    assert not privacy_case.is_privacy_ai_case("come riduco i tempi di incasso?")
    assert privacy_case.privacy_hint("come riduco i tempi di incasso?") == ""


# ── contenuto del frame: i 10 errori della review ────────────────────────────────────────
def test_hint_foto_not_automatically_biometric():
    h = privacy_case.privacy_hint(_OUTFIT)
    assert "FOTO ≠ BIOMETRIA AUTOMATICA" in h
    assert "IDENTIFICAZIONE UNIVOCA" in h
    assert "«foto = biometria = art. 9 = consenso esplicito»" in h   # equazione vietata
    assert "embedding" in h and "immagine generata" in h             # tassonomia


def test_hint_legal_bases_per_purpose():
    h = privacy_case.privacy_hint(_OUTFIT)
    assert "BASI GIURIDICHE PER FINALITÀ" in h
    assert "art. 6" in h and "art. 9" in h                           # separate, non confuse
    assert "esecuzione del contratto" in h
    assert "SEPARATA" in h                                           # training = finalità a parte


def test_hint_dpia_scored_not_automatic():
    h = privacy_case.privacy_hint(_OUTFIT)
    assert "MAI «obbligatoria per legge» in automatico" in h
    assert "obbligatoria / altamente consigliata / prudenziale / elementi" in h


def test_hint_breach_roles_72h():
    h = privacy_case.privacy_hint(_OUTFIT)
    assert "RESPONSABILE notifica al TITOLARE senza ingiustificato ritardo" in h
    assert "TITOLARE" in h and "Garante entro 72 ore" in h


def test_hint_transfers_beyond_server_location():
    h = privacy_case.privacy_hint(_OUTFIT)
    assert "NON equivale ad assenza di trasferimenti" in h
    assert "sub-responsabili" in h
    assert "Transfer Impact Assessment" in h and "art. 49" in h
    assert "verifica il provider concreto" in h                      # no «USA sì/no» generico


def test_hint_provider_product_and_certifications():
    h = privacy_case.privacy_hint(_OUTFIT)
    assert "PRODOTTO SPECIFICO" in h
    assert "Business/Enterprise" in h
    assert "Non dire «devi contattarli» come primo passo" in h
    assert "NON" in h and "obblighi di legge" in h                   # ISO/SOC = evidenze
    assert "CONCLUSIONE SEMPRE CONDIZIONATA" in h


# ── macro: qualificazione del caso + livelli di affidabilità + validazione normativa ─────
def _prompt(text):
    from app.lib.prompts import build_system_prompt_v2
    return build_system_prompt_v2([], {"messages": [{"role": "user", "content": text}],
                                       "collected_data": {}}, required_fields_hint="")


def test_macro_sections_always_present():
    p = _prompt("come riduco i tempi di incasso?")
    assert "QUALIFICAZIONE DEL CASO" in p
    assert "capire il SISTEMA TECNICO" in p                          # sequenza prima di classificare
    assert "LIVELLI DI AFFIDABILITÀ" in p
    assert "non determinabile con i dati disponibili" in p
    assert "VALIDAZIONE NORMATIVA E RUOLI" in p
    assert "mai trasformare una buona pratica in un obbligo di legge" in p
    assert "MAI dichiarare la conformità" in p


def test_privacy_hint_injected_only_when_relevant():
    assert "CASO PRIVACY/AI SU IMMAGINI" in _prompt(_OUTFIT)
    assert "CASO PRIVACY/AI SU IMMAGINI" not in _prompt("come riduco i tempi di incasso?")
