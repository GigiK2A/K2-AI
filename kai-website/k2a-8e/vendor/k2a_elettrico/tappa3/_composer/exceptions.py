"""Eccezioni e segnalazioni del Layer 4 Composer."""
from __future__ import annotations


class ComposerError(Exception):
    """Errore base del composer."""


class TemplateNotFoundError(ComposerError):
    """Template DOCX/markdown non trovato."""


class IncompleteSchemaError(ComposerError):
    """Mancano campi critici per generare il documento."""


class NarratorFallbackUsed(Warning):
    """Segnalazione (non eccezione): il narratore ha usato il testo di fallback."""
