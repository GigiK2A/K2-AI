"""GDPR nel pacchetto normativo (test 08, 20/10/2026): il corpus Normattiva non lo contiene."""
import re
from pathlib import Path

import pytest

from app.lib import norme_evidence as N, norme_ue, deadline_guard

DATI = Path(norme_ue._DIR)
CASO = ("Un dipendente ha inviato per errore a un cliente un file Excel con nome, telefono ed email di circa 120 clienti. "
        "Il destinatario ha confermato per iscritto di averlo cancellato. Dobbiamo notificare l'incidente al Garante?")


def test_i_testi_sono_quelli_ufficiali_e_contengono_i_termini_chiave():
    a33 = (DATI / "gdpr_art_33.txt").read_text(encoding="utf-8")
    assert "entro 72 ore dal momento in cui ne è venuto a conoscenza" in a33
    assert "a meno che sia improbabile che la violazione dei dati personali presenti un rischio" in a33
    assert "Il titolare del trattamento documenta qualsiasi violazione dei dati personali" in a33
    a34 = (DATI / "gdpr_art_34.txt").read_text(encoding="utf-8")
    assert "rischio elevato" in a34 and "Sezione 3" not in a34
    assert "violazione di sicurezza" in (DATI / "gdpr_art_4_n12.txt").read_text(encoding="utf-8")


@pytest.mark.parametrize("t,atteso", [
    (CASO, True),
    ("C'è stato un data breach sul nostro gestionale", True),
    ("Dobbiamo notificare la violazione dei dati al Garante entro 72 ore?", True),
    ("Abbiamo mandato per errore l'elenco dei clienti a un fornitore", True),
    ("Un cliente non mi paga una fattura", False),
    ("Posso licenziare un dipendente per i ritardi?", False),
    ("Che consigli per il marketing?", False),
    ("", False),
])
def test_trigger(t, atteso):
    assert bool(norme_ue.fonti_ue(t, N.Fonte)) is atteso


def test_le_fonti_ue_hanno_titolo_commi_e_numeri():
    fonti = norme_ue.fonti_ue(CASO, N.Fonte)
    assert [f.sigla for f in fonti] == ["GDPR art. 33", "GDPR art. 34", "GDPR art. 4 n. 12"]
    assert fonti[0].tipo == "regolamento_ue" and "72 ore" in fonti[0].testo and fonti[0].testo.startswith("  1. In caso di violazione")
    assert "Articolo 33" not in fonti[0].testo                                     # il titolo sta nella fonte, non ripetuto nel testo


def test_il_pacchetto_porta_le_72_ore_anche_senza_proposte_del_modello(monkeypatch):
    monkeypatch.setattr(N, "abilitato", lambda: True)
    monkeypatch.setattr(N, "disponibile", lambda: True)
    pk = N.costruisci(CASO, "", None, "")
    assert pk and any(f.sigla == "GDPR art. 33" for f in pk.fonti)
    assert "72 ore" in pk.testo and (72, "ore"[:3]) in pk.coppie


def test_la_guardia_sulle_scadenze_non_cancella_le_72_ore_quando_c_e_la_fonte(monkeypatch):
    """Con parole di contesto legale («obbligo», «sanzione») la guardia neutralizza ogni termine che non sta nel pacchetto: senza l'art. 33
    «entro 72 ore» diventava «entro il termine previsto dalla normativa». Con la fonte nel pacchetto resta."""
    monkeypatch.setattr(N, "abilitato", lambda: True)
    monkeypatch.setattr(N, "disponibile", lambda: True)
    risposta = "Hai l'obbligo di notificare la violazione al Garante entro 72 ore da quando ne sei venuto a conoscenza."
    N.imposta(None)
    assert "72 ore" not in deadline_guard.sanitize(risposta)                       # senza fonte: neutralizzato
    try:
        N.imposta(N.costruisci(CASO, "", None, ""))
        assert "entro 72 ore" in deadline_guard.sanitize(risposta)                 # con la fonte: resta
    finally:
        N.imposta(None)


def test_spento_con_la_variabile(monkeypatch):
    monkeypatch.setenv("KBOT_NORME_UE", "0")
    assert norme_ue.fonti_ue(CASO, N.Fonte) == []


def test_gli_articoli_del_codice_privacy_non_pertinenti_si_escludono_ma_quelli_citati_restano():
    assert ("196", 2003) in norme_ue.escluse(CASO)
    assert norme_ue.escluse("Come funziona il TFR?") == set()
    # l'esclusione vale per le PROPOSTE, non per ciò che l'utente cita (la regola sta in costruisci: origine != «utente»)
    import inspect
    assert 'f.origine != "utente"' in inspect.getsource(N.costruisci)


def test_i_richiami_del_prompt_coprono_il_caso_del_software():
    t = N._SISTEMA_PROPOSTA
    for frase in ("art. 1460 c.c.", "art. 1667 c.c.", "D.Lgs. 28/2010 art. 5", "art. 2222 c.c."):
        assert frase in t


# ── 22/10/2026 (test 09 e 11): verifica del beneficiario (Reg. 2024/886) e prassi sulla cessazione della partita IVA ──
def _sigle(testo):
    from app.lib import norme_evidence as E
    return {f.sigla for f in norme_ue.fonti_ue(testo, E.Fonte)}


def test_il_falso_iban_porta_l_art_5_quater():
    q = ("Abbiamo fatto un bonifico di 7.500 euro su un IBAN diverso comunicato da un'email falsa del fornitore. "
         "La banca dice che l'abbiamo autorizzato noi; il sistema non ci ha avvisato che il nome era diverso.")
    assert "Reg. UE 260/2012 art. 5 quater" in _sigle(q)


def test_un_bonifico_normale_non_porta_l_art_5_quater():
    assert "Reg. UE 260/2012 art. 5 quater" not in _sigle("Come registriamo in contabilità il bonifico ricevuto dal cliente?")


def test_l_art_5_quater_e_il_testo_ufficiale():
    from app.lib import norme_evidence as E
    f = [x for x in norme_ue.fonti_ue("bonifico a un IBAN falso, truffa via email", E.Fonte) if x.articolo == "5-quater"][0]
    assert f.anno == 2012 and f.numero == "260" and "9 ottobre 2025" in f.testo and "rimborsa immediatamente" in f.testo


def test_la_partita_iva_cessata_porta_la_prassi_con_la_cautela():
    from app.lib import norme_evidence as E
    fonti = [x for x in norme_ue.fonti_ue("Il fornitore ha la partita IVA cessata da sei mesi: possiamo detrarre?", E.Fonte) if x.sigla == "AdE Risp. 218/2022"]
    assert fonti and "232/E" in fonti[0].testo and "vale per l'istante" in fonti[0].testo
