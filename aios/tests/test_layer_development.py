from aios.llm import FakeLLM
from aios.skills import SkillLibrary
from aios.layers.development import DevelopmentLayer


def test_create_skill_writes_skill_md(tmp_path):
    lib = SkillLibrary(base=tmp_path)
    llm = FakeLLM(responses=['{"name": "promo-estate", "skill_md": "---\\nname: promo-estate\\ndescription: campagne estive\\n---\\nContenuto skill"}'])
    dev = DevelopmentLayer(llm=llm, skills=lib)
    name = dev.create_skill("voglio una skill per le promozioni estive")
    assert name == "promo-estate"
    assert "promo-estate" in lib.names()
    assert "campagne estive" in lib.load("promo-estate")
