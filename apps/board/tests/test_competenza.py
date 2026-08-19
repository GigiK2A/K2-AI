"""Indice completo di tutte le skill del reparto + testo pieno di quelle scelte.

Un reparto ha fra 24 e 77 playbook per 260.000-1.047.000 caratteri: metterli tutti nel
prompt sarebbe un quarto di milione di token e annegherebbe i dati dell'azienda. Quindi
l'agente vede SEMPRE l'indice di tutto (4-8k caratteri) e apre per esteso quelli che
servono ai dati di oggi.
"""
from aios.agents import competenza
from aios.llm import FakeLLM
from aios.skills import SkillLibrary


class LibFinta:
    SKILLS = {
        "prezzi-pmi": "---\nname: prezzi-pmi\ndescription: Listino e margini per PMI.\n---\n\n"
                      "# Prezzi\n\nIntro.\n\n## Metodo\n1. Calcola il margine di contribuzione\n",
        "recupero-crediti": "---\nname: recupero-crediti\ndescription: Solleciti e DSO.\n---\n\n"
                            "# Crediti\n\n## Checklist\n- Estrai le scadute oltre 30 giorni\n",
        "budget-annuale": "---\nname: budget-annuale\ndescription: Costruire il budget.\n---\n\n"
                          "# Budget\n\n## Passi\n1. Parti dai ricavi ricorrenti\n",
    }

    def names(self):
        return list(self.SKILLS)

    def load(self, name):
        if name not in self.SKILLS:
            raise KeyError(name)
        return self.SKILLS[name]

    def describe(self, name):
        return self.SKILLS[name].split("description: ")[1].split("\n")[0]

    def estratto(self, name, cap=2200):
        return SkillLibrary.estratto(self, name, cap)

    _SEZIONI_OPERATIVE = SkillLibrary._SEZIONI_OPERATIVE

    def for_domain(self, dominio, k=12):
        return list(self.SKILLS)[:k]


def test_indice_elenca_tutto_con_le_descrizioni():
    lib = LibFinta()
    nomi = competenza.nomi_reparto(lib, "finance", [])
    idx = competenza.indice(lib, nomi)
    assert "3 playbook" in idx
    for n in lib.names():
        assert n in idx
    assert "Listino e margini per PMI" in idx      # la descrizione, non solo il nome


def test_le_curate_vengono_prima():
    nomi = competenza.nomi_reparto(LibFinta(), "finance", ["budget-annuale"])
    assert nomi[0] == "budget-annuale"
    assert len(nomi) == 3 and len(set(nomi)) == 3   # nessun duplicato


def test_scelta_del_modello_rispettata():
    llm = FakeLLM(responses=['{"skill":["recupero-crediti"]}'])
    scelti = competenza.scegli(llm, ["prezzi-pmi", "recupero-crediti", "budget-annuale"],
                               "indice", "fatture scadute: 12", quante=1)
    assert scelti == ["recupero-crediti"]


def test_nomi_inventati_scartati_e_ripiego():
    """Se il modello inventa nomi, il reparto non resta senza metodo."""
    llm = FakeLLM(responses=['{"skill":["skill-che-non-esiste"]}'])
    scelti = competenza.scegli(llm, ["prezzi-pmi", "recupero-crediti"], "i", "c", quante=2)
    assert scelti == ["prezzi-pmi", "recupero-crediti"]


def test_modello_rotto_non_toglie_il_metodo():
    class Rotto:
        def complete_json(self, **kw):
            raise RuntimeError("giù")

    scelti = competenza.scegli(Rotto(), ["prezzi-pmi", "recupero-crediti"], "i", "c", quante=1)
    assert scelti == ["prezzi-pmi"]


def test_blocco_metodo_senza_frontmatter():
    testo = competenza.blocco_metodo(LibFinta(), ["recupero-crediti"], 2000)
    assert "## SKILL: recupero-crediti" in testo
    assert "description:" not in testo
    assert "oltre 30 giorni" in testo


def test_competenza_mette_insieme_indice_e_metodo():
    llm = FakeLLM(responses=['{"skill":["recupero-crediti"]}'])
    testo = competenza.competenza(LibFinta(), llm, "finance", [], "fatture scadute")
    assert "LA TUA BIBLIOTECA" in testo and "# METODO" in testo
    assert "prezzi-pmi" in testo                  # nell'indice c'è tutto
    assert "oltre 30 giorni" in testo             # per esteso solo la scelta


def test_senza_libreria_nessun_blocco():
    assert competenza.competenza(None, None, "finance", [], "dati") == ""


def test_esigenza_qualita_chiede_numeri_e_alternativa():
    t = competenza.ESIGENZA_QUALITA
    assert f"massimo {competenza.PROPOSTE_MAX} proposte" in t
    assert "NUMERI" in t and "alternativa" in t and "cambiare idea" in t
    assert competenza.PROPOSTE_MAX <= 5, "il tetto alto premia la quantità"


def test_indice_reale_sta_nel_budget():
    """Sui playbook veri l'indice completo deve restare gestibile (~2k token)."""
    lib = SkillLibrary()
    for d in ("finance", "operations", "legal"):
        nomi = competenza.nomi_reparto(lib, d, [])
        assert nomi, f"{d} senza playbook instradati"
        idx = competenza.indice(lib, nomi)
        assert len(idx) < 14000, f"indice di {d} troppo grande: {len(idx)} caratteri"
