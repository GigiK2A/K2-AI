"""Il reparto deve sapere com'è finita ieri.

Caso reale: 10 insert su `privacy_registro_trattamenti` e 6 update su `policy_register`
falliti uno dopo l'altro, perché al legale nessuno ha mai detto che quelle colonne non
esistono. Il dedup evita i doppioni in coda; solo il ritorno dell'errore evita di
ripetere l'errore domani.
"""
from aios.agents import esperienza
from aios.agents.domain import DomainAgent, DomainConfig
from aios.autonomy import ActionType
from aios.founder import default_founder_model
from aios.kernel import Kernel
from aios.llm import FakeLLM

DOM_JSON = '{"proposte":[{"tipo":"task","titolo":"T","contenuto":"c","motivo":"m"}]}'


class Client:
    """Supabase finto con audit e deliverable."""

    def __init__(self, audit=None, deliverables=None):
        self._audit = audit if audit is not None else []
        self._deliv = deliverables if deliverables is not None else []
        self.query = []

    def select(self, table, params):
        self.query.append((table, dict(params)))
        return self._audit if table == "aios_audit" else (
            self._deliv if table == "aios_deliverables" else [])

    def insert(self, table, row):
        return [{"id": 1, **row}]

    def update(self, table, filters, patch):
        return [{"id": 1, **patch}]


def _fallimento(titolo, tabella, errore):
    return {"seq": 1, "detail": {
        "args": {"titolo": titolo, "azione": {"tabella": tabella, "op": "insert"}},
        "esito": {"ok": False, "tabella": tabella, "op": "insert", "errore": errore}}}


def test_legge_i_fallimenti_con_la_causa():
    c = Client(audit=[_fallimento("Registro trattamenti", "privacy_registro_trattamenti",
                                  "nessun campo riconosciuto: ['finalità']")])
    out = esperienza.fallimenti_recenti(c, "legal.azione")
    assert out[0]["tabella"] == "privacy_registro_trattamenti"
    assert "finalità" in out[0]["errore"]
    # deve filtrare per reparto e per event=failed, non scaricare tutto l'audit
    _tab, params = c.query[0]
    assert params["action_key"] == "eq.legal.azione"
    assert params["event"] == "eq.failed"
    assert "limit" in params


def test_blocco_dice_di_non_ripetere():
    c = Client(audit=[_fallimento("Voce registro", "policy_register",
                                  "nessuna riga corrisponde al match")])
    testo = esperienza.blocco_esperienza(c, "legal", "legal.azione")
    assert "NON hanno scritto niente" in testo
    assert "policy_register" in testo
    assert "non inventarla una seconda volta" in testo


def test_blocco_elenca_il_gia_proposto():
    c = Client(deliverables=[{"titolo": "Piano onboarding BDM"},
                             {"titolo": "Piano onboarding BDM"},   # duplicato
                             {"titolo": "Kit colloquio BDM"}])
    testo = esperienza.blocco_esperienza(c, "hr", "hr.azione")
    assert "Hai già prodotto questo" in testo
    assert testo.count("Piano onboarding BDM") == 1     # deduplicato
    assert "Kit colloquio BDM" in testo


def test_niente_esperienza_niente_blocco():
    assert esperienza.blocco_esperienza(Client(), "hr", "hr.azione") == ""
    assert esperienza.blocco_esperienza(None, "hr", "hr.azione") == ""


def test_audit_rotto_non_ferma_l_agente():
    class Rotto:
        def select(self, table, params):
            raise RuntimeError("audit giù")

    assert esperienza.fallimenti_recenti(Rotto(), "x.y") == []
    assert esperienza.blocco_esperienza(Rotto(), "hr", "hr.azione") == ""


def test_l_esperienza_arriva_nel_prompt_del_reparto():
    c = Client(audit=[_fallimento("Voce registro", "policy_register", "colonna inesistente")],
               deliverables=[{"titolo": "Adeguamento ToS art.50"}])
    k = Kernel()
    cfg = DomainConfig(name="legal", action=ActionType("legal", "azione"),
                       tool_name="azione_legal", sensors=[], system="Sei il legale.")
    llm = FakeLLM(responses=[DOM_JSON])
    DomainAgent(kernel=k, llm=llm, founder=default_founder_model(), config=cfg,
                deliverable_client=c).run()
    _system, user = llm.calls[-1]
    assert "LA TUA ESPERIENZA" in user
    assert "colonna inesistente" in user
    assert "Adeguamento ToS art.50" in user
