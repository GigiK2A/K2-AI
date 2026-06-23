"""DPI fotovoltaico — Sistema Protezione Interfaccia CEI 0-21 (BT) / CEI 0-16 (MT)."""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field


class SpiCei021Input(BaseModel):
    P_generazione_kW: float = Field(..., gt=0, description="Potenza nominale impianto FV/accumulo in kW")
    Vn: float = Field(400.0, description="V nominale (230 monofase, 400 trifase)")
    sistema: Literal["monofase", "trifase"] = "trifase"
    accumulo_presente: bool = False
    inverter_certificato_CEI_0_21: bool = Field(True, description="Inverter con SPI integrato certificato")


class SpiCei021Output(BaseModel):
    spi_obbligatorio: bool
    spi_separato_richiesto: bool
    soglie_27_59_V_min_pc: float
    soglie_27_59_V_max_pc: float
    soglia_81_freq_min_Hz: float
    soglia_81_freq_max_Hz: float
    tempi_intervento_ms: dict
    avviso: str
    documentazione_richiesta: list[str]
    trace: dict


def verifica_spi_cei_021(inp: SpiCei021Input) -> SpiCei021Output:
    # Soglia SPI: obbligatorio per generazione >6kW BT (CEI 0-21 §A.1)
    spi_obb = inp.P_generazione_kW > 6.0
    # SPI separato esterno richiesto se inverter NON certificato o impianti >11.08 kW
    spi_separato = (not inp.inverter_certificato_CEI_0_21) or inp.P_generazione_kW > 11.08

    # Soglie tensione (V<>): 27 = sottotens., 59 = sovratens.
    V_min_pc, V_max_pc = 85.0, 110.0  # CEI 0-21 ediz. 2022 V01
    # Soglie frequenza (81 <>): ±0.5 Hz finestra ristretta, ±2.5 Hz ampia
    f_min, f_max = 49.7, 50.3
    # Tempi intervento (CEI 0-21 Tab. A.1)
    tempi = {
        "27.S1_V<0.85Vn_ristretta": 400,  # ms
        "59.S1_V>1.10Vn_ristretta": 600,
        "27.S2_V<0.40Vn_estesa": 200,
        "59.S2_V>1.15Vn_estesa": 200,
        "81<S1_f<49.7Hz_ristretta": 100,
        "81>S1_f>50.3Hz_ristretta": 100,
        "81<S2_f<47.5Hz_estesa": 100,
        "81>S2_f>51.5Hz_estesa": 100,
    }

    doc = []
    if spi_obb:
        doc.append("Dichiarazione di conformità inverter (CEI 0-21 Allegato A.7)")
        doc.append("Certificato funzionale SPI da laboratorio accreditato")
        doc.append("Modello unico TICA per richiesta connessione al distributore")
        if inp.accumulo_presente:
            doc.append("Schema funzionale accumulo (CEI 0-21 Allegato T)")
        if spi_separato:
            doc.append("Rapporto di prova SPI separato + relè di protezione installato")

    avviso = []
    if not spi_obb:
        avviso.append(f"Impianto {inp.P_generazione_kW}kW ≤ 6kW: SPI NON obbligatorio (CEI 0-21 §A.1).")
    elif spi_separato:
        avviso.append("SPI separato esterno richiesto (potenza >11.08kW o inverter non certificato).")
    else:
        avviso.append("SPI integrato inverter accettato (potenza ≤11.08kW e inverter certificato).")

    return SpiCei021Output(
        spi_obbligatorio=spi_obb,
        spi_separato_richiesto=spi_separato,
        soglie_27_59_V_min_pc=V_min_pc,
        soglie_27_59_V_max_pc=V_max_pc,
        soglia_81_freq_min_Hz=f_min,
        soglia_81_freq_max_Hz=f_max,
        tempi_intervento_ms=tempi,
        avviso=" ".join(avviso),
        documentazione_richiesta=doc,
        trace={
            "norma": "CEI 0-21:2022 V01 (BT) — connessione utenti attivi rete distribuzione",
            "soglie_riferimento": {
                "27 (V<)": "0.85·Vn ristretta / 0.40·Vn estesa",
                "59 (V>)": "1.10·Vn ristretta / 1.15·Vn estesa",
                "81< (f<)": "49.7 Hz ristretta / 47.5 Hz estesa",
                "81> (f>)": "50.3 Hz ristretta / 51.5 Hz estesa",
            },
            "ANTI_ISLANDING": "richiesto su tutti gli inverter (LOM detection)",
        },
    )
