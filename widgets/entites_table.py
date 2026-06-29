"""
widgets/entites_table.py
------------------------
Table du "Résumé entités" avec menu contextuel + highlight de recherche.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QColor
from PyQt6.QtWidgets import (
    QApplication, QHeaderView, QMenu, QTableWidget, QTableWidgetItem
)

import styles


class EntitesTable(QTableWidget):

    entitySelected = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(["Type d'entité", "Nombre"])
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSortingEnabled(True)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.horizontalHeader().setStretchLastSection(True)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._menu_contextuel)
        self.itemSelectionChanged.connect(self._on_selection_changed)

        self._highlight_text = ""

    def _on_selection_changed(self) -> None:
        ranges = self.selectedRanges()
        if not ranges:
            return
        row = ranges[0].topRow()
        item = self.item(row, 0)
        if item:
            data = item.data(Qt.ItemDataRole.UserRole)
            if isinstance(data, dict):
                self.entitySelected.emit(data)

    def charger(self, resume: dict) -> None:
        self.setSortingEnabled(False)
        self.setRowCount(0)
        qc = styles.qcolors()
        total = sum(resume.values()) if resume else 0
        for nom, count in sorted(resume.items()):
            row = self.rowCount()
            self.insertRow(row)
            item_n = self._item(nom)
            item_n.setData(Qt.ItemDataRole.UserRole, {"type": nom, "count": count, "total": total})
            self.setItem(row, 0, item_n)
            self.setItem(row, 1, self._item(str(count), align_right=True))
        row = self.rowCount()
        self.insertRow(row)
        item_t = self._item("TOTAL")
        item_t.setData(Qt.ItemDataRole.UserRole, {"type": "TOTAL", "count": total, "total": total})
        item_t.setForeground(qc["accent_green"])
        f = item_t.font(); f.setBold(True); item_t.setFont(f)
        item_c = self._item(str(total), align_right=True)
        item_c.setForeground(qc["accent_green"]); item_c.setFont(f)
        self.setItem(row, 0, item_t)
        self.setItem(row, 1, item_c)
        self.setSortingEnabled(True)

        if self._highlight_text:
            self.appliquer_highlight(self._highlight_text)

    def appliquer_highlight(self, texte: str) -> None:
        self._highlight_text = texte.lower()
        qc = styles.qcolors()
        c = styles.couleurs()
        bg_normal_a = QColor(c["bg_row_a"])
        bg_normal_b = QColor(c["bg_row_b"])
        for row in range(self.rowCount()):
            match = texte != "" and any(
                self.item(row, col) and texte.lower() in self.item(row, col).text().lower()
                for col in range(self.columnCount())
            )
            bg = qc["highlight_bg"] if match else (bg_normal_a if row % 2 == 0 else bg_normal_b)
            for col in range(self.columnCount()):
                item = self.item(row, col)
                if item:
                    item.setBackground(bg)
                    if match:
                        item.setForeground(qc["highlight_fg"])

    def _menu_contextuel(self, pos) -> None:
        menu = QMenu(self)
        row = self.rowAt(pos.y())

        act_copy = QAction("Copier la cellule", self)
        act_copy.triggered.connect(lambda: self._copier_cellule(pos))
        menu.addAction(act_copy)

        act_copy_row = QAction("Copier la ligne", self)
        act_copy_row.triggered.connect(lambda: self._copier_ligne(row))
        menu.addAction(act_copy_row)

        menu.addSeparator()

        act_copy_all = QAction("Copier tout (TSV)", self)
        act_copy_all.triggered.connect(self._copier_tout)
        menu.addAction(act_copy_all)

        menu.exec(self.viewport().mapToGlobal(pos))

    def _copier_cellule(self, pos) -> None:
        item = self.itemAt(pos)
        if item:
            QApplication.clipboard().setText(item.text())

    def _copier_ligne(self, row: int) -> None:
        if row < 0: return
        vals = []
        for col in range(self.columnCount()):
            item = self.item(row, col)
            vals.append(item.text() if item else "")
        QApplication.clipboard().setText("\t".join(vals))

    def _copier_tout(self) -> None:
        lines = []
        headers = [self.horizontalHeaderItem(c).text() for c in range(self.columnCount())]
        lines.append("\t".join(headers))
        for row in range(self.rowCount()):
            vals = []
            for col in range(self.columnCount()):
                item = self.item(row, col)
                vals.append(item.text() if item else "")
            lines.append("\t".join(vals))
        QApplication.clipboard().setText("\n".join(lines))

    @staticmethod
    def _item(text: str, align_right: bool = False) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        if align_right:
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        return item
