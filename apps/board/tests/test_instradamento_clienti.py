"""Chi sa cercare clienti deve ricevere le domande sui clienti.

Solo marketing e vendite hanno il tool `cerca_clienti`. Se una domanda di prospecting
finisce a un altro reparto, quello non può cercare: nel migliore dei casi risponde
«non ci riesco» (è quello che ha fatto legal il 20 ago), nel peggiore elenca aziende
a memoria — che è il bug da cui è partito tutto.

«Dammi 2 aziende in Umbria da contattare, con i contatti» non conteneva NESSUNA parola
chiave del router: è finita al classificatore LLM di riserva, che ha scelto legal.
"""
import pytest

from aios.command import CommandRouter


class LLMSpia:
    """Il classificatore di riserva: registra se viene chiamato e cosa gli si dice."""

    def __init__(self, dominio="legal"):
        self.dominio, self.chiamate, self.system = dominio, 0, ""

    def complete_json(self, *, system, user, schema=None):
        self.chiamate += 1
        self.system = system
        return {"dominio": self.dominio}


class Kernel:
    _supabase = None


class Platform:
    kernel = Kernel()


def _router(llm=None):
    return CommandRouter(Platform(), llm or LLMSpia())


PROSPECTING = [
    "Dammi 2 aziende in Umbria da contattare questa settimana, con i contatti.",
    "Trovami 3 possibili clienti in Umbria escludendo gli studi di ingegneria",
    "cerca clienti nel settore agroalimentare in provincia di Perugia",
    "quanti prospect abbiamo in pipeline?",
    "aziende del manifatturiero da contattare a Terni",
    "fai una ricerca di nuovi clienti",
    "i clienti che non rispondono da un mese",     # plurale: prima non matchava
]


@pytest.mark.parametrize("domanda", PROSPECTING)
def test_le_domande_sui_clienti_vanno_a_chi_sa_cercare(domanda):
    llm = LLMSpia()
    assert _router(llm).route(domanda) == "vendite"
    assert llm.chiamate == 0, "deciso per parola chiave, senza spendere una chiamata LLM"


def test_il_singolare_funzionava_gia_e_continua():
    assert _router().route("aggiorna la scheda del cliente Rossi") == "vendite"


def test_gli_altri_reparti_non_vengono_rubati():
    """I pattern nuovi non devono spostare quello che era già instradato bene."""
    r = _router()
    assert r.route("prepara il contratto di fornitura") == "legal"
    assert r.route("quante fatture scadute abbiamo?") == "finance"
    assert r.route("scrivi la caption del post di domani") == "marketing"
    assert r.route("a che punto è la commessa del capannone?") == "operations"
    # vince la prima parola chiave in ordine di reparto: «pubblica l'annuncio per il
    # candidato» va a marketing, non a hr. Comportamento preesistente, non toccato qui.
    assert r.route("fissa il colloquio con il candidato junior") == "hr"


def test_il_classificatore_di_riserva_sa_di_chi_e_la_ricerca():
    """Quando nessuna parola chiave matcha si finisce sull'LLM: almeno sappia la regola."""
    llm = LLMSpia(dominio="vendite")
    assert _router(llm).route("mi serve una mano con una cosa nuova") == "vendite"
    assert llm.chiamate == 1
    assert "vendite" in llm.system and "cercare sul web" in llm.system


def test_un_dominio_inventato_dal_modello_non_passa():
    llm = LLMSpia(dominio="ceo")          # «ceo» non è un reparto del board
    assert _router(llm).route("una cosa vaga") == "marketing"
