"""Le skill entrano nella chat per SEZIONI pertinenti, non più per i primi 5500 caratteri (20/10/2026)."""
import pytest

from app.lib.skills import load_skill, load_skill_pertinente, load_skill_bundle

CAP = 5500
FISC = "fiscale-tributario-italiano"


def test_prima_la_skill_fiscale_non_conteneva_ammortamento_e_ires():
    vecchio = load_skill(FISC, include_references=False, max_chars=CAP)
    assert "Primo anno: quota ridotta al 50%" not in vecchio and "Aliquota IRES" not in vecchio


def test_la_domanda_sul_computer_porta_ires_e_ammortamento():
    t = load_skill_pertinente(FISC, "Abbiamo comprato un computer da 2.500 euro: ammortamento e IRES risparmiata del primo anno", CAP)
    assert len(t) <= CAP
    assert "Primo anno: quota ridotta al 50%" in t and "Aliquota IRES" in t and "24%" in t


def test_la_domanda_sul_ravvedimento_porta_la_tabella_corretta():
    t = load_skill_pertinente(FISC, "Ho pagato l'IVA con 40 giorni di ritardo: quanto costa il ravvedimento operoso?", CAP)
    assert len(t) <= CAP
    assert "1,39%" in t and "3,125%" in t and "25%" in t


def test_senza_frontmatter_e_con_l_introduzione():
    t = load_skill_pertinente(FISC, "ammortamento", CAP)
    assert not t.startswith("---") and "Usa SEMPRE per" not in t
    assert "Consulente Fiscale e Tributario Italiano" in t


def test_senza_somiglianza_si_comporta_come_prima_ma_senza_frontmatter():
    t = load_skill_pertinente(FISC, "zzzz qqqq", CAP)
    assert len(t) <= CAP and "## 1. Raccolta informazioni" in t


def test_una_skill_corta_si_carica_intera():
    t = load_skill_pertinente("it-law-privacy-ai", "telecamere", CAP)
    assert t and len(t) <= CAP


def test_il_bundle_rispetta_il_tetto_totale_e_usa_la_query():
    b = load_skill_bundle([FISC, "diritto-del-lavoro-italiano"], max_total_chars=9000, max_per_skill_chars=CAP,
                          query="ammortamento computer IRES")
    assert len(b) <= 9000 and "Aliquota IRES" in b
    senza = load_skill_bundle([FISC], max_total_chars=9000, max_per_skill_chars=CAP)
    assert "Aliquota IRES" not in senza


def test_skill_inesistente():
    assert load_skill_pertinente("non-esiste-xyz", "q", CAP) is None


def test_il_prompt_della_chat_porta_le_sezioni_giuste():
    from app.lib.prompts import build_system_prompt_v2
    msgs = [{"role": "user", "content": "SRL, computer da 2.500 euro a ottobre: come funziona l'ammortamento e quanta IRES risparmio?"}]
    p = build_system_prompt_v2([FISC], {"messages": msgs, "collected_data": {}})
    assert "Primo anno: quota ridotta al 50%" in p
