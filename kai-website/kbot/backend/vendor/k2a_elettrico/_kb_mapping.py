"""Mapping tool -> paragrafi normativi della KB (k2a-mcp-norme-tecniche).

Snapshot statico (Tappa 2 Fase 1): i numeri d'articolo provengono dalle
dichiarazioni `trace`/`norma` dei tool stessi (fonte autoritativa, non da
memoria); il `testo_verbatim` è un estratto breve recuperato dalla KB al momento
della compilazione di questo snapshot (Fase 2: recupero dinamico on-demand).

Distinzioni oneste:
- `norma_in_kb`: la norma È caricata nella KB. Caricate: CEI 0-21/0-16/64-8 +
  CEI-UNEL 35024/1:1997-06 (sessione 15) + CEI EN 62305-2:2013 e IEC 61439-1:2020
  (sessione 16, via OCR: Gemini 2.5 Flash per 62305-2; OCR ibrido Gemini+Tesseract
  per 61439-1, perché Gemini rifiuta ~142 pagine del testo IEC protetto con
  finish_reason=RECITATION). La 61439-1 è l'edizione IEC in inglese.
- `testo_verbatim`: estratto breve se recuperabile in modo pulito, altrimenti None.
  Per CEI 64-8 alcuni articoli hanno section_code assente nel chunking DOCX
  (limitazione nota NT-2): il riferimento resta valido, il verbatim può mancare.
"""
from __future__ import annotations

# Norme effettivamente caricate nella KB norme-tecniche (al 22/05/2026).
NORME_IN_KB = {
    "CEI 0-21:2025-04", "CEI 0-16:2025-04", "CEI 64-8:2024",
    "CEI-UNEL 35024/1:1997-06",
    "CEI EN 62305-2:2013", "IEC 61439-1:2020",
    "NTC 2018", "Circolare 7/2019",
}

KB_REFERENCES_BY_TOOL: dict[str, list[dict]] = {
    "icc_bt_multisorgente": [
        {
            "norma": "CEI 0-16:2025-04", "paragrafo": "5.2.1.3",
            "titolo": "Corrente di cortocircuito trifase massima (dimensionamento apparecchiature)",
            "testo_verbatim": "Valore della corrente di cortocircuito assunta (pianificata) per la "
                              "scelta delle apparecchiature, è comunicato dal DSO all'Utente.",
            "contesto_uso": "Un_MT presente",
        },
        {
            "norma": "CEI 0-21:2025-04", "paragrafo": "5.1.2",
            "titolo": "Eliminazione dei guasti / correnti di cortocircuito rete BT",
            "testo_verbatim": None,
            "contesto_uso": "sempre",
        },
    ],
    "verifica_protezione": [
        {
            "norma": "CEI 64-8:2024", "paragrafo": "433.1",
            "titolo": "Coordinamento tra conduttori e dispositivi di protezione (sovraccarico)",
            "testo_verbatim": "IB è la corrente di impiego nel circuito; Iz è la portata continuativa "
                              "della conduttura; In è la corrente nominale del dispositivo di protezione.",
            "contesto_uso": "sempre",
        },
        {
            "norma": "CEI 64-8:2024", "paragrafo": "434.5.2",
            "titolo": "Caratteristiche dei dispositivi di protezione contro i cortocircuiti (I²t ≤ k²S²)",
            "testo_verbatim": None,  # art. con section_code assente nel chunking DOCX (NT-2)
            "contesto_uso": "tipo_connessione=cavo",
        },
        {
            "norma": "IEC 61439-1:2020", "paragrafo": "5.3.5",
            "titolo": "Rated short-time withstand current (Icw) of a main circuit of an assembly",
            "testo_verbatim": "The rated short-time withstand current (Icw) of a main circuit of an "
                              "assembly shall be equal to or higher than the prospective value of "
                              "the short-circuit current Icp at each point of connection to the "
                              "supply. For times up to a maximum of 3 s, the relationship between "
                              "Icw and the associated duration is given by I²t = constant, provided "
                              "the peak value does not exceed Ipk.",
            "contesto_uso": "tipo_connessione in [blindosbarra, sbarra_dedicata]",
        },
        {
            "norma": "IEC 61439-1:2020", "paragrafo": "9.3.2",
            "titolo": "Information concerning short-circuit withstand strength (declared values)",
            "testo_verbatim": "For assemblies with a SCPD incorporated in the incoming unit, the "
                              "assembly manufacturer shall declare the maximum allowable value of "
                              "the prospective short-circuit current at the input terminals; this "
                              "value shall not exceed the appropriate rating(s) (see 5.3.4, 5.3.5, "
                              "5.3.6).",
            "contesto_uso": "tipo_connessione in [blindosbarra, sbarra_dedicata]",
        },
    ],
    "dimensiona_cavo": [
        {
            "norma": "CEI 64-8:2024", "paragrafo": "523",
            "titolo": "Portate dei cavi in regime permanente",
            "testo_verbatim": "Iz è la portata continuativa della conduttura.",
            "contesto_uso": "sempre",
        },
        {
            "norma": "CEI 64-8:2024", "paragrafo": "433.1",
            "titolo": "Coordinamento sezione conduttura / protezione",
            "testo_verbatim": "Ib ≤ In ≤ Iz (coordinamento sovraccarico).",
            "contesto_uso": "In_protezione_fornita=True",
        },
        {
            "norma": "CEI-UNEL 35024/1:1997-06", "paragrafo": "2.1",
            "titolo": "Portate dei cavi e formula Iz = Io·k1·k2",
            "testo_verbatim": "La portata Iz di un cavo si ricava con Iz = Io·k1·k2, dove Io è la "
                              "portata in aria a 30°C (Tab. I/II), k1 il fattore di correzione per "
                              "temperatura ambiente ≠ 30°C (Tab. III), k2 il fattore per più circuiti "
                              "in fascio o strato (Tab. IV/V/VI).",
            "contesto_uso": "sempre",
        },
        {
            "norma": "CEI-UNEL 35024/1:1997-06", "paragrafo": "4.1",
            "titolo": "Fattore di correzione per circuiti in fascio o strato (k2)",
            "testo_verbatim": "Quando più circuiti in cavo sono installati nello stesso fascio o "
                              "strato, la portata deve essere moltiplicata per l'apposito fattore di "
                              "correzione dato nelle Tabelle IV, V o VI.",
            "contesto_uso": "sempre",
        },
    ],
    "caduta_tensione": [
        {
            "norma": "CEI 64-8:2024", "paragrafo": "525",
            "titolo": "Caduta di tensione negli impianti utilizzatori",
            "testo_verbatim": "Si raccomanda che la caduta di tensione tra l'origine dell'impianto "
                              "utilizzatore e qualunque apparecchio non superi il 4 %.",
            "contesto_uso": "sempre",
        },
    ],
    "valuta_rischio_fulmine": [
        {
            "norma": "CEI EN 62305-2:2013", "paragrafo": "4.2.1",
            "titolo": "Rischio R e tipi di perdita (R1 perdita di vite umane)",
            "testo_verbatim": "Il rischio R è la misura della probabile perdita media annua. I rischi "
                              "da valutare in una struttura possono essere: R1 rischio di perdita di "
                              "vite umane; R2 perdita di servizio pubblico; R3 perdita di patrimonio "
                              "culturale insostituibile; R4 perdita economica.",
            "contesto_uso": "sempre",
        },
        {
            "norma": "CEI EN 62305-2:2013", "paragrafo": "C.2",
            "titolo": "Valutazione della perdita LX (costanti Lt, Lf, Lo) — Allegato C",
            "testo_verbatim": "I valori di Lt, Lf e Lo possono essere valutati mediante la relazione "
                              "approssimata LX = (np/nt)·(tp/8760), dove np è il numero di possibili "
                              "vittime, nt il numero atteso di persone, tp il tempo annuo di presenza "
                              "nel luogo pericoloso. Valori medi tipici in Tabella C.1.",
            "contesto_uso": "sempre",
        },
    ],
    "verifica_protezione_generale_mt": [
        {
            "norma": "CEI 0-16:2025-04", "paragrafo": "ALLEGATO_2b",
            "titolo": "Taratura del Sistema di Protezione Generale (SPG) — Tabella 1",
            "testo_verbatim": "La protezione di massima corrente omopolare (51N) a due soglie va "
                              "attivata con una sola soglia (51N.S1) per gli impianti collegati a reti "
                              "MT esercite a neutro isolato e con entrambe le soglie (51N.S1 – 51N.S2) "
                              "per gli impianti collegati a reti MT esercite con neutro a terra tramite "
                              "impedenza.",
            "contesto_uso": "sempre",
        },
        {
            "norma": "CEI 0-16:2025-04", "paragrafo": "ALLEGATO_2b",
            "titolo": "Protezione direzionale di terra 67N (soglia geometrica cavo)",
            "testo_verbatim": "Qualora il contributo alla corrente capacitiva di guasto monofase a "
                              "terra della rete MT dell'Utente superi l'80% della soglia S1 della "
                              "protezione 51N (ad esempio in caso di rete in cavo del cliente superiore "
                              "a 400 m a 20 kV o 533 m a 15 kV), il Sistema di Protezione generale deve "
                              "comprendere una protezione direzionale di terra (67N).",
            "contesto_uso": "sempre",
        },
    ],
    "corrente_guasto_terra_mt": [
        {
            "norma": "CEI 0-16:2025-04", "paragrafo": "5.2.1.7",
            "titolo": "Correnti di guasto monofase a terra e tempo di eliminazione del guasto",
            "testo_verbatim": "I valori massimi attuali delle correnti di guasto monofase a terra e "
                              "del tempo di eliminazione devono essere dichiarati dal DSO all'Utente "
                              "sulla base dei parametri di rete. Nel caso di sistemi con neutro isolato, "
                              "è possibile determinare convenzionalmente il valore della corrente di "
                              "guasto monofase a terra secondo formula empirica (U in kV, L aeree/cavo "
                              "in km); valori più precisi via CEI EN 60909 (CEI 11-25).",
            "contesto_uso": "sempre",
        },
        {
            "norma": "CEI 0-16:2025-04", "paragrafo": "8.5.12.3.2",
            "titolo": "Protezione di massima corrente omopolare (51N) — soglia 140% Ig DSO",
            "testo_verbatim": "Seconda soglia (I>>): valore 140% della corrente di guasto monofase a "
                              "terra comunicata dal DSO (tipicamente 70 A reti a 20 kV e 56 A per reti "
                              "a 15 kV).",
            "contesto_uso": "sempre",
        },
    ],
    "verifica_protezione_interfaccia_mt": [
        {
            "norma": "CEI 0-16:2025-04", "paragrafo": "8.8.7.2",
            "titolo": "Regolazioni del Sistema di Protezione di Interfaccia (SPI) — Tabella 12",
            "testo_verbatim": "Massima tensione (59.S1) 1,10 Un; Massima tensione (59.S2) 1,20 Un, "
                              "0,60 s; Minima tensione (27.S1) 0,85 Un, 1,5 s; Minima tensione (27.S2) "
                              "0,15 Un, 0,20 s; Massima frequenza (81>.S1) 50,2 Hz, 0,15 s (soglia "
                              "restrittiva); Minima frequenza (81<.S1) 49,8 Hz, 0,15 s; Massima "
                              "frequenza (81>.S2) 51,5 Hz, 1,0 s; Minima frequenza (81<.S2) 47,5 Hz, "
                              "4,0 s. È ammessa una tolleranza del ±3%.",
            "contesto_uso": "sempre",
        },
        {
            "norma": "CEI 0-16:2025-04", "paragrafo": "8.8.7.2",
            "titolo": "Tempo di apertura del DDI e inibizione frequenza",
            "testo_verbatim": "Il tempo totale di apertura del DDI si ottiene aggiungendo, al massimo, "
                              "70 ms per apparecchiature MT e 100 ms per apparecchiature BT. Per valori "
                              "di tensione al di sotto di 0,2 Un, la protezione di massima/minima "
                              "frequenza si deve inibire.",
            "contesto_uso": "sempre",
        },
    ],
}


def _contesto_match(contesto: str, ctx: dict) -> bool:
    """Valuta la condizione `contesto_uso` rispetto al dict di contesto."""
    if contesto == "sempre":
        return True
    if " in " in contesto:
        key, vals = contesto.split(" in ", 1)
        valori = [v.strip() for v in vals.strip().strip("[]").split(",")]
        return ctx.get(key.strip()) in valori
    if "=" in contesto:
        key, val = contesto.split("=", 1)
        return str(ctx.get(key.strip())) == val.strip()
    return True


def get_kb_references_for_tool(tool_name: str, output_context: dict | None = None) -> list[dict]:
    """Riferimenti KB applicabili per un tool, filtrati dal contesto di output."""
    refs = KB_REFERENCES_BY_TOOL.get(tool_name, [])
    if output_context is None:
        return list(refs)
    return [r for r in refs if _contesto_match(r["contesto_uso"], output_context)]
