"""
formatters.py
-------------
Fonctions de formatage des valeurs issues du JSON pour affichage
dans les tables PyQt6. Isolé pour pouvoir ajouter facilement de
nouveaux formats (dates, angles en degrés, unités, etc.) sans
toucher au code des widgets.
"""


def formater_valeur(v) -> str:
    """Formate une valeur de paramètre/attribut pour affichage en cellule.

    Règles :
      - liste de 2 éléments  -> "x=.., y=.."
      - liste de 3 éléments  -> "x=.., y=.., z=.."
      - liste de N éléments  -> "v1=.., v2=.., ..."
      - float                 -> arrondi à 4 décimales, zéros inutiles
                                  supprimés (ex: 3.0000000000000013 -> "3")
      - None                  -> chaîne vide
      - autre                 -> str(v)
    """
    if isinstance(v, list):
        if len(v) == 2:
            return f"x={formater_valeur(v[0])}, y={formater_valeur(v[1])}"
        if len(v) == 3:
            return (
                f"x={formater_valeur(v[0])}, "
                f"y={formater_valeur(v[1])}, "
                f"z={formater_valeur(v[2])}"
            )
        return ", ".join(f"v{i + 1}={formater_valeur(e)}" for i, e in enumerate(v))

    if isinstance(v, float):
        if v == 0:
            return "0"
        return f"{v:.4f}".rstrip("0").rstrip(".")

    if v is None:
        return ""

    return str(v)
