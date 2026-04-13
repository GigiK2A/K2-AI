import json
from typing import Any

from loguru import logger

from core import notion_board
from db.client import get_service_client

# Seed iniziale — viene inserito su Supabase al primo avvio se le chiavi non esistono
MEMORY_SEED: dict[str, dict[str, Any]] = {
    "business.mission": {
        "value": "Aiutare B&B, ristoranti e studi tecnici/PMI a introdurre l'intelligenza artificiale in modo concreto, utile e controllato — progettando sistemi, strumenti e workflow personalizzati che aumentano efficienza, velocità e qualità del lavoro, senza togliere l'uomo dal centro.",
        "category": "business",
    },
    "business.positioning": {
        "value": "Prima l'abbiamo applicata su noi stessi. Dal sito alle app operative, dai sistemi documentali al board di agenti AI. Poi l'abbiamo portata fuori. Chi compra compra metodo, non demo.",
        "category": "business",
    },
    "business.philosophy": {
        "value": "L'IA non sostituisce l'uomo, lo potenzia. Human-in-the-loop non è una limitazione — è il prodotto.",
        "category": "business",
    },
    "business.targets": {
        "value": ["B&B e affittacamere", "Piccoli e medi ristoranti", "Studi tecnici e PMI"],
        "category": "business",
    },
    "business.avoid": {
        "value": [
            "Enterprise strutturate con IT interno",
            "Startup AI-native",
            "Chi vuole sostituire tutto il personale",
            "Chi compete solo sul prezzo",
        ],
        "category": "business",
    },
    "offers.list": {
        "value": [
            {
                "name": "AI Orientation",
                "price_range": "300-600 EUR",
                "duration": "1 settimana",
                "description": "Discovery call + audit + mini roadmap. Porta d'ingresso.",
            },
            {
                "name": "AI Workflow Setup",
                "price_range": "1200-4000 EUR",
                "duration": "2-6 settimane",
                "description": "Implementazione workflow/assistente/tool personalizzato.",
            },
            {
                "name": "AI System Custom",
                "price_range": "5000-15000 EUR",
                "duration": "6-16 settimane",
                "description": "Sistema AI completo su misura con agenti e logica operativa.",
            },
            {
                "name": "AI Continuous Support",
                "price_range": "400-1200 EUR/mese",
                "duration": "Ricorrente",
                "description": "Retainer mensile. Supporto, aggiornamenti, ottimizzazioni.",
            },
        ],
        "category": "offers",
    },
    "proof.cases": {
        "value": [
            "Sito internet costruito interamente con assistenti AI di coding",
            "App per verbali di sopralluogo — strumento operativo verticale in uso reale",
            "Sistemi di gestione interna AI-assisted — operativi, non demo",
            "Sistema di verifica e produzione autonoma documenti",
            "Board di agenti AI operativo — il meta-caso studio in costruzione",
        ],
        "category": "proof",
    },
    "rules.communication": {
        "value": "Linguaggio semplice e concreto con clienti non esperti. Zero gergo tecnico nel marketing. Anti-fuffa, anti-hype. Ogni claim deve avere un caso reale a supporto.",
        "category": "rules",
    },
    "rules.approval": {
        "value": "Nessuna comunicazione esterna, pubblicazione contenuti o impegno economico senza approvazione esplicita del fondatore. Tutti gli output passano per Draft → Review → Approval.",
        "category": "rules",
    },
    "messaging.angles": {
        "value": [
            "AI senza caos — per chi è intimidito e non sa da dove partire",
            "Prima l'abbiamo applicata su noi stessi",
            "Sistemi pratici, non demo da fiera",
            "Uomo al centro, AI come motore",
            "Non vendiamo magia, progettiamo strumenti",
        ],
        "category": "messaging",
    },
}

_cache: dict[str, Any] = {}


def load_memory() -> dict[str, Any]:
    """Carica tutta la memoria condivisa da Supabase. Fa seed se vuota."""
    global _cache
    if notion_board.notion_enabled():
        try:
            rows = notion_board.list_memory_items()
            if not rows:
                logger.info("Memoria condivisa Notion vuota — eseguo seed iniziale")
                for key, value in MEMORY_SEED.items():
                    notion_board.upsert_memory_item(key, value["value"], value["category"])
                rows = notion_board.list_memory_items()
            _cache = {row["key"]: row["value"] for row in rows}
            logger.info(f"Memoria condivisa Notion caricata: {len(_cache)} chiavi")
            return _cache
        except Exception as exc:
            logger.error(f"Errore caricamento memoria Notion: {exc}")
            raise

    client = get_service_client()

    try:
        response = client.table("shared_memory").select("*").execute()
        rows = response.data or []

        if not rows:
            logger.info("Memoria condivisa vuota — eseguo seed iniziale")
            _seed_memory()
            response = client.table("shared_memory").select("*").execute()
            rows = response.data or []

        _cache = {row["key"]: row["value"] for row in rows}
        logger.info(f"Memoria condivisa caricata: {len(_cache)} chiavi")
        return _cache
    except Exception as exc:
        logger.error(f"Errore caricamento memoria: {exc}")
        raise


def invalidate_memory_cache() -> None:
    """Svuota la cache locale della memoria condivisa."""
    global _cache
    _cache = {}
    logger.info("Cache memoria condivisa invalidata")


def get_memory(key: str, default: Any = None) -> Any:
    """Legge una chiave dalla cache. Ricarica da DB se cache vuota."""
    if not _cache:
        load_memory()
    return _cache.get(key, default)


def set_memory(key: str, value: Any, category: str, updated_by: str = "founder") -> None:
    """Aggiorna una chiave nella memoria condivisa e su Supabase."""
    global _cache
    if notion_board.notion_enabled():
        notion_board.upsert_memory_item(key, value, category=category, updated_by=updated_by)
        _cache[key] = value
        logger.info(f"Memoria Notion aggiornata: {key}")
        return

    client = get_service_client()
    client.table("shared_memory").upsert(
        {
            "key": key,
            "value": value,
            "category": category,
            "updated_by": updated_by,
        }
    ).execute()
    _cache[key] = value
    logger.info(f"Memoria aggiornata: {key}")


def get_memory_as_context() -> str:
    """
    Restituisce la memoria condivisa formattata come stringa
    da iniettare nel system prompt di ogni agente.
    """
    if not _cache:
        load_memory()

    sections = {
        "business": [],
        "offers": [],
        "proof": [],
        "rules": [],
        "messaging": [],
    }

    for key, value in _cache.items():
        category = key.split(".")[0]
        if category in sections:
            sections[category].append(f"- {key}: {json.dumps(value, ensure_ascii=False)}")

    context = "## CONTESTO BUSINESS (memoria condivisa)\n\n"
    for category, lines in sections.items():
        if lines:
            context += f"### {category.upper()}\n" + "\n".join(lines) + "\n\n"

    return context


def _seed_memory() -> None:
    """Inserisce il seed iniziale su Supabase."""
    client = get_service_client()
    rows = [{"key": key, "value": value["value"], "category": value["category"]} for key, value in MEMORY_SEED.items()]
    client.table("shared_memory").upsert(rows).execute()
    logger.info(f"Seed memoria eseguito: {len(rows)} chiavi inserite")
