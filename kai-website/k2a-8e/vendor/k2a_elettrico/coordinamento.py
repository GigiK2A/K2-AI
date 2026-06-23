"""Schema + collezione tabelle di coordinamento (selettivita'/filiazione) - MT-E2.

Gli esiti vengono **SOLO da tabelle reali del costruttore** (collezione
`data/coordinamento/*.json`, ognuna con `fonte_tabella` + `revisione`).
Coppia non presente in tabella = **GAP dichiarato**, mai esito inventato.
Nessun valore dal modello: ogni `limite_selettivita_kA` e' il valore di cella
stampato nella tabella citata.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator

_COORD_DIR = Path(__file__).parent / "data" / "coordinamento"

TIPI = {"selettivita", "filiazione"}


def chiave_dispositivo(costruttore: str, serie: str, curva: str, In_A: float) -> str:
    """Chiave canonica ASCII di un dispositivo per il match in tabella."""
    return f"{costruttore.strip().upper()}|{serie.strip().upper()}|{curva.strip().upper()}|{float(In_A):g}"


class CoordinamentoEntry(BaseModel):
    """Una cella di tabella di coordinamento del costruttore (monte/valle -> esito)."""

    id: str
    tipo: str = Field(..., description="'selettivita' | 'filiazione'")
    # monte (supply side)
    monte_costruttore: str
    monte_serie: str
    monte_curva: str
    monte_In_A: float
    # valle (load side)
    valle_costruttore: str
    valle_serie: str
    valle_curva: str
    valle_In_A: float
    # esito letto dalla tabella
    esito: str = Field(..., description="selettivita: 'totale'/'parziale'; filiazione: 'ammessa'")
    limite_selettivita_kA: Optional[float] = Field(None, description="valore di cella (kA); None se 'totale'/'T'")
    icc_backup_kA: Optional[float] = Field(None, description="solo filiazione: Icc rinforzata da back-up (kA)")
    tensione_V: Optional[float] = None
    condizioni: Optional[str] = None
    # provenienza (obbligatoria)
    fonte_tabella: str = Field(..., description="documento + sezione/pagina della tabella")
    revisione: str = Field(..., description="codice doc / revisione / edizione")
    vigenza: str

    @field_validator("id", "monte_serie", "valle_serie", "fonte_tabella", "revisione")
    @classmethod
    def _ascii(cls, v: str) -> str:
        if not str(v).strip() or not str(v).isascii():
            raise ValueError(f"campo ASCII non vuoto richiesto: {v!r}")
        return v

    @model_validator(mode="after")
    def _coerenza(self) -> "CoordinamentoEntry":
        if self.tipo not in TIPI:
            raise ValueError(f"tipo non valido: {self.tipo!r} (attesi {sorted(TIPI)})")
        if self.tipo == "selettivita":
            if self.esito not in {"totale", "parziale"}:
                raise ValueError("selettivita: esito atteso 'totale' o 'parziale'")
            if self.esito == "parziale" and self.limite_selettivita_kA is None:
                raise ValueError(
                    "selettivita parziale senza limite_selettivita_kA: valore di tabella mancante "
                    "(non si inventa: voce non caricabile)"
                )
            if self.esito == "parziale" and float(self.limite_selettivita_kA) <= 0:
                raise ValueError("limite_selettivita_kA deve essere > 0")
        if self.tipo == "filiazione" and self.icc_backup_kA is None:
            raise ValueError("filiazione senza icc_backup_kA: valore di tabella mancante (non si inventa)")
        return self

    def chiave_monte(self) -> str:
        return chiave_dispositivo(self.monte_costruttore, self.monte_serie, self.monte_curva, self.monte_In_A)

    def chiave_valle(self) -> str:
        return chiave_dispositivo(self.valle_costruttore, self.valle_serie, self.valle_curva, self.valle_In_A)


def carica_coordinamento(coord_dir: Union[str, Path] = _COORD_DIR) -> tuple[list[CoordinamentoEntry], list[dict]]:
    """Carica tutte le entry di coordinamento dai seed. Voci non valide -> scartate con motivo."""
    entries: list[CoordinamentoEntry] = []
    scartati: list[dict] = []
    for f in sorted(Path(coord_dir).glob("*.json")):
        data = json.loads(Path(f).read_text(encoding="utf-8"))
        recs = data["coordinamenti"] if isinstance(data, dict) and "coordinamenti" in data else data
        for rec in recs:
            try:
                entries.append(CoordinamentoEntry(**rec))
            except Exception as e:
                scartati.append({"record": rec, "motivo": str(e)})
    return entries, scartati


def trova(
    entries: list[CoordinamentoEntry],
    monte_key: str,
    valle_key: str,
    tipo: str = "selettivita",
) -> Optional[CoordinamentoEntry]:
    """Cerca la entry per coppia esatta (monte_key, valle_key) e tipo. None se assente (=GAP)."""
    for e in entries:
        if e.tipo == tipo and e.chiave_monte() == monte_key and e.chiave_valle() == valle_key:
            return e
    return None
