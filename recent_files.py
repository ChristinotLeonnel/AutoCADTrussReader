"""
recent_files.py
---------------
Gestion de l'historique des fichiers récents (max 10 entrées)
stocké dans un fichier JSON à côté de l'exécutable.
"""

import json
from pathlib import Path

MAX_RECENT = 10
_STORE = Path(__file__).parent / ".recent_files.json"


def charger() -> list[str]:
    try:
        with open(_STORE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [p for p in data if Path(p).exists()][:MAX_RECENT]
    except Exception:
        return []


def ajouter(chemin: str | Path) -> None:
    chemins = charger()
    chemin = str(Path(chemin).resolve())
    if chemin in chemins:
        chemins.remove(chemin)
    chemins.insert(0, chemin)
    chemins = chemins[:MAX_RECENT]
    try:
        with open(_STORE, "w", encoding="utf-8") as f:
            json.dump(chemins, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def vider() -> None:
    try:
        _STORE.unlink(missing_ok=True)
    except Exception:
        pass
