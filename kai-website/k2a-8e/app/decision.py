"""Decision Engine — confronto alternative e raccomandazioni motivate (spec §7, §8, §11).

Un consulente non prescrive UNA soluzione: confronta alternative e spiega la
scelta. Questo motore produce:

- `finance_options`: ≥3 opzioni di intervento sulla liquidità, ognuna con
  vantaggi/svantaggi/costi/rischi/tempi/complessità/dipendenze e — decisivo —
  QUANDO sceglierla e QUANDO evitarla; conclusione che spiega la preferenza;
- `recommend`: struttura delle raccomandazioni operative con le 4 domande
  obbligatorie (perché? perché ora? perché questa? perché non un'altra?) e il
  dettaglio esecutivo (chi/quando/con quali dati/cadenza/validazione/KPI/decisore).

Deterministico; il testo è condizionato dagli insight reali (costo scoperto,
saldo, concentrazione) così le opzioni parlano del caso, non del manuale.
Niente costi inventati: dove il costo non è derivabile dai dati, si dichiara
"da quotare", mai un numero a caso.
"""

from __future__ import annotations

from typing import Optional


def _ins(insights: list[dict], id_: str) -> Optional[dict]:
    return next((i for i in insights if i["id"] == id_), None)


def finance_options(inputs: dict, insights: list[dict]) -> dict:
    saldo = _ins(insights, "cash.saldo_mensile")
    costo = _ins(insights, "debt.costo_scoperto")
    capitale = _ins(insights, "wc.capitale_in_crediti")

    deficit = saldo is not None and saldo["valore"] < 0
    costo_txt = (f"~{costo['valore']:.0f}%/anno" if costo else "da quotare")

    opzioni = [
        {"opzione": "A — Comprimere il ciclo di incasso (leva interna)",
         "descrizione": "Fatturazione immediata alla consegna, solleciti strutturati "
                        "dal giorno 1, acconti sui nuovi ordini, presidio dedicato dei "
                        "crediti top client.",
         "vantaggi": ["Costo vivo ~zero: è disciplina, non finanza",
                      "Attacca la CAUSA (capitale nei crediti), non il sintomo",
                      "Attivabile in 2-4 settimane"]
         + ([f"Libera parte dei ~{capitale['valore']:,.0f} € immobilizzati"
             .replace(",", ".")] if capitale else []),
         "svantaggi": ["Richiede costanza organizzativa (è il motivo per cui non si fa)",
                       "Effetto pieno in 60-90 giorni, non immediato"],
         "costi": "Ore interne; nessun onere finanziario",
         "rischi": "Attrito commerciale coi clienti abituati a pagare tardi: va "
                   "gestito, non subito",
         "tempi": "2-4 settimane per l'avvio, 60-90 giorni a regime",
         "complessita": "bassa",
         "dipendenze": "Nessuna esterna; serve un owner interno dei crediti",
         "quando_sceglierla": "SEMPRE come prima mossa: qualunque opzione finanziaria "
                              "costa di più se il ciclo di incasso resta lento",
         "quando_evitarla": "Mai da sola se la cassa è già oltre il fido: va abbinata "
                            "a un ponte finanziario"},
        {"opzione": "B — Anticipo fatture / linea autoliquidante sui crediti",
         "descrizione": "Smobilizzo dei crediti commerciali (anticipo fatture, "
                        "factoring pro-solvendo) concentrato sui clienti più solidi.",
         "vantaggi": ["Liquidità legata al fatturato reale: cresce con i volumi",
                      "In genere meno onerosa dello scoperto di conto "
                      f"(oggi {costo_txt})",
                      "Negoziabile in 3-6 settimane"],
         "svantaggi": ["Costo su ogni fattura anticipata (da quotare con 2-3 istituti)",
                       "Richiede crediti 'bancabili': clienti solidi e fatture pulite",
                       "Può segnalare tensione ai clienti se gestita male (notifica)"],
         "costi": "Da quotare: tasso + commissioni per fattura (confrontare ≥2 offerte)",
         "rischi": "Dipendenza dallo strumento se non si corregge il ciclo di incasso",
         "tempi": "3-6 settimane",
         "complessita": "media",
         "dipendenze": "Istruttoria bancaria; qualità dei crediti",
         "quando_sceglierla": "Quando il capitale nei crediti è il fabbisogno principale "
                              "e i clienti sono solidi (concentrazione alta = crediti "
                              "grandi e anticipabili)",
         "quando_evitarla": "Se i crediti sono frammentati/contestati o i margini non "
                            "assorbono il costo dell'anticipo"},
        {"opzione": "C — Rinegoziare l'esposizione (consolidamento a medio termine)",
         "descrizione": "Trasformare lo scoperto permanente in un finanziamento a "
                        "medio termine con piano di rientro sostenibile.",
         "vantaggi": ["Riduce il costo del debito rispetto allo scoperto "
                      f"(oggi {costo_txt})",
                      "Toglie la spada del rientro a vista",
                      "Rende il fabbisogno esplicito e pianificabile"],
         "svantaggi": ["Cristallizza il debito: senza correzione delle cause, tra un "
                       "anno il problema si ripresenta CON la rata in più",
                       "Richiede negoziazione e spesso garanzie"],
         "costi": "Tasso del finanziamento (da quotare); eventuali garanzie",
         "rischi": "Rata fissa su una cassa già in deficit se fatta prima di A",
         "tempi": "4-8 settimane",
         "complessita": "media-alta",
         "dipendenze": "Merito creditizio; disponibilità della banca; forecast credibile",
         "quando_sceglierla": "Quando lo scoperto è strutturale (lo è: vedi analisi) e "
                              "il forecast dimostra la sostenibilità della rata",
         "quando_evitarla": "Come PRIMA mossa isolata: consolidare senza toccare le "
                            "cause finanzia il problema, non lo risolve"},
    ]

    conclusione = (
        "Sequenza raccomandata: A subito (attacca le cause, costa zero), B in parallelo "
        "sui crediti dei clienti maggiori (ponte di liquidità al costo minore), C solo "
        "dopo, con un forecast credibile in mano"
        + (" — presentarsi in banca con il 13-settimane cambia il negoziato" if deficit
           else "")
        + ". Perché questa e non altre: B senza A cronicizza il costo dello smobilizzo; "
          "C da sola sposta il problema di 12 mesi; A da sola non copre il fabbisogno "
          "immediato. È la combinazione, nell'ordine, a funzionare.")

    return {"nota": "Nessun prodotto/istituto è prescritto: le condizioni vanno messe "
                    "a confronto su ≥2 offerte reali.",
            "opzioni": opzioni,
            "conclusione_motivata": conclusione,
            "source": "system_calculated"}


def recommend(id_: str, titolo: str, *, perche: str, perche_ora: str,
              perche_questa: str, perche_non_altre: str, chi: str, quando: str,
              con_quali_dati: str, cadenza: str, validazione: str,
              kpi_generati: list[str], decisore: str,
              soglie: list[dict] | None = None) -> dict:
    """Raccomandazione completa: 4 perché (spec §11) + dettaglio operativo (spec §8).
    Le soglie citate DEVONO portare la classificazione (spec §12)."""
    return {"id": id_, "titolo": titolo,
            "perche": perche, "perche_ora": perche_ora,
            "perche_questa": perche_questa, "perche_non_altre": perche_non_altre,
            "operativo": {"chi": chi, "quando": quando, "con_quali_dati": con_quali_dati,
                          "cadenza": cadenza, "validazione": validazione,
                          "kpi_generati": kpi_generati, "decisore": decisore},
            "soglie": soglie or []}


def soglia(valore: str, classificazione: str, nota: str = "") -> dict:
    """Soglia classificata (spec §12): mai un numero presentato come fatto."""
    assert classificazione in ("dato_aziendale", "benchmark", "best_practice",
                               "proposta_iniziale", "ipotesi"), classificazione
    return {"valore": valore, "classificazione": classificazione, "nota": nota}


def finance_recommendations(inputs: dict, insights: list[dict]) -> list[dict]:
    saldo = _ins(insights, "cash.saldo_mensile")
    capitale = _ins(insights, "wc.capitale_in_crediti")
    costo = _ins(insights, "debt.costo_scoperto")
    out: list[dict] = []

    if saldo is not None:
        out.append(recommend(
            "rec.forecast_13w", "Adottare il forecast di cassa a 13 settimane",
            perche="La cassa oggi si scopre a consuntivo: il deficit "
                   f"({abs(saldo['valore']):,.0f} €/mese) si manifesta come emergenza "
                   .replace(",", ".") + "invece che come previsione.",
            perche_ora="Ogni mese senza forecast è un mese di interessi evitabili e di "
                       "negoziazione bancaria al buio; il file è già pronto nell'Excel "
                       "allegato: il costo di partenza è un'ora a settimana.",
            perche_questa="Il 13-settimane è lo standard di tesoreria per PMI: orizzonte "
                          "abbastanza lungo da anticipare, abbastanza corto da essere "
                          "credibile.",
            perche_non_altre="Un budget annuale non vede le settimane in cui la cassa "
                             "sfonda; un forecast giornaliero è ingestibile per 18 "
                             "persone senza CFO.",
            chi="Amministrazione (compila), titolare (valida)",
            quando="Prima versione entro 7 giorni",
            con_quali_dati="Scadenzario clienti/fornitori, rate, stipendi, F24",
            cadenza="Aggiornamento ogni lunedì (30-60 minuti)",
            validazione="Confronto previsto/consuntivo a fine settimana; scostamenti "
                        ">10% analizzati",
            kpi_generati=["Saldo minimo previsto a 13 settimane",
                          "Prima settimana negativa", "Scostamento previsto/consuntivo"],
            decisore="Titolare",
            soglie=[soglia("scostamento 10%", "proposta_iniziale",
                           "Soglia iniziale proposta, da validare dopo 30 giorni di "
                           "misurazione.")]))

    if capitale is not None:
        out.append(recommend(
            "rec.ciclo_incasso", "Comprimere il ciclo di incasso",
            perche=f"~{capitale['valore']:,.0f} € del capitale aziendale sono fermi "
                   .replace(",", ".") + "nei crediti: l'azienda finanzia i clienti"
                   + (f" pagando ~{costo['valore']:.0f}%/anno alla banca per farlo"
                      if costo else "") + ".",
            perche_ora="È la leva più grande e più economica disponibile: ogni giorno "
                       "di DSO in meno è cassa liberata senza costi finanziari.",
            perche_questa="Attacca la causa del fabbisogno; le alternative (più fido, "
                          "consolidamento) finanziano l'effetto.",
            perche_non_altre="Aumentare il fido a parità di ciclo di incasso aumenta "
                             "solo gli interessi; tagliare i costi non risolve un "
                             "problema che è di TEMPI, non di volumi.",
            chi="Amministrazione con owner unico dei crediti; commerciale sui top client",
            quando="Avvio entro 2 settimane",
            con_quali_dati="Aging crediti per cliente (foglio dedicato nell'Excel)",
            cadenza="Revisione aging settimanale; sollecito dal giorno 1 di ritardo",
            validazione="DSO misurato mensilmente; obiettivo definito DOPO 30 giorni "
                        "di misurazione reale",
            kpi_generati=["DSO", "Percentuale crediti oltre 30gg", "Incassato/fatturato"],
            decisore="Titolare",
            soglie=[soglia("sollecito dal giorno 1", "best_practice"),
                    soglia("obiettivo DSO", "ipotesi",
                           "Da fissare solo dopo 30 giorni di misurazione: oggi "
                           "mancherebbe la base dati.")]))

    return out
