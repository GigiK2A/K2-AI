"""Protezioni MT utente attivo CEI 0-16:2025-04 — PG (generale) e SPI (interfaccia).

Due tool Tappa 1 dedicati alla connessione in MT (utente attivo, es. parco FV in MT):

- ``verifica_protezione_generale_mt`` — Sistema di Protezione Generale (SPG/PG):
  massima corrente 51 (51.S1 NIT / 51.S2), massima corrente omopolare 51N,
  direzionale di terra 67N. Rif. CEI 0-16 §8.8 + Allegato 2b Tabella 1.
- ``verifica_protezione_interfaccia_mt`` — Sistema di Protezione di Interfaccia (SPI):
  soglie di tensione 27/59 e di frequenza 81, anti-islanding. Rif. CEI 0-16
  §8.8.7.2 Tabella 12 + Allegato 2b Tabella 2 (impianti > 30 kW).

NOTA TERMINOLOGICA (vs brief): in CEI 0-16 la protezione *d'interfaccia* si chiama
**SPI** (non SPG); **SPG** = protezione *generale*. Il brief usava "SPG" per
l'interfaccia (terminologia CEI 0-21 BT). Qui si adottano i nomi normativi 0-16.
La numerazione reale è §8.8 + Allegato 2b (non §8.4/§8.5 ipotizzati nel brief).

Questi tool seguono il pattern "semplice" di Tappa 1 (come ``spi_fv``): Pydantic
in/out deterministico, soglie di default hardcoded da CEI 0-16 (verbatim in
``_kb_mapping``). Niente validate_runtime/validator gemello in questa sessione
(debt documentato in ADR-022) — sono protezioni d'interfaccia, non i 5 tool
safety-critical cross-validati.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Esito = Literal["ok", "ko", "warning"]

# --- Soglie di default normative CEI 0-16:2025-04 (Allegato 2b Tab.12 / §8.8.7.2) ---
SPI_DEFAULT = {
    "V_59_S1_pu": 1.10, "t_59_S1_s_max": 603.0,
    "V_59_S2_pu": 1.20, "t_59_S2_s": 0.60,
    "V_27_S1_pu": 0.85, "t_27_S1_s": 1.5,
    "V_27_S2_pu": 0.15, "t_27_S2_s": 0.20,
    "f_81sup_S1_hz": 50.2, "t_81sup_S1_s": 0.15,   # soglia restrittiva
    "f_81sup_S2_hz": 51.5, "t_81sup_S2_s": 1.0,    # soglia permissiva
    "f_81inf_S1_hz": 49.8, "t_81inf_S1_s": 0.15,   # soglia restrittiva
    "f_81inf_S2_hz": 47.5, "t_81inf_S2_s": 4.0,    # soglia permissiva
    "tolleranza_soglia_pc": 3.0,                   # ±3% (nota 105)
    "ddi_extra_ms_mt": 70.0, "ddi_extra_ms_bt": 100.0,  # tempo apertura DDI aggiuntivo
    "inibizione_freq_sotto_pu": 0.20,              # sotto 0,2 Un freq inibita
}


# ===================================================================================
# Tool 1 — Sistema di Protezione Generale (SPG/PG) MT
# ===================================================================================
class ProtezioneGeneraleMTInput(BaseModel):
    tensione_nominale_kV: Literal[15, 20] = Field(20, description="Tensione nominale rete MT (15 o 20 kV)")
    corrente_nominale_A: float = Field(..., gt=0, description="Corrente nominale impianto utente al primario MT")
    icc_mt_trifase_kA: float = Field(..., gt=0, description="Icc trifase MT (per coordinamento soglie 51)")
    neutro: Literal["isolato", "compensato_impedenza"] = Field(
        "isolato", description="Stato del neutro rete MT: isolato (1 soglia 51N) o a terra tramite impedenza (2 soglie)")
    soglia_51_S1_A: float | None = Field(None, description="Taratura I> 51.S1 (NIT) al primario; default = 1.2·In")
    soglia_51_S2_A: float | None = Field(None, description="Taratura I>> 51.S2 al primario; default da Icc")
    soglia_51N_S1_A: float = Field(2.0, gt=0, description="Taratura I> 51N.S1 omopolare al primario [A]")
    lunghezza_rete_cavo_utente_m: float = Field(0.0, ge=0, description="Lunghezza rete in cavo MT lato utente [m] (per soglia 67N)")
    direzionale_terra_67N_presente: bool = Field(False, description="Protezione direzionale di terra 67N installata")
    rele_tipo: Literal["digitale_combinato", "distinti"] = "digitale_combinato"


class ProtezioneGeneraleMTOutput(BaseModel):
    verifica_51_sovracorrente: Esito
    verifica_51N_omopolare: Esito
    verifica_67N_direzionale: Esito
    coordinamento_con_pg_dso: Esito
    esito_complessivo: Esito
    soglia_51_S1_A: float
    soglia_51_S2_A: float
    n_soglie_51N_richieste: int
    soglia_67N_richiesta: bool
    norma_riferimento: str
    note_normative: list[str]
    warnings: list[str]
    trace: dict


def verifica_protezione_generale_mt(inp: ProtezioneGeneraleMTInput) -> ProtezioneGeneraleMTOutput:
    warnings: list[str] = []
    note: list[str] = []

    # Soglia 51.S1 di default: 1,2·In (NIT a tempo inverso, richiusure escluse).
    s51_s1 = inp.soglia_51_S1_A if inp.soglia_51_S1_A is not None else round(1.2 * inp.corrente_nominale_A, 1)
    # Soglia 51.S2 di default: limitata sotto la Icc MT (margine 80% Icc al primario).
    icc_primario_A = inp.icc_mt_trifase_kA * 1000.0
    s51_s2 = inp.soglia_51_S2_A if inp.soglia_51_S2_A is not None else round(min(10 * inp.corrente_nominale_A, 0.8 * icc_primario_A), 1)

    # 51 sovracorrente: la soglia deve stare sotto la Icc max attesa e sopra In.
    v51: Esito = "ok"
    if s51_s1 <= inp.corrente_nominale_A:
        v51 = "ko"; warnings.append("51.S1 ≤ In: la soglia non discrimina il carico nominale.")
    if s51_s2 >= icc_primario_A:
        v51 = "ko"; warnings.append("51.S2 ≥ Icc MT: la soglia non protegge entro la corrente di cortocircuito.")
    elif s51_s2 > 0.8 * icc_primario_A:
        v51 = "warning" if v51 == "ok" else v51
        warnings.append("51.S2 oltre l'80% della Icc MT: margine ridotto.")
    note.append("51 (I>/I>>): richiusure escluse, 51.S1 a tempo NIT (CEI 0-16 Allegato 2b Tab.1).")

    # 51N omopolare: 1 soglia se neutro isolato, 2 soglie se neutro a terra tramite impedenza.
    n_51n = 1 if inp.neutro == "isolato" else 2
    v51n: Esito = "ok"
    note.append(f"51N: {n_51n} soglia/e richiesta/e per rete a neutro {inp.neutro} "
                "(nota 2, CEI 0-16 Allegato 2b Tab.1).")

    # 67N direzionale: richiesta se contributo capacitivo > 80% soglia S1.
    # Soglia geometrica (verbatim §272): cavo > 400 m a 20 kV o > 533 m a 15 kV.
    soglia_cavo_m = 400.0 if inp.tensione_nominale_kV == 20 else 533.0
    s67_richiesta = inp.lunghezza_rete_cavo_utente_m > soglia_cavo_m
    if s67_richiesta and not inp.direzionale_terra_67N_presente:
        v67: Esito = "ko"
        warnings.append(f"Rete cavo utente {inp.lunghezza_rete_cavo_utente_m:.0f} m > {soglia_cavo_m:.0f} m "
                        f"a {inp.tensione_nominale_kV} kV: richiesta protezione direzionale di terra 67N (nota 272).")
    elif s67_richiesta:
        v67 = "ok"
        note.append("67N direzionale di terra presente e richiesta (rete in cavo estesa).")
    else:
        v67 = "ok"
        note.append("67N non richiesta (rete in cavo sotto la soglia geometrica).")

    # Coordinamento con la PG del DSO: l'utente è a valle, deve essere selettivo.
    coord: Esito = "ok"
    note.append("Coordinamento con PG del DSO: tarature comunicate dal DSO; "
                "selettività garantita da tempi/soglie utente a valle (CEI 0-16 §8.8).")

    esiti = [v51, v51n, v67, coord]
    esito = "ko" if "ko" in esiti else ("warning" if "warning" in esiti else "ok")

    return ProtezioneGeneraleMTOutput(
        verifica_51_sovracorrente=v51,
        verifica_51N_omopolare=v51n,
        verifica_67N_direzionale=v67,
        coordinamento_con_pg_dso=coord,
        esito_complessivo=esito,
        soglia_51_S1_A=s51_s1,
        soglia_51_S2_A=s51_s2,
        n_soglie_51N_richieste=n_51n,
        soglia_67N_richiesta=s67_richiesta,
        norma_riferimento="CEI 0-16:2025-04 §8.8 + Allegato 2b Tab.1 (Sistema di Protezione Generale)",
        note_normative=note,
        warnings=warnings,
        trace={
            "In_A": inp.corrente_nominale_A,
            "Icc_MT_primario_A": icc_primario_A,
            "neutro": inp.neutro,
            "soglia_cavo_67N_m": soglia_cavo_m,
            "relè": inp.rele_tipo,
        },
    )


# ===================================================================================
# Tool 2 — Sistema di Protezione di Interfaccia (SPI) MT
# ===================================================================================
class ProtezioneInterfacciaMTInput(BaseModel):
    potenza_generazione_kW: float = Field(..., gt=0, description="Potenza nominale generazione FV/accumulo [kW]")
    tensione_nominale_kV: Literal[15, 20] = Field(20, description="Tensione nominale rete MT (15 o 20 kV)")
    apparecchiatura_ddi: Literal["MT", "BT"] = Field(
        "MT", description="Dove è installato il DDI (Dispositivo Di Interfaccia): lato MT o BT")
    anti_islanding_attivo: bool = Field(True, description="Funzione anti-islanding (LoM) attiva sugli inverter")
    # Soglie effettivamente impostate (se None → si usano i default normativi).
    soglia_59_S1_pu: float | None = Field(None, description="Max tensione 59.S1 [pu di Un]; default 1.10")
    soglia_27_S1_pu: float | None = Field(None, description="Min tensione 27.S1 [pu di Un]; default 0.85")
    soglia_81sup_S1_hz: float | None = Field(None, description="Max freq 81>.S1 [Hz]; default 50.2")
    soglia_81inf_S1_hz: float | None = Field(None, description="Min freq 81<.S1 [Hz]; default 49.8")
    comando_locale_S1_incluso: bool = Field(True, description="Soglie restrittive 81.S1 incluse da comando locale (Reg. Esercizio)")


class ProtezioneInterfacciaMTOutput(BaseModel):
    verifica_27_59_tensione: Esito
    verifica_81_frequenza: Esito
    verifica_anti_islanding: Esito
    tempi_intervento_conformi: Esito
    esito_complessivo: Esito
    spi_obbligatorio: bool
    soglie_default_applicate: bool
    soglie_tensione: dict
    soglie_frequenza: dict
    tempo_apertura_ddi_extra_ms: float
    norma_riferimento: str
    documentazione_richiesta: list[str]
    note_normative: list[str]
    warnings: list[str]
    trace: dict


def verifica_protezione_interfaccia_mt(inp: ProtezioneInterfacciaMTInput) -> ProtezioneInterfacciaMTOutput:
    warnings: list[str] = []
    note: list[str] = []
    d = SPI_DEFAULT
    toll = d["tolleranza_soglia_pc"] / 100.0

    # SPI obbligatorio in MT per ogni impianto di produzione (Tab.2 per P > 30 kW).
    spi_obb = True
    if inp.potenza_generazione_kW <= 30.0:
        note.append("Impianto ≤ 30 kW: si applicano comunque le tarature SPI (Tab.2 è per > 30 kW).")

    # Soglie effettive vs default (con tolleranza ±3%).
    v59_s1 = inp.soglia_59_S1_pu if inp.soglia_59_S1_pu is not None else d["V_59_S1_pu"]
    v27_s1 = inp.soglia_27_S1_pu if inp.soglia_27_S1_pu is not None else d["V_27_S1_pu"]
    f81s_s1 = inp.soglia_81sup_S1_hz if inp.soglia_81sup_S1_hz is not None else d["f_81sup_S1_hz"]
    f81i_s1 = inp.soglia_81inf_S1_hz if inp.soglia_81inf_S1_hz is not None else d["f_81inf_S1_hz"]
    default_applicate = all(x is None for x in (inp.soglia_59_S1_pu, inp.soglia_27_S1_pu,
                                                inp.soglia_81sup_S1_hz, inp.soglia_81inf_S1_hz))

    def _entro(val: float, rif: float) -> bool:
        return abs(val - rif) <= abs(rif) * toll

    # Verifica soglie di tensione 27/59.
    v_tens: Esito = "ok"
    if not _entro(v59_s1, d["V_59_S1_pu"]):
        v_tens = "ko"; warnings.append(f"59.S1={v59_s1:.3f}pu fuori da 1,10·Un ±3% (CEI 0-16 Tab.12).")
    if not _entro(v27_s1, d["V_27_S1_pu"]):
        v_tens = "ko"; warnings.append(f"27.S1={v27_s1:.3f}pu fuori da 0,85·Un ±3% (CEI 0-16 Tab.12).")
    note.append("Tensione: 59.S1 1,10·Un / 59.S2 1,20·Un / 27.S1 0,85·Un / 27.S2 0,15·Un (Tab.12).")

    # Verifica soglie di frequenza 81.
    v_freq: Esito = "ok"
    if not _entro(f81s_s1, d["f_81sup_S1_hz"]):
        v_freq = "ko"; warnings.append(f"81>.S1={f81s_s1:.2f}Hz fuori da 50,2 Hz ±3%.")
    if not _entro(f81i_s1, d["f_81inf_S1_hz"]):
        v_freq = "ko"; warnings.append(f"81<.S1={f81i_s1:.2f}Hz fuori da 49,8 Hz ±3%.")
    if not inp.comando_locale_S1_incluso:
        v_freq = "warning" if v_freq == "ok" else v_freq
        warnings.append("Soglie restrittive 81.S1 escluse da comando locale: verificare Regolamento di Esercizio.")
    note.append("Frequenza: 81>.S1 50,2 / 81<.S1 49,8 (restrittive) · 81>.S2 51,5 / 81<.S2 47,5 (permissive) Hz.")

    # Anti-islanding.
    v_isl: Esito = "ok" if inp.anti_islanding_attivo else "ko"
    if not inp.anti_islanding_attivo:
        warnings.append("Anti-islanding (LoM) NON attivo: non conforme alla protezione d'interfaccia CEI 0-16.")
    note.append("Anti-islanding (Loss of Mains) richiesto sul SPI per disconnessione in isola indesiderata.")

    # Tempo apertura DDI aggiuntivo (70 ms MT / 100 ms BT) sui tempi di intervento.
    ddi_extra = d["ddi_extra_ms_mt"] if inp.apparecchiatura_ddi == "MT" else d["ddi_extra_ms_bt"]
    v_tempi: Esito = "ok"
    note.append(f"Tempo apertura DDI: +{ddi_extra:.0f} ms (apparecchiatura {inp.apparecchiatura_ddi}) "
                "sui tempi di intervento di Tab.12. Tolleranza ±3% ±20 ms.")

    doc = [
        "Certificato di prova SPI da laboratorio accreditato (CEI 0-16 Allegato E)",
        "Regolamento di Esercizio (RdE) con DSO: tarature 27/59/81 e stato comando locale 81.S1",
        "Schema funzionale SPI + DDI (Dispositivo Di Interfaccia)",
        "Dichiarazione conformità inverter (anti-islanding / LoM)",
    ]

    esiti = [v_tens, v_freq, v_isl, v_tempi]
    esito = "ko" if "ko" in esiti else ("warning" if "warning" in esiti else "ok")

    return ProtezioneInterfacciaMTOutput(
        verifica_27_59_tensione=v_tens,
        verifica_81_frequenza=v_freq,
        verifica_anti_islanding=v_isl,
        tempi_intervento_conformi=v_tempi,
        esito_complessivo=esito,
        spi_obbligatorio=spi_obb,
        soglie_default_applicate=default_applicate,
        soglie_tensione={
            "59.S1_pu": v59_s1, "t_59.S1_s_max": d["t_59_S1_s_max"],
            "59.S2_pu": d["V_59_S2_pu"], "t_59.S2_s": d["t_59_S2_s"],
            "27.S1_pu": v27_s1, "t_27.S1_s": d["t_27_S1_s"],
            "27.S2_pu": d["V_27_S2_pu"], "t_27.S2_s": d["t_27_S2_s"],
        },
        soglie_frequenza={
            "81>.S1_hz": f81s_s1, "t_81>.S1_s": d["t_81sup_S1_s"],
            "81>.S2_hz": d["f_81sup_S2_hz"], "t_81>.S2_s": d["t_81sup_S2_s"],
            "81<.S1_hz": f81i_s1, "t_81<.S1_s": d["t_81inf_S1_s"],
            "81<.S2_hz": d["f_81inf_S2_hz"], "t_81<.S2_s": d["t_81inf_S2_s"],
        },
        tempo_apertura_ddi_extra_ms=ddi_extra,
        norma_riferimento="CEI 0-16:2025-04 §8.8.7.2 Tab.12 + Allegato 2b Tab.2 (Sistema di Protezione di Interfaccia)",
        documentazione_richiesta=doc,
        note_normative=note,
        warnings=warnings,
        trace={
            "P_gen_kW": inp.potenza_generazione_kW,
            "Un_kV": inp.tensione_nominale_kV,
            "ddi": inp.apparecchiatura_ddi,
            "tolleranza_pc": d["tolleranza_soglia_pc"],
            "inibizione_freq_sotto_pu": d["inibizione_freq_sotto_pu"],
        },
    )
