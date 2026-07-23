"""Rivoluzione "prima consulente, poi generatore di report" (spec Luca, 17 lug 2026).

- Due modalità nel prompt: consulenza immediata (risposta diretta, niente report-pushing)
  vs analisi approfondita (intake → CONSULENZA_SUMMARY → report premium).
- Gate primo turno: permette la risposta diretta alle domande puntuali, vieta comunque
  il summary precoce.
- Memoria-profilo cross-sessione (kbot_client_memory): merge deterministico + render.
"""
from __future__ import annotations

import types
import sys

for _name, _attrs in (("dotenv", {"load_dotenv": lambda *a, **k: False}),):
    if _name not in sys.modules:
        _m = types.ModuleType(_name)
        [setattr(_m, k, v) for k, v in _attrs.items()]
        sys.modules[_name] = _m
try:  # pragma: no cover
    from supabase import Client as _ProbeClient  # noqa: F401
except Exception:  # pragma: no cover
    _m = types.ModuleType("supabase")
    _m.Client, _m.create_client = object, (lambda *a, **k: None)
    sys.modules["supabase"] = _m

from app.lib import profile  # noqa: E402
from app.lib.prompts import build_system_prompt_v2  # noqa: E402


def _prompt(messages, collected=None, profilo=None):
    session = {"messages": messages, "collected_data": collected or {}}
    if profilo is not None:
        session["_profilo"] = profilo
    return build_system_prompt_v2([], session, required_fields_hint="")


# ── due modalità nel prompt ────────────────────────────────────────────────────────────

def test_identita_consulente_e_due_modalita():
    p = _prompt([{"role": "user", "content": "ciao"}])
    assert "prima consulente, poi generatore di report" in p.lower()
    assert "CONSULENZA IMMEDIATA" in p and "ANALISI APPROFONDITA" in p
    # niente report-pushing: il passaggio 1→2 si propone una volta sola
    assert "mai forzare" in p.lower() or "non forzarlo" in p.lower()


def test_gate_primo_turno_permette_risposta_diretta():
    p = _prompt([{"role": "user", "content": "Posso licenziare un dipendente in prova?"}])
    assert "FASE COMPRENSIONE" in p                    # marker del gate invariato
    assert "rispondi SUBITO" in p or "rispondi subito" in p.lower()  # modalità A ammessa
    assert "CONSULENZA_SUMMARY" in p                   # il divieto di summary resta
    assert "VIETATO" in p


def test_gate_urgenza_invariato():
    p = _prompt([{"role": "user", "content": "URGENTE: il responsabile è ricoverato e "
                  "domani non riusciamo a pagare gli stipendi"}])
    assert "FASE INTERVISTA (URGENZA)" in p


def test_dal_secondo_turno_gate_sparisce():
    msgs = [{"role": "user", "content": "problema di liquidità"},
            {"role": "assistant", "content": "quanto dura la cassa?"},
            {"role": "user", "content": "2 mesi"}]
    p = _prompt(msgs)
    assert "FASE COMPRENSIONE" not in p and "FASE INTERVISTA" not in p


# ── memoria-profilo ────────────────────────────────────────────────────────────────────

def _sessione_con_dati():
    return {"user_id": "u-1", "collected_data": {
        "extractedData": {"companyName": "Rossi SRL", "businessType": "manifatturiero",
                          "objective": "ridurre i tempi di incasso",
                          "summary": "PMI con DSO alto e crediti scaduti"},
        "deliverable_label": "FinanceBoost", "deliverable_job_id": "job_x1",
        "deliverable_inputs": {"n_dipendenti": 25},
    }}


def test_merge_costruisce_profilo():
    p, changed = profile.merge_from_session(None, _sessione_con_dati())
    assert changed
    assert p["anagrafica"]["ragione_sociale"] == "Rossi SRL"
    assert p["anagrafica"]["settore"] == "manifatturiero"
    assert p["anagrafica"]["dipendenti"] == "25"
    assert "ridurre i tempi di incasso" in p["contesto"]["obiettivi"][0]
    assert p["storico"][0]["tema"] == "FinanceBoost" and p["storico"][0]["tipo"] == "report"


def test_merge_idempotente_e_dedupe():
    p1, _ = profile.merge_from_session(None, _sessione_con_dati())
    p2, changed = profile.merge_from_session(p1, _sessione_con_dati())
    assert not changed                       # stessa sessione due volte → nessun cambio
    assert len(p2["storico"]) == 1           # il report non si duplica


def test_render_block_nel_prompt():
    p, _ = profile.merge_from_session(None, _sessione_con_dati())
    block = profile.render_block(p)
    assert "PROFILO CLIENTE" in block and "Rossi SRL" in block and "FinanceBoost" in block
    # e il prompt lo integra
    full = _prompt([{"role": "user", "content": "ciao"}], profilo=p)
    assert "PROFILO CLIENTE" in full and "Rossi SRL" in full


def test_render_vuoto_senza_profilo():
    assert profile.render_block(None) == ""
    assert profile.render_block({}) == ""
    full = _prompt([{"role": "user", "content": "ciao"}])
    assert "PROFILO CLIENTE" not in full     # anonimo → nessun blocco


def test_update_after_turn_skip_anonimo():
    profile.update_after_turn({"collected_data": {}})  # nessun user_id → no-op, no crash


# ── hardening eval-100 (17 lug): procedi enforcement + blocchi malformati ─────────────

def test_procedi_hard_matcha_solo_intenti_espliciti():
    from app.lib import signals
    si = ("EBITDA 880mila. Liquidità 700mila. Tasso previsto 4,2%. procedi",
          "Obiettivo: trattenere i tecnici under 40. procedi",
          "procedi", "ok procedi", "vai", "fammi il report", "basta domande",
          "La ditta fattura solo alla mia SRL per il 70%. procedi")
    no = ("qual è la procedura di licenziamento?", "come procediamo?",
          "il procedimento è lungo", "vorrei capire come si procede in questi casi",
          "mi spieghi la procedura per la CIGS")
    for t in si:
        assert signals.PROCEDI_HARD_RE.search(t), f"doveva matchare: {t}"
    for t in no:
        assert not signals.PROCEDI_HARD_RE.search(t), f"NON doveva matchare: {t}"


def test_strip_tolerante_blocco_troncato():
    # leak reale (eval 100): DIAGNOSI_STATO_START troncato da max_tokens, niente END
    from app.lib.prompts import strip_diagnosi_block
    t = ('Analisi del caso e prossimi passi.\n\n'
         'DIAGNOSI_STATO_START {"ipotesi":[{"t":"Redditività insufficiente","s":"aperta"}],"manca":"E')
    out = strip_diagnosi_block(t)
    assert "DIAGNOSI" not in out and out.startswith("Analisi del caso")


def test_extract_e_strip_blocco_orfano_senza_start():
    # leak reale (eval 100): JSON + CONSULENZA_SUMMARY_END senza START → il summary
    # va RECUPERATO (report non perso) e il testo ripulito
    from app.lib.prompts import extract_summary, strip_summary_block
    t = ('Perfetto, procedo con il report.\n'
         '{"reportType":"Piano marketing","objective":"lead B2B","summary":"caso ok"}\n'
         'CONSULENZA_SUMMARY_END')
    s = extract_summary(t)
    assert s and s["reportType"] == "Piano marketing"
    out = strip_summary_block(t)
    assert "CONSULENZA_SUMMARY" not in out and "{" not in out
    assert out.startswith("Perfetto")


def test_strip_backstop_marker_nudo():
    from app.lib.prompts import strip_summary_block
    t = "Riepilogo:\nCONSULENZA_SUMMARY: vedi sopra\nGrazie."
    out = strip_summary_block(t)
    assert "CONSULENZA_SUMMARY" not in out and "Grazie." in out


def test_blocchi_ben_formati_invariati():
    from app.lib.prompts import extract_summary, strip_summary_block
    t = ('Ok, genero il report.\nCONSULENZA_SUMMARY_START '
         '{"reportType":"X","summary":"y"} CONSULENZA_SUMMARY_END')
    assert extract_summary(t)["reportType"] == "X"
    assert strip_summary_block(t) == "Ok, genero il report."


def test_urgenza_non_scatta_su_subito_in_domanda_semplice():
    from app.lib import signals
    assert not signals.URGENT_RE.search("mi è arrivata una PEC, devo rispondere subito?")
    # le crisi vere restano riconosciute
    assert signals.URGENT_RE.search("il responsabile è ricoverato e domani ci sono gli stipendi")
    assert signals.URGENT_RE.search("URGENTE: rischiamo di non pagare i fornitori")


def test_quality_gate_non_strippa_summary_su_procedi_esplicito():
    """Eval-100: l'enforcement procedi forzava il summary e il critico lo strippava
    come 'prematuro' → net effect nulla. Con user_procedi=True il flag è disattivato."""
    import app.lib.quality_gate as qg

    class _FakeClient:
        class messages:
            @staticmethod
            def create(**kw):
                class R:
                    content = [type("B", (), {"type": "text", "text":
                        '{"premature_summary":true,"assertive_diagnosis":false,'
                        '"drastic_actions":false,"depth_mismatch":false,'
                        '"missing_question":"che margini hai?","rewrite":"riscritto senza blocco"}'})()]
                return R()

    txt = ('Procedo. CONSULENZA_SUMMARY_START {"reportType":"X","summary":"y"} '
           'CONSULENZA_SUMMARY_END')
    msgs = [{"role": "user", "content": "dati. procedi"}]
    out = qg.review(_FakeClient, "m", msgs, txt, user_procedi=True)
    assert "CONSULENZA_SUMMARY_START" in out   # il summary sopravvive al critico
    out2 = qg.review(_FakeClient, "m", msgs, txt, user_procedi=False)
    assert "CONSULENZA_SUMMARY_START" not in out2  # senza procedi il critico governa


# ── skill anche in consulenza: matcher radici + coperture italiane (17 lug) ───────────

def test_intent_licenziare_accende_skill_legali():
    """'posso licenziare?' non accendeva NESSUNA skill: c'era solo 'licenziamento'
    (parola intera) e P15 aveva solo keyword inglesi. Ora licenzi* matcha le flessioni."""
    from app.lib.services import infer_service_id_from_session, get_service_skills
    sid = infer_service_id_from_session({"messages": [
        {"role": "user", "content": "Posso licenziare un dipendente durante il periodo di prova senza motivazione?"}]})
    assert sid in ("P03", "P15")
    assert get_service_skills(sid)          # skill reali caricate, non BASE


def test_intent_hr_italiano():
    from app.lib.services import infer_service_id_from_session
    assert infer_service_id_from_session({"messages": [
        {"role": "user", "content": "le ferie non godute scadono? e la malattia come funziona?"}]}) == "P15"


def test_intent_fisco_italiano():
    from app.lib.services import infer_service_id_from_session
    assert infer_service_id_from_session({"messages": [
        {"role": "user", "content": "acconto IVA: come si calcola? e le imposte anticipate?"}]}) == "P02"


def test_radici_morte_riparate():
    # 'amministr' con \b finale non matchava MAI 'amministrazione' (keyword morta)
    from app.lib.services import infer_service_id_from_session
    assert infer_service_id_from_session({"messages": [
        {"role": "user", "content": "vorrei sistemare l'amministrazione e le scadenze delle fatture"}]}) == "P02"


def test_radice_licenzi_non_matcha_licenza():
    # 'licenzi*' NON deve matchare 'licenza' (software/commercio)
    from app.lib.services import infer_service_id_from_session
    sid = infer_service_id_from_session({"messages": [
        {"role": "user", "content": "mi serve una licenza software per il gestionale"}]})
    assert sid != "P03"


# ── linguaggio calibrato sulla certezza (spec Luca 17 lug, round 2) ───────────────────

def test_prompt_contiene_livelli_certezza_e_divieto_numeri():
    p = _prompt([{"role": "user", "content": "ciao"}])
    assert "LINGUAGGIO CALIBRATO SULLA CERTEZZA" in p
    assert "DIVIETO ASSOLUTO DI INVENTARE NUMERI" in p
    for frase in ("in generale", "di norma", "dipende dal caso concreto", "occorre verificare"):
        assert frase in p
    for vietata in ("sempre", "mai", "è sicuramente"):
        assert vietata in p.lower()  # citate come ESEMPI da evitare, non usate come regola


def test_prompt_menziona_ccnl_come_fonte_di_incertezza():
    p = _prompt([{"role": "user", "content": "ciao"}])
    assert "CCNL" in p and "quale contratto collettivo" in p


def test_prompt_vieta_numeri_ammorbiditi_con_qualificatori():
    """Round 2 (retest live): il modello ha scritto 'di solito 5-15 giorni' — un numero
    stimato solo ammorbidito con 'di solito'. Il divieto deve coprire ESPLICITAMENTE
    questo caso, non solo il numero nudo."""
    p = _prompt([{"role": "user", "content": "ciao"}])
    assert "ammorbidito" in p.lower() or "non lo rende meno inventato" in p.lower()
    assert "5-15 giorni" in p  # l'esempio concreto dell'errore reale, per pattern-match diretto


def test_divieto_numeri_vale_anche_su_giudizi_e_chitchat():
    """Richiesta Luca: «giudizi soggettivi e chit-chat anche in questo caso». Il divieto di
    cifre inventate non deve valere solo su scadenze/articoli ma anche quando il bot orienta
    o consiglia (loophole visto live: 'marketing 2-5%, 15-25k€' sparati a memoria)."""
    p = _prompt([{"role": "user", "content": "ciao"}])
    assert "VALE ANCHE NEI GIUDIZI" in p
    assert "chit-chat" in p.lower()
    assert "offri" in p.lower() and "verificarla" in p.lower()  # offre di verificare, non inventa


def test_prompt_diffida_da_scadenze_da_web_generico():
    """Caso #6 live: il grounding web ha fatto ripetere «assunzione entro 5 giorni» (errore
    diffuso sul web). Il prompt deve dire esplicitamente di non fidarsi di un termine di legge
    preso da ricerca web generica e di rimandare alla fonte ufficiale."""
    p = _prompt([{"role": "user", "content": "ciao"}])
    assert "RICERCA WEB GENERICA" in p
    assert "entro 5 giorni" in p  # l'errore reale citato come pattern da NON ripetere
    assert "prima dell'inizio del rapporto" in p.lower()


# ── backstop citazioni normative non verificate (17 lug: 'la normativa è rotta') ──────

def test_backstop_rimuove_numero_articolo_ccnl_inventato():
    from app.lib.prompts import sanitize_unverified_legal_citations as san
    t = ("La disciplina è contenuta dagli artt. 62‑e 63 del CCNL (o dal contratto "
         "collettivo applicabile) e prevede il recesso durante la prova.")
    out = san(t)
    assert "62" not in out and "63" not in out
    assert "il CCNL applicato" in out


def test_backstop_rimuove_articolo_codice_civile_inventato():
    from app.lib.prompts import sanitize_unverified_legal_citations as san
    t = "dall'art. 2099‑c al Codice Civile, che prevede la possibilità di recesso."
    out = san(t)
    assert "2099" not in out
    assert "il codice civile" in out


def test_backstop_gestisce_trattino_esotico_gpt_oss():
    # stesso U+2011 già visto nel bug dei PDF: 'artt. 62‑63' con trattino non-breaking
    from app.lib.prompts import sanitize_unverified_legal_citations as san
    t = "vedi artt. 62‑63 del CCNL"
    out = san(t)
    assert "62" not in out and "63" not in out


def test_backstop_non_tocca_testo_senza_citazioni():
    from app.lib.prompts import sanitize_unverified_legal_citations as san
    t = "Sì, puoi farlo. Verifica il tuo CCNL per il periodo di preavviso esatto."
    assert san(t) == t


def test_web_search_hint_obbliga_verifica_numeri_articolo():
    from app.lib.web_search import SYSTEM_HINT
    assert "OBBLIGO SU NUMERI DI ARTICOLO" in SYSTEM_HINT
    assert "MAI scriverlo a memoria" in SYSTEM_HINT


# ── norme_guard: verifica sul corpus 8e, fail-closed (17 lug) ─────────────────────────

def _con_verify(monkey_result):
    """Patcha la verifica remota di norme_guard e ritorna il modulo."""
    from unittest import mock
    from app.lib import norme_guard
    return mock.patch.object(norme_guard, "_verify_remote", lambda testo: monkey_result), norme_guard


def test_norme_guard_default_strippa_anche_articolo_esistente():
    # POLICY DEFAULT (17 lug): esistenza != rilevanza (art. 2099 esiste ma è l'articolo
    # sbagliato per la prova) → in chat NESSUN numero di articolo, sempre descrittivo.
    from app.lib import norme_guard
    t = "Il periodo di prova è disciplinato dall'art. 2096 c.c. e va rispettato."
    out = norme_guard.sanitize(t)
    assert "2096" not in out and "il codice civile" in out


def test_norme_guard_keep_verified_opt_in():
    import os
    from unittest import mock
    from app.lib import norme_guard
    t = "Il periodo di prova è disciplinato dall'art. 2096 c.c. e va rispettato."
    with mock.patch.dict(os.environ, {"KBOT_NORME_KEEP_VERIFIED": "1"}), \
         mock.patch.object(norme_guard, "_verify_remote", lambda testo: [{"label": "art. 2096 c.c.", "verificata": True}]):
        out = norme_guard.sanitize(t)
    assert "art. 2096 c.c." in out          # col flag opt-in torna a tenere l'esistente


def test_norme_guard_default_strippa_tutti_i_numeri_articolo():
    # DEFAULT descriptive-only: TUTTI i numeri di articolo via, verificati o no (esistenza
    # != rilevanza — vedi test_norme_guard_default_strippa_anche_articolo_esistente)
    from app.lib import norme_guard
    t = ("Il periodo di prova è disciplinato dall'art. 2096 c.c.; "
         "vedi anche artt. 62-63 del CCNL per il preavviso.")
    out = norme_guard.sanitize(t)
    assert "2096" not in out and "62" not in out and "63" not in out
    assert "il codice civile" in out and "il CCNL applicato" in out


def test_norme_guard_fail_closed_su_errore_remoto():
    from unittest import mock
    from app.lib import norme_guard
    t = "dall'art. 2099-c al Codice Civile deriva che…"
    with mock.patch.object(norme_guard, "_verify_remote", side_effect=RuntimeError("giù")):
        out = norme_guard.sanitize(t)
    assert "2099" not in out                # errore → strip totale, mai fail-open


def test_norme_guard_fail_closed_su_corpus_assente():
    patch, ng = _con_verify(None)           # None = corpus non disponibile
    t = "come da art. 1341 c.c. sulle clausole vessatorie"
    with patch:
        out = ng.sanitize(t)
    assert "1341" not in out


def test_norme_guard_nessuna_citazione_nessuna_latenza():
    from unittest import mock
    from app.lib import norme_guard
    t = "Sì, puoi farlo: verifica il tuo CCNL per i dettagli."
    with mock.patch.object(norme_guard, "_verify_remote", side_effect=AssertionError("non deve chiamare")):
        assert norme_guard.sanitize(t) == t


# ── regex 'articolo' esteso (eval consulente 17 lug: 'articolo 2099-c' sfuggiva) ──────

def test_legal_article_re_cattura_forma_estesa():
    from app.lib import signals
    for t in ("articolo 2099-c del Codice Civile", "articolo 2096 del codice civile",
              "articoli 62 e 63 del CCNL", "art. 2096 c.c.", "artt. 1341 c.c."):
        assert signals.LEGAL_ARTICLE_RE.search(t), f"deve matchare: {t}"


def test_norme_guard_strippa_articolo_esteso_non_verificato():
    from unittest import mock
    from app.lib import norme_guard
    # '2099-c' inventato → verify ritorna nessuna verificata → strip
    t = "Puoi inserire un periodo di prova (articolo 2099-c del Codice Civile) che ti consente…"
    with mock.patch.object(norme_guard, "_verify_remote", lambda testo: []):
        out = norme_guard.sanitize(t)
    assert "2099" not in out and "il codice civile" in out


def test_norme_guard_default_strippa_articolo_esteso():
    from app.lib import norme_guard
    t = "Il periodo di prova è disciplinato dall'articolo 2096 del codice civile."
    out = norme_guard.sanitize(t)  # default descriptive-only
    assert "2096" not in out and "il codice civile" in out


# ── grounding forzato + principio di conoscenza (filosofia Luca 17 lug) ────────────────

def test_fact_grounding_trigger_cross_dominio():
    # DOMAIN-AGNOSTICO (filosofia: la conoscenza va presa dalle fonti SEMPRE, non solo legale)
    from app.lib import fact_grounding as fg
    for q in ("Entro quanti giorni devo comunicare un'assunzione?",   # HR/legale
              "Qual è l'aliquota IVA sui prodotti alimentari?",        # fisco
              "Quanto costa aprire una SRL?",                          # societario
              "Qual è il prezzo medio di una campagna Google Ads?",    # marketing
              "Quali sono i principali competitor nel packaging in Italia?",  # mercato
              "Quanto è grande il mercato del food delivery in Italia?",       # dati
              "Cos'è il codice ATECO 62.01?"):                          # definizione
        assert fg.needs_grounding(q), f"doveva attivare grounding: {q}"


def test_fact_grounding_no_trigger_su_giudizi_e_chitchat():
    from app.lib import fact_grounding as fg
    # giudizi/strategia (metodo dalle skill, non un fatto esterno) + conversazionale
    for q in ("Quanto dovrei spendere in marketing?",
              "Conviene assumere ora o aspettare?",
              "È meglio una SRL o una ditta individuale?",
              "Come miglioro il clima aziendale?",
              "come faccio a ridurre i costi?",
              "ciao", "grazie mille"):
        assert not fg.needs_grounding(q), f"NON doveva attivare grounding: {q}"


def test_ground_block_none_senza_risultati(monkeypatch):
    from app.lib import fact_grounding as fg
    monkeypatch.setattr(fg, "_enabled", lambda: True)
    monkeypatch.setattr(fg.web_search, "run_openai_search", lambda q: "[ricerca web: nessun risultato]")
    assert fg.ground_block("Qual è l'aliquota IVA sugli alimentari?") is None  # fail-open


def test_ground_block_inietta_i_risultati(monkeypatch):
    from app.lib import fact_grounding as fg
    monkeypatch.setattr(fg, "_enabled", lambda: True)
    monkeypatch.setattr(fg.web_search, "run_openai_search",
                        lambda q: "L'aliquota IVA sui beni di prima necessità è il 4%. Fonti: ...")
    b = fg.ground_block("Qual è l'aliquota IVA sugli alimentari?")
    assert b and "RICERCA WEB" in b and "4%" in b
    # il blocco NON deve spacciare il web come fonte già validata (causa del bug #6)
    assert "NON pre-validati" in b and "fonte ufficiale" in b


def test_prompt_contiene_principio_di_conoscenza():
    p = _prompt([{"role": "user", "content": "ciao"}])
    assert "PRINCIPIO DI CONOSCENZA" in p
    assert "NON è la conoscenza del modello" in p
    assert "ANDARE A PRENDERE" in p


def test_prompt_spiega_il_perche_di_ogni_consiglio():
    """Spec Luca (18 lug): ogni consiglio operativo deve dire anche il PERCHÉ, per far
    percepire il ragionamento del consulente, non un elenco di istruzioni."""
    p = _prompt([{"role": "user", "content": "ciao"}])
    assert "IL PERCHÉ, NON SOLO IL COSA" in p
    assert "far percepire il RAGIONAMENTO" in p or "far sentire il ragionamento" in p.lower()


def test_prompt_ancora_ai_fatti_del_caso():
    """Spec Luca (18 lug): su un caso concreto, collega OGNI raccomandazione ai fatti dati
    dall'utente (niente consulenza generica) e non introdurre obblighi/scadenze non ancorati
    alla normativa o ai dati disponibili."""
    p = _prompt([{"role": "user", "content": "ciao"}])
    assert "ANCORA SEMPRE AI FATTI DEL CASO" in p
    assert "andrebbe bene per chiunque" in p.lower()
    assert "obblighi" in p.lower() and "non inventarlo" in p.lower()


def test_prompt_struttura_risposte_giuridiche():
    """Spec Luca: struttura giuridica = normativa principale (in parole) → spiegazione
    semplice → dipendenze CCNL/contratto/caso → niente assoluti/invenzioni. E 'cita la
    normativa' NON riapre il buco dei numeri di articolo (quelli restano al report)."""
    p = _prompt([{"role": "user", "content": "ciao"}])
    assert "RISPOSTE GIURIDICHE" in p
    assert "LINGUAGGIO SEMPLICE" in p.upper() or "linguaggio semplice" in p.lower()
    assert "CCNL applicato" in p
    # citare la normativa in parole è incoraggiato, ma il NUMERO dell'articolo resta al report
    assert "CITA la normativa principale" in p
    assert "solo il numero dell'articolo" in p.lower() or "è SOLO il numero dell'articolo" in p


# ── webresearch effettivo (lug 2026): ricerca proattiva oltre i numeri-fatto ─────────────
def test_research_query_compliance_and_norms():
    from app.lib import fact_grounding as fg
    # verifica di conformità → si cerca (requisiti dalle fonti)
    q = fg.research_query("la mia app di outfit è in regola col GPDR?")
    assert q and "fonti ufficiali" in q
    # domanda normativa in contesto normativo → si cerca
    q = fg.research_query("è obbligatoria la DPIA per la mia app?", "parliamo di gdpr e privacy")
    assert q and "normativa italiana" in q


def test_research_query_provider_due_diligence():
    from app.lib import fact_grounding as fg
    # provider nominato in contesto normativo (anche dal contesto recente, non solo il turno)
    q = fg.research_query("io in questo caso ho scelto openai, devo contattare loro?",
                          "server extra ue gdpr foto dati personali")
    assert q and "DPA" in q and "data residency" in q
    assert "openai" in q.lower()
    # provider nominato SENZA contesto normativo → nessuna ricerca (chiacchiera di prodotto)
    assert fg.research_query("uso openai per generare le immagini, è velocissimo") is None


def test_research_query_explicit_and_negatives():
    from app.lib import fact_grounding as fg
    assert fg.research_query("cercami i competitor del packaging in Umbria")   # esplicita
    # giudizi/strategia e chitchat → mai
    for t in ("Conviene assumere ora o aspettare?", "come faccio a ridurre i costi?",
              "ok grazie", "Come miglioro il clima aziendale?"):
        assert fg.research_query(t) is None, t
    # il trigger storico sui numeri-fatto resta attivo
    assert fg.research_query("Qual è l'aliquota IVA sugli alimentari?")


def test_ground_block_uses_research_query(monkeypatch):
    from app.lib import fact_grounding as fg
    monkeypatch.setattr(fg, "_enabled", lambda: True)
    seen = {}
    def _fake_search(q):
        seen["q"] = q
        return "OpenAI offre un DPA standard. Fonti: openai.com"
    monkeypatch.setattr(fg.web_search, "run_openai_search", _fake_search)
    b = fg.ground_block("ho scelto openai per le foto, è un problema?", "audit gdpr privacy")
    assert b and "DPA standard" in b and "documentazione verificabili" in b
    assert "DPA" in seen["q"]                       # la query è quella di due diligence
