"""MCP server entrypoint — k2a-elettrico v0.2.

13 tool:
  AC base (8 v0.1):
    dimensiona_cavo, caduta_tensione, corto_circuito, verifica_protezione,
    dispersore_terra, verifica_terra, lookup_cei, list_clausole
  DC (5 v0.2):
    caduta_tensione_dc, corto_circuito_dc, stringa_fv, bess_runtime, srb_tlc
  Speciali AC (3 v0.2):
    valuta_rischio_fulmine, calcola_illuminamento, progetta_wallbox
"""
from __future__ import annotations
import asyncio
import json
from typing import Any

from pydantic import BaseModel, Field
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .cavo import DimensionaCavoInput, dimensiona_cavo
from .caduta_v import CadutaVInput, caduta_tensione
from .cortocircuito import CortoCircuitoInput, corto_circuito
from .protezione import VerificaProtezioneInput, verifica_protezione
from .terra import DispersoreTerraInput, VerificaTerraInput, dispersore_terra, verifica_terra
from .lookup_cei import LookupCeiInput, ListClausoleInput, lookup_cei, list_clausole
from .dc import (
    CadutaVDCInput, CortoCircuitoDCInput, StringaFVInput, BessRuntimeInput, SrbTlcInput,
    caduta_tensione_dc, corto_circuito_dc, stringa_fv, bess_runtime, srb_tlc,
)
from .lps_fulmini import ValutazioneRischioFulmineInput, valuta_rischio_fulmine
from .illuminazione import IlluminamentoLumenInput, calcola_illuminamento
from .wallbox_ev import WallboxEVInput, progetta_wallbox
from .cabina_mt import (
    DimensionaTrafoInput, IccCabinaMTInput, SelettivitaInput,
    dimensiona_trafo, calcola_icc_cabina, verifica_selettivita,
)
from .icc_multisorgente import (
    IccMultisorgenteInput, icc_bt_multisorgente,
)
from .coordinamento_ats import (
    CoordinamentoATSInput, coordinamento_ats_fv_generatore,
)
from .parser_partenze import (
    ParserPartenzeInput, parser_partenze_quadro,
)
from .quadro_termico import (
    VerificaQuadroTermicoInput, verifica_quadro_61439_iec60890,
)
from .selettivita_catena import (
    VerificaSelettivitaCatenaInput, verifica_selettivita_catena,
)
from .parallelo_trafi import ParalleloTrafiInput, parallelo_trafi_circolazione
from .ups import UpsDimensionaInput, dimensiona_ups
from .spi_fv import SpiCei021Input, verifica_spi_cei_021
from .protezioni_mt import (
    ProtezioneGeneraleMTInput, verifica_protezione_generale_mt,
    ProtezioneInterfacciaMTInput, verifica_protezione_interfaccia_mt,
)
from .guasto_terra_mt import CorrenteGuastoTerraMtInput, corrente_guasto_terra_mt
# --- consolidamento Fase MT (additivo): MT-A + MT-B ---
from .trasformatore import VerificaTrafoInput, verifica_trasformatore_mtbt
from .conformita_dg_pg import ConformitaDgPgInput, conformita_dg_pg
# --- DB articoli (additivo): MT-E1 ---
from .query_articoli import QueryArticoliInput, query_articoli
# --- selezione apparato + selettivita' da tabella (additivo): MT-E2 ---
from .seleziona_apparato import SelezionaApparatoInput, seleziona_apparato
from .verifica_selettivita import VerificaSelettivitaTabellaInput, verifica_selettivita_tabella
from .spd_coordinato import SpdCoordinatoInput, verifica_spd_coordinato
from .excel_quadro import ExcelQuadroInput, genera_excel_quadro
from .relazione_docx import RelazioneDocxInput, genera_relazione_docx
from .assembla_allegato import AssembleAllegatoInput, assembla_allegato_asseverativo
from .suggerisci_tool import SuggerisciToolInput, suggerisci_tool_da_paragrafo
from .generatori_cad.unifilare_svg import GeneraUnifilareInput, genera_unifilare_svg
from .generatori_cad.layout_dxf import GeneraLayoutDxfInput, genera_layout_dxf
from .generatori_cad.computo_xlsx import GeneraComputoMetricoInput, genera_computo_metrico_xlsx
from .decisionali import (
    SelezionaProtezioneInput, seleziona_protezione_partenza,
    DimensionaQuadroInput, dimensiona_quadro_partenze,
    ProgettaCabinaInput, progetta_cabina_topologia,
    CoordinaProtezioniInput, coordina_protezioni_automatico,
)
from .progettisti import (
    ProgettistaCabinaInput, progettista_cabina,
    ProgettistaQuadroInput, progettista_quadro,
    CoordinatoreProtezioniInput, coordinatore_protezioni,
)
from .audit_pe import AuditPEInput, audit_coerenza_pe
from .audit_pe_fs import audit_cartella as _audit_cartella
from .valida_pe_pre_esterna import (
    ValidaPEPreEsternaInput, valida_pe_pre_esterna,
)


class AuditCartellaInput(BaseModel):
    cartella: str = Field(..., description="Percorso cartella PE (docx/xlsx/pdf, ricorsivo)")
    punto_consegna: str = Field("MT", description="MT|BT")
    token_obsoleti: list[str] = Field(default_factory=list)
    limite_UE_V: float = 200.0


def _audit_cartella_tool(inp: "AuditCartellaInput") -> dict:
    return _audit_cartella(inp.cartella, inp.punto_consegna, inp.token_obsoleti, inp.limite_UE_V)


server: Server = Server("k2a-elettrico")


def _w(fn, model):
    return lambda a: json.dumps(fn(model(**a)).model_dump(), indent=2)


_TOOLS = [
    # --- AC base ---
    ("dimensiona_cavo", "Sezione min Cu CEI-UNEL 35024/1 + coordinamento 433.1.",
     DimensionaCavoInput, _w(dimensiona_cavo, DimensionaCavoInput)),
    ("caduta_tensione", "ΔV% trifase/monofase, CEI 64-8 art.525 (≤4%).",
     CadutaVInput, _w(caduta_tensione, CadutaVInput)),
    ("corto_circuito", "Icc trifase/monofase F-PE, metodo impedenze IEC 60909.",
     CortoCircuitoInput, _w(corto_circuito, CortoCircuitoInput)),
    ("verifica_protezione", "Coordinamento Ib≤In≤Iz + I²t≤k²S² (CEI 64-8 433/434).",
     VerificaProtezioneInput, _w(verifica_protezione, VerificaProtezioneInput)),
    ("dispersore_terra", "Re dispersore (Sunde): picchetto/corda/anello/piastra. CEI 64-12.",
     DispersoreTerraInput, _w(dispersore_terra, DispersoreTerraInput)),
    ("verifica_terra", "TT (RA·Idn≤U_lim) o TN (Zs·Ia≤U0). CEI 64-8 art.411.",
     VerificaTerraInput, _w(verifica_terra, VerificaTerraInput)),
    ("lookup_cei", "Clausola normativa puntuale (12 clausole).",
     LookupCeiInput, lambda a: json.dumps(lookup_cei(LookupCeiInput(**a)), indent=2)),
    ("list_clausole", "Elenca clausole disponibili.",
     ListClausoleInput, lambda a: json.dumps(list_clausole(ListClausoleInput(**a)), indent=2)),

    # --- DC ---
    ("caduta_tensione_dc", "ΔV DC = 2·L·ρ·I/S. FV/TLC -48V/BESS.",
     CadutaVDCInput, _w(caduta_tensione_dc, CadutaVDCInput)),
    ("corto_circuito_dc", "Icc DC: batteria (V/R) o FV (1.25·Isc·Nstr).",
     CortoCircuitoDCInput, _w(corto_circuito_dc, CortoCircuitoDCInput)),
    ("stringa_fv", "Nserie moduli FV da Voc(Tmin)/Vmpp(Tmax) + range MPPT inverter.",
     StringaFVInput, _w(stringa_fv, StringaFVInput)),
    ("bess_runtime", "Autonomia batterie da capacità, DoD, η_inverter.",
     BessRuntimeInput, _w(bess_runtime, BessRuntimeInput)),
    ("srb_tlc", "Cantieri TLC -48V DC: sezione cavo + batterie tampone (ETSI EN 300 132-2).",
     SrbTlcInput, _w(srb_tlc, SrbTlcInput)),

    # --- Speciali AC ---
    ("valuta_rischio_fulmine", "CEI EN 62305-2 semplificata: R1 vs RT, livello LPL.",
     ValutazioneRischioFulmineInput, _w(valuta_rischio_fulmine, ValutazioneRischioFulmineInput)),
    ("calcola_illuminamento", "Metodo lumen UNI EN 12464: n.apparecchi richiesti.",
     IlluminamentoLumenInput, _w(calcola_illuminamento, IlluminamentoLumenInput)),
    ("progetta_wallbox", "Ricarica EV CEI 64-8/722: cavo, magnetotermico, RCD, SPD.",
     WallboxEVInput, _w(progetta_wallbox, WallboxEVInput)),

    # --- Cabine MT/BT (v0.3) ---
    ("dimensiona_trafo", "Dimensiona trafo MT/BT da P_carico + cosφ + contemporaneità + margine futuro (CEI EN 60076).",
     DimensionaTrafoInput, _w(dimensiona_trafo, DimensionaTrafoInput)),
    ("calcola_icc_cabina", "Icc lato MT e BT cabina + Z_rete + Z_trafo (IEC 60909 / CEI 11-25).",
     IccCabinaMTInput, _w(calcola_icc_cabina, IccCabinaMTInput)),
    ("icc_bt_multisorgente",
     "Icc trifase BT multi-sorgente IEC 60909-0:2016 — rete DSO MT + N trafi paralleli, "
     "Ik3max (c_max=1.10, vcc tol−) e Ik3min (c_min=0.95, vcc tol+), Ipk con κ reale.",
     IccMultisorgenteInput, _w(icc_bt_multisorgente, IccMultisorgenteInput)),
    ("coordinamento_atrs_fv_generatore",
     "Coordinamento ATS multi-sorgente (rete+GE+FV): 3 sequenze (mancanza rete, "
     "cortocircuito, riconnessione), SPI/SPG CEI 0-21, ATS CEI 64-8 §551, "
     "dimensionamento GE + autonomia, diagramma temporale.",
     CoordinamentoATSInput, _w(coordinamento_ats_fv_generatore, CoordinamentoATSInput)),
    ("parser_partenze_quadro",
     "Parser robusto descrizioni testuali partenze quadro elettrico (CEI EN 61439-1/2). "
     "Estrae In, tipo (ACB/MCCB/MCB), Icu, poli, sganciatore (LSIG/LSI/LI), ZSI, "
     "flag motorizzato/estraibile, differenziale. Gestisce punto migliaia italiano.",
     ParserPartenzeInput, _w(parser_partenze_quadro, ParserPartenzeInput)),
    ("verifica_quadro_61439_iec60890",
     "Verifica termica quadri BT secondo IEC 60890 / CEI EN 61439-1 §10.10.4.2. "
     "Calcola ΔT a metà altezza e sommità da P dissipata + Ae enclosure. "
     "Database perdite ABB/Schneider, fattori b per installazione, fattori k/d/c/x da norma. "
     "Limiti tab.6 (sbarre 65K, morsetti 70K). Warning per quadri > 1600 A.",
     VerificaQuadroTermicoInput, _w(verifica_quadro_61439_iec60890, VerificaQuadroTermicoInput)),
    ("verifica_selettivita_catena",
     "Verifica selettività cronometrica + amperometrica su catena ordinata di N livelli "
     "(DSO → MT_protezione → ACB_BT → MCCB_BT). CEI 0-16:2022 §8.5 + CEI 64-8 §536. "
     "Supporto ZSI con Δt ridotto (50ms vs 200ms). Output: coppie analizzate + raccomandazioni.",
     VerificaSelettivitaCatenaInput, _w(verifica_selettivita_catena, VerificaSelettivitaCatenaInput)),
    ("verifica_selettivita", "Selettività cronometrica + amperometrica relè monte/valle (CEI 11-27).",
     SelettivitaInput, _w(verifica_selettivita, SelettivitaInput)),
    ("parallelo_trafi_circolazione",
     "Parallelo di 2 trafi MT/BT su sbarra comune (CEI EN 60076-8): verifica condizioni "
     "(gruppo, rapporto, vcc, potenze), corrente di circolazione da disallineamento rapporto, "
     "ripartizione carico ∝ Sn/vcc e verifica sovraccarico per trafo.",
     ParalleloTrafiInput, _w(parallelo_trafi_circolazione, ParalleloTrafiInput)),

    # --- UPS (v0.3) ---
    ("dimensiona_ups", "UPS static/dynamic: Sn, batterie, autonomia, ridondanza N/N+1/2N (IEC 62040).",
     UpsDimensionaInput, _w(dimensiona_ups, UpsDimensionaInput)),

    # --- DPI FV CEI 0-21 (v0.3) ---
    ("verifica_spi_cei_021", "Sistema Protezione Interfaccia FV: soglie 27/59/81, tempi, documentazione (CEI 0-21:2022).",
     SpiCei021Input, _w(verifica_spi_cei_021, SpiCei021Input)),

    # --- Protezioni MT utente attivo CEI 0-16 (v0.4) ---
    ("verifica_protezione_generale_mt",
     "Sistema di Protezione Generale (SPG/PG) MT utente attivo CEI 0-16 §8.8 + All.2b Tab.1: "
     "max corrente 51 (51.S1 NIT / 51.S2), omopolare 51N (1 soglia neutro isolato / 2 con impedenza), "
     "direzionale di terra 67N (se rete cavo >400m@20kV / >533m@15kV), coordinamento con PG del DSO.",
     ProtezioneGeneraleMTInput, _w(verifica_protezione_generale_mt, ProtezioneGeneraleMTInput)),
    ("verifica_protezione_interfaccia_mt",
     "Sistema di Protezione di Interfaccia (SPI) MT CEI 0-16 §8.8.7.2 Tab.12 + All.2b Tab.2: "
     "soglie tensione 27/59 (0,85/1,10/1,20 Un), frequenza 81 (49,8/50,2/47,5/51,5 Hz restrittive/permissive), "
     "anti-islanding (LoM), tempo apertura DDI (+70ms MT / +100ms BT), tolleranza ±3%.",
     ProtezioneInterfacciaMTInput, _w(verifica_protezione_interfaccia_mt, ProtezioneInterfacciaMTInput)),
    ("corrente_guasto_terra_mt",
     "Corrente di guasto monofase a terra Ig in reti MT (CEI 0-16 §5.2.1.7): 3 modalità "
     "(dati_dso_dichiarati firmabile / neutro_isolato_puro formula empirica / stima_letteratura "
     "indicativa). Opz. catena Ig→U_E se R_terra fornita. Flag firmabilità esplicito.",
     CorrenteGuastoTerraMtInput, _w(corrente_guasto_terra_mt, CorrenteGuastoTerraMtInput)),

    # --- consolidamento Fase MT (additivo): MT-A trasformatore + MT-B conformità DG/PG ---
    ("verifica_trasformatore_mtbt",
     "Trafo MT/BT: In lato MT/BT + Icc presunta lato BT (CEI EN 60076 / IEC 60909, rete a monte infinita). Trace ricco.",
     VerificaTrafoInput, _w(verifica_trasformatore_mtbt, VerificaTrafoInput)),
    ("conformita_dg_pg",
     "Conformità DG/PG/PI a CEI 0-16: confronta tarature impostate + regolazione DSO vs fact-file groundato. Esito per funzione + citazione + trace ricco.",
     ConformitaDgPgInput, _w(conformita_dg_pg, ConformitaDgPgInput)),
    ("query_articoli",
     "DB articoli (MT-E1): cerca articoli di catalogo per requisito (costruttore, tipo, In, curva, poli, potere Icn). "
     "Dati REALI da datasheet con fonte dichiarata per articolo; nessun valore inventato. Niente selettività/filiazione.",
     QueryArticoliInput, _w(query_articoli, QueryArticoliInput)),
    ("seleziona_apparato",
     "Selezione apparato (MT-E2): dato il requisito da dimensiona_cavo (In>=, curva, potere>=Icc) propone gli articoli "
     "REALI del DB che lo soddisfano, ordinati dal più piccolo adeguato, ognuno con fonte. Nessun valore inventato.",
     SelezionaApparatoInput, _w(seleziona_apparato, SelezionaApparatoInput)),
    ("verifica_selettivita_da_tabella",
     "Selettività/filiazione (MT-E2) da TABELLE REALI del costruttore: date due apparecchiature (monte/valle), "
     "restituisce l'esito (totale/limite kA) con fonte (tabella+revisione) e trace. Coppia assente in tabella = GAP "
     "dichiarato, MAI esito inventato; nessun valore dal modello. Distinto da 'verifica_selettivita' (basato su calcolo).",
     VerificaSelettivitaTabellaInput, _w(verifica_selettivita_tabella, VerificaSelettivitaTabellaInput)),

    # --- SPD coordinato (v0.3) ---
    ("verifica_spd_coordinato", "SPD tipo 1+2+3, distanza max protezione, coordinamento Up vs Uw apparato (CEI 81-30).",
     SpdCoordinatoInput, _w(verifica_spd_coordinato, SpdCoordinatoInput)),

    # --- Output asseverabili (v0.3) ---
    ("genera_excel_quadro", "Excel quadro multi-circuito con dim+ΔV+protezione per ogni circuito.",
     ExcelQuadroInput, _w(genera_excel_quadro, ExcelQuadroInput)),
    ("genera_relazione_docx", "Relazione di calcolo DOCX asseverabile da N sezioni di calcolo MCP.",
     RelazioneDocxInput, _w(genera_relazione_docx, RelazioneDocxInput)),
    ("assembla_allegato_asseverativo",
     "Assembla Allegato H di asseverazione indipendente (DOCX + JSON) da N sezioni di verifica, "
     "per qualunque progetto elettrico (civile/industriale/TLC). Frontespizio, sintesi esecutiva, "
     "una pagina per verifica (metodologia, parametri, risultati K2A vs PE, esito, raccomandazioni), "
     "raccomandazioni aggregate, dichiarazione asseverativa. Esito complessivo derivato.",
     AssembleAllegatoInput, _w(assembla_allegato_asseverativo, AssembleAllegatoInput)),

    # --- Generatori CAD (Tappa 3 §5.3.2) ---
    ("genera_unifilare_svg",
     "Schema unifilare SVG da topologia Layer 3 (sorgenti→trafo→quadri→linee). "
     "Simboli IEC 60617 semplificati, etichette con grandezze calcolate. Dep opzionale svgwrite.",
     GeneraUnifilareInput, _w(genera_unifilare_svg, GeneraUnifilareInput)),
    ("genera_layout_dxf",
     "Planimetria DXF SCHEMATICA da topologia (modalità schematica_auto). Layer MURI/"
     "ELEMENTI/QUOTE/TESTO/LEGENDA. NON architettonica (schema A–E privo coordinate). Dep ezdxf.",
     GeneraLayoutDxfInput, _w(genera_layout_dxf, GeneraLayoutDxfInput)),
    ("genera_computo_metrico_xlsx",
     "Computo metrico XLSX (lista materiali) da topologia: cavi/protezioni/trafo/quadri/"
     "terra/SPD, raggruppati per categoria o linea. Senza prezzi (no catalogo). openpyxl.",
     GeneraComputoMetricoInput, _w(genera_computo_metrico_xlsx, GeneraComputoMetricoInput)),

    # --- Tool decisionali (§5.2.3) ---
    ("seleziona_protezione_partenza",
     "Suggerisce In/curva/Icu/differenziale/poli per una partenza da Ib+Iz+Icc+carico+ambiente "
     "(CEI 64-8 433/434/415). Decisionale: suggerimento da validare.",
     SelezionaProtezioneInput, _w(seleziona_protezione_partenza, SelezionaProtezioneInput)),
    ("dimensiona_quadro_partenze",
     "Suggerisce forma di segregazione, In sbarra/generale, n.moduli/file, IP da una lista "
     "di partenze (CEI EN 61439-1/2).",
     DimensionaQuadroInput, _w(dimensiona_quadro_partenze, DimensionaQuadroInput)),
    ("progetta_cabina_topologia",
     "Suggerisce n.trafi, Sn, ridondanza (N/N+1/2N), GE+ATS da bilancio potenza + continuità "
     "richiesta (CEI 0-16/99-2).",
     ProgettaCabinaInput, _w(progetta_cabina_topologia, ProgettaCabinaInput)),
    ("coordina_protezioni_automatico",
     "Suggerisce le tarature dei tempi per selettività cronometrica su una catena di protezioni "
     "(con opzione ZSI) + check selettività amperometrica (CEI 64-8 §536).",
     CoordinaProtezioniInput, _w(coordina_protezioni_automatico, CoordinaProtezioniInput)),

    # --- Orchestratori decisionali (§5.3.1) ---
    ("progettista_cabina",
     "Orchestratore: da bilancio potenza + continuità produce bozza cabina integrata "
     "(topologia + trafo + Icc + protezione generale). Compone più tool. Bozza da validare.",
     ProgettistaCabinaInput, _w(progettista_cabina, ProgettistaCabinaInput)),
    ("progettista_quadro",
     "Orchestratore: da lista partenze (Ib/Iz/Icc/carico) produce tabella protezioni "
     "selezionate + dati quadro (forma/sbarra/moduli). Compone più tool. Bozza da validare.",
     ProgettistaQuadroInput, _w(progettista_quadro, ProgettistaQuadroInput)),
    ("coordinatore_protezioni",
     "Orchestratore: da catena di protezioni produce piano di tarature integrato "
     "(tempi selettività + check amperometrico). Bozza da validare.",
     CoordinatoreProtezioniInput, _w(coordinatore_protezioni, CoordinatoreProtezioniInput)),

    # --- Audit coerenza PE (controllo finale documento) ---
    ("audit_coerenza_pe",
     "Linter documentale per Progetti Esecutivi: rileva norma di connessione errata (POD MT→CEI 0-16), "
     "tensione di contatto UE oltre il limite, e token obsoleti residui. Alta precisione, "
     "controllo finale prima della consegna.",
     AuditPEInput, _w(audit_coerenza_pe, AuditPEInput)),
    ("audit_pe_cartella",
     "Audit di coerenza su un'INTERA cartella PE (docx+xlsx+pdf, ricorsivo): regole R2/R4/R5 "
     "testuali + R6 somme computo (xlsx) + R7 riferimenti indice + R8 nomenclatura. PDF scansionati "
     "saltati con warning.",
     AuditCartellaInput,
     lambda a: json.dumps(_audit_cartella_tool(AuditCartellaInput(**a)), indent=2, default=str)),
    ("valida_pe_pre_esterna",
     "GATE OBBLIGATORIO prima della validazione esterna. Esegue L1-L7: linter per-file, "
     "audit cartella cross-file, pattern semantici incident-database (18 regole CEI/IEC/DPR), "
     "coerenza versioni, de-anonimizzazione fornitore, riserve dichiarate. Produce verbale .docx "
     "di validazione interna firmabile. Il gate è APERTO solo con 0 ERROR. ADR-034.",
     ValidaPEPreEsternaInput, _w(valida_pe_pre_esterna, ValidaPEPreEsternaInput)),

    # --- KB -> Tool (Tappa 2 Fase 2) ---
    ("suggerisci_tool_da_paragrafo",
     "Direzione KB->Tool: dato un riferimento normativo (norma + paragrafo), suggerisce "
     "quali tool MCP del principale sono applicabili, con motivazione e contesto d'uso.",
     SuggerisciToolInput, _w(suggerisci_tool_da_paragrafo, SuggerisciToolInput)),
]


@server.list_tools()
async def _list() -> list[Tool]:
    return [Tool(name=n, description=d, inputSchema=s.model_json_schema()) for n, d, s, _ in _TOOLS]


@server.call_tool()
async def _call(name: str, args: dict[str, Any]) -> list[TextContent]:
    for n, _, _, fn in _TOOLS:
        if n == name:
            try:
                return [TextContent(type="text", text=fn(args))]
            except Exception as e:
                return [TextContent(type="text", text=json.dumps({"error": str(e), "tool": name}))]
    return [TextContent(type="text", text=json.dumps({"error": f"Tool '{name}' non trovato."}))]


async def _run() -> None:
    async with stdio_server() as (r, w):
        await server.run(r, w, server.create_initialization_options())


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
