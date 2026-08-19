"""Gli agenti devono ricevere METODO, non etichette.

Misura del 19 ago 2026: 312 playbook in libreria per 3,2 milioni di caratteri, e gli
agenti ne usavano ~3.100 in tutto (0,1%) — di cui la parte letta era frontmatter YAML.
Quattro reparti su cinque (finance, operations, legal, HR) avevano `skill_focus=[]` e
non aprivano un solo playbook.
"""
import pytest

from aios.agents.domain import (SKILL_CARATTERI, SKILL_PER_REPARTO, DomainAgent,
                                DomainConfig)
from aios.agents.marketing import MarketingAgent
from aios.autonomy import ActionType
from aios.founder import default_founder_model
from aios.kernel import Kernel
from aios.llm import FakeLLM
from aios.skills import SkillLibrary

DOM_JSON = '{"proposte":[{"tipo":"task","titolo":"T","contenuto":"c","motivo":"m"}]}'
MKT_JSON = '{"proposte":[{"tipo":"seo","titolo":"T","contenuto":"c","motivo":"m"}]}'


class SkillFinte:
    """Libreria con una skill in formato reale: frontmatter + intro + metodo."""

    TESTO = ("---\n"
             "name: campaign-plan\n"
             "description: Genera un brief di campagna completo.\n"
             'argument-hint: "<obiettivo>"\n'
             "---\n\n"
             "# Campaign Plan\n\n"
             "> Nota sui placeholder da ignorare.\n\n"
             + ("Introduzione lunga e non operativa. " * 60) + "\n\n"
             "## Metodo\n\n1. Definisci l'obiettivo misurabile\n2. Segmenta il pubblico\n"
             "3. Scegli i canali con il costo per lead atteso\n")

    def names(self):
        return ["campaign-plan", "altra-skill"]

    def load(self, name):
        if name not in self.names():
            raise KeyError(name)
        return self.TESTO

    def estratto(self, name, cap=2200):
        return SkillLibrary.estratto(self, name, cap)

    _SEZIONI_OPERATIVE = SkillLibrary._SEZIONI_OPERATIVE

    def for_domain(self, dominio, k=12):
        return ["campaign-plan", "altra-skill"][:k]


# ---- estratto: salta l'intestazione, punta al metodo ----
def test_estratto_toglie_il_frontmatter():
    testo = SkillFinte().estratto("campaign-plan", 3000)
    assert "name: campaign-plan" not in testo
    assert "argument-hint" not in testo


def test_estratto_parte_dal_metodo_se_non_ci_sta_tutto():
    """Con budget stretto meglio la procedura che l'introduzione."""
    testo = SkillFinte().estratto("campaign-plan", 300)
    assert "## Metodo" in testo
    assert "costo per lead" in testo or "obiettivo misurabile" in testo
    assert "Introduzione lunga" not in testo


def test_estratto_rispetta_il_budget():
    assert len(SkillFinte().estratto("campaign-plan", 200)) <= 200


def test_libreria_vera_non_restituisce_frontmatter():
    """Guardia sulla libreria reale: nessun estratto deve iniziare col frontmatter."""
    lib = SkillLibrary()
    nomi = lib.names()[:12]
    assert nomi, "libreria vuota: il test non verifica niente"
    for n in nomi:
        t = lib.estratto(n, 800)
        assert not t.startswith("---"), f"{n}: estratto ancora con frontmatter"
        assert "argument-hint:" not in t[:200], f"{n}: intestazione nell'estratto"


# ---- i reparti ricevono il metodo ----
def _agente_dominio(nome_reparto, skill_focus):
    k = Kernel()
    cfg = DomainConfig(name=nome_reparto, action=ActionType(nome_reparto, "azione"),
                       tool_name=f"azione_{nome_reparto}", sensors=[],
                       system="Sei il responsabile.", skill_focus=skill_focus)
    llm = FakeLLM(responses=[DOM_JSON])
    return llm, DomainAgent(kernel=k, llm=llm, founder=default_founder_model(),
                            config=cfg, skills=SkillFinte())


@pytest.mark.parametrize("reparto", ["finance", "operations", "legal", "hr"])
def test_i_reparti_senza_skill_curate_ricevono_quelle_instradate(reparto):
    """Erano i quattro con skill_focus=[]: adesso `for_domain` li copre."""
    llm, ag = _agente_dominio(reparto, [])
    ag.run()
    _system, user = llm.calls[-1]
    assert "## SKILL: campaign-plan" in user
    assert "## Metodo" in user or "obiettivo misurabile" in user


def test_col_libreria_vera_il_metodo_e_sostanzioso():
    """La misura che conta, sui playbook reali: prima il finance riceveva 0 caratteri
    di metodo, ora deve riceverne migliaia."""
    k = Kernel()
    cfg = DomainConfig(name="finance", action=ActionType("finance", "azione"),
                       tool_name="azione_finance", sensors=[], system="Sei il CFO.")
    llm = FakeLLM(responses=[DOM_JSON])
    DomainAgent(kernel=k, llm=llm, founder=default_founder_model(), config=cfg,
                skills=SkillLibrary()).run()
    _system, user = llm.calls[-1]
    assert "## SKILL:" in user, "il finance non ha ricevuto nessun playbook"
    blocco = user[user.index("## SKILL:"):]
    assert len(blocco) > 4000, f"solo {len(blocco)} caratteri di metodo: troppo poco"
    assert user.count("## SKILL:") >= 3, "troppo pochi playbook instradati"


def test_il_marketing_non_riceve_piu_solo_l_etichetta():
    k = Kernel()
    llm = FakeLLM(responses=[MKT_JSON])
    MarketingAgent(kernel=k, llm=llm, founder=default_founder_model(),
                   skills=SkillFinte(), discover_competitors=False).run()
    _system, user = llm.calls[-1]
    assert "FRAMEWORK (estratti operativi)" in user
    assert "name: campaign-plan" not in user      # niente frontmatter
    assert "## Metodo" in user or "obiettivo misurabile" in user


def test_tetti_configurabili():
    assert 1 <= SKILL_PER_REPARTO <= 10
    assert SKILL_CARATTERI >= 800
