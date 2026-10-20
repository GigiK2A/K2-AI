"""La skill del lavoro (20/10/2026): prima il tema «lavoro» caricava solo `diritto-italiano`, che non contiene diritto del lavoro."""
from app.lib.skills import load_skill

CAP = 5500   # prompts.build_system_prompt_v2: solo i primi 5500 caratteri di ogni SKILL.md entrano nella chat


def test_la_skill_esiste_e_le_linee_guida_stanno_nel_tetto_della_chat():
    b = load_skill("diritto-del-lavoro-italiano", include_references=False, max_chars=CAP)
    assert b
    for frase in ("Ritardi e trattenute: sono due cose diverse", "Ore non lavorate", "Sanzione disciplinare",
                  "cinque giorni", "quattro ore", "dieci giorni"):
        assert frase.lower() in b.lower(), frase


def test_non_dice_ne_mai_ne_sempre_sulle_trattenute():
    b = load_skill("diritto-del-lavoro-italiano", include_references=False, max_chars=CAP)
    assert "non rispondere «non si può mai trattenere nulla»" in b.lower()


def test_il_testo_di_legge_e_quello_vigente_letto_da_normattiva():
    t = load_skill("diritto-del-lavoro-italiano", include_references=False, max_chars=40000)
    assert "Normattiva" in t and "Sanzioni disciplinari" in t
    assert "multa non può essere disposta per un importo superiore a quattro ore della retribuzione base" in t
