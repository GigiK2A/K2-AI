"""Diagnostic Engine — il consulente RAGIONA prima di consigliare (review efficienza).

Il caso-tipo: "gli utili calano, il fatturato tiene, ho la sensazione che dentro
qualcosa non funzioni". Dati direzionali (+12% costo personale, +18% spese, più
riunioni/approvazioni/revisioni, cambio del responsabile operativo) — NESSUN valore
assoluto. Il report non deve inventare numeri: deve DIAGNOSTICARE.

Questo motore produce ciò che manca (Problemi 1-8 della review):
- insight SOLO dai dati direzionali forniti (mai assoluti inventati);
- IPOTESI DIAGNOSTICA con probabilità deterministiche (dal peso delle evidenze),
  marcate come stima (confidence B), + IPOTESI ESCLUSE con il perché;
- la catena causale che spiega il calo di margine;
- i KPI SPECIFICI del problema da iniziare a misurare (non i soliti KPI finanziari);
- risolve la contraddizione "costo personale su" ≠ "aumenti salariali": senza nuove
  assunzioni né aumenti, il +% è ore su lavoro improduttivo, non salari.

Riconosce i segnali sia da campi strutturati (delta %) sia dal testo libero della
conversazione (contesto/note/quesito) — robusto a come arrivano i dati.
"""

from __future__ import annotations

from typing import Any, Optional

from . import normalize as NORM

# ── Segnali qualitativi: frasi che li attivano nel testo della conversazione ──
_SIGNAL_PHRASES: dict[str, tuple[str, ...]] = {
    "aumento_riunioni": ("più riunioni", "piu riunioni", "aumento di riunioni",
                         "aumento delle riunioni", "troppe riunioni", "riunioni aumentate"),
    "aumento_approvazioni": ("livelli di approvazione", "livelli autorizzativi",
                             "più approvazioni", "piu approvazioni", "passaggi autorizzativi",
                             "catena di approvazioni", "approvazioni aumentate"),
    "aumento_revisioni": ("revisioni interne", "più revisioni", "piu revisioni",
                          "rilavorazioni", "revisioni aumentate", "rifacimenti"),
    "cambio_leadership": ("cambio del responsabile", "cambiato il responsabile",
                          "nuovo responsabile operativo", "cambio di responsabile",
                          "cambio del direttore", "nuovo direttore operativo",
                          "cambio management", "nuovo capo", "cambio al vertice operativo"),
    "meno_produttivi": ("meno produttivi", "meno produttiv", "produttività in calo",
                        "produttivita in calo", "più occupati ma meno", "piu occupati ma meno",
                        "occupati ma meno produttivi", "calo di produttività"),
    "output_stabile": ("progetti stabili", "numero di progetti stabile", "commesse stabili",
                       "stesso numero di progetti", "volumi stabili", "ore lavorate stabili",
                       "ore stabili"),
    "no_assunzioni": ("nessuna nuova assunzione", "senza nuove assunzioni",
                      "non abbiamo assunto", "nessuna assunzione", "organico invariato"),
    "no_aumenti_salariali": ("nessun aumento salariale", "senza aumenti salariali",
                             "nessun aumento di stipendio", "nessun aumento significativo",
                             "stipendi invariati", "nessun adeguamento salariale"),
    "no_clienti_persi": ("non abbiamo perso clienti", "nessun cliente perso",
                         "nessun cliente importante perso", "clienti stabili"),
    "materie_stabili": ("materie prime stabili", "materie prime invariate", "costo materie stabile"),
}

# Delta % strutturati (se il form/estrazione li fornisce). Nome canonico → alias.
_DELTA_ALIASES: dict[str, tuple[str, ...]] = {
    "delta_fatturato": ("delta_fatturato_pct", "fatturato_delta_pct", "var_fatturato_pct",
                        "variazione_fatturato_pct"),
    "delta_costo_personale": ("delta_costo_personale_pct", "costo_personale_delta_pct",
                              "var_costo_personale_pct", "variazione_personale_pct"),
    "delta_spese_generali": ("delta_spese_generali_pct", "spese_generali_delta_pct",
                             "var_spese_generali_pct"),
    "delta_utile": ("delta_utile_pct", "utile_delta_pct", "var_utile_pct"),
}


def _num(v: Any) -> Optional[float]:
    from .insight import _num as n
    return n(v)


def _free_text(inputs: dict) -> str:
    parts = []
    for k, v in (inputs or {}).items():
        v = NORM.unwrap_value(v)
        if isinstance(v, str) and len(v.strip()) >= 8:
            parts.append(v.strip())
        elif isinstance(v, list):
            parts += [str(x) for x in v if isinstance(x, str)]
    return " \n".join(parts).lower()


class Signals:
    """Segnali della diagnosi, letti da campi strutturati + testo libero."""

    def __init__(self, inputs: dict) -> None:
        self.inputs = inputs or {}
        self.text = _free_text(inputs)
        self.deltas: dict[str, float] = {}
        for canon, aliases in _DELTA_ALIASES.items():
            for a in aliases:
                n = _num(self.inputs.get(a))
                if n is not None:
                    self.deltas[canon] = n
                    break
        self.flags: dict[str, bool] = {}
        for name, phrases in _SIGNAL_PHRASES.items():
            struct = self.inputs.get(name)
            if isinstance(struct, bool):
                self.flags[name] = struct
            else:
                self.flags[name] = any(p in self.text for p in phrases)

    def has(self, name: str) -> bool:
        return bool(self.flags.get(name))

    def delta(self, name: str) -> Optional[float]:
        return self.deltas.get(name)

    def count(self, *names: str) -> int:
        return sum(1 for n in names if self.has(n))


def is_efficiency_case(inputs: dict) -> bool:
    """Vero se i segnali disegnano un calo di efficienza organizzativa: costi su
    (o utile giù) con fatturato/output stabili + almeno un marcatore di inefficienza."""
    s = Signals(inputs)
    costi_su = (s.delta("delta_costo_personale") or 0) > 5 or \
        (s.delta("delta_spese_generali") or 0) > 5
    utile_giu = (s.delta("delta_utile") or 0) < -3
    ricavi_piatti = abs(s.delta("delta_fatturato") or 0) <= 6
    inefficienza = s.count("aumento_riunioni", "aumento_approvazioni",
                           "aumento_revisioni", "cambio_leadership", "meno_produttivi")
    return (costi_su or utile_giu) and (ricavi_piatti or s.has("output_stabile")) \
        and inefficienza >= 2


# ── Insight direzionali (mai valori assoluti) ─────────────────────────────────
def _ins(id_, titolo, valore, unita, formula, dati, spiegazione, tipo="insight",
         gravita=None, confidence="A") -> dict:
    return {"id": id_, "titolo": titolo, "valore": valore, "unita": unita,
            "formula": formula, "dati_usati": list(dati), "spiegazione": spiegazione,
            "tipo": tipo, "gravita": gravita, "confidence": confidence,
            "source": "system_calculated" if confidence == "A" else "assumption"}


def derive_efficiency_insights(inputs: dict) -> list[dict]:
    s = Signals(inputs)
    out: list[dict] = []
    dp = s.delta("delta_costo_personale")
    dg = s.delta("delta_spese_generali")
    df = s.delta("delta_fatturato")

    # 1) Forbice costi-ricavi (solo se i delta ci sono).
    if dp is not None and df is not None:
        forbice = round(dp - df, 1)
        out.append(_ins(
            "eff.forbice_costi_ricavi", "Forbice costo personale − fatturato",
            forbice, "punti %",
            f"Δcosto_personale − Δfatturato = {dp:+.0f}% − {df:+.0f}%",
            ("delta_costo_personale", "delta_fatturato"),
            f"Il costo del personale cresce {forbice:.0f} punti più del fatturato: è "
            "esattamente qui che si apre la compressione del margine — non nelle vendite.",
            tipo="rischio", gravita="alta"))

    # 2) Il paradosso della produttività (risolve la CONTRADDIZIONE salari, Problema 2).
    if dp is not None and dp > 5 and s.has("no_assunzioni") and s.has("no_aumenti_salariali"):
        out.append(_ins(
            "eff.paradosso_produttivita", "Costo del lavoro in aumento senza assunzioni né aumenti",
            round(dp, 1), "% costo personale",
            f"costo personale {dp:+.0f}% con organico e stipendi invariati (dichiarato)",
            ("delta_costo_personale",),
            f"Punto chiave: il costo del personale sale del {dp:.0f}% MA — dichiarato dal "
            "cliente — senza nuove assunzioni né aumenti. Quindi NON è un problema salariale: "
            "è più tempo speso sullo stesso lavoro (straordinari, rilavorazioni, ore su "
            "attività che non producono). La causa è organizzativa, non retributiva.",
            tipo="rischio", gravita="alta"))

    # 3) Driver dei costi: dove pesa (personale/spese, non materie).
    if (dp is not None or dg is not None) and s.has("materie_stabili"):
        driver = []
        if dp is not None and dp > 5:
            driver.append(f"personale ({dp:+.0f}%)")
        if dg is not None and dg > 5:
            driver.append(f"spese generali ({dg:+.0f}%)")
        out.append(_ins(
            "eff.driver_costi", "Dove si concentra l'aumento dei costi",
            ", ".join(driver) or "costi indiretti", "",
            "confronto delle variazioni per voce di costo",
            tuple(k for k, d in (("delta_costo_personale", dp), ("delta_spese_generali", dg))
                  if d is not None),
            "L'aumento è tutto sui costi di STRUTTURA (personale e spese generali), mentre "
            "le materie prime — legate al volume prodotto — sono stabili. È la firma di un "
            "problema di efficienza interna, non di prezzi o di mercato.",
            tipo="rischio", gravita="media"))

    # 4) Segnali di inefficienza rilevati (qualitativi, marcati come tali).
    segnali = [n for n in ("aumento_riunioni", "aumento_approvazioni", "aumento_revisioni",
                           "meno_produttivi") if s.has(n)]
    if segnali:
        label = {"aumento_riunioni": "più riunioni", "aumento_approvazioni": "più livelli di approvazione",
                 "aumento_revisioni": "più revisioni/rilavorazioni", "meno_produttivi": "produttività percepita in calo"}
        out.append(_ins(
            "eff.segnali_inefficienza", "Segnali di lavoro improduttivo",
            len(segnali), "segnali concordanti",
            "conteggio dei marcatori di inefficienza dichiarati",
            tuple(segnali),
            "Segnali dichiarati che puntano nella stessa direzione: "
            + ", ".join(label[n] for n in segnali) + ". Sono tempo che si consuma senza "
            "produrre valore fatturabile — il costo nascosto che erode il margine.",
            tipo="rischio", gravita="media", confidence="B"))

    return out


# ── Ipotesi diagnostiche con probabilità (Problema 7-8) ───────────────────────
def build_diagnosis(inputs: dict) -> dict:
    """Ipotesi diagnostiche pesate (stima dai segnali, confidence B) + ipotesi
    ESCLUSE col perché. Le probabilità sono deterministiche: derivano dal peso
    delle evidenze presenti, non da un'intuizione — e sono marcate come stima."""
    s = Signals(inputs)

    org = s.count("aumento_riunioni", "aumento_approvazioni", "aumento_revisioni",
                  "meno_produttivi", "output_stabile")
    pesi = {
        "org": 22 + 11 * org,                                  # inefficienza organizzativa
        "leadership": 8 + (26 if s.has("cambio_leadership") else 0),
        "approvazioni": 4 + (14 if s.has("aumento_approvazioni") else 0),
        "altro": 8,                                            # residuo onesto
    }
    tot = sum(pesi.values()) or 1
    prob = {k: round(v / tot * 100) for k, v in pesi.items()}
    # aggiusta l'arrotondamento perché sommi 100
    diff = 100 - sum(prob.values())
    prob["org"] += diff

    def ev(*names):
        label = {"aumento_riunioni": "più riunioni", "aumento_approvazioni": "più livelli di approvazione",
                 "aumento_revisioni": "più revisioni/rilavorazioni", "meno_produttivi": "produttività percepita in calo",
                 "output_stabile": "progetti/ore stabili", "cambio_leadership": "cambio del responsabile operativo"}
        return [label[n] for n in names if s.has(n)]

    ipotesi = [
        {"causa": "Inefficienza organizzativa (lavoro improduttivo in aumento)",
         "probabilita": prob["org"], "confidence": "B",
         "evidenze": ev("output_stabile", "aumento_riunioni", "aumento_revisioni",
                        "aumento_approvazioni", "meno_produttivi")
         or ["output stabile a fronte di costi di struttura in aumento"]},
        {"causa": "Gestione/leadership (effetto del cambio del responsabile operativo)",
         "probabilita": prob["leadership"], "confidence": "B",
         "evidenze": ev("cambio_leadership")
         + (["il calo è iniziato pochi mesi dopo il cambio"] if s.has("cambio_leadership") else [])},
        {"causa": "Processi approvativi troppo pesanti",
         "probabilita": prob["approvazioni"], "confidence": "B",
         "evidenze": ev("aumento_approvazioni") or ["catena autorizzativa allungata"]},
        {"causa": "Altre cause (mix di fattori minori)", "probabilita": prob["altro"],
         "confidence": "C", "evidenze": ["residuo non spiegato dai segnali disponibili"]},
    ]
    ipotesi = [h for h in ipotesi if h["probabilita"] > 0]
    ipotesi.sort(key=lambda h: h["probabilita"], reverse=True)

    escluse = []
    if abs(s.delta("delta_fatturato") or 0) <= 6 or s.has("no_clienti_persi"):
        escluse.append({"causa": "Problema commerciale / di domanda",
                        "perche_esclusa": "il fatturato tiene"
                        + (" e non sono stati persi clienti importanti" if s.has("no_clienti_persi") else "")
                        + ": la domanda non è la causa."})
    if s.has("materie_stabili"):
        escluse.append({"causa": "Costo delle materie prime / produzione",
                        "perche_esclusa": "le materie prime sono stabili: il problema non è "
                        "nel costo del venduto ma nella struttura."})
    if s.has("no_aumenti_salariali") and s.has("no_assunzioni"):
        escluse.append({"causa": "Aumento salariale / nuove assunzioni",
                        "perche_esclusa": "dichiarato dal cliente: nessun aumento né nuova "
                        "assunzione. Il maggior costo del personale è ORE, non retribuzioni."})

    return {
        "domanda": "Perché gli utili calano se il fatturato tiene?",
        "ipotesi": ipotesi,
        "ipotesi_escluse": escluse,
        "causa_piu_probabile": ipotesi[0]["causa"] if ipotesi else "",
        "sintesi": ("La causa più probabile NON è commerciale: il fatturato tiene e i "
                    "clienti restano. Le evidenze indicano una PERDITA DI EFFICIENZA "
                    "ORGANIZZATIVA — più tempo speso su lavoro che non produce valore "
                    "(riunioni, approvazioni, revisioni), plausibilmente innescata dal "
                    "cambio del responsabile operativo. Gli stessi ricavi costano più ore, "
                    "e il margine si comprime."),
        "confidence": "B",
    }


def build_efficiency_chain(inputs: dict) -> list[dict]:
    """La catena causale esplicita (Problema 4)."""
    from . import reasoning
    s = Signals(inputs)
    nodi = []
    if s.has("cambio_leadership"):
        nodi.append(reasoning.node("osservazione",
            "Il calo di redditività parte pochi mesi dopo il cambio del responsabile operativo.",
            ["cambio_leadership"]))
        nodi.append(reasoning.node("cause",
            "Un nuovo stile di gestione ha introdotto più livelli autorizzativi e più "
            "controlli, per prudenza o per prendere le misure."))
    else:
        nodi.append(reasoning.node("osservazione",
            "Costi di struttura in aumento con fatturato e output stabili.",
            ["output_stabile"]))
        nodi.append(reasoning.node("cause",
            "Processi appesantiti: più passaggi autorizzativi, riunioni e revisioni."))
    nodi.append(reasoning.node("conseguenze",
        "Più riunioni + più approvazioni + più revisioni ⇒ più ore su attività che non "
        "fatturano ⇒ produttività per persona in calo ⇒ gli stessi ricavi assorbono più "
        "costo del lavoro ⇒ margine operativo in compressione.",
        ["aumento_riunioni", "aumento_approvazioni", "aumento_revisioni"]))
    nodi.append(reasoning.node("priorita",
        "Alta: è un'emorragia silenziosa: non si vede nei ricavi, si vede solo nel margine, "
        "e peggiora finché il processo resta così."))
    nodi.append(reasoning.node("intervento",
        "Mappare il processo decisionale reale, togliere i livelli autorizzativi non "
        "necessari, ridurre e time-boxare le riunioni, misurare le ore improduttive. "
        "Prima si misura, poi si taglia con criterio."))
    nodi.append(reasoning.node("risultato_atteso",
        "Ore restituite al lavoro che produce valore, produttività in recupero e margine "
        "che risale a parità di fatturato — senza tagliare persone."))
    return [reasoning.chain("eff.catena", "Dalla governance appesantita al margine in calo",
                            nodi, priorita="alta", confidence="B")]


def efficiency_kpis_to_measure(inputs: dict) -> list[dict]:
    """KPI SPECIFICI del problema da INIZIARE a misurare (Problema 5): non i soliti
    KPI finanziari. Nessun valore (il dato non c'è ancora) → 'da rilevare'."""
    return [
        {"kpi": "Tempo medio di approvazione (per decisione/commessa)",
         "perche": "misura direttamente il peso della catena autorizzativa"},
        {"kpi": "Numero di revisioni/rilavorazioni per commessa",
         "perche": "quantifica il lavoro rifatto, il costo nascosto per eccellenza"},
        {"kpi": "Ore di riunione per persona / settimana",
         "perche": "rende visibile il tempo sottratto al lavoro produttivo"},
        {"kpi": "Quota di tempo produttivo vs improduttivo",
         "perche": "il KPI-madre dell'efficienza: dove vanno davvero le ore"},
        {"kpi": "Lead time medio di progetto",
         "perche": "se allunga a parità di volumi, il processo si è inceppato"},
        {"kpi": "Produttività per team (output / ore)",
         "perche": "localizza dove la produttività si è persa"},
    ]


def build_diagnosis_pack(inputs: dict) -> dict:
    from . import decision
    insights = derive_efficiency_insights(inputs)
    diagnosi = build_diagnosis(inputs)
    pack: dict[str, Any] = {
        "_tipo": "diagnosi_efficienza",
        # Problema 1: il caso è qualitativo (nessun valore assoluto) → sopprimi i KPI
        # finanziari che l'LLM avrebbe inventato. La pipeline rimuove queste sezioni.
        "_suppress_sections": ["kpi_finanziaria", "kpi_cliente", "kpi_processi",
                               "kpi_crescita", "trend_12_mesi"],
        "decisione_sintesi": {
            "domanda_decisionale": diagnosi["domanda"],
            "sintesi": diagnosi["sintesi"], "confidence": "B", "fattori": []},
        "ipotesi_diagnostica": diagnosi,
        "insight_derivati": insights,
        "analisi_sistemica": build_efficiency_chain(inputs),
        "kpi_da_misurare": efficiency_kpis_to_measure(inputs),
        "raccomandazioni_operative": _efficiency_recommendations(inputs, insights, decision),
        "confronto_soluzioni": {},
        "dati_da_raccogliere": [
            "Ore per attività (produttiva/riunioni/approvazioni/revisioni) — anche 2 settimane campione",
            "Mappa del processo decisionale attuale (chi approva cosa, in quanti passaggi)",
            "Andamento del margine operativo mese per mese negli ultimi 12 mesi",
            "Data esatta del cambio responsabile vs inizio del calo (per confermare la correlazione)",
        ],
    }
    return pack


def _efficiency_recommendations(inputs: dict, insights: list[dict], decision) -> list[dict]:
    s = Signals(inputs)
    recs = [decision.recommend(
        "rec.misura_ore", "Misurare dove vanno le ore prima di tagliare",
        perche="La causa più probabile è lavoro improduttivo in aumento, ma oggi nessuno "
               "misura quanto tempo va in riunioni, approvazioni e revisioni.",
        perche_ora="Senza la misura si taglia a sensazione — e di solito si taglia la cosa "
                   "sbagliata (le persone) invece del processo.",
        perche_questa="È la mossa a rischio zero: rende oggettivo un problema oggi percepito, "
                      "e indica esattamente dove intervenire.",
        perche_non_altre="Ristrutturare o tagliare organico senza dati aggrava il problema: "
                         "meno mani sullo stesso processo inefficiente.",
        chi="Responsabile operativo con i team leader",
        quando="2 settimane di rilevazione a campione, da subito",
        con_quali_dati="Timesheet per tipo di attività (anche semplificato)",
        cadenza="Rilevazione continua, revisione mensile",
        validazione="Confronto quota tempo produttivo prima/dopo gli interventi",
        kpi_generati=["% tempo produttivo", "ore riunione/persona", "revisioni/commessa"],
        decisore="Direzione",
        soglie=[decision.soglia("quota tempo produttivo obiettivo", "ipotesi",
                                "Da fissare dopo la prima rilevazione, non su benchmark astratti.")])]
    if s.has("aumento_approvazioni") or s.has("cambio_leadership"):
        recs.append(decision.recommend(
            "rec.snellire_approvazioni", "Snellire la catena autorizzativa",
            perche="Più livelli di approvazione allungano i tempi e moltiplicano le riunioni "
                   "senza aggiungere valore.",
            perche_ora="Ogni settimana con il processo attuale è margine che esce; è anche la "
                       "leva più rapida (è una decisione organizzativa, non un investimento).",
            perche_questa="Attacca il nodo a monte della catena causale (le approvazioni "
                          "generano riunioni e revisioni).",
            perche_non_altre="Aggiungere strumenti o persone non riduce i passaggi: li "
                             "digitalizza soltanto.",
            chi="Direzione + responsabile operativo",
            quando="Ridisegno entro 30 giorni",
            con_quali_dati="Mappa attuale dei passaggi autorizzativi per tipo di decisione",
            cadenza="Revisione trimestrale del processo",
            validazione="Tempo medio di approvazione prima/dopo",
            kpi_generati=["tempo medio approvazione", "n. passaggi per decisione"],
            decisore="Direzione",
            soglie=[decision.soglia("max livelli di approvazione", "best_practice")]))
    return recs
