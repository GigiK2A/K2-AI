"""LegalBoost — modalità QUESITO (parere su caso specifico).

Bug prod (data-breach): il cliente porta un incidente puntuale ("abbiamo inviato per
errore i dati di 300 clienti a un fornitore: dobbiamo notificare al Garante?") ma il
report usciva come audit-compliance PMI generico a 9 aree (contrattualistica, 231, IP,
lavoro, fiscale…), fuori tema, senza rispondere alle domande poste.

Questi test verificano (OFFLINE, niente API) che con un `quesito` sostanziale:
- lo scheletro diventa CASE-FIRST e passa L1 (meta-schema) + L2 (linter);
- il deliverable valida contro l'output-schema;
- la sezione 01 è "Risposta al tuo quesito" (non "Sintesi e mappa rischi");
- il `piano_azione` NON è più l'azione contrattuale hard-coded;
- SENZA quesito il comportamento resta l'audit a 9 voci (zero regressione).

Standalone: python tests/test_legal_quesito.py → exit 0 se PASS.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from jsonschema import Draft202012Validator  # noqa: E402

from app import assets, jobs, legal_quesito, pipeline, validate  # noqa: E402

ok = True


def check(label, cond):
    global ok
    ok = ok and bool(cond)
    print(f"  {'OK ' if cond else 'FAIL'} {label}")


SKILL = "flusso-legalboost-pmi"
SERVICE = "primo_parere_legale"
QUESITO = ("Un nostro dipendente ha inviato per errore a un fornitore un file con nome, "
           "email, telefono e codice cliente di circa 300 clienti. Lo abbiamo contattato "
           "e ha confermato la cancellazione entro 24h. Dobbiamo notificare al Garante? E "
           "ai clienti? Che rischi corriamo?")
INPUTS_QUESITO = {
    "ragione_sociale": "Società oggetto di analisi",
    "forma_giuridica": "srl", "settore_ateco": "servizi B2B e consulenza tecnica",
    "n_dipendenti": 12, "fatturato": 1800000, "quesito": QUESITO,
}
INPUTS_AUDIT = {k: v for k, v in INPUTS_QUESITO.items() if k != "quesito"}


print("── is_quesito: detection ──")
check("vuoto → False", legal_quesito.is_quesito({}) is False)
check("token corto ('gdpr') → False", legal_quesito.is_quesito({"quesito": "gdpr"}) is False)
check("caso reale → True", legal_quesito.is_quesito(INPUTS_QUESITO) is True)
check("non-dict → False", legal_quesito.is_quesito(None) is False)


print("── maybe_quesito: swap scheletro + asset non mutato ──")
bp = assets.load_blueprint(SKILL)
audit_ids = [v["id"] for v in bp["voci"]]
bpq = legal_quesito.maybe_quesito(SKILL, bp, INPUTS_QUESITO)
q_ids = [v["id"] for v in bpq["voci"]]
check("audit ha 9 voci", len(audit_ids) == 9)
check("quesito è case-first (fatti_raccolti presente)", "fatti_raccolti" in q_ids)
check("quesito NON ha le aree audit (contrattualistica assente)", "contrattualistica" not in q_ids)
check("prima voce riusa id sintesi_mappa_rischi (render/heatmap)", q_ids[0] == "sintesi_mappa_rischi")
check("ultima voce riusa id piano_azione_handoff (tabella piano)", q_ids[-1] == "piano_azione_handoff")
check("blueprint lru_cached NON mutato (audit intatto)",
      [v["id"] for v in assets.load_blueprint(SKILL)["voci"]] == audit_ids)
check("no quesito → blueprint invariato (stesso oggetto)",
      legal_quesito.maybe_quesito(SKILL, bp, INPUTS_AUDIT) is bp)
check("skill non-legale → invariato",
      legal_quesito.maybe_quesito("flusso-financeboost-pmi", bp, INPUTS_QUESITO) is bp)


print("── quesito blueprint: L1 (meta-schema) + L2 (linter) ──")
r1 = validate.l1(bpq)
check("L1 pass sul blueprint quesito", r1.get("pass"))
r2 = validate.l2(pipeline._lint_instance(bpq), bpq)
check("L2 pass sul blueprint quesito", r2.get("pass"))
pages = sum((v.get("pagine") or {}).get("min", 2) for v in bpq["voci"])
check(f"somma pagine {pages} ∈ [16,24] (R02)", 16 <= pages <= 24)
check("prima voce ≤ 2 pagine (R05)", (bpq["voci"][0].get("pagine") or {}).get("min") <= 2)


print("── assemble_legalboost: quesito mode (schema-valido, no azione contrattuale) ──")
out_schema = assets.load_output_schema(SKILL)
# sezioni + meta finti (simulano l'LLM) per testare l'ASSEMBLY deterministico offline
sezioni = {v["id"]: f"Prosa di prova per {v['titolo']} sul caso data breach." for v in bpq["voci"]}
meta_struct = {
    "score": 40,
    "mappa_rischi": [{"area": "Protezione dati", "semaforo": "giallo"}],
    "voci_meta": {
        "sintesi_mappa_rischi": {"rischi": [{"descrizione": "Valutare obbligo notifica",
                                             "gravita": "media", "serve_avvocato": False}],
                                 "azioni": ["Documentare l'incidente nel registro delle violazioni"]},
        "valutazione_rischio": {"rischi": [{"descrizione": "Rischio per i diritti degli interessati",
                                            "gravita": "media", "serve_avvocato": True}],
                                "azioni": ["Valutare il rischio ex art. 33 GDPR"]},
        "analisi_normativa": {"rischi": [], "azioni": ["Verificare i termini delle 72 ore"]},
    },
}
deliv = pipeline.assemble_legalboost(bpq, sezioni, [], INPUTS_QUESITO, meta_struct, offline=False)
errs = sorted(Draft202012Validator(out_schema).iter_errors(deliv), key=lambda e: list(e.path))
check("deliverable quesito valida output-schema", not errs)
if errs:
    print("     errori:", [str(e.message) for e in errs[:3]])
titoli = [v["titolo"] for v in deliv["voci"]]
check("voce 01 titolo = 'Risposta al tuo quesito'", titoli[0] == "Risposta al tuo quesito")
azioni_piano = [p["azione"] for p in deliv["piano_azione"]]
check("piano_azione NON è l'azione contrattuale hard-coded",
      not any("1341" in a or "condizioni generali" in a.lower() for a in azioni_piano))
check("piano_azione deriva dalle azioni reali delle voci",
      "Documentare l'incidente nel registro delle violazioni" in azioni_piano)
check("piano handoff_avvocato=True dove la voce ha rischio serve_avvocato",
      any(p["handoff_avvocato"] and "art. 33" in p["azione"] for p in deliv["piano_azione"]))
norme_analisi = next(v["norme_citate"] for v in deliv["voci"] if v["id"] == "analisi_normativa")
check("norme_citate agganciate alla voce analisi (schema ok anche se vuote)",
      isinstance(norme_analisi, list))


print("── FIX TIMEOUT: assemble ONLINE senza meta valido → NIENTE score=-1 (era il dead-end) ──")
# Riproduce il bug prod: structured_meta troncato/None → assemble metteva score=-1 →
# viola output-schema (min 0) → validation_failed → 3 rigenerazioni → timeout 600s.
deliv_nm = pipeline.assemble_legalboost(bpq, sezioni, [], INPUTS_QUESITO, None, offline=False)
sc = deliv_nm["sintesi"]["score_compliance"]
check(f"score online-no-meta in [0,100] (era -1): {sc}", isinstance(sc, int) and 0 <= sc <= 100)
errs_nm = sorted(Draft202012Validator(out_schema).iter_errors(deliv_nm), key=lambda e: list(e.path))
check("deliverable online-no-meta valida output-schema (niente loop rigenerazione→timeout)", not errs_nm)
if errs_nm:
    print("     errori:", [str(e.message) for e in errs_nm[:3]])
check("fallback_score deterministico in range", 0 <= legal_quesito.fallback_score(deliv_nm["voci"]) <= 100)
check("fallback_score senza rischi = 60 (neutro)", legal_quesito.fallback_score([]) == 60)


print("── scrub giurisprudenza: numeri di sentenza inventati neutralizzati, leggi intatte ──")
scr = legal_quesito.scrub_giurisprudenza({"voci": [{"contenuto":
    "La diffamazione online (Cass. Pen. 4873/2020) e la sentenza n. 99/2018 rilevano; "
    "condotta ex art. 595 c.p., illecito art. 2043 c.c., D.Lgs 231/2001, Reg. UE 2016/679."}]})
txt = scr["voci"][0]["contenuto"]
check("numero Cassazione rimosso", "4873/2020" not in txt and "99/2018" not in txt)
check("riferimento all'orientamento conservato", "Cassazione" in txt)
check("norme/numeri di legge INTATTI (595 c.p., 2043 c.c., 231/2001, 2016/679)",
      all(x in txt for x in ("art. 595 c.p.", "art. 2043 c.c.", "231/2001", "2016/679")))
check("guardrail nel system quesito (sentenze + pseudo-precisione + termini)",
      all(k in legal_quesito.SYSTEM for k in ("MAI NUMERI DI SENTENZA", "pseudo-precisione", "TERMINI DI LEGGE")))


print("── piano_azione: fallback offline è NEUTRO (mai l'azione contrattuale) ──")
piano_vuoto = legal_quesito.piano_azione({}, bpq["voci"], INPUTS_QUESITO)
check("fallback ha ≥1 azione", len(piano_vuoto) >= 1)
check("fallback non contrattuale",
      not any("1341" in p["azione"] for p in piano_vuoto))

print("── piano_azione: scarta gli scenari-header e accorcia (fix tabella troncata) ──")
_vm = {"sintesi_mappa_rischi": {"rischi": [], "azioni": [
    "SCENARIO A (PRIORITARIO): raccolta prove immediata e diffida legale con richiesta rimozione",
    "RISPOSTA DIRETTA: le recensioni superano il diritto di critica se prive di prove",
    "Acquisire il testo integrale delle recensioni con timestamp di pubblicazione entro 48 ore, "
    "salvando screenshot autenticati, URL e metadati visibili, per cristallizzare la prova prima "
    "di ogni azione (questo testo è volutamente molto lungo per verificare l'accorciamento)"]}}
_piano = legal_quesito.piano_azione(_vm, bpq["voci"], INPUTS_QUESITO)
_az = [p["azione"] for p in _piano]
check("scenari-header ('SCENARIO A', 'RISPOSTA DIRETTA') scartati",
      not any(a.upper().startswith(("SCENARIO", "RISPOSTA DIRETTA")) for a in _az))
check("azione operativa tenuta", any("Acquisire il testo" in a for a in _az))
check("azioni accorciate (nessuna oltre ~135 char)", all(len(a) <= 135 for a in _az))


print("── regressione AUDIT: assemble senza quesito → 9 voci, norme sulle aree audit ──")
deliv_a = pipeline.assemble_legalboost(bp, {v["id"]: "x" * 80 for v in bp["voci"]}, [],
                                       INPUTS_AUDIT, meta_struct, offline=True)
errs_a = sorted(Draft202012Validator(out_schema).iter_errors(deliv_a), key=lambda e: list(e.path))
check("audit deliverable valida output-schema", not errs_a)
check("audit ha 9 voci", len(deliv_a["voci"]) == 9)
check("audit voce 01 titolo = 'Sintesi e mappa rischi'",
      deliv_a["voci"][0]["titolo"] == "Sintesi e mappa rischi")


print("── integrazione: pipeline.run OFFLINE (quesito) → rendered + PDF ──")
job_id = jobs.create(SERVICE, "flusso-legalboost-pmi", 1.0)
pipeline.run(job_id, SERVICE, INPUTS_QUESITO, "FULL")
j = jobs.get(job_id)
check(f"job status = rendered (era {j.get('status')})", j.get("status") == "rendered")
if j.get("status") == "rendered":
    pdf = (j.get("outputs") or {}).get("pdf_path")
    check("PDF generato su disco", pdf and Path(pdf).is_file())
    import json as _json
    dj = _json.loads(Path((j["outputs"])["json_path"]).read_text(encoding="utf-8"))
    check("deliverable renderizzato è case-first (fatti_raccolti presente)",
          any(v["id"] == "fatti_raccolti" for v in dj["voci"]))
    check("piano_azione renderizzato non contrattuale",
          not any("1341" in p["azione"] for p in dj["piano_azione"]))
else:
    check("run quesito NON refuse", False)
    print("     refusal:", j.get("refusal_reason"), j.get("validation"))


print("── integrazione: pipeline.run OFFLINE (audit, no quesito) → 9 aree ──")
job_id2 = jobs.create(SERVICE, "flusso-legalboost-pmi", 1.0)
pipeline.run(job_id2, SERVICE, INPUTS_AUDIT, "FULL")
j2 = jobs.get(job_id2)
check(f"job audit status = rendered (era {j2.get('status')})", j2.get("status") == "rendered")
if j2.get("status") == "rendered":
    import json as _json
    dj2 = _json.loads(Path((j2["outputs"])["json_path"]).read_text(encoding="utf-8"))
    check("audit renderizzato ha 9 voci", len(dj2["voci"]) == 9)
    check("audit renderizzato ha 'contrattualistica'",
          any(v["id"] == "contrattualistica" for v in dj2["voci"]))


print("\n" + ("TEST LEGAL-QUESITO PASS ✅" if ok else "TEST LEGAL-QUESITO FAIL ❌"))
sys.exit(0 if ok else 1)
