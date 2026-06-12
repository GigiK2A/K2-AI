"""Config di test condivisa.

La suite gira SENZA auth API di default: gli endpoint protetti si testano a parte
(test_api_auth.py / test_security.py) impostando il token via monkeypatch. Se
l'ambiente locale ha `AIOS_API_TOKEN` (es. caricato da `aios/.env`), lo rimuoviamo
qui così i test non-auth non ricevono 401 e la suite resta ermetica e deterministica.
"""
import os

os.environ.pop("AIOS_API_TOKEN", None)
"""Anche l'autonomia in-process non va attivata sotto test."""
os.environ.pop("AIOS_AUTONOMY", None)
