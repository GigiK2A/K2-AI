"""Schema voce-articolo per il DB articoli del cervello (MT-E1).

Riusa la struttura `schema_articolo_interruttore`: chiavi **ASCII**, campi
`id / codice_articolo / costruttore / tipo_dispositivo / dati_targa (per famiglia)
/ etim_class / simbolo_grafico_id / fonte / vigenza`.

Principio invariante (come il resto del cervello): **dati SOLO reali con fonte
dichiarata**; un dato di targa obbligatorio mancante = voce **non caricabile**
(si scarta con motivo), **mai** completata o inventata.
"""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

# Caratteristiche di intervento ammesse per gli interruttori magnetotermici (CEI EN 60898-1 / 60947-2).
CURVE_VALIDE = {"B", "C", "D", "K", "Z"}
POLI_VALIDI = {1, 2, 3, 4}

# Dati di targa OBBLIGATORI per famiglia (chiavi ASCII). Estendibile ad altre famiglie.
TARGA_OBBLIGATORIA = {
    "interruttore": ("In_A", "curva", "poli", "potere_int_Icn_kA"),
}


class Articolo(BaseModel):
    """Voce-articolo di catalogo. Tutte le chiavi sono ASCII."""

    id: str = Field(..., description="identificativo ASCII univoco, es. 'abb_s201_c16'")
    codice_articolo: str = Field(..., description="codice/order code del costruttore, es. '2CDS251001R0164'")
    costruttore: str = Field(..., description="es. 'ABB'")
    tipo_dispositivo: str = Field(..., description="es. 'interruttore_magnetotermico'")
    dati_targa: dict[str, Any] = Field(..., description="dati di targa per famiglia (chiavi ASCII)")
    etim_class: Optional[str] = Field(None, description="classe ETIM, es. 'EC000042' (MCB); None se non groundata")
    simbolo_grafico_id: Optional[str] = Field(None, description="id del simbolo grafico (link al braccio/editor)")
    fonte: str = Field(..., description="URL/datasheet da cui provengono i dati di targa")
    vigenza: str = Field(..., description="validita' del dato di catalogo, es. 'vigente 2026-06'")

    @field_validator("id")
    @classmethod
    def _id_ascii(cls, v: str) -> str:
        if not v or not v.isascii():
            raise ValueError("id deve essere una stringa ASCII non vuota")
        return v

    @field_validator("codice_articolo", "costruttore", "tipo_dispositivo", "fonte", "vigenza")
    @classmethod
    def _non_vuoto(cls, v: str) -> str:
        if not str(v).strip():
            raise ValueError("campo obbligatorio vuoto (non si inventa: voce non caricabile)")
        return v

    @field_validator("dati_targa")
    @classmethod
    def _targa_chiavi_ascii(cls, v: dict[str, Any]) -> dict[str, Any]:
        for k in v:
            if not str(k).isascii():
                raise ValueError(f"chiave dati_targa non ASCII: {k!r}")
        return v

    @model_validator(mode="after")
    def _valida_famiglia(self) -> "Articolo":
        """Validazione dei dati di targa per FAMIGLIA. Mancante = errore (non si inventa)."""
        for prefisso, obbligatori in TARGA_OBBLIGATORIA.items():
            if self.tipo_dispositivo.startswith(prefisso):
                t = self.dati_targa
                for campo in obbligatori:
                    if campo not in t or t[campo] in (None, ""):
                        raise ValueError(
                            f"{prefisso}: dato di targa obbligatorio mancante '{campo}' "
                            "(mancante = voce non caricabile, mai inventata)"
                        )
                if t["curva"] not in CURVE_VALIDE:
                    raise ValueError(f"curva non valida: {t['curva']!r} (attese {sorted(CURVE_VALIDE)})")
                if int(t["poli"]) not in POLI_VALIDI:
                    raise ValueError(f"poli non valido: {t['poli']!r} (attesi {sorted(POLI_VALIDI)})")
                if float(t["In_A"]) <= 0 or float(t["potere_int_Icn_kA"]) <= 0:
                    raise ValueError("In_A e potere_int_Icn_kA devono essere > 0")
        return self


def valida_articolo(record: dict) -> Articolo:
    """Valida un record grezzo -> Articolo. Solleva se non valido (mai inventa/completa)."""
    return Articolo(**record)
