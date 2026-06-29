"""
settings_manager.py
-------------------
Gestion de la persistance des réglages de l'application (mode d'enregistrement, etc.)
dans un fichier JSON.
"""

import json
from pathlib import Path

_STORE = Path(__file__).parent / ".settings.json"

DEFAULT_SETTINGS = {
    "export_mode": "default",  # "default", "ask", "custom"
    "custom_export_path": ""
}


def charger() -> dict:
    """Charge les paramètres actuels, retourne les valeurs par défaut si absent."""
    try:
        if _STORE.exists():
            with open(_STORE, "r", encoding="utf-8") as f:
                data = json.load(f)
            settings = DEFAULT_SETTINGS.copy()
            settings.update(data)
            return settings
    except Exception:
        pass
    return DEFAULT_SETTINGS.copy()


def sauvegarder(settings: dict) -> None:
    """Sauvegarde les paramètres fournis dans le stockage permanent."""
    try:
        with open(_STORE, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
