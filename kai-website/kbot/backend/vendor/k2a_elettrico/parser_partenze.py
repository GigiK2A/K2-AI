"""Parser di descrizioni testuali partenze quadro elettrico — CEI EN 61439-1/2.

Estrae da stringhe libere (tipiche PE) dati strutturati:
  - corrente nominale In, tipo protezione (ACB/MCCB/MCB), poli
  - Icu/Icw, sganciatore (LSIG/LSI/LI), ZSI
  - flag motorizzato/estraibile, differenziale mA

Robusto contro: punto migliaia italiano, spazi multipli, ambiguità ACB/MCCB,
descrizioni incomplete. Avvertenze per ogni anomalia parsing.
"""
from __future__ import annotations
import re
from typing import Literal
from pydantic import BaseModel, Field


# -------- Output models --------

class PartenzaStrutturata(BaseModel):
    sigla: str
    descrizione_originale: str
    tipo_protezione: Literal["ACB", "MCCB", "MCB", "INTERR", "UNKNOWN"]
    In_A: float | None
    Icu_kA: float | None
    Icw_kA: float | None
    poli: int | None
    sganciatore: Literal["LSIG", "LI", "LSI", "ZSI", "UNKNOWN"] | None
    ZSI_attivo: bool
    motorizzato: bool
    estraibile: bool
    differenziale_mA: float | None
    tipo_connessione: Literal["cavo", "blindosbarra", "sbarra_dedicata",
                              "cavi_paralleli", "UNKNOWN"]
    avvertenze_parsing: list[str]


class ParserDefaults(BaseModel):
    isolante: str = "EPR_XLPE"
    posa: str = "E"
    materiale: str = "Cu"
    Tamb_C: float = 30.0
    n_circuiti: int = 1


class ParserPartenzeInput(BaseModel):
    descrizioni: dict[str, str] = Field(..., description="{sigla: descrizione_testuale}")
    defaults: ParserDefaults | None = None


class ParserPartenzeOutput(BaseModel):
    partenze: list[PartenzaStrutturata]
    statistiche: dict
    norma_riferimento_internazionale: str
    norma_riferimento_locale: dict


# -------- Regex precompilate --------

_RX_IN     = re.compile(r"\b(\d{1,3}(?:[\.,]\d{3})*(?:[\.,]\d+)?|\d+)\s*A\b")
_RX_ICU    = re.compile(r"Icu\s*(\d{1,3}(?:[\.,]\d+)?)\s*kA", re.IGNORECASE)
_RX_ICW    = re.compile(r"Icw\s*(\d{1,3}(?:[\.,]\d+)?)\s*kA", re.IGNORECASE)
_RX_POLI   = re.compile(r"\b(\d)P\b", re.IGNORECASE)
_RX_DIFF   = re.compile(r"(?:Idn|Id|RCD)\s*(\d{1,4}(?:[\.,]\d+)?)\s*mA", re.IGNORECASE)


def _parse_numero_italiano(s: str) -> float:
    """Converte '1.250' → 1250, '1250' → 1250, '1,5' → 1.5.

    Regola:
      - punto + virgola: punto=migliaia, virgola=decimale ("1.250,5" → 1250.5)
      - solo punto: heuristica '\\d+\\.\\d{3}$' → migliaia ('1.250'→1250),
        altrimenti decimale ('1.5'→1.5)
      - solo virgola: decimale
    """
    if "." in s and "," in s:
        s = s.replace(".", "").replace(",", ".")
    elif "." in s:
        parts = s.split(".")
        if len(parts) == 2 and len(parts[1]) == 3:
            s = s.replace(".", "")
    elif "," in s:
        s = s.replace(",", ".")
    return float(s)


def _parse_partenza_singola(sigla: str, desc: str) -> PartenzaStrutturata:
    avvertenze: list[str] = []
    s_upper = desc.upper()

    # Tipo protezione — word boundaries per robustezza futura (es. evitare clash con 'CB' generico)
    if re.search(r"\bACB/MCCB\b", s_upper):
        tipo = "ACB"
        avvertenze.append("ACB/MCCB ambiguo, scelto ACB (primo match)")
    elif re.search(r"\bACB\b", s_upper):
        tipo = "ACB"
    elif re.search(r"\bMCCB\b", s_upper):
        tipo = "MCCB"
    elif re.search(r"\bMCB\b", s_upper):
        tipo = "MCB"
    elif re.search(r"INTERRUTTOR", s_upper):
        tipo = "INTERR"
    else:
        tipo = "UNKNOWN"
        avvertenze.append("tipo protezione non identificato")

    # In
    m_in = _RX_IN.search(desc)
    In_A = _parse_numero_italiano(m_in.group(1)) if m_in else None
    if In_A is None:
        avvertenze.append("In non estratta")

    # Icu / Icw
    m_icu = _RX_ICU.search(desc)
    Icu_kA = _parse_numero_italiano(m_icu.group(1)) if m_icu else None
    m_icw = _RX_ICW.search(desc)
    Icw_kA = _parse_numero_italiano(m_icw.group(1)) if m_icw else None

    # Poli
    m_p = _RX_POLI.search(desc)
    poli = int(m_p.group(1)) if m_p else None

    # Sganciatore — sequenza prove (più specifico prima per evitare match prefisso)
    sganciatore = None
    if "LSIG" in s_upper:
        sganciatore = "LSIG"
    elif "LSI" in s_upper:
        sganciatore = "LSI"
    elif re.search(r"\bLI\b", s_upper) and tipo in ("ACB", "MCCB"):
        sganciatore = "LI"
    elif tipo in ("ACB", "MCCB"):
        sganciatore = "UNKNOWN"

    # ZSI separato (può accompagnare LSIG)
    ZSI_attivo = bool(re.search(r"\bZSI\b", s_upper))

    # Flag flessibili (stem-match per gestire 'motoriz.', 'motorizzato')
    motorizzato = bool(re.search(r"motoriz", desc, re.IGNORECASE))
    estraibile = bool(re.search(r"ESTRAIB", s_upper))

    # Differenziale
    m_diff = _RX_DIFF.search(desc)
    differenziale_mA = _parse_numero_italiano(m_diff.group(1)) if m_diff else None

    # Avvertenze contestuali — word boundaries per consistenza
    if re.search(r"\bESCLUSO\b", s_upper) or re.search(r"\bFORNITURA\b", s_upper):
        avvertenze.append("annotazione fornitura/scope nel testo")
    if re.search(r"\bRISERV", s_upper) or re.search(r"\bCASSETT", s_upper):
        avvertenze.append("partenza di riserva (no In specifica)")

    # Tipo connessione — detection da testo + heuristica fallback su In
    if re.search(r"BLINDOSBARR", s_upper) or re.search(r"\bBLINDO\b", s_upper):
        tipo_conn = "blindosbarra"
    elif re.search(r"\bINCOMER\b", s_upper) or re.search(r"SBARRA\s+PRINCIPAL", s_upper):
        tipo_conn = "sbarra_dedicata"
    elif re.search(r"PARALLEL", s_upper):
        tipo_conn = "cavi_paralleli"
    elif In_A is None:
        tipo_conn = "UNKNOWN"
    elif In_A > 1000:
        tipo_conn = "sbarra_dedicata"
        avvertenze.append(f"tipo_connessione=sbarra_dedicata default (In={In_A}A > 1000A)")
    elif In_A > 400:
        tipo_conn = "cavi_paralleli"
        avvertenze.append(f"tipo_connessione=cavi_paralleli default (In={In_A}A > 400A)")
    else:
        tipo_conn = "cavo"

    return PartenzaStrutturata(
        sigla=sigla, descrizione_originale=desc,
        tipo_protezione=tipo, In_A=In_A, Icu_kA=Icu_kA, Icw_kA=Icw_kA,
        poli=poli, sganciatore=sganciatore, ZSI_attivo=ZSI_attivo,
        motorizzato=motorizzato, estraibile=estraibile,
        differenziale_mA=differenziale_mA,
        tipo_connessione=tipo_conn,
        avvertenze_parsing=avvertenze,
    )


def parser_partenze_quadro(inp: ParserPartenzeInput) -> ParserPartenzeOutput:
    """Parser deterministico delle descrizioni testuali di partenze quadro."""
    parsed = [_parse_partenza_singola(s, d) for s, d in inp.descrizioni.items()]

    n_tot = len(parsed)
    # "Parsata complete" = tipo+In estratti senza ambiguità testuali.
    # Le avvertenze "tipo_connessione default" sono decisioni euristiche
    # del parser su parametro non presente nel testo: non conteggiate come ambiguità.
    def _ambiguita_reale(p: PartenzaStrutturata) -> bool:
        return any(
            not a.startswith("tipo_connessione=") for a in p.avvertenze_parsing
        )
    n_complete = sum(
        1 for p in parsed
        if p.In_A is not None and p.tipo_protezione != "UNKNOWN" and not _ambiguita_reale(p)
    )
    n_con_avvertenze = sum(1 for p in parsed if p.avvertenze_parsing)
    n_sconosciute = sum(1 for p in parsed if p.tipo_protezione == "UNKNOWN")

    return ParserPartenzeOutput(
        partenze=parsed,
        statistiche={
            "n_totale": n_tot,
            "n_parsate_complete": n_complete,
            "n_con_avvertenze": n_con_avvertenze,
            "n_sconosciute_tipo": n_sconosciute,
        },
        norma_riferimento_internazionale="IEC 61439-1/2:2020",
        norma_riferimento_locale={
            "IT": "CEI EN 61439-1/2:2021",
            "DE": "DIN EN 61439-1/2:2020",
            "FR": "NF EN 61439-1/2:2020",
            "ES": "UNE-EN 61439-1/2:2021",
            "UK": "BS EN 61439-1/2:2020",
        },
    )
