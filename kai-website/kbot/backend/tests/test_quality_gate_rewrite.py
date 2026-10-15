"""Il commento del critico non deve mai arrivare al cliente.

Visto in produzione il 15/10/2026: il modello locale, nel campo `rewrite`, scriveva anche il
proprio giudizio («La bozza contiene una diagnosi assertiva… Ecco la versione corretta e
prudente: "…"») e review() lo consegnava così com'era.
"""
import json
from types import SimpleNamespace as NS

from app.lib import quality_gate as qg

# testo reale trapelato (accorciato)
RIFATTO_REALE = (
    "La bozza contiene una diagnosi assertiva (affermazione di fatto che le clausole creino squilibrio e "
    "costino a sospendere la merce) senza aver verificato l'effettiva applicabilità al caso.\n\n"
    "Ecco la versione corretta e prudente:\n\n"
    "\"Non è consigliabile firmare il contratto così com'è senza prima una revisione legale.\n\n"
    "1. Clausola di rinuncia alle eccezioni: potrebbe impedirti di esercitare difese di legge.\n"
    "2. Foro esclusivo di Milano: comporta costi e logistica maggiori.\""
)


# ── _ripulisci_rewrite ───────────────────────────────────────────────────────────────────
def test_il_testo_senza_commento_resta_invariato():
    t = "Non firmare così: le clausole vanno approvate specificamente per iscritto."
    assert qg._ripulisci_rewrite(t) == t


def test_il_commento_reale_viene_tolto_e_resta_il_testo_corretto():
    out = qg._ripulisci_rewrite(RIFATTO_REALE)
    assert out is not None
    assert not qg._COMMENTO_CRITICO.search(out)
    assert out.startswith("Non è consigliabile firmare il contratto")
    assert "Foro esclusivo di Milano" in out
    assert not out.startswith('"') and not out.endswith('"')      # niente virgolette di cornice


def test_senza_il_titolo_si_scartano_i_paragrafi_con_il_commento():
    t = ("La bozza presenta una diagnosi assertiva sul caso.\n\n"
         "Ti consiglio di far vedere il contratto a un avvocato prima di firmare.")
    assert qg._ripulisci_rewrite(t) == "Ti consiglio di far vedere il contratto a un avvocato prima di firmare."


def test_se_il_commento_non_si_separa_il_testo_e_scartato():
    assert qg._ripulisci_rewrite("La bozza contiene una diagnosi assertiva.") is None
    assert qg._ripulisci_rewrite("Sul flag premature_summary: vero.") is None
    assert qg._ripulisci_rewrite("") is None
    assert qg._ripulisci_rewrite("   ") is None


def test_parole_innocue_non_sono_commento():
    for t in ("Mandami la bozza del contratto e la guardo.",
              "Una versione corretta del documento va firmata da entrambi."):
        assert qg._ripulisci_rewrite(t) == t


# ── review() completo con un client finto ────────────────────────────────────────────────
def _client(verdetto: dict):
    class _Msgs:
        def create(self, **_kw):
            return NS(content=[NS(type="text", text=json.dumps(verdetto))])

    return NS(messages=_Msgs())


_STORIA = [{"role": "user", "content": "Un cliente ci manda un contratto prestampato, lo firmo?"}]
_BOZZA = "Ti conviene mandare una diffida via PEC prima di firmare e rinunciare alle eccezioni."


def test_review_non_consegna_mai_il_commento_del_critico():
    v = {"premature_summary": False, "assertive_diagnosis": True, "drastic_actions": False,
         "depth_mismatch": False, "missing_question": None, "rewrite": RIFATTO_REALE}
    out = qg.review(_client(v), "m", _STORIA, _BOZZA)
    assert not qg._COMMENTO_CRITICO.search(out), out
    assert "Non è consigliabile firmare" in out


def test_review_con_commento_non_ripulibile_tiene_la_bozza():
    v = {"premature_summary": False, "assertive_diagnosis": True, "drastic_actions": False,
         "depth_mismatch": False, "missing_question": None,
         "rewrite": "La bozza contiene una diagnosi assertiva."}
    assert qg.review(_client(v), "m", _STORIA, _BOZZA) == _BOZZA


def test_review_senza_flag_non_cambia_nulla():
    v = {"premature_summary": False, "assertive_diagnosis": False, "drastic_actions": False,
         "depth_mismatch": False, "missing_question": None, "rewrite": None}
    assert qg.review(_client(v), "m", _STORIA, _BOZZA) == _BOZZA


def test_review_una_riscrittura_pulita_passa_com_e():
    v = {"premature_summary": False, "assertive_diagnosis": False, "drastic_actions": True,
         "depth_mismatch": False, "missing_question": None,
         "rewrite": "Prima di inviare diffide, verifica il contratto con un avvocato."}
    assert qg.review(_client(v), "m", _STORIA, _BOZZA) == v["rewrite"]


def test_review_il_riepilogo_prematuro_resta_soppresso_anche_con_commento():
    bozza = (_BOZZA + "\n\nCONSULENZA_SUMMARY_START\n{\"x\":1}\nCONSULENZA_SUMMARY_END")
    v = {"premature_summary": True, "assertive_diagnosis": False, "drastic_actions": False,
         "depth_mismatch": False, "missing_question": "Qual è il valore del contratto?",
         "rewrite": "La bozza contiene un riepilogo prematuro."}
    out = qg.review(_client(v), "m", _STORIA, bozza)
    assert "CONSULENZA_SUMMARY" not in out
    assert not qg._COMMENTO_CRITICO.search(out)
    assert "Qual è il valore del contratto?" in out
