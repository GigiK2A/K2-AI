"""MCP server entrypoint — k2a-catalogo (ex k2a-agevolazioni; package interno invariato).

Fase 1 — motore agevolazioni deterministico per PMI italiane:
  - de_minimis_plafond           (Reg. UE 2023/2831)
  - transizione_5_0              (DL 19/2024 art.38 + LdB 2025)
  - nuova_sabatini               (L. 98/2013 art.2)
  - credito_rd_innovazione       (L. 160/2019 commi 198-209)
  - cumulabilita_e_finanziabile  (divieto doppio finanziamento + incompatibilità)
  - indici_bancabilita           (screening merito creditizio / fido commerciale)
  - riclassifica_bilancio        (bilancio CEE → SP finanziario + CE valore aggiunto)
  - scoring_crisi_cndcec         (indizi di crisi: PN<0 / DSCR 6m / 5 indici settoriali)

Marketing & SEO — TRASVERSALI (tool deterministici dove c'è calcolo oggettivo):
  - audit_seo_onpage             (title/meta/densità/Gulpease/H1/alt → score A-D)
  - metriche_marketing           (CAC, LTV, LTV/CAC, payback, ROAS, ROI, break-even)
  - lista_settori_pmi            (tassonomia settori PMI per contestualizzare i servizi)
  - lista_abbonamenti            (piani Free/Pro/Business + crediti + consulenza)
  - scheda_listino               (prezzo/crediti/sconti di un prodotto — fonte di verità)
  - classifica_prodotto          (singolo vs Boost composito d'ufficio + prezzo)

Servizi SETTORIALI (calati sul comparto della PMI):
  - metriche_hospitality         (turismo/ricettività: RevPAR, ADR, occupazione, GOPPAR)
  - metriche_ristorazione        (food/ristorazione: food cost, prime cost, coperti, break-even)
  - metriche_retail              (commercio: margine, rotazione magazzino, GMROI, ricavo/mq)
  - metriche_ecommerce           (e-commerce: conversion, AOV, margine netto, reso, ROAS)
  - metriche_benessere           (benessere/estetica: utilizzo, retention, scontrino, ricavo/ora)

Documenti di consulenza (registro di template per tipologia, indice fisso per tipo):
  - genera_documento_consulenza      (documento singolo dalle sezioni)
  - componi_documento_da_risultato   (incapsula l'output di un tool — documento singolo)
  - componi_checkup                  (documento composito: aggrega più tool)
"""
from __future__ import annotations

import asyncio
import json
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .de_minimis import DeMinimisPlafondInput, de_minimis_plafond
from .transizione_5_0 import Transizione50Input, transizione_5_0
from .nuova_sabatini import NuovaSabatiniInput, nuova_sabatini
from .credito_rd import CreditoRDInput, credito_rd_innovazione
from .cumulabilita import CumulabilitaInput, cumulabilita_e_finanziabile
from .bancabilita import BancabilitaInput, indici_bancabilita
from .riclassifica import BilancioCEEInput, riclassifica_bilancio
from .crisi_cndcec import CrisiCNDCECInput, scoring_crisi_cndcec
from .seo import SeoOnPageInput, audit_seo_onpage
from .marketing import MarketingInput, metriche_marketing
from .settori import ListaSettoriInput, lista_settori_pmi
from .listino import (
    ListaAbbonamentiInput, lista_abbonamenti, SchedaListinoInput, scheda_listino,
    StatusCreditiInput, crediti_attivi,
    ListaPercorsiInput, lista_percorsi, SchedaPercorsoInput, scheda_percorso,
)
from .classifica import ClassificaProdottoInput, classifica_prodotto
from .hospitality import HospitalityInput, metriche_hospitality
from .ristorazione import RistorazioneInput, metriche_ristorazione
from .retail import RetailInput, metriche_retail
from .ecommerce import EcommerceInput, metriche_ecommerce
from .benessere import BenessereInput, metriche_benessere
from .documento import (
    DocumentoConsulenzaInput, genera_documento_consulenza,
    DocumentoDaRisultatoInput, componi_documento_da_risultato,
    CheckupInput, componi_checkup,
)


server: Server = Server("k2a-catalogo")


def _w(fn, model):
    return lambda a: json.dumps(fn(model(**a)).model_dump(mode="json"), indent=2, ensure_ascii=False)


_TOOLS = [
    ("de_minimis_plafond",
     "Plafond de minimis residuo su finestra mobile 3 anni (Reg. UE 2023/2831). "
     "Settori: generale 300k / SIEG 750k / agricoltura / pesca. Calcola usato, "
     "residuo, prossima data di liberazione plafond, e verifica capienza nuovo aiuto.",
     DeMinimisPlafondInput, _w(de_minimis_plafond, DeMinimisPlafondInput)),
    ("transizione_5_0",
     "Credito d'imposta Transizione 5.0 (DL 19/2024 art.38 + LdB 2025). Calcola il "
     "credito per scaglioni di investimento in funzione della fascia di risparmio "
     "energetico (struttura 3/6/10% o processo 5/10/15%).",
     Transizione50Input, _w(transizione_5_0, Transizione50Input)),
    ("nuova_sabatini",
     "Contributo Nuova Sabatini (L. 98/2013 art.2): somma quote interessi di un "
     "ammortamento quinquennale a tasso convenzionale (ordinario 2,75% / 4.0-green "
     "3,575%). Restituisce piano di ammortamento e contributo totale.",
     NuovaSabatiniInput, _w(nuova_sabatini, NuovaSabatiniInput)),
    ("credito_rd_innovazione",
     "Credito d'imposta R&S / Innovazione tecnologica / Innovazione 4.0-green / "
     "Design (L. 160/2019 commi 198-209). Credito = min(spese; massimale) x aliquota.",
     CreditoRDInput, _w(credito_rd_innovazione, CreditoRDInput)),
    ("cumulabilita_e_finanziabile",
     "Verifica la cumulabilità di più agevolazioni sui medesimi costi: intensità "
     "totale ≤ 100% del costo (divieto doppio finanziamento), incompatibilità note "
     "(es. Transizione 5.0 vs 4.0/ZES) e importo residuo finanziabile.",
     CumulabilitaInput, _w(cumulabilita_e_finanziabile, CumulabilitaInput)),
    ("indici_bancabilita",
     "Screening del merito creditizio di un'impresa: calcola gli indici di bilancio "
     "usati dalle banche (PFN/EBITDA, DSCR, interest coverage, indipendenza finanziaria, "
     "leverage, current/quick ratio, redditività) con soglie di prassi, punteggio 0-100 "
     "e classe A/B/C/D. Doppia finalità: autovalutazione per finanziamento bancario o "
     "valutazione di un cliente per dilazione di pagamento. Segnala indizi di crisi "
     "(art. 3 D.Lgs. 14/2019).",
     BancabilitaInput, _w(indici_bancabilita, BancabilitaInput)),
    ("riclassifica_bilancio",
     "Riclassifica un bilancio CEE (artt. 2424/2425 c.c.) in Stato Patrimoniale a "
     "criterio finanziario e Conto Economico a valore aggiunto. Calcola valore aggiunto, "
     "EBITDA, EBIT, utile netto, PFN, margini patrimoniali (CCN, tesoreria, struttura), "
     "verifica la quadratura attivo=passivo e produce il blocco 'bancabilita_input' "
     "pronto per il tool indici_bancabilita.",
     BilancioCEEInput, _w(riclassifica_bilancio, BilancioCEEInput)),
    ("scoring_crisi_cndcec",
     "Screening degli indizi di crisi d'impresa (impianto CNDCEC, art. 13 D.Lgs. "
     "14/2019): patrimonio netto negativo, DSCR a 6 mesi e i 5 indici settoriali "
     "(che devono superare le soglie congiuntamente). Riferimento tecnico, non "
     "accertamento automatico (sistema soglie superato dal D.Lgs. 83/2022).",
     CrisiCNDCECInput, _w(scoring_crisi_cndcec, CrisiCNDCECInput)),
    ("audit_seo_onpage",
     "Audit SEO on-page deterministico: lunghezza title/meta, presenza e densità "
     "della keyword target, leggibilità del testo (indice Gulpease per l'italiano), "
     "unicità H1 e copertura attributi alt. Punteggio 0-100, classe A/B/C/D e "
     "raccomandazioni puntuali.",
     SeoOnPageInput, _w(audit_seo_onpage, SeoOnPageInput)),
    ("metriche_marketing",
     "Unit economics di marketing: CAC, LTV, rapporto LTV/CAC, payback del CAC, "
     "ROAS, ROI e break-even. Confronto con benchmark di prassi (LTV/CAC≥3, "
     "payback≤12 mesi) e raccomandazioni.",
     MarketingInput, _w(metriche_marketing, MarketingInput)),
    ("lista_settori_pmi",
     "Elenca i settori industriali delle PMI (tassonomia ATECO adattata) su cui si "
     "applicano i servizi trasversali (marketing, SEO, finanza, agevolazioni). Usare "
     "l'id del settore nel campo 'settore' dei documenti per contestualizzarli al comparto.",
     ListaSettoriInput, _w(lista_settori_pmi, ListaSettoriInput)),
    ("lista_abbonamenti",
     "Listino degli abbonamenti K2-AI (Free/Pro 49€/Business 149€), pacchetti di "
     "crediti e gradino consulenza umana. Iscrizione gratuita ma i servizi richiedono "
     "almeno il piano Pro (consumano API). UNICA fonte di verità sui piani.",
     ListaAbbonamentiInput, _w(lista_abbonamenti, ListaAbbonamentiInput)),
    ("scheda_listino",
     "Dato un prodotto del catalogo, restituisce strato, prezzo di listino, costo in "
     "crediti e il prezzo effettivo per ciascun piano di abbonamento (sconto Boost). "
     "USARE SEMPRE questo tool per il prezzo: NON inventare i prezzi.",
     SchedaListinoInput, _w(scheda_listino, SchedaListinoInput)),
    ("crediti_attivi",
     "Verifica L2-Inattività: dati la data dell'ultima attività del cliente e la data "
     "odierna, dice se i crediti sono ancora attivi o decaduti. I crediti NON scadono a "
     "data fissa, decadono solo dopo 12 mesi di inattività totale (MASTERPLAN §3.6, D-013). "
     "Funzione pura: la data odierna è input esplicito.",
     StatusCreditiInput, _w(crediti_attivi, StatusCreditiInput)),
    ("lista_percorsi",
     "Task #8 — Modello 1 Boost-a-percorsi: elenco compatto dei percorsi disponibili "
     "(id, destinazione, sconto-percorso, n. tappe). Un percorso è la sequenza ordinata "
     "di tappe che porta a un Boost destinazione, con somma tappe < destinazione.",
     ListaPercorsiInput, _w(lista_percorsi, ListaPercorsiInput)),
    ("scheda_percorso",
     "Dato un percorso_id (es. 'advisorboost', 'controlboost', 'webboost', 'buildboost', "
     "'mepboost'), ritorna composizione completa: destinazione, sconto-percorso, lista "
     "tappe ordinate con label, prezzo_listino_eur e prezzo_per_piano (sconto L3). "
     "Funzione pura sul catalogo statico.",
     SchedaPercorsoInput, _w(scheda_percorso, SchedaPercorsoInput)),
    ("classifica_prodotto",
     "Dato l'insieme di tool/aree usati per un deliverable, determina IN MODO "
     "DETERMINISTICO il prodotto corretto (Check express singolo vs Boost composito) "
     "e ne allega il prezzo. Regola: ≥2 componenti della stessa famiglia → Boost "
     "(Servizio), un solo componente → Check express (Consumo). USARE per non "
     "sotto-prezzare un advisory multi-misura come singolo check.",
     ClassificaProdottoInput, _w(classifica_prodotto, ClassificaProdottoInput)),
    ("metriche_hospitality",
     "[SETTORIALE turismo/ricettività] KPI di revenue management alberghiero (USALI): "
     "occupazione, ADR, RevPAR, TRevPAR, GOP/GOPPAR e occupazione di break-even. "
     "Confronto con benchmark orientativi e raccomandazioni.",
     HospitalityInput, _w(metriche_hospitality, HospitalityInput)),
    ("metriche_ristorazione",
     "[SETTORIALE ristorazione/food] Indicatori gestionali del locale: food cost, "
     "beverage cost, prime cost (food+beverage+personale), incidenza del personale, "
     "scontrino medio, margine di contribuzione per coperto e break-even coperti. "
     "Confronto con benchmark e raccomandazioni.",
     RistorazioneInput, _w(metriche_ristorazione, RistorazioneInput)),
    ("metriche_retail",
     "[SETTORIALE commercio/retail] Indicatori del punto vendita: margine commerciale, "
     "markup, rotazione di magazzino, giorni di giacenza, GMROI, ricavo per mq, "
     "sell-through, scontrino medio e break-even. Confronto con benchmark e raccomandazioni.",
     RetailInput, _w(metriche_retail, RetailInput)),
    ("metriche_ecommerce",
     "[SETTORIALE e-commerce] Indicatori dello shop online: conversion rate, AOV, "
     "ricavo per sessione, margine di contribuzione netto (al netto di COGS, "
     "spedizioni e commissioni), incidenza spedizioni/commissioni, tasso di reso e "
     "ROAS. Confronto con benchmark e raccomandazioni.",
     EcommerceInput, _w(metriche_ecommerce, EcommerceInput)),
    ("metriche_benessere",
     "[SETTORIALE benessere/estetica] Indicatori dei servizi alla persona (saloni, "
     "estetica, SPA, palestre): tasso di utilizzo capacità, scontrino medio, ricavo "
     "per ora-operatore, incidenza personale, retail mix, retention clienti e "
     "break-even. Confronto con benchmark e raccomandazioni.",
     BenessereInput, _w(metriche_benessere, BenessereInput)),
    ("genera_documento_consulenza",
     "Compone un documento di consulenza nel formato standard K2-AI, con indice "
     "degli argomenti SEMPRE identico (8 sezioni fisse). Le sezioni senza contenuto "
     "restano nell'indice come 'Non applicabile': la struttura non cambia mai. "
     "Produce anche il rendering markdown.",
     DocumentoConsulenzaInput, _w(genera_documento_consulenza, DocumentoConsulenzaInput)),
    ("componi_documento_da_risultato",
     "Incapsula l'output JSON di un qualunque tool del motore (de_minimis, "
     "transizione_5_0, indici_bancabilita, scoring_crisi_cndcec, ecc.) nel documento "
     "standard a indice invariante, mappandone automaticamente risultati, valutazioni, "
     "riferimenti normativi e avvertenze. Garantisce un output uniforme per ogni servizio.",
     DocumentoDaRisultatoInput, _w(componi_documento_da_risultato, DocumentoDaRisultatoInput)),
    ("componi_checkup",
     "Compone un documento COMPOSITO di check-up aggregando l'output di più tool "
     "(es. checkup_finanziario = riclassifica + bancabilità + crisi; checkup_agevolazioni "
     "= de minimis + 5.0 + Sabatini + R&S + cumulo). Indice dedicato a 9 sezioni "
     "(sintesi esecutiva, esiti per area, quadro indicatori, opportunità/criticità, "
     "piano d'azione). Riporta tier e prezzo a documento dal catalogo.",
     CheckupInput, _w(componi_checkup, CheckupInput)),
]


@server.list_tools()
async def _list() -> list[Tool]:
    return [
        Tool(name=name, description=desc, inputSchema=schema.model_json_schema())
        for name, desc, schema, _ in _TOOLS
    ]


@server.call_tool()
async def _call(name: str, args: dict[str, Any]) -> list[TextContent]:
    for n, _, _, fn in _TOOLS:
        if n == name:
            try:
                return [TextContent(type="text", text=fn(args))]
            except Exception as e:
                return [TextContent(type="text", text=json.dumps({"error": str(e), "tool": name}, ensure_ascii=False))]
    return [TextContent(type="text", text=json.dumps({"error": f"Tool '{name}' non trovato."}))]


async def _run() -> None:
    async with stdio_server() as (r, w):
        await server.run(r, w, server.create_initialization_options())


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
