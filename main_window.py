"""
main_window.py
--------------
Fenêtre principale — v3 (Édition CAO)
Nouvelles fonctionnalités conformes aux spécifications de Skill.md :
  - Volet Explorateur (TreeWidget à gauche) avec Drag & Drop de fichiers JSON et menus contextuels.
  - Volet Propriétés (Formulaire de modification à droite) avec filtre de recherche et édition en direct.
  - Volet Console / Log (TextEdit en bas) pour suivre l'activité.
  - Barre d'outils (QToolBar) avec icônes SVG, infobulles, raccourcis et zoom.
  - Double synchronisation active (Tableau <-> Propriétés, Explorateur <-> Onglets).
  - Statut bar affichant les coordonnées de l'entité sélectionnée.
"""
from pathlib import Path
import json
from PyQt6.QtWebEngineWidgets import QWebEngineView  # type: ignore

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QAction, QFont, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
    QPushButton,
    QSlider,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QDockWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QFormLayout,
    QScrollArea,
    QGroupBox,
    QFrame,
    QTextEdit,
    QToolBar,
    QDialog,
    QListWidget,
    QRadioButton,
    QButtonGroup,
)

from analyse_runner import AnalyseError, lancer_analyse
from json_loader import JsonLoadError, charger_export
from widgets.blocs_view import BlocsView
from widgets.entites_table import EntitesTable
import recent_files
import styles
import icons
import settings_manager

DEFAULT_EXPORT_DIR = "AutoCADExport"


# ─────────────────────────────────────────────────────────────────
# Dialogue Fichiers Récents
# ─────────────────────────────────────────────────────────────────

class DialogueFichiersRecents(QDialog):
    """Dialogue de gestion des fichiers récemment ouverts."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Fichiers Récents")
        self.resize(550, 350)
        self.setModal(True)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(8)

        # Barre de recherche
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Rechercher dans l'historique…")
        self.search_bar.textChanged.connect(self._filtrer)
        self.layout.addWidget(self.search_bar)

        # Liste des fichiers
        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self._ouvrir_selection)
        self.layout.addWidget(self.list_widget)

        # Barre de boutons actions
        btn_layout = QHBoxLayout()
        self.btn_ouvrir = QPushButton("Ouvrir")
        self.btn_ouvrir.setObjectName("primaryAction")
        self.btn_ouvrir.clicked.connect(self._ouvrir_selection)

        self.btn_retirer = QPushButton("Retirer de la liste")
        self.btn_retirer.clicked.connect(self._retirer_selection)

        self.btn_vider = QPushButton("Tout effacer")
        self.btn_vider.clicked.connect(self._vider_tout)

        self.btn_fermer = QPushButton("Fermer")
        self.btn_fermer.clicked.connect(self.reject)

        btn_layout.addWidget(self.btn_ouvrir)
        btn_layout.addWidget(self.btn_retirer)
        btn_layout.addWidget(self.btn_vider)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_fermer)
        self.layout.addLayout(btn_layout)

        self.selected_path: str | None = None
        self._charger_fichiers()

    def _charger_fichiers(self) -> None:
        self.list_widget.clear()
        self.chemins = recent_files.charger()
        for c in self.chemins:
            self.list_widget.addItem(c)
        self._update_states()

    def _update_states(self) -> None:
        has_items = self.list_widget.count() > 0
        self.btn_ouvrir.setEnabled(has_items)
        self.btn_retirer.setEnabled(has_items)
        self.btn_vider.setEnabled(has_items)

    def _filtrer(self, text: str) -> None:
        t = text.strip().lower()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setHidden(t != "" and t not in item.text().lower())

    def _ouvrir_selection(self) -> None:
        item = self.list_widget.currentItem()
        if item and not item.isHidden():
            self.selected_path = item.text()
            self.accept()

    def _retirer_selection(self) -> None:
        item = self.list_widget.currentItem()
        if item:
            path_str = item.text()
            chemins = recent_files.charger()
            if path_str in chemins:
                chemins.remove(path_str)
                try:
                    with open(recent_files._STORE, "w", encoding="utf-8") as f:
                        json.dump(chemins, f, ensure_ascii=False, indent=2)
                except Exception:
                    pass
            self._charger_fichiers()
            if self.parent():
                self.parent()._refresh_recents_menu()

    def _vider_tout(self) -> None:
        reply = QMessageBox.question(self, "Tout effacer",
                                     "Êtes-vous sûr de vouloir vider tout l'historique ?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            recent_files.vider()
            self._charger_fichiers()
            if self.parent():
                self.parent()._refresh_recents_menu()


# ─────────────────────────────────────────────────────────────────
# Dialogue Paramètres d'Exportation
# ─────────────────────────────────────────────────────────────────

class DialogueParametresExport(QDialog):
    """Dialogue de configuration de l'emplacement d'enregistrement de l'export."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Paramètres d'exportation")
        self.resize(520, 240)
        self.setModal(True)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(12, 12, 12, 12)
        self.layout.setSpacing(10)

        # GroupBox Emplacement de sauvegarde
        self.group_box = QGroupBox("Mode d'enregistrement de l'export AutoCAD")
        self.gb_layout = QVBoxLayout(self.group_box)
        self.gb_layout.setSpacing(8)

        # Options
        self.radio_default = QRadioButton("Emplacement par défaut (autocad_export.json dans le dossier du projet)")
        self.radio_ask = QRadioButton("Toujours demander l'emplacement de sauvegarde avant l'extraction")
        self.radio_custom = QRadioButton("Sauvegarder automatiquement dans un fichier personnalisé fixe :")

        self.gb_layout.addWidget(self.radio_default)
        self.gb_layout.addWidget(self.radio_ask)
        self.gb_layout.addWidget(self.radio_custom)

        # Ligne de saisie du chemin personnalisé + bouton parcourir
        self.path_layout = QHBoxLayout()
        self.edit_path = QLineEdit()
        self.edit_path.setPlaceholderText("Sélectionnez un chemin de fichier JSON…")
        self.btn_browse = QPushButton("Parcourir…")
        self.btn_browse.clicked.connect(self._parcourir)
        self.path_layout.addWidget(self.edit_path)
        self.path_layout.addWidget(self.btn_browse)
        self.gb_layout.addLayout(self.path_layout)

        self.layout.addWidget(self.group_box)

        # Connecter l'activation des champs
        self.radio_default.toggled.connect(self._toggle_inputs)
        self.radio_ask.toggled.connect(self._toggle_inputs)
        self.radio_custom.toggled.connect(self._toggle_inputs)

        # Boutons Ok / Annuler
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.btn_ok = QPushButton("Enregistrer")
        self.btn_ok.setObjectName("primaryAction")
        self.btn_ok.clicked.connect(self._sauvegarder)
        self.btn_cancel = QPushButton("Annuler")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_ok)
        btn_layout.addWidget(self.btn_cancel)
        self.layout.addLayout(btn_layout)

        # Charger la configuration
        self.settings = settings_manager.charger()
        self._appliquer_settings_a_l_ui()

    def _appliquer_settings_a_l_ui(self) -> None:
        mode = self.settings.get("export_mode", "default")
        path = self.settings.get("custom_export_path", "")

        self.edit_path.setText(path)

        if mode == "default":
            self.radio_default.setChecked(True)
        elif mode == "ask":
            self.radio_ask.setChecked(True)
        elif mode == "custom":
            self.radio_custom.setChecked(True)

        self._toggle_inputs()

    def _toggle_inputs(self) -> None:
        custom_active = self.radio_custom.isChecked()
        self.edit_path.setEnabled(custom_active)
        self.btn_browse.setEnabled(custom_active)

    def _parcourir(self) -> None:
        chemin, _ = QFileDialog.getSaveFileName(self, "Choisir le fichier d'export cible",
                                                self.edit_path.text(), "Fichiers JSON (*.json)")
        if chemin:
            self.edit_path.setText(chemin)

    def _sauvegarder(self) -> None:
        if self.radio_custom.isChecked() and not self.edit_path.text().strip():
            QMessageBox.warning(self, "Chemin manquant", "Veuillez spécifier un chemin de fichier valide pour l'emplacement personnalisé.")
            return

        mode = "default"
        if self.radio_ask.isChecked():
            mode = "ask"
        elif self.radio_custom.isChecked():
            mode = "custom"

        self.settings["export_mode"] = mode
        self.settings["custom_export_path"] = self.edit_path.text().strip()

        settings_manager.sauvegarder(self.settings)
        self.accept()


# ─────────────────────────────────────────────────────────────────
# Widget Statistiques
# ─────────────────────────────────────────────────────────────────

class StatsView(QWidget):
    """Graphiques simples (barres HTML dans un QLabel scrollable)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 12, 14, 10)

        self._web = None
        try:
            self._web = QWebEngineView()
            lay.addWidget(self._web)
        except Exception:
            self._fallback = QLabel("WebEngine non disponible — statistiques désactivées.")
            self._fallback.setObjectName("sectionLabel")
            lay.addWidget(self._fallback)

        self._data: dict = {}

    def charger(self, data: dict) -> None:
        self._data = data
        self._refresh()

    def _refresh(self) -> None:
        if self._web is None:
            return
        resume = self._data.get("resume_entites", {})
        blocs = self._data.get("blocs_dynamiques", [])

        # Compte par layer dans les blocs
        layer_counts: dict[str, int] = {}
        for b in blocs:
            lay = b.get("layer", "(?)")
            layer_counts[lay] = layer_counts.get(lay, 0) + 1

        c = styles.couleurs()
        accent = c["accent"]
        accent2 = c["accent_green"]
        bg = c["bg_main"]
        fg = c["fg_main"]

        def bar_chart(title, data_dict, color):
            if not data_dict:
                return f"<p style='color:{fg}'>Aucune donnée.</p>"
            max_v = max(data_dict.values()) or 1
            rows = ""
            for k, v in sorted(data_dict.items(), key=lambda x: -x[1])[:20]:
                pct = v / max_v * 100
                rows += f"""
                <tr>
                  <td style='padding:3px 8px;color:{fg};white-space:nowrap;font-size:12px;font-family:Consolas,monospace'>{k}</td>
                  <td style='width:300px;padding:3px 4px'>
                    <div style='background:{color};height:18px;width:{pct:.1f}%;border-radius:2px;min-width:2px'></div>
                  </td>
                  <td style='padding:3px 6px;color:{fg};font-size:12px;font-family:Consolas,monospace'>{v}</td>
                </tr>"""
            return f"<h3 style='color:{fg};margin:12px 0 6px;font-family:Consolas,monospace'>{title}</h3><table>{rows}</table>"

        html = f"""<!DOCTYPE html><html><body style='background:{bg};margin:14px'>
        {bar_chart("Types d'entités", resume, accent)}
        <hr style='border-color:#444;margin:18px 0'>
        {bar_chart("Blocs par layer (top 20)", layer_counts, accent2)}
        </body></html>"""
        self._web.setHtml(html)


# ─────────────────────────────────────────────────────────────────
# Fenêtre principale
# ─────────────────────────────────────────────────────────────────

class VisualiseurExport(QMainWindow):

    def __init__(self, json_path: str | None = None):
        super().__init__()
        self.setWindowTitle("AutoCAD Export — Visualiseur")
        self.resize(1400, 800)
        self.setAcceptDrops(True)

        # Générer les icônes SVG si nécessaire
        icons.generer_si_necessaire()

        self.current_path: Path | None = None
        self.base_row_height = 26
        self.base_font_size = 10
        self._current_data: dict = {}
        self._active_selected_bloc: dict | None = None

        # Résultats de recherche navigation
        self._match_list: list[tuple] = []  # (widget, row)
        self._match_idx: int = -1

        self._build_ui()
        self._build_toolbar()
        self._build_menu_bar()

        # Charger le fichier par défaut ou celui passé en argument
        if json_path:
            self._charger_fichier(Path(json_path))
        else:
            self._log("Prêt. Utilisez Ctrl+G pour extraire depuis AutoCAD ou Ctrl+O pour ouvrir un fichier.")

    # ──────────────────────────────────────────
    # Construction UI
    # ──────────────────────────────────────────

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        # Titre et chemin de fichier en en-tête (style CAO)
        self.header_layout = QHBoxLayout()
        self.label_title = QLabel("VISUALISEUR D'EXPORT CAO")
        self.label_title.setObjectName("title")
        self.label_path = QLabel("Aucun fichier chargé")
        self.label_path.setObjectName("filepath")
        self.header_layout.addWidget(self.label_title)
        self.header_layout.addWidget(QLabel("  |  "))
        self.header_layout.addWidget(self.label_path)
        self.header_layout.addStretch()
        root.addLayout(self.header_layout)

        # Recherche globale et filtres
        root.addLayout(self._build_search_bar())
        root.addLayout(self._build_control_bar())

        # Onglets principaux
        self.tabs = QTabWidget()
        root.addWidget(self.tabs)

        self.table_entites = EntitesTable()
        self.table_entites.entitySelected.connect(self._on_entity_selected)
        self.tabs.addTab(self._wrap(self.table_entites), "Résumé entités")

        self.blocs_view = BlocsView()
        self.blocs_view.blockSelected.connect(self._on_block_selected)
        self.tabs.addTab(self.blocs_view, "Blocs dynamiques")

        self.stats_view = StatsView()
        self.tabs.addTab(self.stats_view, "Statistiques")

        # Synchroniser les changements d'onglets vers l'explorateur
        self.tabs.currentChanged.connect(self._on_tab_changed)

        # Barre de statut
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Prêt.")

        # DOCK GAUCHE : Explorateur
        self._build_explorer_dock()

        # DOCK DROIT : Propriétés
        self._build_properties_dock()

        # DOCK BAS : Console de logs
        self._build_console_dock()

    def _build_search_bar(self) -> QHBoxLayout:
        bar = QHBoxLayout()

        lbl = QLabel("Recherche :")
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Recherche globale (toutes les vues)…")
        self.search_edit.textChanged.connect(self._on_search_changed)

        self.btn_prev = QPushButton("◀")
        self.btn_prev.setObjectName("navBtn")
        self.btn_prev.setFixedWidth(28)
        self.btn_prev.clicked.connect(self._nav_prev)
        self.btn_next = QPushButton("▶")
        self.btn_next.setObjectName("navBtn")
        self.btn_next.setFixedWidth(28)
        self.btn_next.clicked.connect(self._nav_next)
        self.lbl_nav = QLabel("")
        self.lbl_nav.setObjectName("searchNav")

        lbl_col = QLabel("  Filtre col. :")
        self.combo_col = QComboBox()
        self.combo_col.addItem("— Toutes —", None)
        self.combo_col.setMinimumWidth(130)
        self.combo_col.currentIndexChanged.connect(self._on_col_filter_changed)
        self.col_value_edit = QLineEdit()
        self.col_value_edit.setPlaceholderText("valeur…")
        self.col_value_edit.setMaximumWidth(140)
        self.col_value_edit.textChanged.connect(self._on_col_filter_changed)

        bar.addWidget(lbl)
        bar.addWidget(self.search_edit, stretch=2)
        bar.addWidget(self.btn_prev)
        bar.addWidget(self.btn_next)
        bar.addWidget(self.lbl_nav)
        bar.addWidget(lbl_col)
        bar.addWidget(self.combo_col)
        bar.addWidget(self.col_value_edit)
        return bar

    def _build_control_bar(self) -> QHBoxLayout:
        bar = QHBoxLayout()
        zoom_label = QLabel("Zoom grille :")
        zoom_label.setObjectName("zoomLabel")
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setMinimum(70)
        self.zoom_slider.setMaximum(220)
        self.zoom_slider.setValue(100)
        self.zoom_slider.setFixedWidth(160)
        self.zoom_slider.valueChanged.connect(self._appliquer_zoom)
        self.zoom_value_label = QLabel("100%")
        self.zoom_value_label.setObjectName("zoomLabel")
        self.zoom_value_label.setFixedWidth(38)
        bar.addStretch()
        bar.addWidget(zoom_label)
        bar.addWidget(self.zoom_slider)
        bar.addWidget(self.zoom_value_label)
        return bar

    @staticmethod
    def _wrap(widget: QWidget) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 8, 0, 0)
        lay.addWidget(widget)
        return w

    # ──────────────────────────────────────────
    # Construction des Docks
    # ──────────────────────────────────────────

    def _build_explorer_dock(self) -> None:
        self.dock_explorer = QDockWidget("Explorateur de Projet", self)
        self.dock_explorer.setObjectName("DockExplorer")
        self.dock_explorer.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)

        self.tree_explorer = QTreeWidget()
        self.tree_explorer.setHeaderHidden(True)
        self.tree_explorer.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree_explorer.customContextMenuRequested.connect(self._menu_contextuel_explorer)
        self.tree_explorer.itemClicked.connect(self._on_explorer_item_clicked)

        self.dock_explorer.setWidget(self.tree_explorer)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.dock_explorer)

    def _build_properties_dock(self) -> None:
        self.dock_properties = QDockWidget("Propriétés CAO", self)
        self.dock_properties.setObjectName("DockProperties")
        self.dock_properties.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)

        prop_container = QWidget()
        prop_layout = QVBoxLayout(prop_container)
        prop_layout.setContentsMargins(6, 6, 6, 6)
        prop_layout.setSpacing(6)

        # Zone de filtre
        self.prop_search = QLineEdit()
        self.prop_search.setPlaceholderText("Filtrer les propriétés…")
        self.prop_search.textChanged.connect(self._filtrer_proprietes)
        prop_layout.addWidget(self.prop_search)

        # Zone défilante des propriétés
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.prop_scroll_widget = QWidget()
        self.prop_form_layout = QVBoxLayout(self.prop_scroll_widget)
        self.prop_form_layout.setContentsMargins(0, 0, 0, 0)
        self.prop_form_layout.setSpacing(8)
        self.prop_form_layout.addStretch()

        scroll.setWidget(self.prop_scroll_widget)
        prop_layout.addWidget(scroll)

        self.dock_properties.setWidget(prop_container)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock_properties)

    def _build_console_dock(self) -> None:
        self.dock_console = QDockWidget("Console / Historique", self)
        self.dock_console.setObjectName("DockConsole")
        self.dock_console.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea | Qt.DockWidgetArea.TopDockWidgetArea)

        self.console_view = QTextEdit()
        self.console_view.setObjectName("consoleView")
        self.console_view.setReadOnly(True)

        self.dock_console.setWidget(self.console_view)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.dock_console)

    def _log(self, message: str) -> None:
        """Ajoute un message daté dans la console interne."""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.console_view.append(f"[{timestamp}] {message}")
        self.console_view.ensureCursorVisible()

    # ──────────────────────────────────────────
    # Barre d'outils (QToolBar)
    # ──────────────────────────────────────────

    def _build_toolbar(self) -> None:
        self.toolbar = QToolBar("Barre d'outils")
        self.toolbar.setObjectName("ToolBar")
        self.toolbar.setIconSize(QSize(20, 20))
        self.toolbar.setMovable(False)
        self.addToolBar(self.toolbar)

        # Action Ouvrir
        act_open = QAction(QIcon(str(Path(__file__).parent / "icons" / "open.svg")), "Ouvrir", self)
        act_open.setToolTip("Ouvrir un export JSON d'AutoCAD (Ctrl+O)")
        act_open.setShortcut("Ctrl+O")
        act_open.triggered.connect(self._dialogue_ouvrir)
        self.toolbar.addAction(act_open)

        # Action Sauvegarder
        act_save = QAction(QIcon(str(Path(__file__).parent / "icons" / "save.svg")), "Sauvegarder", self)
        act_save.setToolTip("Sauvegarder les modifications dans le fichier JSON actuel (Ctrl+S)")
        act_save.setShortcut("Ctrl+S")
        act_save.triggered.connect(self._sauvegarder_fichier)
        self.toolbar.addAction(act_save)

        # Action Recharger
        act_reload = QAction(QIcon(str(Path(__file__).parent / "icons" / "reload.svg")), "Recharger", self)
        act_reload.setToolTip("Recharger le fichier depuis le disque (F5)")
        act_reload.setShortcut("F5")
        act_reload.triggered.connect(self._recharger)
        self.toolbar.addAction(act_reload)

        # Action Analyser
        act_analyse = QAction(QIcon(str(Path(__file__).parent / "icons" / "analyse.svg")), "Analyser", self)
        act_analyse.setToolTip("Extraire les entités et blocs dynamiques du dessin actif dans AutoCAD (Ctrl+G)")
        act_analyse.setShortcut("Ctrl+G")
        act_analyse.triggered.connect(self._generer_analyse)
        self.toolbar.addAction(act_analyse)

        self.toolbar.addSeparator()

        # Zoom In / Out
        act_zoom_in = QAction(QIcon(str(Path(__file__).parent / "icons" / "zoom_in.svg")), "Agrandir", self)
        act_zoom_in.setToolTip("Agrandir la taille du texte de la grille")
        act_zoom_in.triggered.connect(self._zoom_in)
        self.toolbar.addAction(act_zoom_in)

        act_zoom_out = QAction(QIcon(str(Path(__file__).parent / "icons" / "zoom_out.svg")), "Réduire", self)
        act_zoom_out.setToolTip("Réduire la taille du texte de la grille")
        act_zoom_out.triggered.connect(self._zoom_out)
        self.toolbar.addAction(act_zoom_out)

        self.toolbar.addSeparator()

        # Bascule Thème
        act_theme = QAction(QIcon(str(Path(__file__).parent / "icons" / "theme.svg")), "Thème", self)
        act_theme.setToolTip("Bascule Thème Clair / Sombre (Ctrl+T)")
        act_theme.setShortcut("Ctrl+T")
        act_theme.triggered.connect(self._basculer_theme)
        self.toolbar.addAction(act_theme)

        self.toolbar.addSeparator()

        # Visibilité des volets (Docks)
        self.act_toggle_explorer = QAction(QIcon(str(Path(__file__).parent / "icons" / "explorer.svg")), "Explorateur", self)
        self.act_toggle_explorer.setToolTip("Afficher/Masquer l'explorateur")
        self.act_toggle_explorer.setCheckable(True)
        self.act_toggle_explorer.setChecked(True)
        self.act_toggle_explorer.triggered.connect(self.dock_explorer.setVisible)
        self.toolbar.addAction(self.act_toggle_explorer)
        self.dock_explorer.visibilityChanged.connect(self.act_toggle_explorer.setChecked)

        self.act_toggle_properties = QAction(QIcon(str(Path(__file__).parent / "icons" / "properties.svg")), "Propriétés", self)
        self.act_toggle_properties.setToolTip("Afficher/Masquer le volet propriétés")
        self.act_toggle_properties.setCheckable(True)
        self.act_toggle_properties.setChecked(True)
        self.act_toggle_properties.triggered.connect(self.dock_properties.setVisible)
        self.toolbar.addAction(self.act_toggle_properties)
        self.dock_properties.visibilityChanged.connect(self.act_toggle_properties.setChecked)

    # ──────────────────────────────────────────
    # Menu Bar
    # ──────────────────────────────────────────

    def _build_menu_bar(self) -> None:
        mb = self.menuBar()

        # ── Fichier ──
        m_fichier = mb.addMenu("Fichier")

        act_open = QAction("Ouvrir JSON…", self)
        act_open.setShortcut("Ctrl+O")
        act_open.triggered.connect(self._dialogue_ouvrir)
        m_fichier.addAction(act_open)

        act_manage_recents = QAction("Gérer les fichiers récents…", self)
        act_manage_recents.triggered.connect(self._ouvrir_gestionnaire_recents)
        m_fichier.addAction(act_manage_recents)

        act_save = QAction("Sauvegarder", self)
        act_save.setShortcut("Ctrl+S")
        act_save.triggered.connect(self._sauvegarder_fichier)
        m_fichier.addAction(act_save)

        act_reload = QAction("Recharger", self)
        act_reload.setShortcut("F5")
        act_reload.triggered.connect(self._recharger)
        m_fichier.addAction(act_reload)

        act_settings = QAction("Paramètres d'exportation…", self)
        act_settings.triggered.connect(self._ouvrir_parametres_export)
        m_fichier.addAction(act_settings)

        act_generer = QAction("⚙  Extraire AutoCAD", self)
        act_generer.setShortcut("Ctrl+G")
        act_generer.triggered.connect(self._generer_analyse)
        m_fichier.addAction(act_generer)

        m_fichier.addSeparator()
        self.menu_recents = m_fichier.addMenu("Fichiers récents")
        self._refresh_recents_menu()
        m_fichier.addSeparator()

        act_quit = QAction("Quitter", self)
        act_quit.setShortcut("Ctrl+Q")
        act_quit.triggered.connect(self.close)
        m_fichier.addAction(act_quit)

        # ── Affichage ──
        m_aff = mb.addMenu("Affichage")

        act_theme = QAction("Basculer thème clair/sombre", self)
        act_theme.setShortcut("Ctrl+T")
        act_theme.triggered.connect(self._basculer_theme)
        m_aff.addAction(act_theme)

        m_aff.addSeparator()

        # Docks Visibilité
        act_view_exp = QAction("Afficher l'Explorateur", self)
        act_view_exp.setCheckable(True)
        act_view_exp.setChecked(True)
        act_view_exp.triggered.connect(self.dock_explorer.setVisible)
        self.dock_explorer.visibilityChanged.connect(act_view_exp.setChecked)
        m_aff.addAction(act_view_exp)

        act_view_prop = QAction("Afficher les Propriétés", self)
        act_view_prop.setCheckable(True)
        act_view_prop.setChecked(True)
        act_view_prop.triggered.connect(self.dock_properties.setVisible)
        self.dock_properties.visibilityChanged.connect(act_view_prop.setChecked)
        m_aff.addAction(act_view_prop)

        act_view_cons = QAction("Afficher la Console", self)
        act_view_cons.setCheckable(True)
        act_view_cons.setChecked(True)
        act_view_cons.triggered.connect(self.dock_console.setVisible)
        self.dock_console.visibilityChanged.connect(act_view_cons.setChecked)
        m_aff.addAction(act_view_cons)

        m_aff.addSeparator()

        act_tab0 = QAction("Résumé entités", self)
        act_tab0.setShortcut("Ctrl+1")
        act_tab0.triggered.connect(lambda: self.tabs.setCurrentIndex(0))
        m_aff.addAction(act_tab0)

        act_tab1 = QAction("Blocs dynamiques", self)
        act_tab1.setShortcut("Ctrl+2")
        act_tab1.triggered.connect(lambda: self.tabs.setCurrentIndex(1))
        m_aff.addAction(act_tab1)

        act_tab2 = QAction("Statistiques", self)
        act_tab2.setShortcut("Ctrl+3")
        act_tab2.triggered.connect(lambda: self.tabs.setCurrentIndex(2))
        m_aff.addAction(act_tab2)

        # ── Aide ──
        m_aide = mb.addMenu("Aide")
        act_about = QAction("À propos…", self)
        act_about.triggered.connect(self._about)
        m_aide.addAction(act_about)

    def _refresh_recents_menu(self) -> None:
        self.menu_recents.clear()
        chemins = recent_files.charger()
        if not chemins:
            act = QAction("(aucun fichier récent)", self)
            act.setEnabled(False)
            self.menu_recents.addAction(act)
        else:
            for ch in chemins:
                act = QAction(ch, self)
                act.triggered.connect(lambda checked, p=ch: self._charger_fichier(Path(p)))
                self.menu_recents.addAction(act)
            self.menu_recents.addSeparator()
            act_clear = QAction("Effacer l'historique", self)
            act_clear.triggered.connect(self._vider_recents)
            self.menu_recents.addAction(act_clear)

    def _vider_recents(self) -> None:
        recent_files.vider()
        self._refresh_recents_menu()
        self._log("Historique des fichiers récents effacé.")

    def _ouvrir_gestionnaire_recents(self) -> None:
        """Ouvre le dialogue de gestion des fichiers récents."""
        dlg = DialogueFichiersRecents(self)
        if dlg.exec() and dlg.selected_path:
            self._charger_fichier(Path(dlg.selected_path))
        # Toujours rafraîchir le menu au cas où des entrées auraient été retirées
        self._refresh_recents_menu()

    def _ouvrir_parametres_export(self) -> None:
        """Ouvre le dialogue de configuration de l'emplacement d'enregistrement."""
        dlg = DialogueParametresExport(self)
        if dlg.exec():
            mode = dlg.settings.get("export_mode", "default")
            labels = {"default": "Défaut", "ask": "Toujours demander", "custom": "Personnalisé"}
            self._log(f"Paramètres d'exportation mis à jour — Mode : {labels.get(mode, mode)}")

    # ──────────────────────────────────────────
    # Thème
    # ──────────────────────────────────────────

    def _basculer_theme(self) -> None:
        new_theme = styles.basculer_theme()
        QApplication.instance().setStyleSheet(styles.feuille_de_style())
        self._log(f"Bascule vers le thème {new_theme.upper()}.")
        if self._current_data:
            self._afficher_donnees(self._current_data)
        self.stats_view._refresh()

    # ──────────────────────────────────────────
    # Zoom
    # ──────────────────────────────────────────

    def _zoom_in(self) -> None:
        self.zoom_slider.setValue(self.zoom_slider.value() + 15)

    def _zoom_out(self) -> None:
        self.zoom_slider.setValue(self.zoom_slider.value() - 15)

    # ──────────────────────────────────────────
    # Drag and Drop
    # ──────────────────────────────────────────

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith('.json'):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = Path(url.toLocalFile())
                if file_path.suffix.lower() == '.json':
                    self._charger_fichier(file_path)
                    event.acceptProposedAction()
                    self._log(f"Fichier importé par Drag & Drop : {file_path.name}")
                    return

    # ──────────────────────────────────────────
    # Chargement / Sauvegarde / Génération
    # ──────────────────────────────────────────

    def _charger_fichier(self, chemin: Path) -> None:
        self._log(f"Chargement du fichier : {chemin}")
        try:
            data = charger_export(chemin)
        except JsonLoadError as exc:
            QMessageBox.critical(self, "Erreur de lecture", str(exc))
            self.status.showMessage("Échec du chargement.", 4000)
            self._log(f"Erreur lors du chargement : {exc}")
            return

        self.current_path = chemin
        self.label_path.setText(chemin.name)
        self._afficher_donnees(data)
        self.setWindowTitle(f"AutoCAD Export — {chemin.name}")
        self.status.showMessage(f"Fichier chargé : {chemin.name}", 4000)
        recent_files.ajouter(chemin)
        self._refresh_recents_menu()
        self._populate_col_filter()

        # Remplir l'explorateur
        self._remplir_explorateur(chemin.name, data)
        self._log(f"Fichier chargé avec succès ({len(data.get('blocs_dynamiques', []))} blocs dynamiques).")

    def _sauvegarder_fichier(self) -> None:
        if not self.current_path:
            # Demander un chemin de fichier
            chemin, _ = QFileDialog.getSaveFileName(self, "Sauvegarder l'export AutoCAD", "", "Fichiers JSON (*.json)")
            if not chemin:
                return
            self.current_path = Path(chemin)

        self._log(f"Sauvegarde en cours dans : {self.current_path}...")
        try:
            with open(self.current_path, "w", encoding="utf-8") as f:
                json.dump(self._current_data, f, ensure_ascii=False, indent=2)
            self.status.showMessage("Sauvegarde réussie.", 4000)
            self._log("Sauvegarde effectuée avec succès.")
            self.setWindowTitle(f"AutoCAD Export — {self.current_path.name}")
            self.label_path.setText(self.current_path.name)
        except Exception as exc:
            QMessageBox.critical(self, "Erreur de sauvegarde", f"Impossible d'écrire le fichier :\n{exc}")
            self._log(f"Erreur lors de la sauvegarde : {exc}")

    def _generer_analyse(self) -> None:
        # ─ Déterminer le chemin de sortie selon les paramètres configurés ─
        settings = settings_manager.charger()
        mode = settings.get("export_mode", "default")

        if mode == "ask":
            # Toujours demander à l'utilisateur où sauvegarder
            dernier = str(self.current_path.parent) if self.current_path else str(Path(__file__).parent / DEFAULT_EXPORT_DIR)
            chemin_str, _ = QFileDialog.getSaveFileName(
                self, "Choisir l'emplacement de l'export AutoCAD",
                dernier, "Fichiers JSON (*.json)"
            )
            if not chemin_str:
                self._log("Extraction annulée par l'utilisateur (aucun fichier sélectionné).")
                return
            chemin_sortie = Path(chemin_str)

        elif mode == "custom":
            custom_path = settings.get("custom_export_path", "").strip()
            if not custom_path:
                QMessageBox.warning(self, "Chemin personnalisé manquant",
                                    "Le mode d'enregistrement personnalisé est actif mais aucun chemin n'est défini.\n"
                                    "Veuillez configurer l'emplacement via Fichier > Paramètres d'exportation…")
                self._log("Extraction annulée : chemin personnalisé non défini dans les paramètres.")
                return
            chemin_sortie = Path(custom_path)

        else:
            # Mode par défaut
            chemin_sortie = Path(__file__).parent / DEFAULT_EXPORT_DIR

        # ─ Lancer l'extraction AutoCAD ─
        self.status.showMessage("Analyse en cours — lecture du dessin AutoCAD…")
        self._log(f"Extraction AutoCAD → destination : {chemin_sortie}")
        self.setEnabled(False)
        try:
            data = lancer_analyse(chemin_sortie=chemin_sortie)
        except AnalyseError as exc:
            self.setEnabled(True)
            QMessageBox.critical(self, "Échec de l'analyse", str(exc))
            self.status.showMessage("Échec de l'analyse AutoCAD.", 5000)
            self._log(f"Échec de l'analyse : {exc}")
            return
        finally:
            self.setEnabled(True)

        self.current_path = data.get("fichier", chemin_sortie)
        self.label_path.setText(self.current_path.name)
        self._afficher_donnees(data)
        self.setWindowTitle(f"AutoCAD Export — {self.current_path.name}")
        self.status.showMessage(f"Analyse enregistrée dans {self.current_path.name}", 5000)
        self._remplir_explorateur(self.current_path.name, data)
        recent_files.ajouter(self.current_path)
        self._refresh_recents_menu()
        self._log(f"Analyse AutoCAD terminée. Fichier de sortie écrit : {self.current_path.name}")


    def _dialogue_ouvrir(self) -> None:
        chemin, _ = QFileDialog.getOpenFileName(self, "Ouvrir un export AutoCAD", "", "Fichiers JSON (*.json)")
        if chemin:
            self._charger_fichier(Path(chemin))

    def _recharger(self) -> None:
        if self.current_path:
            self._charger_fichier(self.current_path)
        else:
            self.status.showMessage("Aucun fichier à recharger.", 3000)

    def _afficher_donnees(self, data: dict) -> None:
        self._current_data = data
        self.table_entites.charger(data.get("resume_entites", {}))
        msg = self.blocs_view.charger(data.get("blocs_dynamiques", []))
        self.stats_view.charger(data)
        self._appliquer_zoom(self.zoom_slider.value())
        self.status.showMessage(msg, 4000)

        # Ré-appliquer les signaux dynamiques si blocs_view a été recréé
        # Ré-appliquer filtre si actif
        texte = self.search_edit.text()
        if texte:
            self._on_search_changed(texte)

    def _populate_col_filter(self) -> None:
        self.combo_col.blockSignals(True)
        self.combo_col.clear()
        self.combo_col.addItem("— Toutes —", None)
        seen = set()
        for table in self._toutes_les_tables():
            for col in range(table.columnCount()):
                h = table.horizontalHeaderItem(col)
                if h and h.text() not in seen:
                    seen.add(h.text())
                    self.combo_col.addItem(h.text(), h.text())
        self.combo_col.blockSignals(False)

    # ──────────────────────────────────────────
    # Population / Click de l'Explorateur
    # ──────────────────────────────────────────

    def _remplir_explorateur(self, nom_fichier: str, data: dict) -> None:
        self.tree_explorer.clear()

        # Noeud racine
        root = QTreeWidgetItem([nom_fichier])
        root.setIcon(0, QIcon(str(Path(__file__).parent / "icons" / "open.svg")))
        root.setData(0, Qt.ItemDataRole.UserRole, {"type": "root"})
        self.tree_explorer.addTopLevelItem(root)

        # Résumé des entités
        item_resume = QTreeWidgetItem(["Résumé des entités"])
        item_resume.setData(0, Qt.ItemDataRole.UserRole, {"type": "resume"})
        root.addChild(item_resume)

        # Blocs dynamiques
        item_blocs = QTreeWidgetItem(["Blocs dynamiques"])
        item_blocs.setData(0, Qt.ItemDataRole.UserRole, {"type": "blocs_root"})
        root.addChild(item_blocs)

        # Regrouper les blocs par type pour la sous-liste
        blocs = data.get("blocs_dynamiques", [])
        groupes: dict[str, int] = {}
        for b in blocs:
            nom = b.get("nom", "(sans nom)")
            groupes[nom] = groupes.get(nom, 0) + 1

        for nom_type, count in sorted(groupes.items()):
            sub_item = QTreeWidgetItem([f"{nom_type} ({count})"])
            sub_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "bloc_type", "name": nom_type})
            item_blocs.addChild(sub_item)

        # Statistiques
        item_stats = QTreeWidgetItem(["Statistiques"])
        item_stats.setData(0, Qt.ItemDataRole.UserRole, {"type": "stats"})
        root.addChild(item_stats)

        self.tree_explorer.expandAll()

    def _on_explorer_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data or not isinstance(data, dict):
            return
        t = data.get("type")
        if t == "resume":
            self.tabs.setCurrentIndex(0)
        elif t == "stats":
            self.tabs.setCurrentIndex(2)
        elif t == "bloc_type":
            self.tabs.setCurrentIndex(1)
            self.blocs_view.selectionner_bloc_type(data.get("name"))

    def _on_tab_changed(self, index: int) -> None:
        """Garde l'arbre de l'explorateur sélectionné synchronisé avec l'onglet actif."""
        self.tree_explorer.blockSignals(True)
        if index == 0:
            items = self.tree_explorer.findItems("Résumé des entités", Qt.MatchFlag.MatchRecursive)
            if items:
                self.tree_explorer.setCurrentItem(items[0])
        elif index == 2:
            items = self.tree_explorer.findItems("Statistiques", Qt.MatchFlag.MatchRecursive)
            if items:
                self.tree_explorer.setCurrentItem(items[0])
        elif index == 1:
            if self.blocs_view.sub_tabs:
                active_idx = self.blocs_view.sub_tabs.currentIndex()
                if active_idx >= 0:
                    tab_text = self.blocs_view.sub_tabs.tabText(active_idx)
                    nom_type = tab_text.split("  (")[0]
                    # Trouver le sous-nœud de bloc
                    items = self.tree_explorer.findItems(nom_type, Qt.MatchFlag.MatchRecursive)
                    for it in items:
                        d = it.data(0, Qt.ItemDataRole.UserRole)
                        if d and d.get("type") == "bloc_type":
                            self.tree_explorer.setCurrentItem(it)
                            break
        self.tree_explorer.blockSignals(False)

    def _menu_contextuel_explorer(self, pos) -> None:
        item = self.tree_explorer.itemAt(pos)
        if not item:
            return
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return

        menu = QMenu(self.tree_explorer)
        if data.get("type") == "root":
            act_reload = QAction("Recharger ce fichier", self)
            act_reload.triggered.connect(self._recharger)
            menu.addAction(act_reload)

            act_close = QAction("Fermer le projet", self)
            act_close.triggered.connect(self._fermer_projet)
            menu.addAction(act_close)

        elif data.get("type") == "bloc_type":
            nom_bloc = data.get("name")
            act_filter = QAction(f"Filtrer la vue sur {nom_bloc}", self)
            act_filter.triggered.connect(lambda: self.search_edit.setText(nom_bloc))
            menu.addAction(act_filter)

        if not menu.isEmpty():
            menu.exec(self.tree_explorer.viewport().mapToGlobal(pos))

    def _fermer_projet(self) -> None:
        self._current_data = {}
        self.tree_explorer.clear()
        self.table_entites.setRowCount(0)
        self.blocs_view.charger([])
        self.stats_view.charger({})
        self.current_path = None
        self.label_path.setText("Aucun fichier chargé")
        self.setWindowTitle("AutoCAD Export — Visualiseur")
        self._log("Projet fermé.")

    # ──────────────────────────────────────────
    # Remplissage et édition du Dock Propriétés
    # ──────────────────────────────────────────

    def _on_entity_selected(self, data: dict) -> None:
        """Remplit le volet propriétés avec les statistiques de l'entité sélectionnée."""
        self._active_selected_bloc = None
        self._nettoyer_properties_layout()

        gb = QGroupBox("Général")
        flay = QFormLayout(gb)
        flay.setContentsMargins(6, 8, 6, 8)
        flay.setSpacing(6)

        lbl_type = QLabel(data.get("type"))
        lbl_type.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        flay.addRow("Type d'entité :", lbl_type)

        lbl_count = QLabel(str(data.get("count")))
        lbl_count.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        flay.addRow("Nombre :", lbl_count)

        if data.get("type") != "TOTAL":
            pct = data.get("count", 0) / (data.get("total", 1) or 1) * 100
            flay.addRow("Ratio total :", QLabel(f"{pct:.1f}%"))

        self.prop_form_layout.insertWidget(self.prop_form_layout.count() - 1, gb)
        self.status.showMessage(f"Entité sélectionnée : {data.get('type')}")

    def _on_block_selected(self, bloc: dict) -> None:
        """Remplit le volet propriétés avec les attributs et paramètres dynamiques du bloc."""
        self._active_selected_bloc = bloc
        self._nettoyer_properties_layout()

        # Affichage des coordonnées (Origin) dans la barre de statut si présentes
        params = bloc.get("parametres", {}) or {}
        origin = params.get("Origin")
        if isinstance(origin, list) and len(origin) >= 2:
            coord_str = f"Origin: X={origin[0]:.4f}, Y={origin[1]:.4f}"
            self.status.showMessage(f"Bloc : {bloc.get('nom')}  |  {coord_str}")
        else:
            self.status.showMessage(f"Bloc sélectionné : {bloc.get('nom')}")

        # Catégorie 1 : Général
        gb_gen = QGroupBox("Général")
        flay_gen = QFormLayout(gb_gen)
        flay_gen.setContentsMargins(6, 8, 6, 8)
        flay_gen.setSpacing(6)

        # Nom (Lecture seule)
        lbl_nom = QLabel(bloc.get("nom"))
        lbl_nom.setStyleSheet("font-weight: bold;")
        flay_gen.addRow("Nom :", lbl_nom)

        # Layer (Modifiable)
        edit_layer = QLineEdit(bloc.get("layer", ""))
        edit_layer.editingFinished.connect(lambda b=bloc, el=edit_layer: self._on_property_edited(b, "layer", "", el.text()))
        flay_gen.addRow("Calque (Layer) :", edit_layer)

        self.prop_form_layout.insertWidget(self.prop_form_layout.count() - 1, gb_gen)

        # Catégorie 2 : Attributs (si présents)
        attribs = bloc.get("attributs", {}) or {}
        if attribs:
            gb_attr = QGroupBox("Attributs")
            flay_attr = QFormLayout(gb_attr)
            flay_attr.setContentsMargins(6, 8, 6, 8)
            flay_attr.setSpacing(6)

            for key, val in sorted(attribs.items()):
                edit_val = QLineEdit(str(val))
                # Connecter la modification à chaud
                edit_val.editingFinished.connect(lambda b=bloc, k=key, ev=edit_val: self._on_property_edited(b, "attributs", k, ev.text()))
                flay_attr.addRow(f"{key} :", edit_val)

            self.prop_form_layout.insertWidget(self.prop_form_layout.count() - 1, gb_attr)

        # Catégorie 3 : Paramètres dynamiques (si présents)
        if params:
            gb_param = QGroupBox("Paramètres CAO")
            flay_param = QFormLayout(gb_param)
            flay_param.setContentsMargins(6, 8, 6, 8)
            flay_param.setSpacing(6)

            for key, val in sorted(params.items()):
                # Cas d'un vecteur / point (ex. Origin [X, Y])
                if isinstance(val, list):
                    # Générer des champs distincts pour chaque coordonnée
                    for idx, axis in enumerate(["X", "Y", "Z"][:len(val)]):
                        edit_axis = QLineEdit(f"{val[idx]:.5f}")
                        edit_axis.editingFinished.connect(lambda b=bloc, k=key, i=idx, ea=edit_axis: self._on_coord_edited(b, "parametres", k, i, ea.text()))
                        flay_param.addRow(f"{key} {axis} :", edit_axis)
                else:
                    edit_val = QLineEdit(str(val))
                    # Connecter la modification à chaud
                    edit_val.editingFinished.connect(lambda b=bloc, k=key, ev=edit_val: self._on_property_edited(b, "parametres", k, ev.text()))
                    flay_param.addRow(f"{key} :", edit_val)

            self.prop_form_layout.insertWidget(self.prop_form_layout.count() - 1, gb_param)

        # Appliquer filtre de recherche si le champ n'est pas vide
        if self.prop_search.text():
            self._filtrer_proprietes(self.prop_search.text())

    def _on_property_edited(self, bloc: dict, category: str, key: str, text_val: str) -> None:
        """Gère la mise à jour typée d'une propriété éditée depuis le volet Propriétés."""
        original_val = bloc[category][key] if category != "layer" else bloc["layer"]
        typed_val = text_val
        try:
            if isinstance(original_val, int):
                typed_val = int(text_val)
            elif isinstance(original_val, float):
                typed_val = float(text_val)
        except ValueError:
            pass

        self._update_table_item_for_bloc(bloc, category, key, typed_val)

    def _on_coord_edited(self, bloc: dict, category: str, key: str, index: int, text_val: str) -> None:
        """Gère la modification d'un élément d'une liste (ex. Origin X, Origin Y)."""
        try:
            val = float(text_val)
        except ValueError:
            return
        original_list = bloc[category][key]
        if isinstance(original_list, list) and index < len(original_list):
            original_list[index] = val
            self._update_table_item_for_bloc(bloc, category, key, original_list)

    def _update_table_item_for_bloc(self, bloc: dict, category: str, key: str, value) -> None:
        """Met à jour les données internes et rafraîchit la cellule correspondante dans la table active."""
        if category == "layer":
            bloc["layer"] = value
            self._log(f"Modification Calque du bloc '{bloc.get('nom')}' : {value}")
        else:
            bloc[category][key] = value
            self._log(f"Modification '{key}' du bloc '{bloc.get('nom')}' ({category}) : {value}")

        # Mettre à jour l'en-tête de l'explorateur (si jamais le nombre change) - facultatif ici
        # Retrouver la cellule dans le tableau de la vue des blocs
        from formatters import formater_valeur
        for table in self.blocs_view.toutes_les_tables():
            for row in range(table.rowCount()):
                item_layer = table.item(row, 0)
                if item_layer and item_layer.data(Qt.ItemDataRole.UserRole) is bloc:
                    # Trouvé la ligne correspondante !
                    if category == "layer":
                        item_layer.setText(str(value))
                    else:
                        prefix = "Attr: " if category == "attributs" else "Param: "
                        header_name = f"{prefix}{key}"
                        for col in range(table.columnCount()):
                            header_item = table.horizontalHeaderItem(col)
                            if header_item and header_item.text() == header_name:
                                table.item(row, col).setText(formater_valeur(value))
                                break
                    break

    def _nettoyer_properties_layout(self) -> None:
        """Supprime tous les GroupBox de propriétés existants du layout."""
        for groupbox in self.prop_scroll_widget.findChildren(QGroupBox):
            self.prop_form_layout.removeWidget(groupbox)
            groupbox.deleteLater()

    def _filtrer_proprietes(self, text: str) -> None:
        """Filtre la visibilité des lignes de propriétés par mot-clé."""
        t = text.strip().lower()
        for groupbox in self.prop_scroll_widget.findChildren(QGroupBox):
            layout = groupbox.layout()
            if not isinstance(layout, QFormLayout):
                continue
            visible_rows = 0
            for row in range(layout.rowCount()):
                label_item = layout.itemAt(row, QFormLayout.ItemRole.LabelRole)
                field_item = layout.itemAt(row, QFormLayout.ItemRole.FieldRole)
                if not label_item or not field_item:
                    continue
                lbl_widget = label_item.widget()
                fld_widget = field_item.widget()

                match = not t or (lbl_widget and t in lbl_widget.text().lower())
                lbl_widget.setVisible(match)
                fld_widget.setVisible(match)
                if match:
                    visible_rows += 1

            groupbox.setVisible(visible_rows > 0)

    # ──────────────────────────────────────────
    # Recherche globale et filtres (conservés)
    # ──────────────────────────────────────────

    def _on_search_changed(self, texte: str) -> None:
        t = texte.strip().lower()
        self.blocs_view.appliquer_filtre(t)
        self.table_entites.appliquer_highlight(t)

        self._match_list = []
        if t:
            for table in self._toutes_les_tables():
                for row in range(table.rowCount()):
                    if not table.isRowHidden(row):
                        if any(
                            table.item(row, col) and t in table.item(row, col).text().lower()
                            for col in range(table.columnCount())
                        ):
                            self._match_list.append((table, row))

        n = len(self._match_list)
        self._match_idx = 0 if n > 0 else -1
        self._update_nav_label()
        if self._match_idx >= 0:
            self._scroll_to_match(self._match_idx)

    def _nav_next(self) -> None:
        if not self._match_list:
            return
        self._match_idx = (self._match_idx + 1) % len(self._match_list)
        self._update_nav_label()
        self._scroll_to_match(self._match_idx)

    def _nav_prev(self) -> None:
        if not self._match_list:
            return
        self._match_idx = (self._match_idx - 1) % len(self._match_list)
        self._update_nav_label()
        self._scroll_to_match(self._match_idx)

    def _update_nav_label(self) -> None:
        n = len(self._match_list)
        if n == 0:
            txt = self.search_edit.text()
            self.lbl_nav.setText("0 résultat" if txt.strip() else "")
        else:
            self.lbl_nav.setText(f"{self._match_idx + 1}/{n}")
        self.btn_prev.setEnabled(len(self._match_list) > 1)
        self.btn_next.setEnabled(len(self._match_list) > 1)

    def _scroll_to_match(self, idx: int) -> None:
        if idx < 0 or idx >= len(self._match_list):
            return
        table, row = self._match_list[idx]
        table.scrollToItem(table.item(row, 0))
        table.selectRow(row)

    def _on_col_filter_changed(self) -> None:
        col_name = self.combo_col.currentData()
        value = self.col_value_edit.text().strip().lower()

        for table in self._toutes_les_tables():
            col_idx = None
            if col_name:
                for c in range(table.columnCount()):
                    h = table.horizontalHeaderItem(c)
                    if h and h.text() == col_name:
                        col_idx = c
                        break

            for row in range(table.rowCount()):
                if col_idx is None or not value:
                    table.setRowHidden(row, False)
                else:
                    item = table.item(row, col_idx)
                    match = item and value in item.text().lower()
                    table.setRowHidden(row, not match)

    def _toutes_les_tables(self):
        return [self.table_entites] + self.blocs_view.toutes_les_tables()

    def _appliquer_zoom(self, pct: int) -> None:
        self.zoom_value_label.setText(f"{pct}%")
        factor = pct / 100.0
        font_size = max(7, round(self.base_font_size * factor))
        row_height = max(16, round(self.base_row_height * factor))
        for table in self._toutes_les_tables():
            f = table.font()
            f.setPointSize(font_size)
            table.setFont(f)
            table.horizontalHeader().setFont(f)
            table.horizontalHeader().setFixedHeight(row_height + 6)
            for row in range(table.rowCount()):
                table.setRowHeight(row, row_height)

    def _about(self) -> None:
        QMessageBox.about(self, "À propos",
            "<b>AutoCAD Export — Visualiseur v3 (CAO)</b><br><br>"
            "Visionneuse d'exports JSON AutoCAD avec design et ergonomie avancés.<br>"
            "Fonctionnalités : Barre d'outils Ribbon SVG, volets Explorateur, Propriétés éditables et Console, "
            "double synchronisation, glisser-déposer de fichiers, filtres avancés, thèmes."
        )
