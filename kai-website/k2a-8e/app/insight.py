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
}

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
