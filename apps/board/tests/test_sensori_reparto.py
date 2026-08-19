"""Un reparto non si ferma perché una fonte è giù, e non inventa lavoro sul vuoto.

Due guasti reali di agosto 2026:
- token Instagram invalidato → `_gather()` del marketing sollevava sul primo read e il
  reparto non produceva NIENTE per giorni;
- tabelle sorgente vuote (`invoices`, `employees`, `project_tasks` a zero righe) → gli
  agenti riempivano il vuoto con solleciti e assunzioni immaginarie, 646 proposte da
  annullare in blocco.
"""
import pytest

from aios.agents import sensori
from aios.agents.domain import DomainAgent, DomainConfig
from aios.agents.marketing import MarketingAgent
from aios.autonomy import ActionType
from aios.founder import default_founder_model
from aios.kernel import Kernel
from aios.llm import FakeLLM
from aios.tools import Tool


# ---- lettura isolata ----
def test_sensore_che_solleva_non_propaga():
    fonti = {}

    def reader(nome, **a):
        raise RuntimeError("Token Instagram scaduto o invalidato dalla Meta API")

    assert sensori.leggi_sicuro(reader, "leggi_profilo_ig", fonti) is None
    assert fonti["leggi_profilo_ig"].startswith("guasto: Token Instagram")


def test_sensore_che_ritorna_error_e_guasto():
    """I connettori env-gated non sollevano: ritornano {'error': ...}."""
    fonti = {}
    assert sensori.leggi_sicuro(lambda n, **a: {"error": "manca la chiave"}, "x", fonti) is None
    assert fonti["x"] == "guasto: manca la chiave"


def test_lista_vuota_e_vuoto_non_guasto():
    fonti = {}
    assert sensori.leggi_sicuro(lambda n, **a: [], "invoices", fonti) is None
    assert fonti["invoices"] == "vuoto"


def test_dati_veri_riportano_il_conteggio():
    fonti = {}
    out = sensori.leggi_sicuro(lambda n, **a: [{"id": 1}, {"id": 2}], "lead", fonti)
    assert out == [{"id": 1}, {"id": 2}]
    assert fonti["lead"] == "ok (2 righe)"


# ---- blocco di stato nel prompt ----
def test_blocco_distingue_vuoto_da_guasto():
    b = sensori.blocco_stato({"lead": "ok (3 righe)", "invoices": "vuoto",
                              "leggi_profilo_ig": "guasto: token invalidato"})
    assert "Con dati: lead" in b
    assert "invoices" in b.split("VUOTE")[1].split("GUASTE")[0]
    assert "token invalidato" in b
    # la regola contro l'invenzione deve esserci sempre
    assert "mai numeri inventati" in b


def test_blocco_vuoto_se_nessuna_fonte():
    assert sensori.blocco_stato({}) == ""


# ---- integrazione: il reparto gira comunque ----
MKT_JSON = '{"proposte":[{"tipo":"seo","titolo":"Piano SEO","contenuto":"c","motivo":"m"}]}'


def _kernel_con_sensori(ig_rotto: bool):
    k = Kernel()
    k.register_tool(Tool(name="leggi_servizi", action_type=None, readonly=True,
                         run=lambda **_: [{"nome": "HOST"}]))
    k.register_tool(Tool(name="leggi_topics", action_type=None, readonly=True,
                         run=lambda **_: [{"titolo": "RAG"}]))
    k.register_tool(Tool(name="leggi_ranking_seo", action_type=None, readonly=True,
                         run=lambda **_: [{"query": "agenti ai", "clicks": 12}]))

    def _ig(**_):
        if ig_rotto:
            raise RuntimeError("Token Instagram scaduto o invalidato dalla Meta API")
        return [{"id": "p1", "like": 10}]

    k.register_tool(Tool(name="leggi_profilo_ig", action_type=None, readonly=True, run=_ig))
    k.register_tool(Tool(name="leggi_post_ig", action_type=None, readonly=True, run=_ig))
    return k


def test_marketing_produce_anche_con_instagram_giu():
    k = _kernel_con_sensori(ig_rotto=True)
    llm = FakeLLM(responses=[MKT_JSON])
    ag = MarketingAgent(kernel=k, llm=llm, founder=default_founder_model(),
                        discover_competitors=False)
    res = ag.run()
    assert len(res.proposals) == 1                     # il reparto ha lavorato
    assert ag.fonti["leggi_profilo_ig"].startswith("guasto")
    assert ag.fonti["leggi_ranking_seo"].startswith("ok")
    # il prompt deve dire all'LLM di non parlare di Instagram e di non inventare
    _system, user = llm.calls[-1]
    assert "Instagram non è disponibile" in user
    assert "STATO DELLE FONTI" in user
    assert "Ranking SEO" in user


def test_marketing_con_instagram_vivo_chiede_analisi_post():
    k = _kernel_con_sensori(ig_rotto=False)
    llm = FakeLLM(responses=[MKT_JSON])
    MarketingAgent(kernel=k, llm=llm, founder=default_founder_model(),
                   discover_competitors=False).run()
    _system, user = llm.calls[-1]
    assert "Valuta i post uno per uno" in user
    assert "Instagram non è disponibile" not in user


DOM_JSON = '{"proposte":[{"tipo":"task","titolo":"T","contenuto":"c","motivo":"m"}]}'


def test_dominio_sopravvive_a_un_sensore_rotto():
    k = Kernel()
    k.register_tool(Tool(name="sensore_ok", action_type=None, readonly=True,
                         run=lambda **_: [{"id": 1}]))
    k.register_tool(Tool(name="sensore_rotto", action_type=None, readonly=True,
                         run=lambda **_: (_ for _ in ()).throw(RuntimeError("giù"))))
    cfg = DomainConfig(name="finance", action=ActionType("finance", "azione"),
                       tool_name="azione_finance",
                       sensors=[("sensore_ok", {}), ("sensore_rotto", {})],
                       system="Sei il CFO.")
    llm = FakeLLM(responses=[DOM_JSON])
    ag = DomainAgent(kernel=k, llm=llm, founder=default_founder_model(), config=cfg)
    res = ag.run()
    assert len(res.proposals) == 1
    assert ag.fonti["sensore_rotto"].startswith("guasto")
    _system, user = llm.calls[-1]
    assert "STATO DELLE FONTI" in user and "sensore_rotto" in user
