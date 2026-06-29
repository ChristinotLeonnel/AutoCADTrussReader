"""
analyse_runner.py
-------------------
Pont entre l'UI et tiont.py : appelle les fonctions d'extraction
AutoCAD directement (même process, pas de sous-processus) et
remonte des erreurs lisibles si AutoCAD n'est pas joignable.

tiont.py doit se trouver dans le même dossier que ce fichier.
"""

from pathlib import Path
from typing import Any

import tiont


class AnalyseError(Exception):
    """Levée quand l'extraction AutoCAD échoue (AutoCAD fermé, COM, etc.)."""


def lancer_analyse(chemin_sortie: Path | str) -> dict[str, Any]:
    """
    Extrait les entités et blocs dynamiques du dessin AutoCAD actif,
    sauvegarde dans chemin_sortie (fichier .json ou dossier), et retourne
    les données ainsi que le chemin du fichier JSON écrit.
    """
    try:
        acad = tiont.get_autocad()
    except Exception as exc:
        raise AnalyseError(
            "AutoCAD n'est pas accessible.\n"
            "Vérifie qu'AutoCAD est bien lancé avec un dessin ouvert.\n\n"
            f"Détail technique : {exc}"
        ) from exc

    try:
        model_space = tiont.get_model_space(acad)
        filename = Path(acad.ActiveDocument.FullName).stem
    except Exception as exc:
        raise AnalyseError(
            "Impossible d'accéder au document actif d'AutoCAD.\n"
            "Vérifie qu'un dessin (.dwg) est bien ouvert.\n\n"
            f"Détail technique : {exc}"
        ) from exc

    try:
        entites = tiont.lister_entites(model_space)
        blocs = tiont.collecter_blocs_dynamiques(model_space)
    except Exception as exc:
        raise AnalyseError(
            "Erreur pendant la lecture des entités du dessin.\n\n"
            f"Détail technique : {exc}"
        ) from exc

    try:
        fichier_json = tiont.sauvegarder_json(
            entites=entites,
            blocs=blocs,
            chemin=chemin_sortie,
            filename=filename,
        )
    except OSError as exc:
        raise AnalyseError(
            f"Impossible d'écrire le fichier de sortie :\n{chemin_sortie}\n\n"
            f"Détail technique : {exc}"
        ) from exc

    return {
        "resume_entites": entites,
        "blocs_dynamiques": blocs,
        "fichier": Path(fichier_json),
    }
