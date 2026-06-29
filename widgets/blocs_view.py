"""
widgets/blocs_view.py
----------------------
Vue des blocs dynamiques avec menu contextuel + highlight de recherche.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QColor
from PyQt6.QtWidgets import (
    QApplication, QHeaderView, QLabel, QMenu,
    QTableWidget, QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget,
)

from formatters import formater_valeur
import styles


def _wrap_table(table: QTableWidget) -> QWidget:
    w = QWidget()
    lay = QVBoxLayout(w)
    lay.setContentsMargins(0, 8, 0, 0)
    lay.addWidget(table)
    return w


def _creer_table(headers: list[str]) -> QTableWidget:
    table = QTableWidget()
    table.setColumnCount(len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    table.setSortingEnabled(True)
    table.verticalHeader().setVisible(False)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
    table.horizontalHeader().setStretchLastSection(True)
    table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
    table.customContextMenuRequested.connect(lambda pos, t=table: _menu_contextuel(t, pos))
    return table


def _menu_contextuel(table: QTableWidget, pos) -> None:
    menu = QMenu(table)
    row = table.rowAt(pos.y())

    act_cell = QAction("Copier la cellule", table)
    act_cell.triggered.connect(lambda: _copier_cellule(table, pos))
    menu.addAction(act_cell)

    act_row = QAction("Copier la ligne", table)
    act_row.triggered.connect(lambda: _copier_ligne(table, row))
    menu.addAction(act_row)

    menu.addSeparator()

    act_all = QAction("Copier tout (TSV)", table)
    act_all.triggered.connect(lambda: _copier_tout(table))
    menu.addAction(act_all)

    menu.exec(table.viewport().mapToGlobal(pos))


def _copier_cellule(table, pos):
    item = table.itemAt(pos)
    if item:
        QApplication.clipboard().setText(item.text())


def _copier_ligne(table, row):
    if row < 0: return
    vals = [table.item(row, c).text() if table.item(row, c) else "" for c in range(table.columnCount())]
    QApplication.clipboard().setText("\t".join(vals))


def _copier_tout(table):
    lines = ["\t".join(table.horizontalHeaderItem(c).text() for c in range(table.columnCount()))]
    for row in range(table.rowCount()):
        if not table.isRowHidden(row):
            vals = [table.item(row, c).text() if table.item(row, c) else "" for c in range(table.columnCount())]
            lines.append("\t".join(vals))
    QApplication.clipboard().setText("\n".join(lines))


def _table_item(text: str, bg: QColor | None = None) -> QTableWidgetItem:
    item = QTableWidgetItem(text)
    item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    if bg is not None:
        item.setBackground(bg)
    return item


class BlocsView(QWidget):

    blockSelected = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 8, 0, 0)
        self.sub_tabs: QTabWidget | None = None
        self.bloc_tables: list[QTableWidget] = []
        self._current_filter = ""

    def _on_table_selection_changed(self, table: QTableWidget) -> None:
        ranges = table.selectedRanges()
        if not ranges:
            return
        row = ranges[0].topRow()
        item = table.item(row, 0)
        if item:
            bloc = item.data(Qt.ItemDataRole.UserRole)
            if isinstance(bloc, dict):
                self.blockSelected.emit(bloc)

    def charger(self, blocs: list[dict]) -> str:
        if self.sub_tabs is not None:
            self._layout.removeWidget(self.sub_tabs)
            self.sub_tabs.deleteLater()
            self.sub_tabs = None
        self.bloc_tables = []

        if not blocs:
            label = QLabel("Aucun bloc dynamique trouvé.")
            label.setObjectName("sectionLabel")
            self._layout.addWidget(label)
            return "Aucun bloc dynamique trouvé."

        groupes: dict[str, list[dict]] = {}
        for bloc in blocs:
            groupes.setdefault(bloc.get("nom", "(sans nom)"), []).append(bloc)

        self.sub_tabs = QTabWidget()
        self.sub_tabs.setObjectName("subTabs")
        self._layout.addWidget(self.sub_tabs)

        qc = styles.qcolors()
        for nom_type in sorted(groupes.keys()):
            instances = groupes[nom_type]
            table = self._construire_table_type(instances, qc)
            table.itemSelectionChanged.connect(lambda t=table: self._on_table_selection_changed(t))
            self.bloc_tables.append(table)
            self.sub_tabs.addTab(_wrap_table(table), f"{nom_type}  ({len(instances)})")

        if self._current_filter:
            self.appliquer_filtre(self._current_filter)

        return f"{len(blocs)} bloc(s) dynamique(s) — {len(groupes)} type(s)."

    @staticmethod
    def _construire_table_type(instances, qc) -> QTableWidget:
        attr_keys: list[str] = []
        param_keys: list[str] = []
        for bloc in instances:
            for k in (bloc.get("attributs", {}) or {}).keys():
                if k not in attr_keys: attr_keys.append(k)
            for k in (bloc.get("parametres", {}) or {}).keys():
                if k not in param_keys: param_keys.append(k)

        headers = ["Layer"]
        headers += [f"Attr: {k}" for k in attr_keys]
        headers += [f"Param: {k}" for k in param_keys]

        table = _creer_table(headers)
        table.setSortingEnabled(False)

        c = styles.couleurs()
        for idx, bloc in enumerate(instances):
            row = table.rowCount()
            table.insertRow(row)
            bg = QColor(c["bg_row_a"]) if idx % 2 == 0 else QColor(c["bg_row_b"])

            item_layer = _table_item(bloc.get("layer", ""), bg=bg)
            item_layer.setData(Qt.ItemDataRole.UserRole, bloc)
            table.setItem(row, 0, item_layer)

            attributs = bloc.get("attributs", {}) or {}
            for i, k in enumerate(attr_keys):
                table.setItem(row, 1 + i, _table_item(formater_valeur(attributs.get(k, "")), bg=bg))
            parametres = bloc.get("parametres", {}) or {}
            for i, k in enumerate(param_keys):
                table.setItem(row, 1 + len(attr_keys) + i, _table_item(formater_valeur(parametres.get(k, "")), bg=bg))

        table.setSortingEnabled(True)
        return table

    def appliquer_filtre(self, texte: str) -> None:
        self._current_filter = texte
        t = texte.strip().lower()
        qc = styles.qcolors()
        c = styles.couleurs()
        for table in self.bloc_tables:
            for row in range(table.rowCount()):
                match = t != "" and any(
                    table.item(row, col) and t in table.item(row, col).text().lower()
                    for col in range(table.columnCount())
                )
                visible = t == "" or match
                table.setRowHidden(row, not visible)
                if t:
                    bg_normal = QColor(c["bg_row_a"]) if row % 2 == 0 else QColor(c["bg_row_b"])
                    bg = qc["highlight_bg"] if match else bg_normal
                    for col in range(table.columnCount()):
                        item = table.item(row, col)
                        if item:
                            item.setBackground(bg)
                            if match:
                                item.setForeground(qc["highlight_fg"])

    def selectionner_bloc_type(self, nom_type: str) -> None:
        if self.sub_tabs is None:
            return
        for i in range(self.sub_tabs.count()):
            if self.sub_tabs.tabText(i).startswith(nom_type + " "):
                self.sub_tabs.setCurrentIndex(i)
                break

    def toutes_les_tables(self) -> list[QTableWidget]:
        return list(self.bloc_tables)

