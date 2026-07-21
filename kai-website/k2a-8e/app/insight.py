"""Insight Engine — ogni dato fornito diventa analisi, non citazione (spec §4-§5).

Causa radice del comportamento "da manuale": il guard anti-allucinazione vieta
(giustamente) i numeri non forniti, ma senza un motore di calcolo deterministico
nessun numero DERIVATO può comparire → i dati vengono citati e mai analizzati.

Questo motore calcola, dai soli input forniti, KPI e insight con:
- valore + formula riproducibile + dati usati (provenienza);
- tipo (insight | rischio | opportunita) e gravità;
- spiegazione in linguaggio da consulente (il PERCHÉ conta);
- confidence A (calcolo su dati dichiarati).

Traccia inoltre la COVERAGE: quali input sono stati usati da almeno un'analisi e
quali no ("nessun dato importante deve rimanere inutilizzato").

Deterministico, nessun LLM. Tollerante sugli alias dei nomi campo (il K-BOT e i
form usano nomi diversi per lo stesso dato).
"""

from __future__ import annotations

from typing import Any, Optional

from . import normalize as NORM

# Alias → campo canonico (tolleranza sui nomi che arrivano da form/conversazione).
_ALIASES: dict[str, tuple[str, ...]] = {
    "incassi_mese": ("incassi_mese", "incassi_medi_mese", "entrate_mese", "incassi"),
    "uscite_mese": ("uscite_mese", "uscite_medie_mese", "uscite", "pagamenti_mese"),
    "scoperto": ("scoperto", "scoperto_bancario", "fido_utilizzato", "esposizione_banca"),
    "interessi_annui": ("interessi_annui", "interessi_passivi", "oneri_finanziari",
                        "interessi"),
    "fatturato_annuo": ("fatturato_annuo", "fatturato", "ricavi_annui", "ricavi"),
    "dipendenti": ("dipendenti", "organico", "addetti", "numero_dipendenti"),
    "concentrazione_top1": ("concentrazione_top1", "top_cliente_pct", "quota_top_cliente",
                            "top1_pct"),
    "concentrazione_top3": ("concentrazione_top3", "top3_pct", "quota_top3"),
    "dso": ("dso", "dso_giorni", "giorni_incasso", "tempi_incasso_giorni"),
    "dpo": ("dpo", "dpo_giorni", "giorni_pagamento"),
    "crediti_clienti": ("crediti_clienti", "crediti", "crediti_commerciali"),
    "costi_operativi": ("costi_operativi", "costi_mese", "costi"),
    # operations (cruscotto/ControlBoost)
    "progetti_in_corso": ("progetti_in_corso", "commesse_attive", "commesse_in_corso"),
    "progetti_in_ritardo": ("progetti_in_ritardo", "commesse_in_ritardo"),
    "ore_lavorate": ("ore_lavorate",),
    "ore_fatturabili": ("ore_fatturabili",),
    "clienti_attivi": ("clienti_attivi",),
    "clienti_persi": ("clienti_persi",),
    "clienti_nuovi": ("clienti_nuovi", "nuovi_clienti"),
    "scarti_resi_reclami": ("scarti_resi_reclami", "reclami", "non_conformita"),
    "concentrazione_top5": ("concentrazione_top5", "concentrazione_top5_pct"),
    # marketing / canali
    "dipendenza_canale": ("ota_dependency_pct", "dipendenza_canale_pct",
                          "quota_canale_principale"),
    "budget_marketing": ("budget_mensile_eur", "budget_marketing", "budget_marketing_mese"),
    # strategia / crescita
    "margine_canale_diretto": ("margine_ecommerce_pct", "margine_diretto_pct"),
    "margine_distributore": ("margine_distributore_pct",),
    "budget_espansione": ("budget_espansione_eur",),
    "mol_pct": ("mol_medio_pct", "ebitda_pct", "mol_pct"),
    # M&A / acquisizione (dati del TARGET)
    "ebitda": ("ebitda", "ebitda_target", "ebitda_eur"),
    "utile_netto": ("utile_netto", "utile_netto_target", "risultato_netto"),
    "patrimonio_netto": ("patrimonio_netto", "pn", "equity_target"),
    "prezzo_richiesto": ("prezzo_richiesto", "prezzo", "prezzo_acquisto",
                         "asking_price", "valore_richiesto"),
    "debiti_finanziari": ("debiti_finanziari", "debiti_fin", "pfl", "debito_finanziario"),
    "liquidita": ("liquidita", "liquidità", "cassa", "disponibilita_liquide"),
}

# Alias per uscite: anche 'pagamenti' (cruscotto) e organico da 'dimensione_organico'.
_ALIASES["uscite_mese"] = _ALIASES["uscite_mese"] + ("pagamenti",)
_ALIASES["dipendenti"] = _ALIASES["dipendenti"] + ("dimensione_organico", "n_dipendenti")

# Boolean di compliance (LegalBoost): letti così come sono, non numerici.
LEGAL_FLAGS = ("tratta_dati_personali", "ha_contratti_standard", "ha_modello_231",
               "ha_marchio", "usa_ai_profilazione", "opera_estero", "ha_sito_ecommerce")

# Campi che, se forniti, DEVONO essere usati da almeno un'analisi.
IMPORTANT_FIELDS = tuple(_ALIASES.keys())


def _num(v: Any) -> Optional[float]:
    v = NORM.unwrap_value(v)
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        t = v.strip().replace("€", "").replace("%", "").replace(" ", "")
        if not t:
            return None
        if "," in t:
            t = t.replace(".", "").replace(",", ".")
        else:
            t = t.replace(".", "") if t.count(".") > 1 or (
                "." in t and len(t.split(".")[-1]) == 3) else t
        try:
            return float(t)
        except ValueError:
            return None
    return None


class Facts:
    """Vista canonica sugli input: risolve gli alias e ricorda cosa è stato usato."""

    def __init__(self, inputs: dict) -> None:
        self._inputs = inputs or {}
        self.resolved: dict[str, float] = {}
        self.source_key: dict[str, str] = {}
        self.used: set[str] = set()
        for canon, aliases in _ALIASES.items():
            for a in aliases:
                if a in self._inputs:
                    n = _num(self._inputs[a])
                    if n is not None:
                        self.resolved[canon] = n
                        self.source_key[canon] = a
                        break

    def get(self, canon: str) -> Optional[float]:
        if canon in self.resolved:
            self.used.add(canon)
            return self.resolved[canon]
        return None

    def has(self, *canons: str) -> bool:
        return all(c in self.resolved for c in canons)

    def provided(self) -> set[str]:
        return set(self.resolved)

    def unused(self) -> list[str]:
        return sorted(self.provided() - self.used)


def _ins(id_, titolo, valore, unita, formula, dati, spiegazione,
         tipo="insight", gravita=None) -> dict:
    return {"id": id_, "titolo": titolo, "valore": valore, "unita": unita,
            "formula": formula, "dati_usati": list(dati), "spiegazione": spiegazione,
            "tipo": tipo, "gravita": gravita, "confidence": "A",
            "source": "system_calculated"}


def derive_finance_insights(inputs: dict) -> tuple[list[dict], Facts]:
    """Deriva insight quantitativi di tesoreria/liquidità dai dati disponibili.
    Ogni insight nasce SOLO da campi forniti; niente dati → niente insight."""
    f = Facts(inputs)
    out: list[dict] = []

    # 1) Saldo mensile di cassa (es. 145.000 − 158.000 = −13.000 €/mese).
    if f.has("incassi_mese", "uscite_mese"):
        inc, usc = f.get("incassi_mese"), f.get("uscite_mese")
        saldo = round(inc - usc, 2)
        out.append(_ins(
            "cash.saldo_mensile", "Saldo mensile di cassa", saldo, "€/mese",
            f"incassi_mese − uscite_mese = {inc:,.0f} − {usc:,.0f}",
            ("incassi_mese", "uscite_mese"),
            ("L'azienda brucia cassa ogni mese: il deficit strutturale, non un picco, "
             "è ciò che alimenta lo scoperto." if saldo < 0 else
             "La gestione corrente genera cassa: il problema di liquidità, se c'è, "
             "viene dai tempi di incasso, non dai volumi."),
            tipo="rischio" if saldo < 0 else "insight",
            gravita="alta" if saldo < 0 else None))
        if saldo < 0:
            out.append(_ins(
                "cash.deficit_annuo", "Deficit di cassa proiettato su 12 mesi",
                round(saldo * 12, 2), "€/anno",
                f"saldo_mensile × 12 = {saldo:,.0f} × 12",
                ("incassi_mese", "uscite_mese"),
                "A parità di condizioni, in un anno il buco raddoppia l'esposizione "
                "attuale: il tempo lavora contro.", tipo="rischio", gravita="alta"))

    # 2) Costo effettivo dello scoperto (es. 18.000 / 95.000 ≈ 19%).
    if f.has("scoperto", "interessi_annui"):
        sc, itr = f.get("scoperto"), f.get("interessi_annui")
        if sc > 0:
            costo_pct = round(itr / sc * 100, 1)
            out.append(_ins(
                "debt.costo_scoperto", "Costo effettivo dello scoperto",
                costo_pct, "%/anno",
                f"interessi_annui / scoperto = {itr:,.0f} / {sc:,.0f}",
                ("scoperto", "interessi_annui"),
                f"Ogni euro di scoperto costa ~{costo_pct:.0f} centesimi l'anno: è tra le "
                "forme di finanziamento più care disponibili — finanziare il circolante "
                "così erode il margine.", tipo="rischio",
                gravita="alta" if costo_pct >= 10 else "media"))

    # 3) Peso degli interessi sul risultato (se noto il fatturato).
    if f.has("interessi_annui", "fatturato_annuo"):
        itr, fat = f.get("interessi_annui"), f.get("fatturato_annuo")
        if fat > 0:
            peso = round(itr / fat * 100, 2)
            out.append(_ins(
                "debt.peso_interessi", "Interessi passivi sul fatturato", peso, "%",
                f"interessi_annui / fatturato_annuo = {itr:,.0f} / {fat:,.0f}",
                ("interessi_annui", "fatturato_annuo"),
                "È margine che esce dall'azienda prima ancora di pagare fornitori e "
                "persone: ogni punto qui è capacità di investimento persa."))

    # 4) Capitale immobilizzato nei crediti per effetto del DSO.
    if f.has("dso", "fatturato_annuo"):
        dso, fat = f.get("dso"), f.get("fatturato_annuo")
        capitale = round(fat / 365 * dso, 0)
        out.append(_ins(
            "wc.capitale_in_crediti", "Capitale immobilizzato nei crediti",
            capitale, "€",
            f"fatturato_annuo / 365 × DSO = {fat:,.0f} / 365 × {dso:.0f}",
            ("dso", "fatturato_annuo"),
            f"Con incassi a ~{dso:.0f} giorni l'azienda presta ai clienti "
            f"~{capitale:,.0f} € in permanenza — più dello scoperto che paga alla "
            "banca: il finanziamento del circolante è il nodo, non il fido.",
            tipo="rischio", gravita="alta" if dso >= 60 else "media"))

    # 5) Rischio di concentrazione clienti.
    top1, top3 = f.get("concentrazione_top1"), f.get("concentrazione_top3")
    conc = top3 if top3 is not None else top1
    if conc is not None:
        campo = "concentrazione_top3" if top3 is not None else "concentrazione_top1"
        out.append(_ins(
            "risk.concentrazione", "Indice di concentrazione clienti", conc, "%",
            f"quota fatturato dei clienti principali = {conc:.0f}%",
            (campo,),
            f"Con il {conc:.0f}% del fatturato su pochi clienti, il ritardo di UN "
            "pagamento sposta la cassa dell'intero mese: la concentrazione trasforma "
            "un problema commerciale in un problema di tesoreria.",
            tipo="rischio", gravita="alta" if conc >= 50 else "media"))

    # 6) Fatturato per addetto (produttività, se forniti entrambi).
    if f.has("fatturato_annuo", "dipendenti"):
        fat, dip = f.get("fatturato_annuo"), f.get("dipendenti")
        if dip > 0:
            out.append(_ins(
                "org.fatturato_addetto", "Fatturato per addetto",
                round(fat / dip, 0), "€/addetto",
                f"fatturato_annuo / dipendenti = {fat:,.0f} / {dip:.0f}",
                ("fatturato_annuo", "dipendenti"),
                "Base per dimensionare qualunque piano: dice quanta struttura regge "
                "il fatturato attuale."))

    # 7) Margine di manovra: quanti mesi di deficit copre il fido residuo (se noti).
    if f.has("incassi_mese", "uscite_mese", "scoperto"):
        saldo = f.get("incassi_mese") - f.get("uscite_mese")
        if saldo < 0:
            sc = f.get("scoperto")
            out.append(_ins(
                "cash.autonomia", "Velocità di assorbimento dello scoperto",
                round(abs(sc / saldo), 1), "mesi equivalenti",
                f"scoperto / |saldo_mensile| = {sc:,.0f} / {abs(saldo):,.0f}",
                ("scoperto", "incassi_mese", "uscite_mese"),
                "Lo scoperto attuale equivale a questo numero di mesi di deficit: "
                "misura quanto a lungo la banca ha già finanziato il problema.",
                tipo="insight"))

    return out, f


def coverage_report(facts: Facts) -> dict:
    """Copertura d'uso dei dati: cosa è stato analizzato e cosa no (spec §4)."""
    provided = sorted(facts.provided())
    unused = facts.unused()
    return {
        "dati_forniti": provided,
        "dati_analizzati": sorted(facts.used),
        "dati_non_sfruttati": unused,
        "copertura_pct": round(len(facts.used) / len(provided) * 100, 0) if provided else 100.0,
    }


# ── Operations / commesse ─────────────────────────────────────────────────────
def derive_ops_insights(inputs: dict) -> tuple[list[dict], Facts]:
    f = Facts(inputs)
    out: list[dict] = []

    if f.has("progetti_in_corso", "progetti_in_ritardo"):
        tot, rit = f.get("progetti_in_corso"), f.get("progetti_in_ritardo")
        if tot > 0:
            pct = round(rit / tot * 100, 1)
            out.append(_ins(
                "ops.pct_ritardo", "Commesse in ritardo", pct, "%",
                f"in_ritardo / in_corso = {rit:.0f} / {tot:.0f}",
                ("progetti_in_corso", "progetti_in_ritardo"),
                "Ogni commessa in ritardo occupa capacità che non fattura e rimanda "
                "l'incasso: il ritardo operativo diventa problema di cassa.",
                tipo="rischio", gravita="alta" if pct >= 20 else "media"))

    if f.has("ore_lavorate", "ore_fatturabili"):
        lav, fat = f.get("ore_lavorate"), f.get("ore_fatturabili")
        if lav > 0:
            util = round(fat / lav * 100, 1)
            out.append(_ins(
                "ops.utilizzo", "Utilizzo fatturabile della capacità", util, "%",
                f"ore_fatturabili / ore_lavorate = {fat:.0f} / {lav:.0f}",
                ("ore_lavorate", "ore_fatturabili"),
                f"Il {100 - util:.0f}% delle ore lavorate non produce fatturato: lì "
                "dentro ci sono riunioni, rilavorazioni e gestione dei blocchi — è il "
                "costo nascosto della disorganizzazione.",
                tipo="rischio" if util < 70 else "insight",
                gravita="alta" if util < 60 else ("media" if util < 70 else None)))

    if f.has("clienti_attivi", "clienti_persi"):
        att, persi = f.get("clienti_attivi"), f.get("clienti_persi")
        if att > 0:
            churn = round(persi / att * 100, 1)
            out.append(_ins(
                "ops.churn", "Clienti persi sul parco attivo", churn, "%",
                f"clienti_persi / clienti_attivi = {persi:.0f} / {att:.0f}",
                ("clienti_attivi", "clienti_persi"),
                "Sostituire un cliente costa più che tenerlo: il churn è il moltiplicatore "
                "silenzioso dello sforzo commerciale.",
                tipo="rischio" if churn >= 5 else "insight",
                gravita="media" if churn >= 5 else None))

    conc5 = f.get("concentrazione_top5")
    if conc5 is not None:
        out.append(_ins(
            "risk.concentrazione", "Concentrazione sui primi clienti", conc5, "%",
            f"quota fatturato top 5 = {conc5:.0f}%", ("concentrazione_top5",),
            "Pochi clienti muovono la maggioranza del lavoro: le loro priorità "
            "diventano le tue, anche quando non conviene.",
            tipo="rischio", gravita="alta" if conc5 >= 60 else "media"))

    return out, f


# ── Marketing / canali ────────────────────────────────────────────────────────
def derive_marketing_insights(inputs: dict) -> tuple[list[dict], Facts]:
    f = Facts(inputs)
    out: list[dict] = []

    dep = f.get("dipendenza_canale")
    if dep is not None:
        out.append(_ins(
            "mkt.dipendenza_canale", "Dipendenza dal canale principale", dep, "%",
            f"quota prenotazioni/lead dal canale principale = {dep:.0f}%",
            ("dipendenza_canale",),
            "Il canale principale detta commissioni, visibilità e regole: sopra il 50% "
            "non è un canale, è un padrone. Ogni suo cambio di algoritmo o tariffa "
            "entra dritto nel margine.",
            tipo="rischio", gravita="alta" if dep >= 60 else "media"))

    if f.has("budget_marketing", "fatturato_annuo"):
        b, fat = f.get("budget_marketing"), f.get("fatturato_annuo")
        if fat > 0:
            pct = round(b * 12 / fat * 100, 1)
            out.append(_ins(
                "mkt.peso_budget", "Investimento marketing sul fatturato", pct, "%",
                f"budget_mensile × 12 / fatturato = {b:,.0f} × 12 / {fat:,.0f}",
                ("budget_marketing", "fatturato_annuo"),
                "Misura se il canale diretto ha davvero le risorse per crescere o se "
                "l'indipendenza dal canale dominante è solo un auspicio."))

    if f.has("clienti_attivi", "clienti_nuovi"):
        att, nuovi = f.get("clienti_attivi"), f.get("clienti_nuovi")
        if att > 0:
            out.append(_ins(
                "mkt.tasso_acquisizione", "Nuovi clienti sul parco attivo",
                round(nuovi / att * 100, 1), "%",
                f"clienti_nuovi / clienti_attivi = {nuovi:.0f} / {att:.0f}",
                ("clienti_attivi", "clienti_nuovi"),
                "Il ritmo di acquisizione dice quanta strada può fare la "
                "diversificazione dei canali con le forze attuali."))

    return out, f


# ── HR / organizzazione ───────────────────────────────────────────────────────
def derive_hr_insights(inputs: dict) -> tuple[list[dict], Facts]:
    f = Facts(inputs)
    out: list[dict] = []

    if f.has("fatturato_annuo", "dipendenti"):
        fat, dip = f.get("fatturato_annuo"), f.get("dipendenti")
        if dip > 0:
            out.append(_ins(
                "org.fatturato_addetto", "Fatturato per addetto",
                round(fat / dip, 0), "€/addetto",
                f"fatturato / dipendenti = {fat:,.0f} / {dip:.0f}",
                ("fatturato_annuo", "dipendenti"),
                "La produttività per persona è il tetto della crescita a organico "
                "invariato: sotto la media di settore si cresce solo assumendo, sopra "
                "c'è spazio organizzativo."))

    if f.has("costi_operativi", "dipendenti"):
        c, dip = f.get("costi_operativi"), f.get("dipendenti")
        if dip > 0:
            out.append(_ins(
                "org.costo_struttura_addetto", "Costo di struttura per addetto",
                round(c / dip, 0), "€/addetto",
                f"costi_operativi / dipendenti = {c:,.0f} / {dip:.0f}",
                ("costi_operativi", "dipendenti"),
                "Insieme al fatturato per addetto definisce il margine di manovra per "
                "assunzioni e aumenti: si decide sui numeri, non sulle sensazioni."))

    if f.has("ore_lavorate", "dipendenti"):
        lav, dip = f.get("ore_lavorate"), f.get("dipendenti")
        if dip > 0:
            out.append(_ins(
                "org.carico_medio", "Ore lavorate medie per addetto (periodo)",
                round(lav / dip, 0), "ore",
                f"ore_lavorate / dipendenti = {lav:.0f} / {dip:.0f}",
                ("ore_lavorate", "dipendenti"),
                "Il carico medio rende visibile la saturazione PRIMA che diventi "
                "turnover: chi è saturo non si lamenta, se ne va."))

    return out, f


# ── Legale / compliance (gap analysis sui flag dichiarati) ────────────────────
def derive_legal_insights(inputs: dict) -> tuple[list[dict], Facts]:
    f = Facts(inputs)
    out: list[dict] = []

    def flag(name: str):
        v = NORM.unwrap_value((inputs or {}).get(name))
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            lv = v.strip().lower()
            if lv in ("si", "sì", "true", "yes", "1"):
                return True
            if lv in ("no", "false", "0"):
                return False
        return None

    tratta_dati = flag("tratta_dati_personali")
    contratti = flag("ha_contratti_standard")
    ecommerce = flag("ha_sito_ecommerce")
    ai_prof = flag("usa_ai_profilazione")
    estero = flag("opera_estero")
    marchio = flag("ha_marchio")
    modello231 = flag("ha_modello_231")

    def gap(id_, titolo, presente, spiegazione, gravita="media"):
        if presente is False:
            out.append(_ins(id_, titolo, "assente", "",
                            f"dichiarato dal cliente: {titolo.lower()} = no",
                            (id_.split(".")[-1],), spiegazione,
                            tipo="rischio", gravita=gravita))

    if tratta_dati and contratti is False:
        gap("legal.ha_contratti_standard", "Contratti standard", False,
            "Si trattano dati personali senza una base contrattuale standard: ogni "
            "rapporto è un negoziato (o un rischio) a sé.", "alta")
    elif contratti is False:
        gap("legal.ha_contratti_standard", "Contratti standard", False,
            "Senza condizioni standard ogni incarico nasce su termini improvvisati: "
            "il contenzioso si previene alla firma, non in tribunale.")
    if ecommerce and tratta_dati:
        out.append(_ins("legal.gdpr_ecommerce", "Perimetro GDPR e-commerce", "attivo", "",
                        "e-commerce + trattamento dati dichiarati", 
                        ("ha_sito_ecommerce", "tratta_dati_personali"),
                        "Vendita online + dati personali = informative, cookie, registro "
                        "trattamenti e data breach plan: il perimetro c'è per legge, la "
                        "domanda è solo se è presidiato.", tipo="rischio", gravita="media"))
    if ai_prof:
        out.append(_ins("legal.ai_profilazione", "Profilazione con AI", "attiva", "",
                        "dichiarato: usa AI per profilazione",
                        ("usa_ai_profilazione",),
                        "La profilazione automatizzata attiva obblighi specifici (GDPR "
                        "art. 22, AI Act in arrivo): va mappata ora, non quando arriva "
                        "il controllo.", tipo="rischio", gravita="alta"))
    gap("legal.ha_marchio", "Tutela del marchio", marchio,
        "Il nome su cui si costruisce la reputazione non è registrato: chiunque può "
        "occuparlo, e difendersi DOPO costa multipli della registrazione.")
    if estero and contratti is False:
        out.append(_ins("legal.estero_no_contratti", "Operatività estera senza contratti standard",
                        "critico", "", "dichiarato: opera all'estero + no contratti standard",
                        ("opera_estero", "ha_contratti_standard"),
                        "All'estero senza clausole su foro e legge applicabile: un "
                        "contenzioso si gioca in casa dell'altro.", tipo="rischio",
                        gravita="alta"))
    if modello231 is False:
        n = f.get("dipendenti")
        if n is not None and n >= 15:
            out.append(_ins("legal.modello_231", "Modello organizzativo 231", "assente", "",
                            f"dichiarato: no modello 231 con {n:.0f} dipendenti",
                            ("ha_modello_231", "dipendenti"),
                            "Con questa dimensione l'assenza del 231 espone la società "
                            "alla responsabilità amministrativa per reati dei singoli: "
                            "lo scudo esiste solo se costruito prima.", tipo="rischio",
                            gravita="media"))
    return out, f


# ── Strategia / crescita ──────────────────────────────────────────────────────
def derive_strategy_insights(inputs: dict) -> tuple[list[dict], Facts]:
    f = Facts(inputs)
    out: list[dict] = []

    md, mdist = f.get("margine_canale_diretto"), f.get("margine_distributore")
    if md is not None and mdist is not None:
        delta = round(md - mdist, 1)
        out.append(_ins(
            "strat.delta_margine_canali", "Differenza di margine tra canali",
            delta, "punti %",
            f"margine diretto − margine distributore = {md:.0f}% − {mdist:.0f}%",
            ("margine_canale_diretto", "margine_distributore"),
            "Ogni euro spostato sul canale a margine più alto vale questo delta: la "
            "scelta dei canali È una decisione di margine, non solo di volumi."))

    if f.has("budget_espansione", "fatturato_annuo"):
        b, fat = f.get("budget_espansione"), f.get("fatturato_annuo")
        if fat > 0:
            out.append(_ins(
                "strat.peso_budget_espansione", "Budget espansione sul fatturato",
                round(b / fat * 100, 1), "%",
                f"budget_espansione / fatturato = {b:,.0f} / {fat:,.0f}",
                ("budget_espansione", "fatturato_annuo"),
                "Dimensiona l'ambizione: sotto certe soglie l'espansione è un test, "
                "non una strategia — va bene, purché lo si sappia."))

    mol = f.get("mol_pct")
    if mol is not None:
        out.append(_ins(
            "strat.mol", "Marginalità operativa dichiarata", mol, "%",
            f"MOL/EBITDA dichiarato = {mol:.0f}%", ("mol_pct",),
            "È il carburante dell'espansione: definisce quanti errori il piano può "
            "permettersi prima di intaccare la gestione corrente.",
            tipo="rischio" if mol < 10 else "insight",
            gravita="media" if mol < 10 else None))

    conc = f.get("concentrazione_top1") or f.get("concentrazione_top3") or f.get("concentrazione_top5")
    if conc is not None:
        out.append(_ins(
            "risk.concentrazione", "Concentrazione del fatturato", conc, "%",
            f"quota clienti principali = {conc:.0f}%",
            ("concentrazione_top1",),
            "Espandersi partendo da una base concentrata significa costruire il nuovo "
            "sul fragile: la diversificazione È parte del piano di crescita.",
            tipo="rischio", gravita="alta" if conc >= 50 else "media"))

    return out, f


# ── M&A / acquisizione (valutazione del target) ───────────────────────────────
def derive_ma_insights(inputs: dict) -> tuple[list[dict], Facts]:
    """Indicatori di valutazione di un'acquisizione, dai dati del target.
    Ogni multiplo/indice ha formula, dati usati e lettura consulenziale."""
    f = Facts(inputs)
    out: list[dict] = []

    fat = f.get("fatturato_annuo")
    ebitda = f.get("ebitda")
    utile = f.get("utile_netto")
    pn = f.get("patrimonio_netto")
    prezzo = f.get("prezzo_richiesto")
    debiti = f.get("debiti_finanziari")
    liq = f.get("liquidita")

    # PFN = debiti finanziari − liquidità (base per l'Enterprise Value).
    pfn = None
    if debiti is not None:
        pfn = round(debiti - (liq or 0), 2)
        out.append(_ins(
            "ma.pfn", "Posizione Finanziaria Netta (PFN)", pfn, "€",
            f"debiti_finanziari − liquidità = {debiti:,.0f} − {liq or 0:,.0f}",
            ("debiti_finanziari",) + (("liquidita",) if liq is not None else ()),
            "È il debito 'vero' che l'acquirente eredita: si somma al prezzo dell'equity "
            "per capire quanto costa DAVVERO l'azienda (Enterprise Value)."))

    # Enterprise Value = Equity (prezzo) + PFN.
    ev = None
    if prezzo is not None and pfn is not None:
        ev = round(prezzo + pfn, 2)
        out.append(_ins(
            "ma.enterprise_value", "Enterprise Value implicito", ev, "€",
            f"prezzo (equity) + PFN = {prezzo:,.0f} + {pfn:,.0f}",
            ("prezzo_richiesto", "debiti_finanziari"),
            "Il prezzo dell'equity nasconde il debito: l'EV è il costo reale del "
            "controllo dell'azienda, ed è su questo che si misurano i multipli."))

    # EV/EBITDA — il multiplo principe dell'M&A.
    if ev is not None and ebitda and ebitda > 0:
        mult = round(ev / ebitda, 2)
        out.append(_ins(
            "ma.ev_ebitda", "Multiplo EV/EBITDA", mult, "x",
            f"Enterprise Value / EBITDA = {ev:,.0f} / {ebitda:,.0f}",
            ("prezzo_richiesto", "debiti_finanziari", "ebitda"),
            f"L'azienda viene valutata {mult:.1f} volte l'EBITDA. Per una PMI non "
            "quotata un multiplo 4-6x è tipico: sopra si paga un premio che i flussi "
            "devono giustificare, sotto può esserci un affare o un rischio nascosto.",
            tipo="rischio" if mult >= 7 else "insight",
            gravita="media" if mult >= 7 else None))

    # Prezzo/EBITDA (equity multiple) — a confronto con EV/EBITDA fa vedere il peso del debito.
    if prezzo is not None and ebitda and ebitda > 0:
        out.append(_ins(
            "ma.prezzo_ebitda", "Multiplo Prezzo/EBITDA (equity)", round(prezzo / ebitda, 2), "x",
            f"prezzo / EBITDA = {prezzo:,.0f} / {ebitda:,.0f}",
            ("prezzo_richiesto", "ebitda"),
            "Guardando solo il prezzo il deal sembra più economico di quanto sia: la "
            "differenza con l'EV/EBITDA è il debito che ti stai portando in casa."))

    # Debt/EBITDA — sostenibilità della leva del target.
    if debiti is not None and ebitda and ebitda > 0:
        lev = round(debiti / ebitda, 2)
        out.append(_ins(
            "ma.debt_ebitda", "Leva del target (Debiti/EBITDA)", lev, "x",
            f"debiti_finanziari / EBITDA = {debiti:,.0f} / {ebitda:,.0f}",
            ("debiti_finanziari", "ebitda"),
            f"Il target ripaga i debiti in ~{lev:.1f} anni di EBITDA. Oltre 3x la "
            "struttura è tesa: la banca la guarda, e tu la erediti.",
            tipo="rischio" if lev >= 3 else "insight",
            gravita="alta" if lev >= 4 else ("media" if lev >= 3 else None)))

    # Prezzo/Patrimonio netto (P/B).
    if prezzo is not None and pn and pn > 0:
        out.append(_ins(
            "ma.prezzo_pn", "Prezzo/Patrimonio netto", round(prezzo / pn, 2), "x",
            f"prezzo / patrimonio_netto = {prezzo:,.0f} / {pn:,.0f}",
            ("prezzo_richiesto", "patrimonio_netto"),
            "Quanto si paga sopra il valore contabile: il premio remunera avviamento, "
            "clienti e posizione — va giustificato, non dato per scontato."))

    # Prezzo/Utile (P/E) e ROI/payback dell'equity.
    if prezzo is not None and utile and utile > 0:
        pe = round(prezzo / utile, 2)
        roi = round(utile / prezzo * 100, 1)
        out.append(_ins(
            "ma.prezzo_utile", "Prezzo/Utile (P/E) del target", pe, "x",
            f"prezzo / utile_netto = {prezzo:,.0f} / {utile:,.0f}",
            ("prezzo_richiesto", "utile_netto"),
            f"A utile costante il capitale investito rientra in ~{pe:.1f} anni "
            f"(ROI ~{roi:.0f}%): è il primo metro della convenienza, prima delle sinergie."))
        out.append(_ins(
            "ma.roi_preliminare", "ROI preliminare dell'equity", roi, "%",
            f"utile_netto / prezzo = {utile:,.0f} / {prezzo:,.0f}",
            ("utile_netto", "prezzo_richiesto"),
            "Ritorno lordo prima delle sinergie e del costo del debito d'acquisizione: "
            "la soglia da battere è il costo del capitale che useresti per pagarlo.",
            tipo="insight"))

    # Concentrazione clienti del target = rischio che si acquista.
    conc = f.get("concentrazione_top5") or f.get("concentrazione_top3") or f.get("concentrazione_top1")
    if conc is not None:
        campo = ("concentrazione_top5" if f.get("concentrazione_top5") is not None
                 else "concentrazione_top3" if f.get("concentrazione_top3") is not None
                 else "concentrazione_top1")
        out.append(_ins(
            "risk.concentrazione", "Concentrazione clienti del target", conc, "%",
            f"quota fatturato clienti principali = {conc:.0f}%", (campo,),
            f"Il {conc:.0f}% del fatturato su pochi clienti è il rischio che compri: "
            "se uno se ne va dopo il closing, l'EBITDA su cui hai pagato il multiplo "
            "svanisce. Va protetto con clausole (earn-out) e verificato in due diligence.",
            tipo="rischio", gravita="alta" if conc >= 50 else "media"))

    return out, f
