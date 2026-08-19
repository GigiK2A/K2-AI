"""Come un reparto usa la sua biblioteca professionale.

Il problema, misurato il 19 ago 2026: 312 playbook in `skills_lib` per 3,2 milioni di
caratteri, e gli agenti ne leggevano ~3.100 — lo 0,1%, per di più frontmatter YAML.

Il problema opposto non si risolve con un tetto più alto: un reparto ha fra 24 e 77
skill per 260.000-1.047.000 caratteri di testo pieno. Metterle tutte nel prompt sarebbe
un quarto di milione di token e annegherebbe i dati reali dell'azienda.

Quindi: **indice completo sempre, testo pieno su scelta**.
  1. `indice()` — nome e descrizione di TUTTE le skill del reparto (4-8k caratteri):
     l'agente sa esattamente cosa ha in mano, niente è invisibile;
  2. `scegli()` — un passo economico decide quali aprire per i dati di OGGI, con
     ripiego deterministico se il modello non collabora;
  3. `blocco_metodo()` — il testo operativo delle scelte, senza intestazioni.

È la stessa disciplina del fattore 3 dei 12-Factor Agents (own your context window):
il contesto si costruisce, non si riversa.
"""
from __future__ import annotations

import os
import re
from typing import Any

# Quante skill aprire per intero e con quanto testo ciascuna.
SKILL_APERTE = int(os.environ.get("AIOS_SKILL_APERTE", "5"))
SKILL_CARATTERI = int(os.environ.get("AIOS_SKILL_CARATTERI", "4000"))
# Quante voci di indice al massimo (77 è il reparto più fornito: ci stanno tutte).
INDICE_MAX = int(os.environ.get("AIOS_SKILL_INDICE_MAX", "120"))
DESCRIZIONE_MAX = 140


def nomi_reparto(skills: Any, dominio: str, curate: list | None = None) -> list[str]:
    """Tutte le skill del reparto: prima quelle curate a mano nel config, poi le
    instradate automaticamente (`for_domain`), senza duplicati."""
    fuori = list(curate or [])
    try:
        for n in skills.for_domain(dominio, INDICE_MAX):
            if n not in fuori:
                fuori.append(n)
    except Exception:
        pass
    return fuori[:INDICE_MAX]


def indice(skills: Any, nomi: list[str]) -> str:
    """Indice leggibile di tutta la biblioteca del reparto."""
    righe = []
    for n in nomi:
        try:
            desc = (skills.describe(n) or "").strip().replace("\n", " ")
        except Exception:
            desc = ""
        righe.append(f"- {n}: {desc[:DESCRIZIONE_MAX]}")
    if not righe:
        return ""
    return ("\n\n# LA TUA BIBLIOTECA (tutte le tue competenze, "
            f"{len(righe)} playbook)\n" + "\n".join(righe))


_SCHEMA_SCELTA = {"type": "object", "properties": {
    "skill": {"type": "array", "items": {"type": "string"}}}, "required": ["skill"]}


def scegli(llm: Any, nomi: list[str], indice_testo: str, contesto: str,
           quante: int | None = None) -> list[str]:
    """Quali playbook aprire per il lavoro di oggi.

    Passo economico: vede solo l'indice e una sintesi dei dati, non i playbook interi.
    Se il modello non risponde o inventa nomi, si ripiega sull'ordine di pertinenza di
    `for_domain` — mai lasciare il reparto senza metodo per un errore del modello."""
    quante = quante or SKILL_APERTE
    ripiego = nomi[:quante]
    if not nomi or llm is None:
        return ripiego
    try:
        out = llm.complete_json(
            system=("Scegli i playbook da aprire per il lavoro di oggi. Rispondi SOLO "
                    "con i nomi esatti presi dall'elenco, quelli più utili ai DATI di "
                    "oggi. Meglio pochi e pertinenti che tanti."),
            user=(indice_testo + "\n\n# DATI DI OGGI (sintesi)\n" + contesto[:1500]
                  + f"\n\nScegli al massimo {quante} nomi dall'elenco."),
            schema=_SCHEMA_SCELTA)
        scelti = [str(x).strip() for x in (out.get("skill") or []) if str(x).strip()]
    except Exception:
        return ripiego
    validi = [n for n in scelti if n in nomi][:quante]
    # completa col ripiego se il modello ne ha scelte troppo poche o inesistenti
    for n in ripiego:
        if len(validi) >= quante:
            break
        if n not in validi:
            validi.append(n)
    return validi


def blocco_metodo(skills: Any, nomi: list[str], cap: int | None = None) -> str:
    """Il testo operativo dei playbook scelti (senza frontmatter)."""
    cap = cap or SKILL_CARATTERI
    pezzi = []
    for n in nomi:
        try:
            pezzi.append(f"## SKILL: {n}\n" + skills.estratto(n, cap))
        except KeyError:
            continue
    if not pezzi:
        return ""
    return "\n\n# METODO (i playbook che hai scelto, per esteso)\n" + "\n\n".join(pezzi)


def competenza(skills: Any, llm: Any, dominio: str, curate: list | None,
               contesto: str) -> str:
    """Blocco completo da mettere nel prompt: indice di tutto + metodo delle scelte."""
    if skills is None:
        return ""
    nomi = nomi_reparto(skills, dominio, curate)
    if not nomi:
        return ""
    idx = indice(skills, nomi)
    scelti = scegli(llm, nomi, idx, contesto)
    return idx + blocco_metodo(skills, scelti, SKILL_CARATTERI)


# ---- qualità sopra quantità -------------------------------------------------
# Prima le istruzioni chiedevano "max 8 proposte" e "copri più aree possibile":
# premiavano il numero di righe. Un CFO vero produce un'analisi che cambia una
# decisione, non otto task. Il tetto basso è la leva più economica sulla qualità.
PROPOSTE_MAX = int(os.environ.get("AIOS_PROPOSTE_MAX", "3"))

ESIGENZA_QUALITA = (
    f"\n\nQUALITÀ SOPRA QUANTITÀ: massimo {PROPOSTE_MAX} proposte, non una in più. "
    "Ognuna deve avere, nel campo motivo: (a) i NUMERI presi dai dati reali qui sopra "
    "— se il numero non c'è nei dati, non esiste e non si scrive; (b) l'alternativa che "
    "hai scartato e perché; (c) cosa ti farebbe cambiare idea. Una proposta senza numeri "
    "o senza alternativa scartata è un'opinione, e le opinioni non si accodano. "
    "Meglio una proposta che cambia una decisione che otto righe di attività.")


def pulisci_placeholder(testo: str) -> str:
    """Toglie i segnaposto non risolti da un testo destinato all'umano."""
    return re.sub(r"\{\{[^}]*\}\}|\$\{[^}]*\}", "…", testo or "")
