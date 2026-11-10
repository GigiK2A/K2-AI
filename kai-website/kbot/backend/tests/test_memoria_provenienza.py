"""10/11/2026, test B: il K-BOT ha citato «da conversazioni precedenti» un fatto mai detto nel collaudo e una scheda con fatturato 7,5 mln,
altra ragione sociale, data breach e fornitore con P.IVA cessata. Verificato nel database: esiste UNA riga per utente (kbot_client_memory)
che accumula i dati di TUTTE le conversazioni dell'account (anche di prova) con «l'ultimo vince», senza provenienza e iniettata come verità
(«USALA: non richiedere MAI dati già presenti»). Non è un'esposizione fra utenti (il recupero è per user_id): è contaminazione fra
conversazioni dello stesso account. Qui: provenienza per voce, dati confermati distinti da quelli appresi, la conversazione in corso vince,
nessuna sovrascrittura dei dati confermati, tracciabilità senza valori, correzione/cancellazione."""
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_company_profile import _Client, fake_store  # noqa: E402,F401  (store Supabase finto)
from app.lib import profile as P  # noqa: E402

SID = "abcd1234-0000-4000-8000-000000000000"


def _sessione(**coll):
    return {"id": SID, "user_id": "uA", "collected_data": coll}


# ── isolamento fra utenti ────────────────────────────────────────────────────────────
def test_il_profilo_di_un_utente_non_entra_nel_prompt_di_un_altro(fake_store):
    P.save_anagrafica("uA", {"ragione_sociale": "Azienda Riservata Srl", "fatturato": "7500000"})
    assert P.load("uB") is None and P.render_block(P.load("uB")) == ""
    assert "Riservata" not in P.render_block(P.load("uB"), scheda=None)


# ── provenienza ──────────────────────────────────────────────────────────────────────
def test_ogni_voce_appresa_porta_conversazione_e_data():
    s = _sessione(extractedData={"fatturato": "850000"},
                  scheda_cliente={"citta": {"valore": "Foligno", "citazione": "siamo a Foligno"}})
    p, changed = P.merge_from_session({}, s)
    assert changed and p["anagrafica"]["fatturato"] == "850000" and p["anagrafica"]["citta"] == "Foligno"
    assert p["prov"]["fatturato"]["sid"] == SID[:8] and p["prov"]["fatturato"]["data"]
    assert p["prov"]["citta"]["sid"] == SID[:8]


# ── confermati vs appresi ─────────────────────────────────────────────────────────────
def test_un_dato_confermato_dall_utente_non_si_sovrascrive_dalle_conversazioni():
    prof = {"anagrafica": {"ragione_sociale": "Acme Srl"}, "confermati": ["ragione_sociale"]}
    p, _ = P.merge_from_session(prof, _sessione(extractedData={"ragione_sociale": "DemoTech S.r.l."}))
    assert p["anagrafica"]["ragione_sociale"] == "Acme Srl"


def test_save_anagrafica_segna_i_campi_come_confermati_e_il_vuoto_li_toglie(fake_store):
    P.save_anagrafica("u1", {"ragione_sociale": "Acme Srl", "dipendenti": "10"})
    assert set(P.load("u1")["confermati"]) == {"ragione_sociale", "dipendenti"}
    P.save_anagrafica("u1", {"dipendenti": ""})
    assert P.load("u1")["confermati"] == ["ragione_sociale"]


def test_il_blocco_separa_confermato_da_appreso():
    prof = {"anagrafica": {"ragione_sociale": "Acme Srl", "fatturato": "7500000"}, "confermati": ["ragione_sociale"],
            "prov": {"fatturato": {"sid": "abcd1234", "data": "2026-10-22"}}}
    b = P.render_block(prof)
    conf, _, app = b.partition("NON VERIFICATA")
    assert "Acme Srl" in conf and "7500000" not in conf
    assert "7500000" in app and "22/10/2026" in app and "Acme Srl" not in app


def test_profilo_vecchio_senza_conferme_e_tutto_non_verificato():
    prof = {"anagrafica": {"ragione_sociale": "DemoTech S.r.l.", "fatturato": "7500000.0"},
            "fatti": {"incidente": "data breach di 120 clienti"}, "contesto": {"problemi": ["personale aumentato senza margine"]}}
    b = P.render_block(prof)
    assert "CONFERMATI" not in b and "NON VERIFICATA" in b
    for voce in ("DemoTech", "7500000", "data breach", "personale aumentato"):
        assert voce in b.split("NON VERIFICATA", 1)[1]


def test_cio_che_l_utente_dice_in_questa_conversazione_vince_sulla_memoria():
    prof = {"anagrafica": {"fatturato": "7500000.0", "dipendenti": "12"}, "fatti": {"citta": "Torino"}}
    scheda = {"fatturato": {"valore": "850.000", "citazione": "fatturato di 850.000"}, "citta": {"valore": "Foligno", "citazione": "x"}}
    b = P.render_block(prof, scheda=scheda)
    assert "7500000" not in b and "Torino" not in b and "12" in b


def test_il_blocco_appreso_dice_di_non_affermare_e_di_chiedere_conferma():
    b = P.render_block({"anagrafica": {"fatturato": "7500000"}})
    assert "non" in b.lower() and "conferma" in b.lower() and "MAI dati già presenti" not in b


# ── tracciabilità senza dati personali ─────────────────────────────────────────────────
def test_le_statistiche_non_contengono_valori():
    prof = {"anagrafica": {"ragione_sociale": "Acme Srl", "fatturato": "7500000"}, "confermati": ["ragione_sociale"],
            "fatti": {"incidente": "data breach"}}
    s = P.statistiche(prof, scheda=None)
    assert s == {"confermati": 1, "appresi": 2}
    assert "Acme" not in str(s) and "7500000" not in str(s)


# ── correzione e cancellazione ─────────────────────────────────────────────────────────
def test_elenco_e_cancellazione_della_memoria_appresa(fake_store):
    P.save_anagrafica("u2", {"ragione_sociale": "Acme Srl"})
    prof = P.load("u2")
    prof["anagrafica"]["fatturato"] = "7500000"
    prof["fatti"] = {"incidente": "data breach"}
    prof["prov"] = {"fatturato": {"sid": "abcd1234", "data": "2026-10-22"}}
    P._save("u2", prof)
    voci = P.memoria_appresa("u2")
    assert {v["chiave"] for v in voci} == {"fatturato", "incidente"} and voci[0]["conversazione"]
    assert P.dimentica("u2", "incidente") == 1 and {v["chiave"] for v in P.memoria_appresa("u2")} == {"fatturato"}
    assert P.dimentica("u2") == 1
    assert P.memoria_appresa("u2") == [] and P.load("u2")["anagrafica"]["ragione_sociale"] == "Acme Srl"


# ── endpoint: ognuno vede e cancella solo la propria memoria ───────────────────────────
def test_gli_endpoint_della_memoria_sono_per_utente(fake_store):
    from app.api import profile as API
    from app.lib.auth import AuthUser
    A = AuthUser(id="utente-A", email="a@example.com", has_paid=False, raw={})
    B = AuthUser(id="utente-B", email="b@example.com", has_paid=False, raw={})
    P._save("utente-A", {"anagrafica": {"fatturato": "7500000"}, "fatti": {"incidente": "data breach"}})
    assert {v["chiave"] for v in API.get_memoria(A)["voci"]} == {"fatturato", "incidente"}
    assert API.get_memoria(B)["voci"] == []
    API.delete_memoria(B)                                           # B non può cancellare la memoria di A
    assert len(API.get_memoria(A)["voci"]) == 2
    assert API.delete_memoria_voce("incidente", A) == {"rimosse": 1}
    assert [v["chiave"] for v in API.get_memoria(A)["voci"]] == ["fatturato"]


def test_il_prompt_di_un_utente_non_contiene_la_memoria_di_un_altro(fake_store):
    from app.lib.prompts import build_system_prompt_v2
    P._save("utente-A", {"anagrafica": {"ragione_sociale": "Azienda Riservata Srl", "fatturato": "7500000"}})
    sessB = {"id": "s-b", "user_id": "utente-B", "messages": [{"role": "user", "content": "ciao, ho 12 dipendenti"}],
             "collected_data": {}, "_profilo": P.load("utente-B")}
    assert "Riservata" not in build_system_prompt_v2(["diagnosi-ai-operativa-pmi"], sessB)
    sessA = {**sessB, "user_id": "utente-A", "_profilo": P.load("utente-A")}
    prompt_a = build_system_prompt_v2(["diagnosi-ai-operativa-pmi"], sessA)
    assert "Azienda Riservata Srl" in prompt_a and "NON VERIFICATA" in prompt_a


# ── il report non si intesta con una ragione sociale appresa ────────────────────────────────────────
def test_la_ragione_sociale_di_un_report_viene_solo_dal_dato_confermato():
    from app.api.deliverables import _session_company
    assert _session_company({"_profilo": {"anagrafica": {"ragione_sociale": "Acme Srl"}, "confermati": ["ragione_sociale"]}}) == "Acme Srl"
    assert _session_company({"_profilo": {"anagrafica": {"ragione_sociale": "DemoTech S.r.l."}}}) is None


def test_il_modulo_dati_azienda_mostra_solo_i_dati_confermati(fake_store):
    P._save("u9", {"anagrafica": {"ragione_sociale": "DemoTech S.r.l.", "fatturato": "7500000"}})      # appresi (profilo vecchio)
    assert P.load_anagrafica("u9") == {}
    P.save_anagrafica("u9", {"ragione_sociale": "Acme Srl"})
    assert P.load_anagrafica("u9") == {"ragione_sociale": "Acme Srl"}            # il fatturato appreso non diventa «dato dell'account»
    assert "fatturato" in {v["chiave"] for v in P.memoria_appresa("u9")}
