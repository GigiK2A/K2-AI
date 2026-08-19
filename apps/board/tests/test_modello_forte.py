"""«Forte» deve significare forte, e la riserva deve reggere anche il guasto del forte.

Difetto trovato il 19 ago 2026 guardando la configurazione reale: con
AIOS_LLM_BACKEND=local, `_make_llm(strong=True)` ritornava lo STESSO modello locale con
solo più token. Sonnet non entrava mai nel giro degli agenti, quindi «il giudizio passa
al modello forte» era falso in produzione.

E il fallback ripiegava solo su Ollama: con ANTHROPIC_BASE_URL che puntava a un tunnel
Cloudflare morto, ogni chiamata Anthropic moriva con "Connection error." senza riserva.
"""
import pytest

from aios.llm import FakeLLM, FallbackLLM, LocalLLM, LocalLLMUnreachable, guasto_di_trasporto
from aios.platform import _make_llm


# ---- riconoscimento del guasto ----
class APIConnectionError(Exception):
    """Stesso nome della classe dell'SDK Anthropic."""


class BadRequestError(Exception):
    pass


class AuthenticationError(Exception):
    """401: chiave non valida. È esattamente quello che avevamo in produzione."""


class RateLimitError(Exception):
    pass


class ErroreConStatus(Exception):
    def __init__(self, status_code):
        super().__init__(f"http {status_code}")
        self.status_code = status_code


def test_ollama_giu_e_trasporto():
    assert guasto_di_trasporto(LocalLLMUnreachable("non raggiungibile")) is True


def test_connessione_anthropic_e_trasporto():
    assert guasto_di_trasporto(APIConnectionError("Connection error.")) is True
    assert guasto_di_trasporto(TimeoutError("timeout")) is True


def test_chiave_non_valida_e_provider_inutilizzabile():
    """Il 401 trovato in produzione: insistere è inutile, la riserva è la risposta."""
    assert guasto_di_trasporto(AuthenticationError("API key is invalid.")) is True


def test_rate_limit_e_provider_inutilizzabile():
    assert guasto_di_trasporto(RateLimitError("slow down")) is True


def test_riconosce_anche_il_solo_status_code():
    assert guasto_di_trasporto(ErroreConStatus(401)) is True
    assert guasto_di_trasporto(ErroreConStatus(529)) is True
    assert guasto_di_trasporto(ErroreConStatus(400)) is False


def test_errore_di_contenuto_non_e_trasporto():
    assert guasto_di_trasporto(BadRequestError("prompt troppo lungo")) is False
    assert guasto_di_trasporto(ValueError("nessun oggetto JSON")) is False


# ---- la riserva scatta anche se cade il forte ----
class ForteGiu:
    def __init__(self):
        self.tentativi = 0

    def complete_json(self, **kw):
        self.tentativi += 1
        raise APIConnectionError("Connection error.")

    def complete(self, **kw):
        self.tentativi += 1
        raise APIConnectionError("Connection error.")


def test_con_chiave_non_valida_i_reparti_lavorano_comunque():
    """Scenario reale di stasera: giudizio su Anthropic, chiave invalida. Senza riserva
    l'agente si sarebbe rotto al primo heartbeat."""
    class ChiaveRotta:
        def complete_json(self, **kw):
            raise AuthenticationError("API key is invalid.")

    llm = FallbackLLM(ChiaveRotta(), FakeLLM(responses=['{"proposte":[{"tipo":"t"}]}']))
    assert llm.complete_json(system="s", user="u") == {"proposte": [{"tipo": "t"}]}
    assert llm.fallback_usati == 1


def test_se_anthropic_non_risponde_si_ripiega_sul_locale():
    primario = ForteGiu()
    llm = FallbackLLM(primario, FakeLLM(responses=['{"proposte":[]}']))
    assert llm.complete_json(system="s", user="u") == {"proposte": []}
    assert primario.tentativi == 1 and llm.fallback_usati == 1


def test_errore_di_contenuto_non_viene_mascherato():
    class Contenuto:
        def complete_json(self, **kw):
            raise BadRequestError("schema non valido")

    llm = FallbackLLM(Contenuto(), FakeLLM(responses=['{"ok":true}']))
    with pytest.raises(BadRequestError):
        llm.complete_json(system="s", user="u")
    assert llm.fallback_usati == 0


# ---- la fabbrica costruisce le priorità giuste ----
def test_backend_locale_il_giudizio_e_anthropic(monkeypatch):
    monkeypatch.setenv("AIOS_LLM_BACKEND", "local")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    monkeypatch.setattr("aios.llm._anthropic_client", lambda key: object())
    forte = _make_llm(max_tokens=8192, strong=True)
    assert isinstance(forte, FallbackLLM)
    # il PRIMARIO del giudizio deve essere Anthropic, il ripiego il locale
    assert type(forte._primario).__name__ == "AnthropicLLM"
    assert isinstance(forte._backup(), LocalLLM)


def test_backend_locale_il_lavoro_normale_resta_locale(monkeypatch):
    monkeypatch.setenv("AIOS_LLM_BACKEND", "local")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    monkeypatch.setattr("aios.llm._anthropic_client", lambda key: object())
    leggero = _make_llm(max_tokens=4096)
    assert isinstance(leggero, FallbackLLM)
    assert isinstance(leggero._primario, LocalLLM)     # letture sul locale, come prima


def test_senza_chiave_anthropic_resta_solo_il_locale(monkeypatch):
    monkeypatch.setenv("AIOS_LLM_BACKEND", "local")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert isinstance(_make_llm(max_tokens=8192, strong=True), LocalLLM)
