"""Tool MCP `verifica_selettivita` (MT-E2): esito SOLO da tabella reale; assente = GAP.

Riceve due dispositivi (monte = supply side, valle = load side), consulta la
collezione di tabelle di coordinamento reali del costruttore e restituisce
l'esito con la **fonte** (tabella + revisione) e il **trace**.
Se la coppia non e' in tabella -> **GAP dichiarato**, MAI esito inventato.
Nessun valore dal modello: il limite di selettivita' e' il valore di cella.

NB: questo e' un nome NUOVO e distinto dal preesistente `verifica_selettivita_*`
basato su calcolo; qui l'esito viene esclusivamente dalle tabelle del costruttore.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from .coordinamento import carica_coordinamento, chiave_dispositivo, trova


class DispositivoRef(BaseModel):
    costruttore: str = Field(..., description="es. 'ABB'")
    serie: str = Field(..., description="serie costruttore, es. 'S290', 'S240'")
    curva: str = Field(..., description="caratteristica: B/C/D")
    In_A: float = Field(..., description="corrente nominale (A)")
    poli: Optional[int] = None


class VerificaSelettivitaTabellaInput(BaseModel):
    monte: DispositivoRef = Field(..., description="dispositivo a monte (supply side)")
    valle: DispositivoRef = Field(..., description="dispositivo a valle (load side)")
    icc_kA: Optional[float] = Field(None, description="Icc presunta nel punto (kA), confrontata col limite di selettivita'")
    tipo: str = Field("selettivita", description="'selettivita' | 'filiazione'")


class VerificaSelettivitaTabellaOutput(BaseModel):
    esito: str = Field(..., description="selettiva_totale | selettiva_fino_a_limite | non_selettiva_oltre_limite | gap")
    gap: bool
    limite_selettivita_kA: Optional[float]
    dettaglio: str
    fonte: Optional[dict]
    trace: dict


def verifica_selettivita_tabella(inp: VerificaSelettivitaTabellaInput) -> VerificaSelettivitaTabellaOutput:
    entries, _ = carica_coordinamento()
    mk = chiave_dispositivo(inp.monte.costruttore, inp.monte.serie, inp.monte.curva, inp.monte.In_A)
    vk = chiave_dispositivo(inp.valle.costruttore, inp.valle.serie, inp.valle.curva, inp.valle.In_A)
    e = trova(entries, mk, vk, tipo=inp.tipo)

    trace_base = {
        "norma": "selettivita'/filiazione da TABELLA del costruttore (CEI EN 60947-2 / 60898-1)",
        "metodo": "lookup tabella di coordinamento; nessun valore dal modello",
        "chiave_monte": mk,
        "chiave_valle": vk,
    }

    if e is None:
        return VerificaSelettivitaTabellaOutput(
            esito="gap",
            gap=True,
            limite_selettivita_kA=None,
            dettaglio=(
                f"GAP: nessuna tabella di coordinamento per la coppia monte={mk} valle={vk} "
                f"(tipo '{inp.tipo}'). Selettivita' NON inferita: serve la tabella reale del costruttore."
            ),
            fonte=None,
            trace={**trace_base, "esito": "GAP (tabella assente) - nessun esito inventato"},
        )

    fonte = {"tabella": e.fonte_tabella, "revisione": e.revisione, "vigenza": e.vigenza, "tensione_V": e.tensione_V}

    if e.tipo == "filiazione":
        return VerificaSelettivitaTabellaOutput(
            esito="filiazione_ammessa",
            gap=False,
            limite_selettivita_kA=None,
            dettaglio=f"Back-up (filiazione) ammessa: Icc rinforzata {e.icc_backup_kA} kA (da tabella).",
            fonte=fonte,
            trace={**trace_base, "valore_tabella": f"Icc back-up {e.icc_backup_kA} kA"},
        )

    # selettivita'
    if e.esito == "totale":
        det = "Selettivita' TOTALE (cella 'T') da tabella."
        if inp.icc_kA is not None:
            det += f" Icc {inp.icc_kA} kA: selettiva (totale)."
        return VerificaSelettivitaTabellaOutput(
            esito="selettiva_totale", gap=False, limite_selettivita_kA=None, dettaglio=det,
            fonte=fonte, trace={**trace_base, "valore_tabella": "T (totale)"},
        )

    lim = e.limite_selettivita_kA
    if inp.icc_kA is None:
        esito = "selettiva_fino_a_limite"
        det = f"Selettivita' PARZIALE: garantita fino a {lim:g} kA (limite di tabella)."
    elif inp.icc_kA <= lim:
        esito = "selettiva_fino_a_limite"
        det = f"Icc {inp.icc_kA:g} kA <= limite {lim:g} kA: selettiva (entro il limite di tabella)."
    else:
        esito = "non_selettiva_oltre_limite"
        det = f"Icc {inp.icc_kA:g} kA > limite {lim:g} kA: NON selettiva oltre il limite di tabella."

    return VerificaSelettivitaTabellaOutput(
        esito=esito, gap=False, limite_selettivita_kA=lim, dettaglio=det,
        fonte=fonte, trace={**trace_base, "valore_tabella": f"{lim:g} kA (limite di selettivita')"},
    )
