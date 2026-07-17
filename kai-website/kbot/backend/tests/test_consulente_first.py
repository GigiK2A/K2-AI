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
