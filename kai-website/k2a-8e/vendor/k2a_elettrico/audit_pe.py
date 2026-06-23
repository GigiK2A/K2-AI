"""Audit di coerenza di un Progetto Esecutivo (PE) — "linter" documentale.

Rule-based, deterministico e ad ALTA PRECISIONE (pochi falsi positivi): data la lista
dei paragrafi di un PE (+ contesto), rileva i difetti di coerenza tipici di un documento
generato/revisionato. Pensato come controllo finale prima della consegna.

Regole (scelte per precisione, non per copertura esaustiva):
  R2 — norma di connessione vs punto di consegna (POD MT → CEI 0-16, 0-21 solo sub-BT)
  R4 — tensione di contatto UE oltre il limite UTP senza condizione esplicita
  R5 — token obsoleti: stringhe note-superate ancora presenti (escluse forme storiche "era X")

NB: NON si tenta un confronto numerico "automatico" generico sulle correnti (Icc/Ipk),
perché in un PE quelle grandezze variano legittimamente per nodo e configurazione
(MT vs BT, parallelo vs N-1, calcolato vs tenuta): un confronto naïve genererebbe falsi
positivi. Per i valori da bonificare si usa R5 con token espliciti (workflow: dopo una
correzione, si elencano i valori superati e si verifica che non sopravvivano nel testo).
Nessun LLM.
"""
from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field

Severita = Literal["alta", "media", "bassa"]


class Finding(BaseModel):
    regola: str
    severita: Severita
    oggetto: str
    riga: str
    messaggio: str
    suggerimento: str


class AuditPEInput(BaseModel):
    paragrafi: list[str] = Field(..., description="Testo dei paragrafi del PE (in ordine)")
    punto_consegna: Literal["MT", "BT"] = Field("MT", description="Punto di consegna verso DSO")
    token_obsoleti: list[str] = Field(
        default_factory=list,
        description="Stringhe superate da NON trovare più (es. ['48,8 kA','1.800 kW']). "
                    "Le forme storiche 'era X' / 'originale X' sono ignorate.")
    limite_UE_V: float = Field(200.0, description="Limite UTP per la tensione di contatto (R4)")


class AuditPEOutput(BaseModel):
    esito: Literal["pulito", "rilievi"]
    n_findings: int
    findings: list[Finding]
    norma_riferimento: str = "Controllo coerenza documentale K2A (CEI 0-16/0-21, CEI EN 50522)"


def audit_coerenza_pe(inp: AuditPEInput) -> AuditPEOutput:
    findings: list[Finding] = []
    testo = [p for p in inp.paragrafi if p and p.strip()]
    full = "\n".join(testo).lower()

    # --- R2: norma di connessione vs punto di consegna ---
    if inp.punto_consegna == "MT":
        cita_021_if = bool(re.search(r"0-21[^\n]{0,40}(interfaccia|spi|dso)|"
                                     r"(interfaccia|spi)[^\n]{0,40}0-21", full))
        cita_016 = "0-16" in full
        sev = None
        if cita_021_if and not cita_016:
            sev = "alta"
            msg = ("POD in MT ma l'interfaccia verso il DSO è riferita alla CEI 0-21 senza "
                   "alcun richiamo alla CEI 0-16.")
        elif cita_021_if:
            sev = "media"
            msg = ("POD in MT: verificare che la CEI 0-21 sia usata SOLO per il sotto-sistema BT "
                   "(inverter), non come interfaccia principale verso il DSO.")
        if sev:
            riga = next((t.strip()[:120] for t in testo if "0-21" in t), "")
            findings.append(Finding(
                regola="R2 norma-connessione", severita=sev, oggetto="Interfaccia DSO",
                riga=riga, messaggio=msg,
                suggerimento="Utente attivo in MT → norma principale verso DSO CEI 0-16 (SPG/PG); "
                             "CEI 0-21 solo per il sotto-sistema BT."))

    # --- R4: tensione di contatto UE oltre il limite ---
    for t in testo:
        m = re.search(r"\bU\s*E\b[^0-9]{0,6}([0-9]+)\s*V|UE\s*[=≈]\s*([0-9]+)\s*V", t)
        if m:
            ue = float(m.group(1) or m.group(2))
            if ue > inp.limite_UE_V and "condizion" not in t.lower():
                findings.append(Finding(
                    regola="R4 terra-UE", severita="alta", oggetto="Tensione di contatto UE",
                    riga=t.strip()[:120],
                    messaggio=f"UE={ue:.0f} V > limite UTP {inp.limite_UE_V:.0f} V senza condizione esplicita.",
                    suggerimento="Verificare la terra (misura ρ) o dichiarare l'esito condizionato."))

    # --- R5: token obsoleti ancora presenti ---
    for tok in inp.token_obsoleti:
        tl = tok.lower()
        for t in testo:
            low = t.lower()
            idx = low.find(tl)
            while idx != -1:
                ctx = low[max(0, idx - 10):idx]
                if "era" not in ctx and "originale" not in ctx:
                    findings.append(Finding(
                        regola="R5 token-obsoleto", severita="alta", oggetto=tok,
                        riga=t.strip()[:120],
                        messaggio=f"Token superato ancora presente nel testo: «{tok}».",
                        suggerimento="Rimuovere/aggiornare l'occorrenza al valore corrente."))
                    break  # un finding per paragrafo
                idx = low.find(tl, idx + 1)

    return AuditPEOutput(
        esito="rilievi" if findings else "pulito",
        n_findings=len(findings), findings=findings)
