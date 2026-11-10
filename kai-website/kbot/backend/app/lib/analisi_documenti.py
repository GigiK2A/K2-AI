"""Memoria di pratica sui documenti: elenco allegati + analisi già svolte, rimessi nel contesto a ogni turno.

Prima (audit 6): dopo molti turni il modello poteva rispondere «non ho accesso al PDF / alla mia
analisi» perché della conversazione restava solo il riassunto compattato. Qui la persistenza non
dipende dalla memoria del modello: l'elenco dei file sta in `collected_data.uploaded_files`
(scritto dall'upload, legato alla sessione e quindi all'utente) e le analisi lunghe prodotte
mentre c'erano allegati sono copiate in `collected_data.analisi_documenti`.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List

SOGLIA_ANALISI = 700          # una risposta più corta non è un'analisi del documento
MAX_ANALISI = 3
CHIARO_MAX = 3000


def elenco(collected: dict) -> List[dict]:
    out = []
    for f in (collected or {}).get("uploaded_files") or []:
        testo = str(f.get("extractedText") or f.get("extractedSummary") or "")
        out.append({"nome": str(f.get("name") or "file"), "tipo": str(f.get("type") or ""),
                    "byte": int(f.get("size") or 0), "metodo": str(f.get("extractionMethod") or ""),
                    "caratteri": len(testo.strip())})
    return out


def registra(collected: dict, testo_risposta: str, domanda: str = "") -> bool:
    """Salva la risposta lunga di un turno con allegati presenti. True se ha registrato."""
    if not (collected or {}).get("uploaded_files"):
        return False
    t = str(testo_risposta or "").strip()
    if len(t) < SOGLIA_ANALISI or "CONSULENZA_SUMMARY" in t:
        return False
    voci = list(collected.get("analisi_documenti") or [])
    voci.append({"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                 "file": [f["nome"] for f in elenco(collected)],
                 "domanda": str(domanda or "")[:300], "testo": t[:6000]})
    collected["analisi_documenti"] = voci[-MAX_ANALISI:]
    return True


def blocco(collected: dict) -> str:
    """Testo per il prompt: documenti della pratica e analisi precedenti (vuoto se non c'è nulla)."""
    docs = elenco(collected)
    if not docs:
        return ""
    righe = ["\nDOCUMENTI DI QUESTA PRATICA (caricati dall'utente in questa conversazione, restano disponibili):"]
    for d in docs:
        stato = (f"{d['caratteri']} caratteri di testo letto" if d["caratteri"] > 80
                 else "nessun testo estraibile (scansione/immagine illeggibile)")
        righe.append(f"- {d['nome']} — {stato}")
    righe.append("Non dire mai di non avere accesso a questi documenti o alla loro analisi: sono qui sotto. "
                 "Se un passaggio non compare negli estratti, dillo e indica cosa serve (pagina, sezione).")
    voci = (collected or {}).get("analisi_documenti") or []
    if voci:
        righe.append("ANALISI GIÀ SVOLTE SUI DOCUMENTI (tue risposte precedenti, da riusare senza rifare tutto):")
        for v in voci[-2:]:
            righe.append(f"[{v.get('ts', '')}] «{v.get('domanda', '')}»\n{str(v.get('testo', ''))[:CHIARO_MAX]}")
    return "\n".join(righe) + "\n"
