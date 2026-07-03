"""Test del riclassificatore di bilancio DETERMINISTICO (app/finance.py).

Motivazione (giu 2026): FinanceBoost produceva numeri SBAGLIATI perché Haiku
estraeva 'patrimonio_netto'/'ebitda'/'debiti_finanziari' (quantità DERIVATE, non
voci di bilancio) da un OCR e li sbagliava (PN=utile, debiti=totale passività) →
calc.py calcolava fedelmente D/E=6,39 su input spazzatura. Garbage in, garbage out.

Soluzione: l'LLM TRASCRIVE le voci (affidabile); la riclassificazione + l'aritmetica
le fa Python (corretto). Ground-truth = BILANCIO 2024 reale di K2A S.r.l.s.

Standalone: python tests/test_finance.py → exit 0 se PASS.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import finance  # noqa: E402

ok = True


def check(label, cond):
    global ok
    ok = ok and cond
    print(f"  {'OK ' if cond else 'FAIL'} {label}")


def approx(a, b, tol=0.02):
    return a is not None and b is not None and abs(a - b) <= tol


# ════════════ FIXTURE: BILANCIO 2024 K2A S.r.l.s. (voci REALI) ════════════
# Voci a livello di categoria (i subtotali etichettati dal bilancio a 4 sezioni).
# Immobilizzazioni a valore LORDO sull'attivo, fondi ammortamento nel passivo
# (formato 4 sezioni) → vanno nettati. `sezione` disambigua erario/banche/fornitori.
VOCI = [
    # ───── ATTIVO ─────
    {"sezione": "attivo", "descrizione": "COSTI D'IMPIANTO E DI AMPLIAMENTO", "importo": 951.11},
    {"sezione": "attivo", "descrizione": "BENI IMMATERIALI", "importo": 2459.52},
    {"sezione": "attivo", "descrizione": "IMPIANTI E MACCHINARI", "importo": 3400.00},
    {"sezione": "attivo", "descrizione": "ATTREZZATURE INDUSTRIALI E COMMERCIALI", "importo": 56063.49},
    {"sezione": "attivo", "descrizione": "ALTRE IMMOBILIZZAZIONI MATERIALI", "importo": 55945.26},
    {"sezione": "attivo", "descrizione": "CLIENTI", "importo": 177460.58},
    {"sezione": "attivo", "descrizione": "CREDITI VARI V/TERZI", "importo": 49152.92},
    {"sezione": "attivo", "descrizione": "BANCHE C/C E POSTA C/C", "importo": 289835.07},
    {"sezione": "attivo", "descrizione": "CASSA", "importo": 173.18},
    {"sezione": "attivo", "descrizione": "RATEI E RISCONTI ATTIVI", "importo": 5395.81},
    {"sezione": "attivo", "descrizione": "FORNITORI", "importo": 83.92},
    {"sezione": "attivo", "descrizione": "ERARIO C/IVA", "importo": 654.65},
    {"sezione": "attivo", "descrizione": "ERARIO C/RIT. SUBITE E CREDITI D'IMPOSTA", "importo": 7046.88},
    # ───── PASSIVO ─────
    {"sezione": "passivo", "descrizione": "BANCHE C/C E POSTA C/C", "importo": 51951.38},  # Ifis factoring
    {"sezione": "passivo", "descrizione": "CAPITALE SOCIALE", "importo": 200.00},
    {"sezione": "passivo", "descrizione": "RISULTATI PORTATI A NUOVO", "importo": 88239.26},
    {"sezione": "passivo", "descrizione": "FONDO TFR", "importo": 66672.45},
    {"sezione": "passivo", "descrizione": "MUTUI E FINANZIAMENTI", "importo": 40907.33},
    {"sezione": "passivo", "descrizione": "FATTURE/NOTE CREDITO DA RICEVERE", "importo": 61755.84},
    {"sezione": "passivo", "descrizione": "FORNITORI", "importo": 15081.85},
    {"sezione": "passivo", "descrizione": "ERARIO C/IVA", "importo": 54079.60},
    {"sezione": "passivo", "descrizione": "ERARIO C/SOSTITUTO D'IMPOSTA", "importo": 7982.41},
    {"sezione": "passivo", "descrizione": "ERARIO C/IMPOSTE", "importo": 5664.87},
    {"sezione": "passivo", "descrizione": "ENTI PREVIDENZIALI", "importo": 8651.00},
    {"sezione": "passivo", "descrizione": "DEBITI VARI", "importo": 10454.72},
    {"sezione": "passivo", "descrizione": "DEBITI VERSO IL PERSONALE", "importo": 19223.00},
    {"sezione": "passivo", "descrizione": "FONDI AMMORT. IMMOBILIZZAZ. IMMATERIALI", "importo": 2728.48},
    {"sezione": "passivo", "descrizione": "FONDI AMMORTAMENTO IMPIANTI E MACCHINARI", "importo": 1785.00},
    {"sezione": "passivo", "descrizione": "FONDI AMMORT. ATTREZZ. INDUSTR.E COMMERC.", "importo": 23608.47},
    {"sezione": "passivo", "descrizione": "FONDI AMMORTAMENTO ALTRI BENI MATERIALI", "importo": 50334.80},
    {"sezione": "passivo", "descrizione": "RATEI E RISCONTI PASSIVI", "importo": 51613.75},
    # ───── CONTO ECONOMICO ─────
    {"sezione": "ricavi", "descrizione": "RICAVI DA PRESTAZIONI", "importo": 782222.21},
    {"sezione": "ricavi", "descrizione": "PROVENTI DIVERSI", "importo": 7543.96},
    {"sezione": "ricavi", "descrizione": "PROVENTI FINANZIARI VARI", "importo": 0.33},
    {"sezione": "costi", "descrizione": "PRESTAZIONI DI LAVORO AUTONOMO", "importo": 225908.52},
    {"sezione": "costi", "descrizione": "COSTI PERSONALE DIPENDENTE", "importo": 207373.49},
    {"sezione": "costi", "descrizione": "COSTI DIVERSI PERSONALE DIPENDENTE", "importo": 54324.59},
    {"sezione": "costi", "descrizione": "ALTRI COSTI DI ESERCIZIO", "importo": 53484.96},
    {"sezione": "costi", "descrizione": "COMPENSI ORGANI SOCIALI", "importo": 26154.40},
    {"sezione": "costi", "descrizione": "ALTRI COSTI GODIMENTO BENI DI TERZI", "importo": 26000.00},
    {"sezione": "costi", "descrizione": "SPESE AMMINISTRATIVE E GENERALI", "importo": 18668.22},
    {"sezione": "costi", "descrizione": "GESTIONE IMMOBILI", "importo": 16311.62},
    {"sezione": "costi", "descrizione": "SERVIZI PER LA PRODUZIONE", "importo": 10350.00},
    {"sezione": "costi", "descrizione": "COSTI PER UTENZE", "importo": 7494.58},
    {"sezione": "costi", "descrizione": "LOCAZ. E CANONI AUTOV. E ALTRI VEICOLI", "importo": 7255.00},
    {"sezione": "costi", "descrizione": "ONERI TRIBUTARI", "importo": 3693.54},
    {"sezione": "costi", "descrizione": "ESERCIZIO AUTOVETTURE E ALTRI VEICOLI", "importo": 3284.77},
    {"sezione": "costi", "descrizione": "MANUTENZIONI MACCHINARI E ATTREZZATURE", "importo": 2520.00},
    {"sezione": "costi", "descrizione": "SPESE COMMERCIALI E DI VIAGGIO", "importo": 2192.17},
    {"sezione": "costi", "descrizione": "LOCAZIONI E CANONI IMPIANTI E ATTREZZ.", "importo": 2167.66},
    # voci che la riclassificazione deve ISOLARE (ammortamenti / oneri fin / imposte)
    {"sezione": "costi", "descrizione": "AMM.TI CIVILISTICI IMMOBILIZZ. MATERIALI", "importo": 11788.25},
    {"sezione": "costi", "descrizione": "AMM.TI CIVILISTICI IMMOBILIZZ. IMMATER.", "importo": 682.12},
    {"sezione": "costi", "descrizione": "ONERI FINANZIARI VERSO BANCHE", "importo": 2197.33},
    {"sezione": "costi", "descrizione": "ONERI FINANZIARI DIVERSI", "importo": 10983.95},
    {"sezione": "costi", "descrizione": "IMPOSTE DELL'ESERCIZIO", "importo": 8522.00},
    # risultato d'esercizio (riportato esplicitamente dal bilancio: "Utile del periodo")
    {"sezione": "risultato", "descrizione": "UTILE DEL PERIODO", "importo": 87688.18},
]

r = finance.reclassify_bilancio(VOCI, anno=2024)
sp, ce, idx = r["sp"], r["ce"], r["indici"]

print("── Quadratura (controllo integrità) ──")
check("quadratura OK (attivo == passivo + utile)", r["quadratura"]["ok"])
check("attivo lordo = 648.622,39", approx(r["quadratura"]["attivo_lordo"], 648622.39))

print("── Stato patrimoniale riclassificato ──")
check("PATRIMONIO NETTO = 176.127,44 (NON 87.688 né 'capitale minimo')",
      approx(sp["patrimonio_netto"], 176127.44))
check("debiti finanziari = 92.858,71 (factoring 51.951 + mutui 40.907)",
      approx(sp["debiti_finanziari"], 92858.71))
check("debiti v/terzi totali = 394.038,20 (netto fondi amm.)",
      approx(sp["debiti_terzi"], 394038.20))
check("liquidità = 290.008,25", approx(sp["liquidita"], 290008.25))
check("immobilizzazioni NETTE = 40.362,63 (lordo 118.819 - fondi 78.457)",
      approx(sp["immobilizzazioni_nette"], 40362.63))
check("attivo corrente = 529.803,01", approx(sp["attivo_corrente"], 529803.01))
check("passivo corrente = 286.458,42", approx(sp["passivo_corrente"], 286458.42))
check("totale attivo (netto) = 570.165,64", approx(sp["totale_attivo"], 570165.64))

print("── Conto economico riclassificato ──")
check("EBITDA = 121.861,50 (NON 'non disponibile')", approx(ce["ebitda"], 121861.50))
check("EBIT = 109.391,13", approx(ce["ebit"], 109391.13))
check("oneri finanziari = 13.181,28", approx(ce["oneri_finanziari"], 13181.28))
check("ammortamenti = 12.470,37", approx(ce["ammortamenti"], 12470.37))
check("utile netto = 87.688,18", approx(ce["utile_netto"], 87688.18))
check("ricavi operativi = 789.766,17", approx(ce["ricavi"], 789766.17))

print("── Indici (i numeri che il bot sbagliava) ──")
check("D/E finanziario = 0,53 (NON 6,39)", approx(idx["de"], 0.53))
check("D/E totale = 2,24", approx(idx["de_totale"], 2.24))
check("PFN = -197.149,54 → CASSA NETTA (segno negativo)",
      approx(idx["pfn"], -197149.54) and idx["pfn"] < 0)
check("EBITDA margin = 15,4%", approx(idx["ebitda_margin"], 15.4, tol=0.1))
check("ROE = 49,8%", approx(idx["roe"], 49.8, tol=0.1))
check("ROS = 13,9%", approx(idx["ros"], 13.9, tol=0.1))
check("ROI = 19,2%", approx(idx["roi"], 19.2, tol=0.1))
check("current ratio = 1,85", approx(idx["current_ratio"], 1.85, tol=0.01))
check("interest coverage = 8,30x", approx(idx["interest_coverage"], 8.30, tol=0.05))
check("autonomia finanziaria = 30,9%", approx(idx["autonomia_finanziaria"], 30.9, tol=0.1))
check("CCN = 243.344,59", approx(idx["ccn"], 243344.59))

print("── Onestà sui dati mancanti (no invenzioni) ──")
# DSO calcolabile (clienti + ricavi presenti)
check("DSO ≈ 82 giorni", approx(idx["dso"], 82.0, tol=1.0))
# rimanenze assenti → quick ratio = current ratio (nessun magazzino), non un errore
check("nessun magazzino → quick = current", approx(idx["quick_ratio"], idx["current_ratio"], tol=0.01))

print("── Caso degenere: bilancio vuoto → non_disponibile, MAI crash/invenzione ──")
empty = finance.reclassify_bilancio([], anno=2024)
check("vuoto → quadratura non ok / flag", empty["quadratura"]["ok"] is False)
check("vuoto → PN non inventato (None)", empty["sp"]["patrimonio_netto"] is None)

print("── Caso quadratura SBALLATA: deve essere SEGNALATA, non nascosta ──")
sbal = finance.reclassify_bilancio([
    {"sezione": "attivo", "descrizione": "BANCHE", "importo": 100000.0},
    {"sezione": "passivo", "descrizione": "MUTUI E FINANZIAMENTI", "importo": 30000.0},
    {"sezione": "passivo", "descrizione": "CAPITALE SOCIALE", "importo": 10000.0},
    # attivo 100k ≠ passivo 40k → squadra di 60k
], anno=2024)
check("squadratura rilevata (ok=False)", sbal["quadratura"]["ok"] is False)
check("delta squadratura ≈ 60.000", approx(abs(sbal["quadratura"]["delta"]), 60000.0, tol=1.0))

print("── Bridge calc.py: le VOCI battono gli aggregati (anche se sbagliati) ──")
from app import calc  # noqa: E402
# bilancio con line-items REALI + aggregati SBAGLIATI come li metteva Haiku
# (patrimonio_netto=utile, debiti_finanziari=totale passività): le voci devono vincere.
b_voci = {"anno": 2024, "voci": VOCI,
          "patrimonio_netto": 87688.18, "debiti_finanziari": 560934.21}
ff_voci = {"bilanci": [b_voci]}
check("calc de = 0,53 (voci vincono, NON 6,39 da aggregati Haiku)",
      approx(calc.resolve_formula_fact("de", ff_voci)["valore"], 0.53))
check("calc roe = 49,8 (PN deterministico 176k, non 87k)",
      approx(calc.resolve_formula_fact("roe", ff_voci)["valore"], 49.8, tol=0.1))
check("calc ebitda_margin = 15,4 (NON non_disponibile)",
      approx(calc.resolve_formula_fact("ebitda_margin", ff_voci)["valore"], 15.4, tol=0.1))
# senza voci, comportamento storico invariato (aggregati usati)
b_noagg = {"anno": 2024, "ricavi": 1000000, "ebitda": 150000}
check("senza voci: ebitda_margin da aggregati = 15.0 (backward compat)",
      calc.resolve_formula_fact("ebitda_margin", {"bilanci": [b_noagg]})["valore"] == 15.0)

print("── Indici deterministici per il report (computati, non scritti dall'LLM) ──")
ind = finance.build_indici(r)
by_nome = {i["nome"]: i for i in ind}
check("build_indici è una lista non vuota", isinstance(ind, list) and len(ind) >= 6)
check("nessun valore-stringa 'non disponibile' nei numeri",
      all(not (isinstance(i["valore"], str) and "disponibil" in i["valore"].lower()) for i in ind))
check("ogni indice ha semaforo valido", all(i["semaforo"] in ("verde", "giallo", "rosso") for i in ind))
deeq = next((i for i in ind if i["nome"].lower().startswith("d/e finanz")), None)
check("D/E finanziario presente, valore 0,53, semaforo verde", deeq and approx(deeq["valore"], 0.53) and deeq["semaforo"] == "verde")
pfn_i = next((i for i in ind if "pfn" in i["nome"].lower() or "posizione finanziaria" in i["nome"].lower()), None)
check("PFN presente e semaforo verde (cassa netta)", pfn_i and pfn_i["semaforo"] == "verde")

print("── Caso degenere build_indici su bilancio vuoto: nessun crash ──")
check("build_indici([]) gestito (lista, eventualmente vuota)", isinstance(finance.build_indici(empty), list))

print("── Integrazione pipeline: reclass dagli inputs + override deliverable ──")
inputs = {"ragione_sociale": "K2A S.r.l.s.", "settore_ateco": "engineering",
          "bilanci": [{"anno": 2023, "voci": []}, {"anno": 2024, "voci": VOCI}]}
rc = finance.latest_reclass_from_inputs(inputs)
check("latest_reclass_from_inputs sceglie l'anno recente con voci (PN=176k)",
      rc is not None and approx(rc["sp"]["patrimonio_netto"], 176127.44))

# deliverable come lo produce l'LLM: indici SBAGLIATI + meta non personalizzata
deliverable_llm = {
    "meta": {"servizio": "FinanceBoost", "versione": "1.0.0", "data": "2026", "azienda": "Cliente"},
    "executive_summary": {"score_globale": 40, "semafori_aree": [{"area": "Solidità", "semaforo": "rosso"}]},
    "indici": [{"nome": "D/E", "valore": "6.39", "benchmark": "1.0", "semaforo": "rosso"}],
    "piano_azione": [{"priorita": 1, "azione": "Ricapitalizzare urgentemente"}],
    "limitazioni": "nessuna",
}
fixed = finance.apply_to_financeboost(deliverable_llm, rc, inputs)
de_row = next((i for i in fixed["indici"] if i["nome"].lower().startswith("d/e finanz")), None)
check("indici SOVRASCRITTI col deterministico (D/E 0,53, non '6.39')",
      de_row and approx(de_row["valore"], 0.53))
check("nessun indice resta col vecchio D/E=6.39",
      not any(str(i.get("valore")) == "6.39" for i in fixed["indici"]))
check("meta.azienda personalizzata dagli input (non 'Cliente')",
      fixed["meta"]["azienda"] == "K2A S.r.l.s.")
check("meta.data riflette l'esercizio 2024 (non '2026')", "2024" in str(fixed["meta"]["data"]))
check("meta.periodo valorizzato (cover non più 'Periodo: —')", "2024" in str(fixed["meta"].get("periodo", "")))

print("── Sezioni FinanceBoost 9-voci popolate DETERMINISTICAMENTE (riclass/margin/valut) ──")
ric = finance.build_riclassificazione(r)
check("riclassificazione ha anni [2024]", ric.get("anni") == [2024])
check("riclass SP contiene Patrimonio netto 176.127",
      any(row["voce"].lower().startswith("patrimonio") and approx(row["valori"][0], 176127.44) for row in ric["stato_patrimoniale"]))
check("riclass CE contiene EBITDA 121.861",
      any("ebitda" in row["voce"].lower() and approx(row["valori"][0], 121861.50) for row in ric["conto_economico"]))

mar = finance.build_marginalita(r)
check("marginalita: stima_da_aggregati=True (BEP non derivabile dagli aggregati)", mar.get("stima_da_aggregati") is True)
check("marginalita: BEP onesto = None (non inventato)", mar.get("bep_valore") is None)

val = finance.build_valutazione(r, 7.0)
check("valutazione: WACC bindato 7.0", approx(val.get("wacc"), 7.0))
check("valutazione: ROI scomposto margine_operativo ≈ 13.85", approx(val["roi_scomposto"]["margine_operativo"], 13.85, tol=0.1))
check("valutazione: EVA computata (NOPAT - CI*WACC)", isinstance(val.get("eva"), (int, float)))
val_nw = finance.build_valutazione(r, None)
check("valutazione: senza WACC → eva None (non inventata)", val_nw.get("eva") is None)

print("── apply_financeboost_sections: sovrascrive le 3 sezioni nel deliverable ──")
deliv = {"riclassificazione": {"x": 1}, "marginalita": {"bep_valore": 999999}, "valutazione_performance": {"wacc": 99}}
deliv2 = finance.apply_financeboost_sections(deliv, r, 7.0)
check("riclassificazione sovrascritta (deterministica)", "stato_patrimoniale" in deliv2["riclassificazione"])
check("marginalita sovrascritta (BEP non più 999999)", deliv2["marginalita"].get("bep_valore") is None)
check("valutazione sovrascritta (wacc 7.0 non 99)", approx(deliv2["valutazione_performance"]["wacc"], 7.0))

print("── user_wacc_from_inputs: WACC utente batte il CAPM (bug S5: prosa 9,5% vs EVA 11,24) ──")
check("estrae 'WACC 9,5%' → 9.5", approx(finance.user_wacc_from_inputs({"note": "il consulente usa WACC 9,5%"}), 9.5))
check("estrae 'tasso di sconto 8%' → 8.0", approx(finance.user_wacc_from_inputs({"a": "tasso di sconto 8%"}), 8.0))
check("nessun WACC nel testo → None (fallback CAPM)", finance.user_wacc_from_inputs({"a": "EBITDA 720k margine 15%"}) is None)
check("WACC assurdo 250% → None (bound sanità)", finance.user_wacc_from_inputs({"a": "wacc 250%"}) is None)

print("── apply_to_financeboost: tabella indici + meta.periodo deterministici (bug placeholder 'FinanceBoost:1') ──")
_inp = {"ragione_sociale": "Test Srl", "bilanci": [{"anno": 2024, "voci": VOCI}]}
_r = finance.latest_reclass_from_inputs(_inp)
_deliv = {"indici": [{"nome": "FinanceBoost", "valore": 1, "benchmark": 1, "semaforo": "verde"}], "meta": {"periodo": "FinanceBoost"}}
_deliv = finance.apply_to_financeboost(_deliv, _r, _inp)
check("indici SOVRASCRITTI con quelli veri (>=4, non il placeholder)", len(_deliv["indici"]) >= 4 and not any(i["nome"] == "FinanceBoost" for i in _deliv["indici"]))
check("indici contengono D/E finanziario", any("D/E finanz" in i["nome"] for i in _deliv["indici"]))
check("meta.periodo = 'Esercizio 2024' (non 'FinanceBoost')", _deliv["meta"]["periodo"] == "Esercizio 2024")
check("meta.azienda popolata", _deliv["meta"].get("azienda") == "Test Srl")

print("── periodo_from_inputs: PARTIAL (aggregati, NO voci) → periodo dall'anno, non 'FinanceBoost' ──")
check("bilancio aggregato senza voci → 'Esercizio 2024'",
      finance.periodo_from_inputs({"bilanci": [{"anno": 2024, "fatturato": 500000}]}) == "Esercizio 2024")
check("più anni → prende il più recente",
      finance.periodo_from_inputs({"bilanci": [{"anno": 2022}, {"anno": 2024}, {"anno": 2023}]}) == "Esercizio 2024")
check("nessun anno → None (la pipeline mette label onesto)",
      finance.periodo_from_inputs({"bilanci": [{"fatturato": 500000}]}) is None)
check("niente bilanci → None", finance.periodo_from_inputs({"note": "solo fatturato a voce"}) is None)
check("anno assurdo (fuori 1990-2100) scartato → None",
      finance.periodo_from_inputs({"bilanci": [{"anno": 12}]}) is None)

print("── neutralize_financeboost_partial: svuota le sezioni quantitative + fissa periodo (no 'FinanceBoost') ──")
_llm_partial = {
    "meta": {"servizio": "FinanceBoost", "periodo": "FinanceBoost"},
    "executive_summary": {"score_globale": 45, "semafori_aree": [{"area": "Solidità", "semaforo": "rosso"}]},
    "indici": [{"nome": "FinanceBoost", "valore": 1, "benchmark": 1, "semaforo": "verde"}],
    "riclassificazione": {"anni": [], "stato_patrimoniale": [{"voce": "FinanceBoost"}], "conto_economico": [{"voce": "FinanceBoost"}]},
    "marginalita": {"stima_da_aggregati": False},
    "valutazione_performance": {"eva": 1},
    "scenari": [{"nome": "base", "ricavi_proiettati": 1, "sensitivity": [{"variabile": "FinanceBoost", "impatto": 1}]}],
    "piano_azione": [{"priorita": 1, "azione": "Fornire il bilancio strutturato"}],
    "limitazioni": "Analisi preliminare: manca il bilancio.",
}
_clean, _mf = finance.neutralize_financeboost_partial(_llm_partial, {"bilanci": [{"anno": 2024, "fatturato": 500000}]})
check("indici svuotati (no placeholder 'FinanceBoost:1')", _clean["indici"] == [])
check("scenari svuotati (no proiezioni inventate)", _clean["scenari"] == [])
check("riclassificazione svuotata a shape valida", _clean["riclassificazione"] == {"anni": [], "stato_patrimoniale": [], "conto_economico": []})
check("valutazione_performance svuotata (no 'EVA 1')", _clean["valutazione_performance"] == {})
check("marginalita svuotata", _clean["marginalita"] == {})
check("meta.periodo deterministico da anno ('Esercizio 2024')", _clean["meta"]["periodo"] == "Esercizio 2024")
check("sezioni qualitative CONSERVATE (piano_azione, limitazioni)",
      _clean["piano_azione"] and _clean["limitazioni"] and _clean["executive_summary"]["score_globale"] == 45)
check("meta filiera segnala indici/scenari non calcolabili", "indici_non_calcolabili" in _mf and "scenari_non_derivabili" in _mf)

print("\nTEST FINANCE " + ("PASS ✅" if ok else "FAIL ❌"))
sys.exit(0 if ok else 1)
