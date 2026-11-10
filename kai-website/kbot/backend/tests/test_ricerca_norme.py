"""Ricerca ibrida nel database normativo (test del 10/11/2026 sull'art. 113 comma 2 D.Lgs. 81/2008). Usa il corpus vero (saltato se manca)."""
from types import SimpleNamespace as NS

import pytest

from app.lib import norme_evidence as N
from app.lib import ricerca_norme as R

pytestmark = pytest.mark.skipif(not N.disponibile(), reason="corpus Normattiva non disponibile")


def _art(esito, art):
    return [s for s in esito["risultati"] if s["articolo"] == art]


def test_riferimento_esatto_con_comma():
    e = R.cerca(norma="D.Lgs. 81/2008", articolo="113", comma="2")
    s = _art(e, "113")[0]
    assert s["comma"] == "2" and "75 gradi" in s["testo"] and "gabbia di sicurezza" in s["testo"]
    assert s["origine"] == "riferimento esatto" and s["versione"] and s["fonte"] in ("supplemento", "corpus")
    assert s["sigla"] and s["rubrica"].lower().startswith("scale")


def test_riferimento_scritto_nella_query():
    e = R.cerca(query="Cosa dice l'art. 113 comma 2 del D.Lgs. 81/2008 dopo il D.L. 159/2025?")
    assert _art(e, "113") and "75 gradi" in _art(e, "113")[0]["testo"]


def test_descrizione_del_problema_trova_l_art_113():
    e = R.cerca(query="scale verticali permanenti di altezza superiore a 5 metri con inclinazione superiore a 75 gradi gabbia di sicurezza")
    assert "113" in [s["articolo"] for s in e["risultati"][:3]], [s["sigla"] for s in e["risultati"]]


def test_norma_piu_parole_chiave():
    e = R.cerca(query="scale verticali permanenti protezione contro le cadute", norma="D.Lgs. 81/2008")
    assert "113" in [x["articolo"] for x in e["risultati"][:3]]                  # 113 (scale) e 115 (cadute) sono entrambe pertinenti


def test_articolo_inesistente_si_dichiara_senza_inventare():
    e = R.cerca(norma="D.Lgs. 81/2008", articolo="9999")
    assert not e["risultati"] and "NON presente" in e["avviso"]
    assert "non ricostruire" in R.formatta(e, 1).lower()


def test_comma_inesistente_elenca_i_commi_veri():
    e = R.cerca(norma="D.Lgs. 81/2008", articolo="113", comma="99")
    assert "comma 99" in e["risultati"][0]["avviso"] and "1, 2, 3" in e["risultati"][0]["avviso"]


# ── versione ──────────────────────────────────────────────────────────────────────────────────────────
def test_versione_dall_api_e_dal_consolidato():
    api = "---\ndata_vigenza: '2026-11-10'\ninizio_vigenza_articolo: '2025-12-31'\nfonte: Normattiva OpenData — API dettaglio-atto-urn\n---\n"
    assert "dal 31/12/2025" in R.versione(api) and "10/11/2026" in R.versione(api)
    corpus = "---\nmodifiche_note:\n- 'alias: eli/id/2008/04/30/008G0104/CONSOLIDATED/20260407'\n---\n"
    assert "consolidato al 07/04/2026" in R.versione(corpus)
    assert R.versione("senza metadati") == "versione non indicata nel corpus"


# ── strumento ─────────────────────────────────────────────────────────────────────────────────────────
def test_lo_strumento_registra_la_consultazione_e_il_pacchetto():
    R.inizia_turno()
    N.imposta(N.Pacchetto(testo=""))
    out = R.esegui({"norma": "D.Lgs. 81/2008", "articolo": "113", "comma": "2"})
    assert "consultazione n. 1" in out and "75 gradi" in out and "Fonte:" in out
    assert R.consultazioni()[0]["trovati"]
    assert N.citazione_consentita("art. 113 D.Lgs. 81/2008")             # la citazione che ne deriva non viene de-specificata
    N.imposta(None)


def test_non_si_dichiara_di_aver_interrogato_il_database_senza_averlo_fatto():
    R.inizia_turno()
    t = "Ho interrogato il database normativo e l'art. 113 non risulta."
    assert "ho interrogato" not in R.correggi_dichiarazioni(t).lower() and "estratto" in R.correggi_dichiarazioni(t)
    R.esegui({"norma": "D.Lgs. 81/2008", "articolo": "113"})
    assert R.correggi_dichiarazioni(t) == t                              # dopo una consultazione vera la frase resta


def test_definizione_dello_strumento():
    d = R.definizione()
    assert d["name"] == "cerca_norma" and set(d["input_schema"]["properties"]) == {"query", "norma", "articolo", "comma"}


def test_il_supplemento_aggiornato_porta_vigenza_e_note_del_2025():
    """Il TU sicurezza è stato riscaricato dall'API ufficiale (vigente al 10/11/2026): art. 113 con la nota del D.L. 159/2025 / L. 198/2025."""
    s = _art(R.cerca(norma="D.Lgs. 81/2008", articolo="113", comma="2"), "113")[0]
    assert s["fonte"] == "supplemento" and "dal 31/12/2025" in s["versione"] and "10/11/2026" in s["versione"]
    assert "159" in s["note"] and "198" in s["note"] and "1° febbraio 2026" in s["note"]
    assert s["rubrica"] == "Scale"


# ── pacchetto automatico ───────────────────────────────────────────────────────────────────────────────
Q_SCALE = ("Abbiamo una scala fissa a pioli verticale permanente di 7 metri con inclinazione superiore a 75 gradi che porta alla copertura "
           "di un impianto. Serve la gabbia di sicurezza o basta l'imbracatura?")


def test_il_pacchetto_automatico_include_l_art_113_per_la_descrizione_del_problema():
    pk = N.costruisci(Q_SCALE, "", None, "")
    assert pk and "D.Lgs 81/2008, art. 113" in [f.sigla for f in pk.fonti], [f.sigla for f in pk.fonti]


def test_il_pacchetto_non_e_piu_sempre_lo_stesso_elenco():
    """Con la voce fissa «lavori in quota» il pacchetto era sempre 107/111/115/148/126: ora la domanda sposta le fonti."""
    a = {f.sigla for f in N.costruisci(Q_SCALE, "", None, "").fonti}
    b = {f.sigla for f in N.costruisci("Il dipendente deve fare un sopralluogo sul tetto piano a 8 metri senza parapetti: serve l'imbracatura?", "", None, "").fonti}
    assert a != b and any("113" in x for x in a) and not any("113" in x for x in b)     # le scale portano l'art. 113, il tetto senza scale no


def test_il_riferimento_esatto_con_comma_porta_il_comma_e_la_versione():
    pk = N.costruisci("Cosa prevede esattamente l'art. 113 comma 2 del D.Lgs. 81/2008 dopo il D.L. 159/2025?", "", None, "")
    f = [x for x in pk.fonti if x.articolo == "113"][0]
    assert "comma 2:" in f.testo and "75 gradi" in f.testo and "comma 1:" not in f.testo
    assert "dal 31/12/2025" in f.versione and "159" in f.aggiornamenti
    blocco = pk.testo
    assert "Versione:" in blocco and "Modifiche normative in nota" in blocco and "ESTRATTO" in blocco
