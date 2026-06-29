"""
main.py
-------
Point d'entrée de l'application.

Lancement :
    python main.py
    python main.py chemin/vers/export.json
"""

import sys

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication

from main_window import VisualiseurExport
import styles


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet(styles.feuille_de_style())
    app.setFont(QFont("Consolas", 100))

    json_path = sys.argv[1] if len(sys.argv) > 1 else None
    fenetre = VisualiseurExport(json_path)
    fenetre.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
