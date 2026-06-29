"""
json_loader.py
---------------
Lecture et écriture des fichiers JSON d'export AutoCAD.
Isolé du reste de l'UI pour pouvoir changer le format de stockage
(SQLite, autre schéma, etc.) sans toucher aux widgets.
"""

import json
from pathlib import Path
from typing import Any


class JsonLoadError(Exception):
    """Levée quand un fichier JSON d'export est illisible ou invalide."""


def charger_export(chemin: Path) -> dict[str, Any]:
    """Charge un fichier JSON d'export AutoCAD.

    Retourne un dict avec au minimum les clés "resume_entites" et
    "blocs_dynamiques" (listes/dicts vides si absentes du fichier).

    Lève JsonLoadError si le fichier est illisible ou mal formé.
    """
    try:
        with open(chemin, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        raise JsonLoadError(f"Impossible de lire le fichier :\n{exc}") from exc

    if not isinstance(data, dict):
        raise JsonLoadError("Le fichier JSON ne contient pas un objet valide.")

    data.setdefault("resume_entites", {})
    data.setdefault("blocs_dynamiques", [])
    return data


def sauvegarder_export(
    entites: dict, blocs: list[dict], chemin: Path | str = "autocad_export.json"
) -> None:
    """Sauvegarde les données extraites au format JSON attendu par le viewer."""
    data = {
        "resume_entites": entites,
        "blocs_dynamiques": blocs,
    }
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
