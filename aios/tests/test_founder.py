from aios.founder import FounderModel, default_founder_model


def test_to_prompt_contains_voice_and_priorities():
    fm = FounderModel(
        voice="diretto, pragmatico, niente buzzword",
        priorities=["acquisire PMI 5-50 dipendenti"],
        delegation_rules=["mai pubblicare senza approvazione"],
        voice_samples=["Automatizza la contabilità e libera ore"],
    )
    p = fm.to_prompt()
    assert "diretto, pragmatico" in p
    assert "acquisire PMI" in p
    assert "mai pubblicare senza approvazione" in p
    assert "Automatizza la contabilità" in p


def test_default_founder_model_is_k2ai_flavored():
    fm = default_founder_model()
    assert fm.voice and isinstance(fm.priorities, list) and fm.priorities
    blob = fm.to_prompt().lower()
    assert "italiano" in blob or "tu" in blob
    assert "pmi" in blob
