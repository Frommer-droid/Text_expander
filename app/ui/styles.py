from __future__ import annotations

from app.services.ui_scale_service import scale_point_size, scale_px


# Палитра OneDark Pro (https://github.com/Binaryify/OneDark-Pro)
ONEDARK_BG = "#1F2329"  # основной фон окна
ONEDARK_BG_SOFT = "#282C34"  # фон вложенных областей (дерево, поля, меню)
ONEDARK_BG_HOVER = "#323843"  # hover элементов списков и вкладок
ONEDARK_BORDER = "#3E4654"  # границы и выделение
ONEDARK_FG = "#C3CBD8"  # основной текст
ONEDARK_FG_BRIGHT = "#FFFFFF"  # яркий текст
ONEDARK_BLUE = "#4E8FE8"  # акцент (кнопки, вкладки)
ONEDARK_BLUE_HOVER = "#68A5F3"
ONEDARK_BLUE_PRESSED = "#386FC0"
ONEDARK_CYAN = "#56B6C2"  # лейблы, статусная строка
ONEDARK_GREEN = "#98C379"  # основное действие («Сохранить»)
ONEDARK_GREEN_HOVER = "#A9D68B"
ONEDARK_GREEN_PRESSED = "#7CB05E"
ONEDARK_ORANGE = "#D19A66"  # предупреждение («Удалить»)
ONEDARK_ORANGE_HOVER = "#E8B887"
ONEDARK_ORANGE_PRESSED = "#A7763E"
ONEDARK_RED = "#E06C75"  # негативный статус


def _px(value: int, scale_factor: float, minimum: int = 0) -> str:
    return f"{scale_px(value, scale_factor, minimum)}px"


def _pt(value: int | float, scale_factor: float) -> str:
    return f"{scale_point_size(value, scale_factor):g}pt"


def build_app_stylesheet(scale_factor: float = 1.0) -> str:
    main_font = _pt(15, scale_factor)
    status_font = _pt(12, scale_factor)
    border_radius = _px(6, scale_factor, 1)
    group_radius = _px(8, scale_factor, 1)
    control_padding = _px(7, scale_factor, 1)
    thin_padding = _px(2, scale_factor, 1)

    return f"""
    QMainWindow, QWidget {{
        background-color: {ONEDARK_BG};
        color: {ONEDARK_FG};
        font-family: Aptos, sans-serif;
        font-size: {main_font};
    }}
    QStatusBar {{
        background-color: {ONEDARK_BG_SOFT};
        color: {ONEDARK_CYAN};
        font-size: {status_font};
    }}
    QStatusBar::item {{ border: 0px; }}
    QTabWidget::pane {{
        border: {_px(1, scale_factor, 1)} solid {ONEDARK_BORDER};
        border-radius: {group_radius};
        background-color: {ONEDARK_BG};
        top: {_px(-1, scale_factor, 0)};
    }}
    QTabBar::tab {{
        background: {ONEDARK_BG_SOFT};
        color: {ONEDARK_FG};
        border: {_px(1, scale_factor, 1)} solid {ONEDARK_BORDER};
        border-bottom: none;
        border-top-left-radius: {border_radius};
        border-top-right-radius: {border_radius};
        padding: {control_padding} {_px(12, scale_factor, 2)};
        margin-right: {_px(2, scale_factor, 1)};
    }}
    QTabBar::tab:selected {{
        background: {ONEDARK_BG};
        color: {ONEDARK_FG_BRIGHT};
        border-color: {ONEDARK_BLUE};
        border-bottom: {_px(1, scale_factor, 1)} solid {ONEDARK_BG};
    }}
    QTabBar::tab:hover {{ background: {ONEDARK_BG_HOVER}; }}
    QLabel {{
        color: {ONEDARK_CYAN};
        padding: {thin_padding};
    }}
    QGroupBox {{
        border: {_px(1, scale_factor, 1)} solid {ONEDARK_BORDER};
        border-radius: {group_radius};
        margin-top: {_px(16, scale_factor, 1)};
        padding: {control_padding} {control_padding};
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: {_px(10, scale_factor, 1)};
        padding: 0 {_px(5, scale_factor, 1)};
        font-weight: bold;
        color: {ONEDARK_FG_BRIGHT};
    }}
    QGroupBox#window_filter_group {{
        margin-top: {_px(4, scale_factor, 1)};
        padding: {_px(2, scale_factor, 1)} {_px(2, scale_factor, 1)} {thin_padding} {_px(2, scale_factor, 1)};
    }}
    QPushButton#filter_header_btn {{
        background-color: transparent;
        color: {ONEDARK_FG_BRIGHT};
        border: none;
        border-radius: {border_radius};
        min-height: {_px(28, scale_factor, 16)};
        padding: {thin_padding} {control_padding};
        text-align: left;
        font-weight: bold;
    }}
    QPushButton#filter_header_btn:hover {{ background-color: {ONEDARK_BG_HOVER}; }}
    QLineEdit, QTextEdit, QComboBox {{
        background-color: {ONEDARK_BG_SOFT};
        border: {_px(1, scale_factor, 1)} solid {ONEDARK_BORDER};
        border-radius: {border_radius};
        padding: {control_padding};
        color: {ONEDARK_FG};
    }}
    QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
        border: {_px(1, scale_factor, 1)} solid {ONEDARK_BLUE};
        background-color: #20252D;
    }}
    QComboBox::drop-down {{ border: none; width: {_px(28, scale_factor, 12)}; }}
    QComboBox QAbstractItemView {{
        background-color: {ONEDARK_BG_SOFT};
        color: {ONEDARK_FG};
        border: {_px(1, scale_factor, 1)} solid {ONEDARK_BORDER};
        selection-background-color: {ONEDARK_BORDER};
        selection-color: {ONEDARK_FG_BRIGHT};
    }}
    QComboBox QAbstractItemView::item {{
        min-height: {_px(28, scale_factor, 16)};
        padding: {_px(4, scale_factor, 1)};
    }}
    QComboBox QAbstractItemView::item:hover {{
        background-color: {ONEDARK_BG_HOVER};
        color: {ONEDARK_FG};
    }}
    QCheckBox::indicator {{
        width: {_px(18, scale_factor, 10)};
        height: {_px(18, scale_factor, 10)};
    }}
    QTreeWidget QCheckBox {{
        background-color: transparent;
        padding: 0px;
        margin: 0px;
    }}
    QTreeWidget {{
        background-color: {ONEDARK_BG_SOFT};
        border: {_px(1, scale_factor, 1)} solid {ONEDARK_BORDER};
    }}
    QTreeWidget::item:selected {{ background-color: {ONEDARK_BORDER}; color: {ONEDARK_FG_BRIGHT}; }}
    QTreeWidget::item {{ padding: {control_padding}; border-radius: {border_radius}; }}
    QTreeWidget::item:hover {{ background-color: {ONEDARK_BG_HOVER}; }}
    QSplitter::handle {{ background-color: {ONEDARK_BORDER}; }}
    QSplitter::handle:horizontal {{ width: {_px(5, scale_factor, 1)}; }}
    QPushButton {{
        background-color: {ONEDARK_BLUE};
        color: {ONEDARK_FG_BRIGHT};
        border: none;
        border-radius: {border_radius};
        min-height: {_px(40, scale_factor, 24)};
        padding: {control_padding} {_px(10, scale_factor, 2)};
    }}
    QPushButton:hover {{ background-color: {ONEDARK_BLUE_HOVER}; }}
    QPushButton:pressed {{ background-color: {ONEDARK_BLUE_PRESSED}; }}
    QPushButton:disabled {{ background-color: {ONEDARK_BORDER}; color: #7D8695; }}
    QPushButton#warning_btn {{ background-color: {ONEDARK_ORANGE}; color: {ONEDARK_FG_BRIGHT}; }}
    QPushButton#warning_btn:hover {{ background-color: {ONEDARK_ORANGE_HOVER}; color: #282C34; }}
    QPushButton#warning_btn:pressed {{ background-color: {ONEDARK_ORANGE_PRESSED}; }}
    QPushButton#start_btn {{
        background-color: {ONEDARK_GREEN};
        color: #282C34;
        font-weight: bold;
    }}
    QPushButton#start_btn:hover {{ background-color: {ONEDARK_GREEN_HOVER}; }}
    QPushButton#start_btn:pressed {{ background-color: {ONEDARK_GREEN_PRESSED}; }}
    QMenu {{
        background-color: {ONEDARK_BG_SOFT};
        border: {_px(1, scale_factor, 1)} solid {ONEDARK_BORDER};
        color: {ONEDARK_FG};
    }}
    QMenu::item:selected {{ background-color: {ONEDARK_BG_HOVER}; color: {ONEDARK_FG_BRIGHT}; }}
    QMessageBox {{ background-color: {ONEDARK_BG}; }}
    QMessageBox QLabel {{ color: {ONEDARK_FG}; }}
    QMessageBox QPushButton {{
        background-color: {ONEDARK_BLUE};
        color: {ONEDARK_FG_BRIGHT};
        border-radius: {border_radius};
        min-height: {_px(35, scale_factor, 22)};
        min-width: {_px(100, scale_factor, 60)};
        padding: {control_padding} {_px(15, scale_factor, 4)};
    }}
    QMessageBox QPushButton:hover {{ background-color: {ONEDARK_BLUE_HOVER}; }}
    QMessageBox QPushButton:pressed {{ background-color: {ONEDARK_BLUE_PRESSED}; }}
    QScrollBar:vertical, QScrollBar:horizontal {{
        background: {ONEDARK_BG_SOFT};
        border: none;
        margin: 0px;
    }}
    QScrollBar:vertical {{ width: {_px(14, scale_factor, 8)}; }}
    QScrollBar:horizontal {{ height: {_px(14, scale_factor, 8)}; }}
    QScrollBar::handle {{
        background: {ONEDARK_BORDER};
        border-radius: {_px(6, scale_factor, 2)};
        min-height: {_px(24, scale_factor, 12)};
        min-width: {_px(24, scale_factor, 12)};
    }}
    QScrollBar::add-line, QScrollBar::sub-line {{
        width: 0px;
        height: 0px;
    }}
    """.strip()
