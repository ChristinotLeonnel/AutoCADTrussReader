"""
styles.py
---------
Thèmes clair et sombre (QSS + couleurs partagées).
"""

from PyQt6.QtGui import QColor

# ------------------------------------------------------------------
# Thème SOMBRE (défaut)
# ------------------------------------------------------------------

_DARK = dict(
    bg_main="#1e1e1e",
    bg_widget="#252526",
    bg_button="#2d2d2d",
    bg_button_hover="#2d2d30",
    bg_input="#1e1e1e",
    bg_table="#252526",
    bg_row_a="#252526",
    bg_row_b="#1e1e1e",
    bg_header="#2d2d2d",
    bg_tab="#2d2d2d",
    bg_tab_selected="#252526",
    bg_status="#007acc",
    bg_status_err="#d24726",
    bg_primary="#007acc",
    bg_primary_hover="#0098ff",
    fg_main="#f0f0f0",
    fg_title="#ffffff",
    fg_path="#969696",
    fg_zoom="#969696",
    fg_section="#4ec9b0",
    fg_header="#f0f0f0",
    fg_tab="#969696",
    fg_tab_selected="#ffffff",
    fg_status="#ffffff",
    fg_primary="#ffffff",
    fg_disabled="#6a6a6a",
    border="#3a3a3a",
    border_btn="#3a3a3a",
    border_btn_hover="#007acc",
    border_primary="#007acc",
    border_table="#3a3a3a",
    accent="#007acc",
    accent_green="#4ec9b0",
    accent_tab_selected="#007acc",
    accent_subtab="#4ec9b0",
    selection_bg="#264f78",
    scrollbar_handle="#3a3a3a",
    scrollbar_handle_hover="#5a5a5a",
    grid="#3a3a3a",
    highlight_bg="#264f78",
    highlight_fg="#ffffff",
    hover="#2d2d30",
)

# ------------------------------------------------------------------
# Thème CLAIR
# ------------------------------------------------------------------

_LIGHT = dict(
    bg_main="#f5f5f5",
    bg_widget="#ffffff",
    bg_button="#e8e8e8",
    bg_button_hover="#d6d6d6",
    bg_input="#ffffff",
    bg_table="#ffffff",
    bg_row_a="#ffffff",
    bg_row_b="#f0f0f0",
    bg_header="#e0e0e0",
    bg_tab="#e8e8e8",
    bg_tab_selected="#ffffff",
    bg_status="#0078d4",
    bg_status_err="#c42b1c",
    bg_primary="#0078d4",
    bg_primary_hover="#106ebe",
    fg_main="#1a1a1a",
    fg_title="#000000",
    fg_path="#555555",
    fg_zoom="#666666",
    fg_section="#107c10",
    fg_header="#333333",
    fg_tab="#555555",
    fg_tab_selected="#000000",
    fg_status="#ffffff",
    fg_primary="#ffffff",
    fg_disabled="#aaaaaa",
    border="#cccccc",
    border_btn="#cccccc",
    border_btn_hover="#999999",
    border_primary="#0078d4",
    border_table="#cccccc",
    accent="#0078d4",
    accent_green="#107c10",
    accent_tab_selected="#0078d4",
    accent_subtab="#107c10",
    selection_bg="#cce4f7",
    scrollbar_handle="#c0c0c0",
    scrollbar_handle_hover="#999999",
    grid="#cccccc",
    highlight_bg="#cce4f7",
    highlight_fg="#000000",
    hover="#e8e8e8",
)

_current_theme = "dark"


def theme_actuel() -> str:
    return _current_theme


def basculer_theme() -> str:
    global _current_theme
    _current_theme = "light" if _current_theme == "dark" else "dark"
    return _current_theme


def couleurs():
    return _DARK if _current_theme == "dark" else _LIGHT


def qcolors():
    c = couleurs()
    return {
        "row_a": QColor(c["bg_row_a"]),
        "row_b": QColor(c["bg_row_b"]),
        "accent_blue": QColor(c["accent"]),
        "accent_green": QColor(c["accent_green"]),
        "error": QColor(c["bg_status_err"]),
        "highlight_bg": QColor(c["highlight_bg"]),
        "highlight_fg": QColor(c["highlight_fg"]),
    }


def build_stylesheet(c: dict) -> str:
    return f"""
QMainWindow {{
    background-color: {c['bg_main']};
}}
QWidget {{
    background-color: {c['bg_widget']};
    color: {c['fg_main']};
    font-family: "Segoe UI", "Inter", "Helvetica Neue", sans-serif;
    font-size: 12px;
}}
QLabel#title {{
    font-size: 15px; font-weight: bold;
    color: {c['fg_title']}; padding: 4px 0px;
}}
QLabel#filepath {{ color: {c['fg_path']}; font-size: 11px; font-family: "Consolas", monospace; }}
QLabel#zoomLabel {{ color: {c['fg_zoom']}; font-size: 11px; }}
QLabel#sectionLabel {{ color: {c['fg_section']}; font-size: 12px; font-weight: bold; }}
QLabel#searchNav {{ color: {c['accent']}; font-size: 11px; min-width: 80px; }}

QGroupBox {{
    border: 1px solid {c['border']};
    border-radius: 6px;
    margin-top: 12px;
    font-weight: bold;
    font-size: 11px;
    color: {c['accent_green']};
    padding: 10px 4px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 8px;
    padding: 0 4px;
    background-color: {c['bg_widget']};
}}

QPushButton {{
    background-color: {c['bg_button']};
    border: 1px solid {c['border_btn']};
    color: {c['fg_main']};
    padding: 5px 12px; border-radius: 6px;
}}
QPushButton:hover {{
    background-color: {c['bg_button_hover']};
    border: 1px solid {c['border_btn_hover']};
}}
QPushButton:pressed {{ background-color: {c['accent']}; border: 1px solid {c['accent']}; color: white; }}
QPushButton:disabled {{
    color: {c['fg_disabled']};
    background-color: {c['bg_main']};
    border: 1px solid {c['border']};
}}
QPushButton#primaryAction {{
    background-color: {c['accent']};
    border: 1px solid {c['border_primary']};
    color: white; font-weight: bold;
}}
QPushButton#primaryAction:hover {{ background-color: {c['bg_primary_hover']}; }}
QPushButton#navBtn {{
    background-color: {c['bg_button']};
    border: 1px solid {c['border_btn']};
    color: {c['fg_main']};
    padding: 2px 4px; border-radius: 4px; font-size: 11px;
}}
QPushButton#navBtn:disabled {{ color: {c['fg_disabled']}; }}

QLineEdit, QComboBox {{
    background-color: {c['bg_input']};
    border: 1px solid {c['border']};
    color: {c['fg_main']};
    padding: 4px 6px; border-radius: 6px;
}}
QLineEdit:focus, QComboBox:focus {{ border: 1px solid {c['accent']}; }}
QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border-left: 1px solid {c['border']};
}}

QSlider::groove:horizontal {{
    height: 4px; background: {c['border']}; border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {c['accent']}; width: 14px; height: 14px;
    margin: -5px 0; border-radius: 7px;
}}
QSlider::handle:horizontal:hover {{ background: {c['accent']}cc; }}

QTableWidget, QTreeWidget {{
    background-color: {c['bg_table']};
    gridline-color: {c['grid']};
    border: 1px solid {c['border_table']};
    border-radius: 6px;
    selection-background-color: {c['selection_bg']};
    selection-color: {c['fg_title']};
    font-family: "Consolas", "Cascadia Mono", monospace;
    font-size: 11px;
}}
QTreeWidget {{
    font-family: "Segoe UI", sans-serif;
    font-size: 12px;
}}
QHeaderView::section {{
    background-color: {c['bg_header']};
    color: {c['fg_header']};
    padding: 6px; border: none;
    border-right: 1px solid {c['border']};
    border-bottom: 1px solid {c['border']};
    font-weight: bold;
    font-family: "Segoe UI", sans-serif;
    font-size: 11px;
}}
QTableWidget::item {{ padding: 4px 6px; }}

QTabWidget::pane {{ border: 1px solid {c['border']}; top: -1px; border-radius: 6px; background-color: {c['bg_table']}; }}
QTabBar::tab {{
    background-color: {c['bg_tab']};
    color: {c['fg_tab']};
    padding: 6px 14px;
    border: 1px solid {c['border']};
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
}}
QTabBar::tab:selected {{
    background-color: {c['bg_tab_selected']};
    color: {c['fg_tab_selected']};
    border-bottom: 1px solid {c['bg_tab_selected']};
    border-top: 2px solid {c['accent']};
}}
QTabBar::tab:hover {{ color: {c['fg_main']}; }}

QTabWidget#subTabs::pane {{ border: 1px solid {c['grid']}; top: -1px; }}
QTabWidget#subTabs QTabBar::tab {{
    background-color: {c['bg_row_b']};
    color: {c['fg_path']};
    padding: 4px 10px; font-size: 11px;
    border: 1px solid {c['grid']}; border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}}
QTabWidget#subTabs QTabBar::tab:selected {{
    background-color: {c['bg_tab_selected']};
    color: {c['accent_subtab']};
    border-bottom: 1px solid {c['bg_tab_selected']};
    border-top: 2px solid {c['accent_subtab']};
}}

QStatusBar {{
    background-color: {c['bg_header']};
    color: {c['fg_main']}; 
    font-size: 11px;
    border-top: 1px solid {c['border']};
}}
QStatusBar::item {{
    border: none;
}}

QScrollBar:vertical {{ background: {c['bg_main']}; width: 10px; margin: 0px; }}
QScrollBar::handle:vertical {{
    background: {c['scrollbar_handle']}; min-height: 20px; border-radius: 5px;
}}
QScrollBar::handle:vertical:hover {{ background: {c['scrollbar_handle_hover']}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}

QScrollBar:horizontal {{ background: {c['bg_main']}; height: 10px; margin: 0px; }}
QScrollBar::handle:horizontal {{
    background: {c['scrollbar_handle']}; min-width: 20px; border-radius: 5px;
}}
QScrollBar::handle:horizontal:hover {{ background: {c['scrollbar_handle_hover']}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0px; }}

QMenuBar {{
    background-color: {c['bg_header']};
    color: {c['fg_main']};
    border-bottom: 1px solid {c['border']};
}}
QMenuBar::item {{
    background: transparent;
    padding: 4px 8px;
    margin: 2px 0px;
    border-radius: 4px;
}}
QMenuBar::item:selected {{ background-color: {c['hover']}; color: {c['fg_title']}; }}
QMenuBar::item:pressed {{ background-color: {c['accent']}; color: white; }}

QMenu {{
    background-color: {c['bg_widget']};
    color: {c['fg_main']};
    border: 1px solid {c['border']};
    padding: 4px;
    border-radius: 6px;
}}
QMenu::item {{
    padding: 4px 20px;
    border-radius: 4px;
}}
QMenu::item:selected {{ background-color: {c['accent']}; color: white; }}
QMenu::separator {{ height: 1px; background: {c['border']}; margin: 4px 0; }}

QDockWidget {{
    titlebar-close-icon: url(none);
    titlebar-normal-icon: url(none);
    border: 1px solid {c['border']};
}}
QDockWidget::title {{
    background-color: {c['bg_header']};
    color: {c['fg_title']};
    padding: 6px;
    font-weight: bold;
    border-bottom: 1px solid {c['border']};
}}

QToolBar {{
    background-color: {c['bg_header']};
    border-bottom: 1px solid {c['border']};
    spacing: 6px;
    padding: 4px;
}}
QToolBar QToolButton {{
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 4px;
}}
QToolBar QToolButton:hover {{
    background-color: {c['hover']};
    border: 1px solid {c['border']};
}}
QToolBar QToolButton:pressed {{
    background-color: {c['accent']};
    color: white;
}}
QToolBar QToolButton:checked {{
    background-color: {c['selection_bg']};
    border: 1px solid {c['accent']};
}}

QTextEdit#consoleView {{
    background-color: {c['bg_input']};
    border: 1px solid {c['border']};
    border-radius: 6px;
    color: #4ec9b0;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 11px;
}}

QDialog {{
    background-color: {c['bg_widget']};
    color: {c['fg_main']};
}}

QListWidget {{
    background-color: {c['bg_table']};
    border: 1px solid {c['border']};
    border-radius: 6px;
    selection-background-color: {c['selection_bg']};
    selection-color: {c['fg_title']};
    font-size: 12px;
    outline: none;
}}
QListWidget::item {{
    padding: 6px 8px;
    border-radius: 4px;
}}
QListWidget::item:hover {{
    background-color: {c['hover']};
}}
QListWidget::item:selected {{
    background-color: {c['selection_bg']};
    color: {c['fg_title']};
}}

QRadioButton {{
    color: {c['fg_main']};
    spacing: 8px;
    font-size: 12px;
}}
QRadioButton::indicator {{
    width: 14px;
    height: 14px;
    border: 2px solid {c['border']};
    border-radius: 7px;
    background-color: {c['bg_input']};
}}
QRadioButton::indicator:checked {{
    background-color: {c['accent']};
    border: 2px solid {c['accent']};
}}
QRadioButton::indicator:hover {{
    border-color: {c['accent']};
}}
"""


def feuille_de_style() -> str:
    return build_stylesheet(couleurs())

