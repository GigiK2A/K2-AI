"""Il modello locale che non risponde non deve far perdere il giro a un reparto.

Il GB10 arriva via tailnet e va e viene: il 19 ago 2026 alle 06:24 finance, operations e
legal sono andati in timeout su Ollama e non hanno prodotto niente, alle 07:15 hanno
girato tutti e tre. L'errore restava solo nei log.
"""
import pytest

from aios.llm import FakeLLM, FallbackLLM, LocalLLMUnreachable


class LocaleGiu:
    """Primario irraggiungibile, come LocalLLM quando la tailnet è giù."""

    def __init__(self):
        self.tentativi = 0

    def complete(self, *, system, user):
        self.tentativi += 1
        raise LocalLLMUnreachable("LocalLLM: Ollama non raggiungibile su http://100.x: timed out")

    def complete_json(self, *, system, user, schema=None):
        self.tentativi += 1
        raise LocalLLMUnreachable("LocalLLM: Ollama non raggiungibile su http://100.x: timed out")


class LocaleRotto:
    """Primario raggiungibile che risponde male: NON è un caso da riserva."""

    def complete(self, *, system, user):
        raise ValueError("nessun oggetto JSON nella risposta")

    def complete_json(self, *, system, user, schema=None):
        raise ValueError("nessun oggetto JSON nella risposta")


def test_locale_giu_passa_alla_riserva():
    primario = LocaleGiu()
    llm = FallbackLLM(primario, FakeLLM(responses=['{"proposte":[{"tipo":"t"}]}']))
    out = llm.complete_json(system="s", user="u")
    assert out == {"proposte": [{"tipo": "t"}]}
    assert primario.tentativi == 1      # il primario è stato provato per primo
    assert llm.fallback_usati == 1


def test_riserva_anche_su_complete_testuale():
    llm = FallbackLLM(LocaleGiu(), FakeLLM(responses=["risposta di riserva"]))
    assert llm.complete(system="s", user="u") == "risposta di riserva"


def test_riserva_costruita_solo_quando_serve():
    """La riserva è un callable: senza guasti non deve nemmeno essere istanziata
    (istanziare AnthropicLLM richiede la API key)."""
    costruzioni = []

    def factory():
        costruzioni.append(1)
        return FakeLLM(responses=["riserva"])

    llm = FallbackLLM(FakeLLM(responses=["dal primario"]), factory)
    assert llm.complete(system="s", user="u") == "dal primario"
    assert costruzioni == []             # mai costruita
    assert llm.fallback_usati == 0


def test_errore_di_contenuto_non_va_in_riserva():
    """Un JSON malformato è un problema del primario e deve emergere, non essere
    mascherato da una risposta della riserva."""
    llm = FallbackLLM(LocaleRotto(), FakeLLM(responses=['{"ok":true}']))
    with pytest.raises(ValueError):
        llm.complete_json(system="s", user="u")
    assert llm.fallback_usati == 0


def test_streaming_usa_la_riserva_se_il_primario_non_ce_l_ha():
    """LocalLLM non ha stream_agentic: la chat multi-agente deve funzionare comunque."""

    class ConStreaming:
        def stream_agentic(self, **kw):
            yield {"phase": "done", "text": "ciao"}

    llm = FallbackLLM(FakeLLM(responses=["x"]), ConStreaming())
    eventi = list(llm.stream_agentic(system="s", user="u", tools=[], tool_exec=None))
    assert eventi == [{"phase": "done", "text": "ciao"}]
