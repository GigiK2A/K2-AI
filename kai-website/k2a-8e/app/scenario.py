"""Scenario Engine — forecast reali e simulazioni what-if (spec §6, §9).

"Implementare un forecast" senza costruirlo è un consiglio da manuale. Questo
motore, quando i dati lo permettono, il forecast lo COSTRUISCE:

- `cash_forecast_13w`: proiezione di cassa a 13 settimane su 3 scenari
  (prudente / realistico / critico) con settimana, entrate, uscite, saldo
  progressivo — e le IPOTESI esplicitate una per una;
- `what_if`: simulazioni sui rischi principali ("il top client paga a +30gg",
  "DSO +15 giorni", "fatturato −10%") con calcolo riproducibile.

Regole: solo aritmetica sui dati forniti; ogni numero derivato porta formula e
ipotesi; niente dati → niente scenario (mai serie inventate: il quality gate
già blocca le serie non ancorate, questo motore le produce ancorate).
"""

from __future__ import annotations

from typing import Optional

from .insight import Facts

_W_PER_MONTH = 13 / 3          # 13 settimane = 3 mesi
IPOTESI_BASE = (
    "Entrate e uscite distribuite uniformemente sulle settimane (media mensile / 4,33)",
    "Nessuna stagionalità considerata (dato non fornito)",
    "Saldo iniziale = −scoperto attuale se fornito, altrimenti 0",
)

SCENARI = {
    "prudente": {"entrate": 0.85, "uscite": 1.05,
                 "ipotesi": "entrate −15%, uscite +5% (ritardi incasso, imprevisti)"},
    "realistico": {"entrate": 1.0, "uscite": 1.0,
                   "ipotesi": "medie mensili dichiarate, invariate"},
    "critico": {"entrate": 0.70, "uscite": 1.0,
                "ipotesi": "entrate −30% (ritardo dei clienti principali)"},
}


def cash_forecast_13w(inputs: dict) -> Optional[dict]:
    """Forecast 13 settimane × 3 scenari. None se mancano incassi/uscite mensili."""
    f = Facts(inputs)
    if not f.has("incassi_mese", "uscite_mese"):
        return None
    inc_m, usc_m = f.get("incassi_mese"), f.get("uscite_mese")
    saldo0 = -(f.get("scoperto") or 0.0)

    scenari_out = {}
    for nome, cfg in SCENARI.items():
        inc_w = inc_m / 4.33 * cfg["entrate"]
        usc_w = usc_m / 4.33 * cfg["uscite"]
        saldo = saldo0
        rows = []
        for w in range(1, 14):
            saldo = saldo + inc_w - usc_w
            rows.append({"settimana": w, "entrate": round(inc_w, 0),
                         "uscite": round(usc_w, 0), "saldo": round(saldo, 0)})
        scenari_out[nome] = {
            "ipotesi_scenario": cfg["ipotesi"],
            "settimane": rows,
            "saldo_finale": rows[-1]["saldo"],
            "prima_settimana_negativa": next(
                (r["settimana"] for r in rows if r["saldo"] < 0), None),
        }

    return {
        "titolo": "Forecast di cassa a 13 settimane",
        "source": "system_calculated",
        "dati_usati": ["incassi_mese", "uscite_mese"]
        + (["scoperto"] if f.has("scoperto") else []),
        "ipotesi": list(IPOTESI_BASE) + [f"{k}: {v['ipotesi_scenario']}"
                                         for k, v in scenari_out.items()],
        "scenari": scenari_out,
        "nota": "Simulazione indicativa costruita sui dati dichiarati: serve a vedere "
                "QUANDO il fabbisogno si manifesta, non a prevedere il centesimo. "
                "Da ricalibrare ogni settimana coi consuntivi.",
    }


def what_if(inputs: dict) -> list[dict]:
    """Simulazioni sui rischi principali. Solo quelle possibili coi dati forniti."""
    f = Facts(inputs)
    sims: list[dict] = []

    fat = f.get("fatturato_annuo")
    top1 = f.get("concentrazione_top1")
    top3 = f.get("concentrazione_top3")
    inc = f.get("incassi_mese")
    usc = f.get("uscite_mese")

    # 1) Il cliente principale paga con 30 giorni di ritardo.
    conc = top1 if top1 is not None else top3
    if fat and conc:
        buco = round(fat * conc / 100 / 12, 0)
        label = "top client" if top1 is not None else "primi 3 clienti"
        sims.append({
            "domanda": f"Cosa succede se il {label} paga con 30 giorni di ritardo?",
            "risultato": f"~{buco:,.0f} € di incassi slittano di un mese".replace(",", "."),
            "calcolo": f"fatturato × {conc:.0f}% / 12 mesi",
            "dati_usati": ["fatturato_annuo",
                           "concentrazione_top1" if top1 is not None else "concentrazione_top3"],
            "implicazione": ("Su una cassa già in deficit significa sfondare il fido: "
                             "serve un piano-B PRIMA che accada (anticipo fatture sul "
                             "cliente specifico, o riserva di liquidità)."
                             if inc is not None and usc is not None and inc < usc else
                             "La cassa del mese dipende dal comportamento di un solo "
                             "soggetto: da presidiare con date certe e sollecito immediato."),
            "source": "system_calculated",
        })

    # 2) Il DSO peggiora di 15 giorni.
    if fat:
        extra = round(fat / 365 * 15, 0)
        sims.append({
            "domanda": "Cosa succede se il DSO aumenta di 15 giorni?",
            "risultato": f"~{extra:,.0f} € in più immobilizzati nei crediti".replace(",", "."),
            "calcolo": "fatturato / 365 × 15 giorni",
            "dati_usati": ["fatturato_annuo"],
            "implicazione": "È nuovo fabbisogno da finanziare allo stesso costo dello "
                            "scoperto: il controllo del ciclo di incasso vale quanto "
                            "una linea di credito in più.",
            "source": "system_calculated",
        })

    # 3) Il fatturato cala del 10% (a struttura invariata).
    if inc is not None and usc is not None:
        nuovo_saldo = round(inc * 0.9 - usc, 0)
        sims.append({
            "domanda": "Cosa succede se il fatturato (e quindi gli incassi) cala del 10%?",
            "risultato": f"il saldo mensile passa a {nuovo_saldo:,.0f} €/mese".replace(",", "."),
            "calcolo": "incassi × 0,90 − uscite (uscite invariate: i costi non scendono da soli)",
            "dati_usati": ["incassi_mese", "uscite_mese"],
            "implicazione": "Mostra quanto è sottile il margine di sicurezza: ogni piano "
                            "di rientro deve reggere anche questo scenario, non solo "
                            "quello medio.",
            "source": "system_calculated",
        })

    return sims
