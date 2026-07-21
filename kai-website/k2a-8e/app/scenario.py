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


def what_if_ops(inputs: dict) -> list[dict]:
    """Simulazioni operations in unità NATIVE (ore, commesse, %): niente euro inventati."""
    f = Facts(inputs)
    sims: list[dict] = []
    tot, rit = f.get("progetti_in_corso"), f.get("progetti_in_ritardo")
    lav, fatb = f.get("ore_lavorate"), f.get("ore_fatturabili")

    if tot and rit is not None and tot > 0:
        nuovo = round((rit * 1.5) / tot * 100, 1)
        sims.append({
            "domanda": "Cosa succede se le commesse in ritardo aumentano del 50%?",
            "risultato": f"il ritardo passa al {nuovo}% del portafoglio",
            "calcolo": f"({rit:.0f} × 1,5) / {tot:.0f}",
            "dati_usati": ["progetti_in_corso", "progetti_in_ritardo"],
            "implicazione": "Oltre questa soglia le urgenze dettano l'agenda: la "
                            "pianificazione diventa rincorsa. Il registro blocchi va "
                            "attivato PRIMA di arrivarci.",
            "source": "system_calculated"})
    if lav and fatb is not None and lav > 0:
        perse = round(lav * 0.05, 0)
        util = fatb / lav * 100
        sims.append({
            "domanda": "Cosa succede se l'utilizzo fatturabile cala di 5 punti?",
            "risultato": f"~{perse:,.0f} ore/periodo in più non fatturano "
                         f"(utilizzo dal {util:.0f}% al {util - 5:.0f}%)".replace(",", "."),
            "calcolo": "ore_lavorate × 5%",
            "dati_usati": ["ore_lavorate", "ore_fatturabili"],
            "implicazione": "È l'equivalente di perdere una persona part-time senza "
                            "che nessuno se ne accorga: l'utilizzo va misurato ogni mese.",
            "source": "system_calculated"})
    return sims


def what_if_marketing(inputs: dict) -> list[dict]:
    f = Facts(inputs)
    sims: list[dict] = []
    dep = f.get("dipendenza_canale")
    if dep is not None:
        sims.append({
            "domanda": "Cosa succede se il canale principale riduce la visibilità del 20%?",
            "risultato": f"a rischio fino al {round(dep * 0.2, 0):.0f}% della domanda totale",
            "calcolo": f"dipendenza {dep:.0f}% × 20%",
            "dati_usati": ["dipendenza_canale"],
            "implicazione": "Un cambio di algoritmo o di commissioni non si negozia: "
                            "si subisce. L'unica difesa è il mix di canali costruito prima.",
            "source": "system_calculated"})
        sims.append({
            "domanda": "Cosa succede spostando 10 punti di mix sul canale diretto in 12 mesi?",
            "risultato": f"la dipendenza scende dal {dep:.0f}% al {dep - 10:.0f}%",
            "calcolo": f"{dep:.0f}% − 10 punti",
            "dati_usati": ["dipendenza_canale"],
            "implicazione": "Obiettivo realistico con incentivi al canale diretto e base "
                            "clienti proprietaria: misurarlo ogni mese, non a fine anno.",
            "source": "system_calculated"})
    return sims


def what_if_hr(inputs: dict) -> list[dict]:
    f = Facts(inputs)
    sims: list[dict] = []
    fat, dip = f.get("fatturato_annuo"), f.get("dipendenti")
    if fat and dip and dip > 0:
        per_addetto = fat / dip
        sims.append({
            "domanda": "Cosa succede se si perdono 2 persone chiave in 6 mesi?",
            "risultato": f"~{round(per_addetto * 2, 0):,.0f} € di fatturato/anno da "
                         "ricoprire, più i tempi di sostituzione".replace(",", "."),
            "calcolo": f"fatturato per addetto × 2 = {per_addetto:,.0f} × 2",
            "dati_usati": ["fatturato_annuo", "dipendenti"],
            "implicazione": "Con un organico piccolo ogni uscita è strutturale, non "
                            "statistica: la retention dei ruoli chiave È gestione del rischio.",
            "source": "system_calculated"})
        sims.append({
            "domanda": "Cosa succede assumendo 1 persona a produttività invariata?",
            "risultato": f"servono ~{round(per_addetto, 0):,.0f} € di nuovo fatturato "
                         "per mantenere la produttività attuale".replace(",", "."),
            "calcolo": f"fatturato per addetto attuale = {per_addetto:,.0f}",
            "dati_usati": ["fatturato_annuo", "dipendenti"],
            "implicazione": "Assumere prima del fatturato è un investimento, dopo è una "
                            "conseguenza: basta saperlo quando si firma.",
            "source": "system_calculated"})
    return sims


def what_if_strategy(inputs: dict) -> list[dict]:
    f = Facts(inputs)
    sims: list[dict] = []
    md, mdist = f.get("margine_canale_diretto"), f.get("margine_distributore")
    fat = f.get("fatturato_annuo")
    if md is not None and mdist is not None and fat:
        delta_eur = round(fat * 0.10 * (md - mdist) / 100, 0)
        sims.append({
            "domanda": "Cosa succede spostando il 10% del fatturato sul canale diretto?",
            "risultato": f"~{delta_eur:,.0f} €/anno di margine in più a parità di "
                         "volumi".replace(",", "."),
            "calcolo": f"fatturato × 10% × (margine diretto − distributore) "
                       f"= {fat:,.0f} × 10% × {md - mdist:.0f}pp",
            "dati_usati": ["fatturato_annuo", "margine_canale_diretto",
                           "margine_distributore"],
            "implicazione": "Il mix di canale è una leva di margine grande quanto una "
                            "rinegoziazione prezzi — ma senza toccare il listino.",
            "source": "system_calculated"})
    b = f.get("budget_espansione")
    mol = f.get("mol_pct")
    if b and fat and mol is not None:
        recupero = round(b / (fat * mol / 100) * 12, 0) if fat * mol > 0 else None
        if recupero:
            sims.append({
                "domanda": "In quanto tempo il MOL attuale ripaga il budget di espansione?",
                "risultato": f"~{recupero:.0f} mesi di MOL a livelli correnti",
                "calcolo": f"budget / (fatturato × MOL%) × 12 = {b:,.0f} / "
                           f"({fat:,.0f} × {mol:.0f}%)",
                "dati_usati": ["budget_espansione", "fatturato_annuo", "mol_pct"],
                "implicazione": "Misura la pazienza che il piano richiede: se il "
                                "rientro atteso è più lungo, il budget è sottodimensionato "
                                "o l'ambizione va scalata.",
                "source": "system_calculated"})
    return sims
