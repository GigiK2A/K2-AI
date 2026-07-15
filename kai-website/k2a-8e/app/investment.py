"""Investment Engine — decisione di INVESTIMENTO industriale (eval ElectroDrive, 15 lug).

FinanceBoost non deve essere un referto descrittivo ma un INVESTMENT DECISION SUPPORT
SYSTEM: risponde a «questo investimento conviene? è sostenibile? quanto debito aggiuntivo
regge l'azienda? in quanto rientro del CAPEX? cosa succede se il cliente riduce gli ordini?».

Modulo DETERMINISTICO (no LLM), coerente col resto di finance.py. Ogni numero con formula e
assunzioni esplicite (regola cardine: «meglio nessun numero che un numero sbagliato»). Usa i
dati di bilancio riconciliati (EBITDA/PFN/liquidità VERI del cliente, non i derivati garbage).

Modello (dichiarato):
  FCF_t              = EBITDA_incrementale_t × (1 − aliquota) − Δcapitale_circolante_t
  Δcap.circolante    = ricavi_incrementali × (giorni_incasso / 365)   (solo anno di ramp)
  NPV                = Σ FCF_t /(1+WACC)^t − CAPEX
  IRR                = tasso che annulla l'NPV (bisezione deterministica)
  payback            = anno in cui il FCF cumulato copre il CAPEX
  ROI_semplice       = Σ FCF / CAPEX
  PFN/EBITDA post    = (PFN + quota_CAPEX_a_debito) / (EBITDA + EBITDA_incrementale_regime)
  DSCR               = (EBITDA_post − imposte) / servizio_del_debito   (se stimabile)
"""
from __future__ import annotations

from typing import Any, Optional

_TAX = 0.279       # aliquota effettiva proxy (allineata a finance._TAX_PROXY)
_WACC_DEFAULT = 10.0
_COVENANT_PFN_EBITDA = 3.0   # soglia bancaria tipica PFN/EBITDA
_ORIZZONTE_DEFAULT = 5


def _num(v: Any) -> Optional[float]:
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        s = v.strip().replace("€", "").replace("%", "").replace(" ", "")
        if "," in s and "." in s:
            s = s.replace(".", "").replace(",", ".") if s.rfind(",") > s.rfind(".") else s.replace(",", "")
        elif "," in s:
            s = s.replace(",", ".")
        try:
            return float(s)
        except ValueError:
            return None
    return None


def _npv(rate_pct: float, flows: list[float]) -> float:
    """flows[0] = t0 (di norma −CAPEX), flows[t] = FCF anno t."""
    r = rate_pct / 100.0
    return sum(f / (1 + r) ** t for t, f in enumerate(flows))


def _irr(flows: list[float]) -> Optional[float]:
    """IRR in % via bisezione (deterministica, no scipy). None se non c'è cambio di segno
    o non converge (es. tutti i flussi positivi/negativi)."""
    if not flows or all(f >= 0 for f in flows) or all(f <= 0 for f in flows):
        return None
    lo, hi = -90.0, 1000.0
    f_lo, f_hi = _npv(lo, flows), _npv(hi, flows)
    if f_lo * f_hi > 0:
        return None
    for _ in range(200):
        mid = (lo + hi) / 2.0
        f_mid = _npv(mid, flows)
        if abs(f_mid) < 1e-6:
            return round(mid, 2)
        if f_lo * f_mid < 0:
            hi, f_hi = mid, f_mid
        else:
            lo, f_lo = mid, f_mid
    return round((lo + hi) / 2.0, 2)


def _payback(capex: float, fcf_annui: list[float]) -> Optional[float]:
    """Anni per recuperare il CAPEX dal FCF cumulato (interpolazione lineare nell'anno di
    attraversamento). None se non si recupera nell'orizzonte."""
    cum = 0.0
    for i, f in enumerate(fcf_annui, 1):
        prev = cum
        cum += f
        if cum >= capex:
            resto = capex - prev
            return round((i - 1) + (resto / f if f > 0 else 0), 2)
    return None


def _ramp(anno1: float, regime: float, orizzonte: int) -> list[float]:
    """Ramp lineare dei ricavi incrementali da anno1 a regime sull'orizzonte, poi piatto."""
    if orizzonte <= 1:
        return [regime]
    n_ramp = min(3, orizzonte)  # ramp su ~3 anni fino al potenziale
    out = []
    for t in range(1, orizzonte + 1):
        if t < n_ramp:
            out.append(anno1 + (regime - anno1) * (t - 1) / (n_ramp - 1))
        else:
            out.append(regime)
    return out


def _fcf_series(r1: float, reg: float, margine_pct: float, orizzonte: int,
                giorni: float, wacc: float, g_terminale: float = 1.0):
    """FCF operativi per anno + terminal value. FCF = EBITDA×(1−tax) − ΔWC."""
    ricavi_series = _ramp(r1, reg, orizzonte)
    ebitda_series = [rv * margine_pct / 100.0 for rv in ricavi_series]
    dwc_series, prev = [], 0.0
    for rv in ricavi_series:
        dwc_series.append((rv - prev) * (giorni / 365.0) if giorni else 0.0)
        prev = rv
    fcf = [ebitda_series[i] * (1 - _TAX) - dwc_series[i] for i in range(orizzonte)]
    fcf_regime = ebitda_series[-1] * (1 - _TAX)  # a regime niente ΔWC
    tv = fcf_regime / ((wacc - g_terminale) / 100.0) if wacc > g_terminale else 0.0
    return fcf, ricavi_series, round(tv, 2)


def _sensitivity(r1, reg, margine, orizzonte, giorni, wacc, capex):
    """NPV al variare di margine, WACC e orizzonte: la decisione non deve dipendere da un
    singolo set di assunzioni (spec: sensitività + scenari)."""
    def npv_for(m=margine, w=wacc, o=orizzonte):
        fcf, _, tv = _fcf_series(r1, reg, m, o, giorni, w)
        fl = [-capex] + list(fcf)
        fl[-1] += tv
        return round(_npv(w, fl), 2)
    return {
        "margine_-3pp": npv_for(m=max(0.0, margine - 3)),
        "margine_base": npv_for(),
        "margine_+3pp": npv_for(m=margine + 3),
        "wacc_+2pp": npv_for(w=wacc + 2),
        "wacc_-2pp": npv_for(w=max(1.0, wacc - 2)),
        "orizzonte_7a": npv_for(o=7),
        "orizzonte_10a": npv_for(o=10),
    }


_COVENANT_DSCR = 1.2
_COVENANT_INT_COV = 3.0
_TASSO_DEBITO_DEFAULT = 5.0


def _r2(x):
    return round(x, 2) if isinstance(x, (int, float)) else x


def debt_engine(capex: float, financials: dict, params: dict,
                ebitda_incr_regime: float = 0.0) -> dict:
    """Debt Engine: leva, interest coverage, DSCR, covenant headroom PRIMA e DOPO
    l'investimento. Sempre calcolabile dai dati di bilancio + tasso del debito + CAPEX;
    non dipende dai ricavi incrementali del progetto (per questo gira anche su CoolTech,
    dove il tema è la SOSTENIBILITÀ del debito, non l'NPV)."""
    ebitda_now = _num(financials.get("ebitda")) or 0.0
    ebit_now = _num(financials.get("ebit"))
    pfn_now = _num(financials.get("pfn"))
    df_now = _num(financials.get("debiti_finanziari")) or 0.0
    tasso = (_num(params.get("tasso_debito_pct")) or _TASSO_DEBITO_DEFAULT) / 100.0
    quota_debito = _num(params.get("quota_debito_pct"))
    assunzioni = []
    if _num(params.get("tasso_debito_pct")) is None:
        assunzioni.append(f"tasso medio del debito assunto {tasso*100:g}% (non dichiarato)")
    if quota_debito is None:
        quota_debito = 100.0
        assunzioni.append("CAPEX finanziato 100% a debito (conservativo per la sostenibilità)")
    capex_debito = capex * quota_debito / 100.0
    # ammortamento del nuovo debito sull'orizzonte della commessa/piano
    anni_amm = int(_num(params.get("durata_anni")) or _num(params.get("orizzonte_anni")) or 7)
    ebitda_post = ebitda_now + ebitda_incr_regime
    df_post = df_now + capex_debito
    pfn_post = (pfn_now + capex_debito) if pfn_now is not None else None
    lev_now = pfn_now / ebitda_now if (pfn_now is not None and ebitda_now) else None
    lev_post = pfn_post / ebitda_post if (pfn_post is not None and ebitda_post) else None
    # interest coverage = EBIT / interessi
    interessi_post = df_post * tasso
    int_cov_post = ebit_now / interessi_post if (ebit_now is not None and interessi_post) else None
    # DSCR = CFADS / servizio del debito. CFADS ≈ EBITDA − imposte correnti (su EBIT−interessi).
    imposte = max(0.0, ((ebit_now or 0.0) - interessi_post)) * _TAX
    cfads = ebitda_post - imposte
    quota_capitale = df_post / anni_amm if anni_amm else 0.0
    servizio_debito = interessi_post + quota_capitale
    dscr = cfads / servizio_debito if servizio_debito else None
    # servizio del SOLO nuovo debito (per il break-even dei ricavi incrementali: il debito
    # preesistente è già servito dall'EBITDA attuale)
    servizio_nuovo_debito = capex_debito * tasso + (capex_debito / anni_amm if anni_amm else 0.0)
    assunzioni.append(f"servizio del debito = interessi + quota capitale (debito totale post "
                      f"€{df_post:,.0f} ammortizzato in {anni_amm} anni)".replace(",", "."))
    headroom = (_COVENANT_PFN_EBITDA * ebitda_post - (pfn_now or 0)) if ebitda_post else None
    return {
        "pfn_ebitda_attuale": _r2(lev_now), "pfn_ebitda_post": _r2(lev_post),
        "pfn_attuale_eur": _r2(pfn_now), "pfn_post_eur": _r2(pfn_post),
        "debiti_finanziari_post_eur": _r2(df_post),
        "covenant_pfn_ebitda": _COVENANT_PFN_EBITDA,
        "entro_covenant_leva": (lev_post is not None and lev_post <= _COVENANT_PFN_EBITDA),
        "interessi_annui_post_eur": _r2(interessi_post),
        "interest_coverage_post": _r2(int_cov_post),
        "interest_coverage_soglia": _COVENANT_INT_COV,
        "dscr_post": _r2(dscr), "dscr_soglia": _COVENANT_DSCR,
        "entro_covenant_dscr": (dscr is not None and dscr >= _COVENANT_DSCR),
        "servizio_debito_annuo_eur": _r2(servizio_debito),
        "servizio_nuovo_debito_annuo_eur": _r2(servizio_nuovo_debito),
        "debito_aggiuntivo_max_a_covenant_eur": _r2(headroom),
        "covenant_headroom_eur": _r2((_COVENANT_PFN_EBITDA * ebitda_post - (pfn_post or 0))) if ebitda_post else None,
        "formula": ("PFN/EBITDA post = (PFN + CAPEX a debito)/(EBITDA + EBITDA incrementale); "
                    "interest coverage = EBIT/interessi; DSCR = (EBITDA − imposte)/(interessi + "
                    "quota capitale)"),
        "assunzioni": assunzioni,
    }


def working_capital_engine(financials: dict, params: dict,
                           ricavi_incr_regime: float = 0.0) -> dict:
    """Working Capital Engine: assorbimento di cassa e fabbisogno finanziario dai termini di
    pagamento. A 120gg su ricavi rilevanti l'assorbimento è ingente → è il vero vincolo."""
    fatturato = _num(financials.get("fatturato")) or 0.0
    giorni = _num(params.get("giorni_incasso")) or 0.0
    costi_var_pct = _num(params.get("costi_variabili_pct"))
    if not giorni:
        return {"nota": "termini di pagamento non forniti: assorbimento di circolante non stimabile."}
    # crediti generati dal nuovo business (o dall'intero fatturato se il progetto è dominante)
    base_ricavi = ricavi_incr_regime or fatturato
    crediti = base_ricavi * giorni / 365.0
    # se noto il mix costi variabili, il fabbisogno NETTO tiene conto dei debiti v/fornitori
    # (assunti a ~60gg come prassi): cassa assorbita ≈ crediti − debiti_fornitori
    debiti_fornitori = (base_ricavi * (costi_var_pct / 100.0) * 60 / 365.0) if costi_var_pct else 0.0
    fabbisogno = crediti - debiti_fornitori
    # Cash Conversion Cycle: DSO + giorni magazzino − DPO. I giorni non dichiarati sono
    # STIME ESPLICITE (mai N/D muto): DPO 60gg prassi fornitori, magazzino 0 se non noto.
    dso = _num(params.get("dso_giorni")) or giorni
    dpo = _num(params.get("dpo_giorni"))
    dio = _num(params.get("giorni_magazzino"))
    ccc_assunzioni = []
    if dpo is None:
        dpo = 60.0
        ccc_assunzioni.append("DPO assunto 60gg (prassi pagamento fornitori — stima ≈)")
    if dio is None:
        dio = 0.0
        ccc_assunzioni.append("giorni magazzino non dichiarati → assunti 0 (CCC sottostimato se c'è scorta)")
    ccc = dso + dio - dpo
    return {
        "giorni_incasso": giorni,
        "crediti_generati_eur": _r2(crediti),
        "debiti_fornitori_stimati_eur": _r2(debiti_fornitori) if debiti_fornitori else None,
        "assorbimento_cassa_netto_eur": _r2(fabbisogno),
        "base_ricavi_eur": _r2(base_ricavi),
        "cash_conversion_cycle_giorni": _r2(ccc),
        "ccc_componenti": {"dso": _r2(dso), "giorni_magazzino": _r2(dio), "dpo": _r2(dpo)},
        "ccc_assunzioni": ccc_assunzioni,
        "lettura": (f"A {giorni:g} giorni di incasso, il circolante assorbe ~€{fabbisogno:,.0f} di cassa: "
                    "va finanziato oltre al CAPEX. È il vincolo tipico di una grande commessa.").replace(",", "."),
        "formula": ("crediti = ricavi × giorni/365; assorbimento netto = crediti − debiti fornitori "
                    "(60gg); CCC = DSO + giorni magazzino − DPO"),
    }


def financing_options(lev_post: Optional[float], dscr: Optional[float],
                      wc: dict, giorni: float) -> dict:
    """Financing Optimizer: opzioni REALISTICHE per finanziare CAPEX + circolante. NON
    'ridurre i pagamenti a 60gg' (impossibile con una multinazionale): factoring, reverse
    factoring, supply chain finance, leasing, equity — selezionate dalla situazione."""
    opzioni = []
    # circolante a pagamenti lunghi → strumenti sul credito commerciale
    if giorni and giorni >= 90:
        opzioni.append({"strumento": "Factoring pro-soluto sui crediti del cliente",
                        "quando": f"incassi a {giorni:g}gg: smobilizza i crediti e trasferisce il rischio, "
                                  "libera cassa senza toccare la leva bancaria"})
        opzioni.append({"strumento": "Supply chain finance / reverse factoring",
                        "quando": "se il cliente (multinazionale) ha un programma SCF: anticipo a costo "
                                  "basso sul suo rating, senza chiedere sconti sui termini"})
        opzioni.append({"strumento": "Confirming / anticipo su contratto",
                        "quando": "anticipo bancario garantito dai minimi contrattuali della commessa"})
    # CAPEX su asset industriali → leasing invece di debito bancario
    opzioni.append({"strumento": "Leasing/finanziamento asset per il CAPEX",
                    "quando": "sposta l'investimento fuori dalla PFN bancaria e allinea il costo "
                              "alla vita utile dell'impianto"})
    # leva alta → serve equity/quasi-equity
    if lev_post is not None and lev_post > _COVENANT_PFN_EBITDA:
        opzioni.append({"strumento": "Quota equity / finanziamento soci / mezzanino",
                        "quando": f"leva post {lev_post:.1f}x oltre il covenant {_COVENANT_PFN_EBITDA:g}x: "
                                  "una quota a equity riporta la leva sotto soglia"})
    return {"opzioni": opzioni,
            "nota": "Alternative alla riduzione dei termini di pagamento (spesso non negoziabile con "
                    "una multinazionale): finanziare il circolante, non combatterlo."}


def _decision_board(npv, irr, wacc, debt: dict, wc: dict, ricavi_noti: bool) -> dict:
    """DECISION BOARD: verdetto 🟢/🟡/🔴 con CRITERI QUANTITATIVI derivati dai dati (soglie
    covenant reali, non inventate). GO SOLO SE elenca le condizioni oggettive da soddisfare."""
    lev_post = debt.get("pfn_ebitda_post")
    dscr = debt.get("dscr_post")
    int_cov = debt.get("interest_coverage_post")
    criteri = []
    def check(nome, ok, dettaglio):
        criteri.append({"criterio": nome, "soddisfatto": bool(ok), "dettaglio": dettaglio})
    check(f"Leva post ≤ {_COVENANT_PFN_EBITDA:g}x", debt.get("entro_covenant_leva"),
          f"PFN/EBITDA post = {lev_post}x")
    check(f"DSCR ≥ {_COVENANT_DSCR:g}x", debt.get("entro_covenant_dscr"),
          f"DSCR post = {dscr}x")
    check(f"Interest coverage ≥ {_COVENANT_INT_COV:g}x",
          (int_cov is not None and int_cov >= _COVENANT_INT_COV), f"EBIT/interessi = {int_cov}x")
    if ricavi_noti and npv is not None:
        check("NPV > 0 al WACC", npv > 0, f"NPV = €{npv:,.0f}".replace(",", "."))
        check(f"IRR > WACC ({wacc:g}%)", (irr is not None and irr > wacc), f"IRR = {irr}%")
    n_ok = sum(1 for c in criteri if c["soddisfatto"])
    n_tot = len(criteri)
    non_soddisfatti = [c for c in criteri if not c["soddisfatto"]]
    # NO GO solo per problemi FONDAMENTALI (non finanziabili con una struttura diversa):
    #   • rendimento negativo (quando i ricavi sono noti), oppure
    #   • non si pagano nemmeno gli interessi (int.cov < 1,5), oppure
    #   • leva così alta (>5x) che nemmeno una quota equity ragionevole la riporta sotto.
    # Leva/DSCR sopra soglia con CAPEX 100% a debito sono STRUTTURABILI (equity/leasing/
    # factoring) → GO CON CONDIZIONI, non NO GO. È la differenza tra "non farlo" e "falla bene".
    npv_neg = ricavi_noti and npv is not None and npv <= 0
    non_paga_interessi = int_cov is not None and int_cov < 1.5
    leva_insanabile = lev_post is not None and lev_post > 5.0
    if npv_neg or non_paga_interessi or leva_insanabile:
        verdetto, semaforo = "NO GO", "🔴"
        causa = ("rendimento negativo" if npv_neg else
                 f"interest coverage {int_cov}x < 1,5 (non copre gli interessi)" if non_paga_interessi else
                 f"leva post {lev_post}x oltre 5x (non sanabile con equity ragionevole)")
        motivo = f"vincolo fondamentale violato: {causa}."
    elif n_ok == n_tot:
        verdetto, semaforo = "GO", "🟢"
        motivo = "tutti i criteri di sostenibilità e rendimento sono rispettati."
    else:
        verdetto, semaforo = "GO CON CONDIZIONI", "🟡"
        motivo = ("procedibile SE si soddisfano queste condizioni oggettive: "
                  + "; ".join(f"{c['criterio']} (ora {c['dettaglio']})" for c in non_soddisfatti)
                  + ". Leve: quota equity/leasing per la leva, allungamento piano o anticipo "
                    "contrattuale per il DSCR.")
    return {"verdetto": verdetto, "semaforo": semaforo, "motivo": motivo,
            "criteri": criteri, "criteri_soddisfatti": f"{n_ok}/{n_tot}",
            "condizioni_go": [c["criterio"] for c in non_soddisfatti] if semaforo == "🟡" else []}


def build_investment(capex: float, ricavi_incr_anno1: Optional[float],
                     ricavi_incr_regime: Optional[float], margine_ebitda_pct: float,
                     financials: dict, params: Optional[dict] = None) -> Optional[dict]:
    """Analisi di un investimento. Gira sul solo CAPEX (sostenibilità del debito: leva, DSCR,
    interest coverage, circolante, financing, decision board). Se ci sono anche i RICAVI
    incrementali del progetto → aggiunge NPV/IRR/payback/scenari. financials = {ebitda, ebit,
    pfn, debiti_finanziari, liquidita, patrimonio_netto, fatturato}."""
    if not capex or capex <= 0:
        return None
    p = params or {}
    orizzonte = int(_num(p.get("orizzonte_anni")) or _num(p.get("durata_anni")) or _ORIZZONTE_DEFAULT)
    wacc = _num(p.get("wacc_pct")) or _WACC_DEFAULT
    giorni = _num(p.get("giorni_incasso")) or 0.0
    quota_debito = _num(p.get("quota_debito_pct"))
    assunzioni: list[str] = []

    r1 = _num(ricavi_incr_anno1)
    reg = _num(ricavi_incr_regime) or r1
    if r1 is None:
        r1 = reg
    ricavi_noti = r1 is not None and reg is not None
    ebitda_incr_regime = (reg * margine_ebitda_pct / 100.0) if ricavi_noti else 0.0

    # --- moduli SEMPRE calcolabili dal bilancio + CAPEX (indip. dai ricavi incrementali) ---
    debt = debt_engine(capex, financials, p, ebitda_incr_regime)
    wc = working_capital_engine(financials, p, reg or 0.0)
    fin_opts = financing_options(debt.get("pfn_ebitda_post"), debt.get("dscr_post"), wc, giorni)
    # break-even dell'investimento: ricavi incrementali annui che coprono il servizio del
    # SOLO NUOVO debito (il preesistente è già servito dall'EBITDA attuale) — sempre
    # calcolabile, risponde a "quanto devo vendere perché l'investimento si paghi da solo".
    serv = debt.get("servizio_nuovo_debito_annuo_eur")
    if serv and margine_ebitda_pct > 0:
        debt["break_even_ricavi_incrementali_eur"] = _r2(serv / (margine_ebitda_pct / 100.0 * (1 - _TAX)))
        debt.setdefault("formula", "")
        debt["formula"] += ("; break-even ricavi incrementali = servizio del NUOVO debito / "
                            "(margine EBITDA × (1−aliquota))")

    if not ricavi_noti:
        # SOSTENIBILITÀ senza rendimento (caso CoolTech): NPV/IRR non calcolabili, ma NON
        # inventati né lasciati come N/D muti — nota esplicita del perché.
        board = _decision_board(None, None, wacc, debt, wc, ricavi_noti=False)
        return {
            "decisione_investimento": {"verdetto": board["verdetto"], "motivo": board["motivo"]},
            "decision_board": board,
            "debt_capacity": debt,
            "working_capital": wc,
            "financing_options": fin_opts,
            "investment_summary": {
                "capex_eur": _r2(capex),
                "npv_eur": None, "irr_pct": None, "payback_anni": None,
                "nota": "NPV/IRR/payback NON calcolati: i ricavi incrementali attesi dalla commessa "
                        "non sono stati forniti. Fornire ricavi anno-1 e a regime per il rendimento. "
                        "L'analisi di SOSTENIBILITÀ del debito è invece completa qui sopra.",
            },
            "kpi_non_calcolabili": [
                {"kpi": "NPV", "motivo": "servono i ricavi incrementali attesi della commessa (anno 1 e a regime)"},
                {"kpi": "IRR", "motivo": "come NPV: senza flussi di ricavo non esiste un tasso interno"},
                {"kpi": "Payback", "motivo": "senza flussi incrementali non c'è un anno di recupero del CAPEX"},
            ],
            "metodo_investimento": ("Analisi di sostenibilità del debito (leva/DSCR/interest coverage/"
                                    "circolante) sul CAPEX dichiarato; il rendimento (NPV/IRR) richiede "
                                    "i ricavi del progetto."),
        }

    if _num(p.get("wacc_pct")) is None:
        assunzioni.append(f"WACC assunto {wacc:g}% (non dichiarato)")
    assunzioni.append(f"EBITDA incrementale = ricavi incrementali × {margine_ebitda_pct:g}% "
                      "(margine del business esistente; da validare per il nuovo contratto)")
    if giorni:
        assunzioni.append(f"capitale circolante = ricavi × {giorni:g}gg/365 (assorbimento nell'anno di ramp)")

    fcf_annui, ricavi_series, tv = _fcf_series(r1, reg, margine_ebitda_pct, orizzonte, giorni, wacc)
    # Il TERMINAL VALUE (perpetuità del FCF a regime) rappresenta la vita dell'asset OLTRE
    # l'orizzonte: senza, un CAPEX industriale che rende in perpetuità sembra distruggere
    # valore per il solo troncamento a N anni. g=1% prudente. Sommato all'ultimo anno.
    flows = [-capex] + list(fcf_annui)
    flows[-1] += tv
    assunzioni.append(f"terminal value = FCF a regime / (WACC − 1%) al termine dell'orizzonte "
                      f"(€{tv:,.0f}), per la vita dell'asset oltre i {orizzonte} anni".replace(",", "."))

    npv = _npv(wacc, flows)
    irr = _irr(flows)
    payback = _payback(capex, fcf_annui)  # payback sul FCF operativo (senza TV): prudente
    roi = (sum(fcf_annui) + tv) / capex * 100.0 if capex else None

    lev_post = debt.get("pfn_ebitda_post")
    sens = _sensitivity(r1, reg, margine_ebitda_pct, orizzonte, giorni, wacc, capex)
    scenari = _scenari_investimento(r1, reg, margine_ebitda_pct, orizzonte, giorni, wacc, capex)
    board = _decision_board(npv, irr, wacc, debt, wc, ricavi_noti=True)
    return {
        "decisione_investimento": {"verdetto": board["verdetto"], "motivo": board["motivo"]},
        "decision_board": board,
        "investment_summary": {
            "capex_eur": _r2(capex), "npv_eur": _r2(npv), "irr_pct": irr, "wacc_pct": _r2(wacc),
            "payback_anni": payback, "roi_semplice_pct": _r2(roi),
            "orizzonte_anni": orizzonte,
            "fcf_per_anno_eur": [_r2(x) for x in fcf_annui],
            "ricavi_incrementali_per_anno_eur": [_r2(x) for x in ricavi_series],
            "terminal_value_eur": _r2(tv),
            "formula": ("NPV = Σ FCF/(1+WACC)^t + TV/(1+WACC)^N − CAPEX; FCF = EBITDA incr.×"
                        "(1−aliquota) − ΔWC; IRR = tasso che annulla l'NPV; payback = anno di "
                        "recupero del CAPEX sul FCF operativo"),
            "assunzioni": assunzioni,
        },
        "scenari_investimento": scenari,
        "sensitivita_npv": sens,
        "debt_capacity": debt,
        "working_capital": wc,
        "financing_options": fin_opts,
        "metodo_investimento": ("Investment decision support: NPV/IRR/payback sul flusso incrementale, "
                                "sostenibilità del debito (leva/DSCR/interest coverage), circolante, "
                                "financing e decision board. Numeri derivati dai dati del cliente."),
    }


def _scenari_investimento(r1, reg, margine, orizzonte, giorni, wacc, capex) -> dict:
    """Scenari prudente/base/aggressivo su ricavi incrementali (−30%/base/+20%): NPV/IRR."""
    def one(fatt):
        fcf, _, tv = _fcf_series(r1 * fatt, reg * fatt, margine, orizzonte, giorni, wacc)
        fl = [-capex] + list(fcf)
        fl[-1] += tv
        return {"npv_eur": round(_npv(wacc, fl), 2), "irr_pct": _irr(fl)}
    return {
        "prudente": {**one(0.70), "assunzione": "ricavi incrementali −30%"},
        "base": {**one(1.0), "assunzione": "ricavi come stimati"},
        "aggressivo": {**one(1.20), "assunzione": "ricavi incrementali +20%"},
    }


_STRESS_QUOTE = (15.0, 25.0, 35.0, 45.0)


def stress_investment(ricavi_incr_regime: float, margine_ebitda_pct: float,
                      fatturato: float, ebitda_now: float, giorni_incasso: float = 0.0) -> dict:
    """Stress test dell'investimento: perdita cliente / riduzione volumi / ritardo pagamenti.
    Impatto su EBITDA e concentrazione."""
    ebitda_incr = ricavi_incr_regime * margine_ebitda_pct / 100.0
    tot_post = fatturato + ricavi_incr_regime if fatturato else None
    quota = ricavi_incr_regime / tot_post * 100.0 if tot_post else None
    scenari = [
        {"scenario": "perdita del cliente", "impatto_ebitda_eur": -round(ebitda_incr, 2),
         "nota": "l'intero EBITDA incrementale salta; il CAPEX resta da ammortizzare"},
        {"scenario": "-30% volumi", "impatto_ebitda_eur": -round(ebitda_incr * 0.30, 2),
         "nota": "ricavi incrementali sotto le attese"},
        {"scenario": "-50% volumi", "impatto_ebitda_eur": -round(ebitda_incr * 0.50, 2),
         "nota": "ordine dimezzato"},
    ]
    ritardo = None
    if giorni_incasso:
        wc_extra = ricavi_incr_regime * (30 / 365.0)  # +30gg di ritardo
        ritardo = {"scenario": "+30gg ritardo pagamenti",
                   "capitale_circolante_aggiuntivo_eur": round(wc_extra, 2),
                   "nota": "assorbimento di cassa aggiuntivo, nessun impatto su EBITDA ma su liquidità"}
    return {
        "concentrazione_cliente_pct": round(quota, 2) if quota is not None else None,
        "scenari": scenari,
        "ritardo_pagamenti": ritardo,
        "lettura": ("La perdita del nuovo cliente è il rischio dominante: dimensiona il CAPEX e "
                    "i covenant su uno scenario prudente, non sul potenziale pieno."),
        "formula": "EBITDA incrementale = ricavi incrementali × margine EBITDA",
    }


def _collect_numbers(obj) -> list:
    out: list = []
    if isinstance(obj, dict):
        for v in obj.values():
            out.extend(_collect_numbers(v))
    elif isinstance(obj, list):
        for v in obj:
            out.extend(_collect_numbers(v))
    elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
        out.append(round(float(obj), 4))
        out.append(round(abs(float(obj)), 4))
    return out


def analysis_from_inputs(inputs: dict, reclass: Optional[dict]) -> Optional[dict]:
    """Core dell'analisi di investimento dagli input del form (usata sia dal binder sia
    dalla SSOT pre-generazione). None se il caso non descrive un investimento."""
    if not isinstance(inputs, dict):
        return None
    prog = inputs.get("investimento_progetto") if isinstance(inputs.get("investimento_progetto"), dict) else {}
    capex = _num(prog.get("capex") or inputs.get("investimento_eur") or inputs.get("capex")
                 or prog.get("investimento"))
    if not capex or capex <= 0:
        return None
    r1 = (prog.get("ricavi_incrementali_anno1") or inputs.get("ricavi_incrementali_anno1")
          or prog.get("contratto_iniziale_eur"))
    reg = (prog.get("ricavi_incrementali_regime") or inputs.get("ricavi_incrementali_potenziale")
           or prog.get("potenziale_eur"))
    rc = reclass or {}
    ce, idx, sp = rc.get("ce") or {}, rc.get("indici") or {}, rc.get("sp") or {}
    fatturato = _num(ce.get("ricavi"))
    ebitda = _num(ce.get("ebitda"))
    margine = _num(prog.get("margine_ebitda_pct") or inputs.get("margine_incrementale_pct"))
    if margine is None:
        margine = idx.get("ebitda_margin") or 14.0
    financials = {"ebitda": ebitda, "ebit": _num(ce.get("ebit")), "pfn": idx.get("pfn"),
                  "debiti_finanziari": sp.get("debiti_finanziari"),
                  "liquidita": sp.get("liquidita"), "patrimonio_netto": sp.get("patrimonio_netto"),
                  "fatturato": fatturato}
    params = {"wacc_pct": _num(prog.get("wacc_pct") or inputs.get("wacc_pct")),
              "giorni_incasso": _num(prog.get("giorni_incasso") or inputs.get("giorni_pagamento")),
              "orizzonte_anni": _num(prog.get("orizzonte_anni")),
              "durata_anni": _num(prog.get("durata_anni") or prog.get("durata_commessa_anni")
                                  or inputs.get("durata_commessa_anni")),
              "quota_debito_pct": _num(prog.get("quota_debito_pct")),
              "tasso_debito_pct": _num(prog.get("tasso_debito_pct") or inputs.get("tasso_debito_pct")),
              "costi_variabili_pct": _num(prog.get("costi_variabili_pct") or inputs.get("costi_variabili_pct"))}
    analisi = build_investment(capex, r1, reg, margine, financials, params)
    if not analisi:
        return None
    if fatturato and ebitda is not None and reg:
        analisi["stress_test_investimento"] = stress_investment(
            _num(reg) or 0.0, margine, fatturato, ebitda, params["giorni_incasso"] or 0.0)
    return analisi


def apply_investment(deliverable: dict, inputs: dict, reclass: Optional[dict],
                     facts: Optional[dict] = None) -> tuple[dict, Optional[dict]]:
    """Hook FinanceBoost: se gli input descrivono un investimento (`investimento_progetto`
    o `capex` + ricavi incrementali), inietta l'analisi di investimento. No-op altrimenti."""
    if not isinstance(deliverable, dict) or not isinstance(inputs, dict):
        return deliverable, None
    analisi = analysis_from_inputs(inputs, reclass)
    if not analisi:
        return deliverable, None
    out = dict(deliverable)
    for k, v in analisi.items():
        if v is not None:
            out[k] = v
    if isinstance(facts, dict):
        facts["_investment_grounded_numbers"] = {"numeri": _collect_numbers(analisi)}
    return out, {"investment_engine": True, "verdetto": analisi["decisione_investimento"]["verdetto"],
                 "npv_eur": analisi["investment_summary"]["npv_eur"]}


def financial_ssot(inputs: dict, reclass: Optional[dict]) -> Optional[dict]:
    """SINGLE SOURCE OF TRUTH finanziaria (audit CoolTech-2: 'debito totale €15M in una
    sezione, €8M in un'altra'). Blocco COMPATTO dei numeri ufficiali già calcolati, da
    iniettare nel prompt di generazione: la prosa deve USARE questi valori identici, mai
    ricalcolarli localmente. Gli stessi numeri vengono poi riscritti dai binder nelle
    sezioni strutturate (idempotente) e registrati come grounded al gate."""
    rc = reclass or {}
    ce, idx, sp = rc.get("ce") or {}, rc.get("indici") or {}, rc.get("sp") or {}
    ssot: dict = {}
    for label, v in (("ricavi_eur", ce.get("ricavi")), ("ebitda_eur", ce.get("ebitda")),
                     ("ebit_eur", ce.get("ebit")), ("utile_netto_eur", ce.get("utile_netto")),
                     ("liquidita_eur", sp.get("liquidita")),
                     ("debiti_finanziari_attuali_eur", sp.get("debiti_finanziari")),
                     ("pfn_attuale_eur", idx.get("pfn")),
                     ("patrimonio_netto_eur", sp.get("patrimonio_netto")),
                     ("ebitda_margin_pct", idx.get("ebitda_margin"))):
        if v is not None:
            ssot[label] = v
    analisi = analysis_from_inputs(inputs, reclass)
    if analisi:
        d = analisi.get("debt_capacity") or {}
        s = analisi.get("investment_summary") or {}
        w = analisi.get("working_capital") or {}
        for label, v in (("capex_eur", s.get("capex_eur")),
                         ("nuovo_debito_eur", (d.get("debiti_finanziari_post_eur") or 0)
                          - (ssot.get("debiti_finanziari_attuali_eur") or 0)
                          if d.get("debiti_finanziari_post_eur") is not None else None),
                         ("debito_totale_post_investimento_eur", d.get("debiti_finanziari_post_eur")),
                         ("pfn_post_investimento_eur", d.get("pfn_post_eur")),
                         ("leva_pfn_ebitda_attuale", d.get("pfn_ebitda_attuale")),
                         ("leva_pfn_ebitda_post", d.get("pfn_ebitda_post")),
                         ("dscr_post", d.get("dscr_post")),
                         ("interest_coverage_post", d.get("interest_coverage_post")),
                         ("interessi_annui_post_eur", d.get("interessi_annui_post_eur")),
                         ("npv_eur", s.get("npv_eur")), ("irr_pct", s.get("irr_pct")),
                         ("payback_anni", s.get("payback_anni")),
                         ("circolante_assorbito_eur", w.get("assorbimento_cassa_netto_eur")),
                         ("verdetto", (analisi.get("decision_board") or {}).get("verdetto"))):
            if v is not None:
                ssot[label] = v
    return ssot or None
