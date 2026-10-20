"""Instradamento delle skill per tema: le domande di un pre-consulente caricano le skill giuste (20/10/2026)."""
import json
from pathlib import Path

import pytest

from app.lib import skill_router as R
from app.lib.services import BASE_SKILL, resolve_skills_for_session
from app.settings import SKILLS_DIR


def _sess(*msgs):
    return {"collected_data": {}, "messages": [{"role": "user", "content": m} for m in msgs]}


def test_ogni_skill_della_mappa_esiste_in_lib_skills():
    if not Path(SKILLS_DIR).exists():
        pytest.skip("cartella delle skill non disponibile")
    d = json.load(open(R._PERCORSO, encoding="utf-8"))
    mancanti = [(t["id"], s) for t in d["temi"] for s in t["skill"] if not (Path(SKILLS_DIR) / s / "SKILL.md").exists()]
    assert not mancanti, f"skill inesistenti nella mappa: {mancanti}"


def test_la_mappa_si_legge_ed_ha_i_campi():
    d = json.load(open(R._PERCORSO, encoding="utf-8"))
    assert len(d["temi"]) >= 10
    for t in d["temi"]:
        assert t["id"] and t["trigger"] and t["skill"] and len(t["skill"]) <= R.MAX_SKILL, t["id"]
    assert len(R._temi()) == len(d["temi"])               # tutte le regex compilano


@pytest.mark.parametrize("domanda,attese", [
    ("Un mio dipendente è stato assente 4 ore: posso licenziarlo?", ["diritto-italiano"]),
    ("Come funziona il periodo di prova?", ["diritto-italiano"]),                    # prima: recruiting-pipeline, onboarding…
    ("Posso installare telecamere in reparto?", ["it-law-privacy-ai"]),
    ("Devo rinnovare il DVR ogni anno?", ["sicurezza-lavoro"]),
    ("Ho ricevuto un avviso di accertamento, entro quando ricorro?", ["fiscale-tributario-italiano"]),
    ("Voglio cedere le quote della mia srl", ["diritto-societario-italiano"]),
    ("Un cliente non mi paga una fattura da 8 mesi", ["diritto-italiano"]),          # prima: contabilità e budget forecast
    ("Dal bilancio calcolami PFN/EBITDA e DSO", ["analisi-bilancio-pmi"]),
    ("Che bandi e agevolazioni posso chiedere per un macchinario?", ["matching-bandi-agevolazioni"]),
    ("Il titolare effettivo va comunicato al registro?", ["titolare-effettivo-antiriciclaggio"]),
])
def test_le_domande_caricano_le_skill_giuste(domanda, attese):
    sk = resolve_skills_for_session(_sess(domanda))
    assert sk[0] == BASE_SKILL                              # la skill di metodo resta sempre
    for a in attese:
        assert a in sk, (domanda, sk)
    assert len(sk) <= R.MAX_SKILL + 1


@pytest.mark.parametrize("domanda,non_attese", [
    ("Come funziona il periodo di prova?", ["recruiting-pipeline", "interview-prep", "onboarding", "comp-analysis"]),
    ("Un cliente non mi paga una fattura da 8 mesi", ["budget-forecast-pmi", "reconciliation", "programmazione-controllo"]),
])
def test_non_carica_piu_le_skill_del_vecchio_pillar_fuori_tema(domanda, non_attese):
    sk = resolve_skills_for_session(_sess(domanda))
    assert not set(non_attese) & set(sk), sk


def test_senza_tema_resta_l_instradamento_storico():
    assert resolve_skills_for_session(_sess("Ciao, mi puoi aiutare?")) == [BASE_SKILL]
    assert R.skill_per_tema(["Ciao, mi puoi aiutare?"]) == []


def test_l_ultimo_messaggio_pesa_di_piu():
    p = R.punteggi(["Ho una srl con tre soci", "Un cliente non mi paga e mi ha anche mandato una diffida"])
    assert p["recupero-crediti"] > p["societario"]
    sk = R.skill_per_tema(["Ho una srl con tre soci", "Un cliente non mi paga e mi ha anche mandato una diffida"])
    assert sk[0] == "diritto-italiano"


def test_al_massimo_due_temi_e_quattro_skill():
    sk = R.skill_per_tema(["Licenzio un dipendente, il bilancio va male, ho telecamere, un DVR scaduto, accertamento fiscale e quote srl"])
    assert 0 < len(sk) <= R.MAX_SKILL


def test_un_service_id_esplicito_vince_sul_tema():
    s = _sess("Un cliente non mi paga")
    s["collected_data"] = {"service_id": "P03"}
    from app.lib.services import get_service_skills
    atteso = get_service_skills("P03")
    assert atteso and set(atteso) <= set(resolve_skills_for_session(s))


def test_interruttore(monkeypatch):
    monkeypatch.setenv("KBOT_SKILL_TEMI", "0")
    assert R.skill_per_tema(["Posso licenziare un dipendente?"]) == []
