import logging
import os
import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMainWindow

from app.services.logging_service import configure_logging
from app.services.paths import get_application_path
from app.services.startup_service import get_startup_locations
from app.ui.listener_mixin import ListenerMixin
from app.ui.settings_mixin import SettingsMixin
from app.ui.snippet_data_mixin import SnippetDataMixin
from app.ui.snippet_editor_mixin import SnippetEditorMixin
from app.ui.tray_mixin import TrayMixin
from app.ui.ui_setup_mixin import UiSetupMixin
from app.ui.window_events_mixin import WindowEventsMixin
from app.version import __version__


class TextExpanderApp(
    WindowEventsMixin,
    QMainWindow,
    UiSetupMixin,
    SnippetDataMixin,
    SnippetEditorMixin,
    ListenerMixin,
    TrayMixin,
    SettingsMixin,
):
    CATEGORY_PATH_SEPARATOR = " / "

    def __init__(self, is_admin=False):
        super().__init__()
        self.setWindowTitle(f"Менеджер сниппетов Text expander v{__version__}")
        self.setMinimumSize(900, 700)
        self.statusBar()

        application_path = get_application_path()
        configure_logging(application_path)
        logging.info(
            "Окружение: admin=%s frozen=%s",
            bool(is_admin),
            bool(getattr(sys, "frozen", False)),
        )

        self.settings_file = os.path.join(application_path, "expander_settings.json")
        self.snippets_file = os.path.join(application_path, "snippets.json")
        self.snippets_data = {}
        self.category_combo_paths = {}
        self.original_abbr = None
        self.original_category_path = None
        self.worker = None
        self.listener_thread = None
        self.is_closing = False
        self.right_click_on_close = False
        self.startup_locations = get_startup_locations()
        self.autostart_shortcut_name = "Text_expander.lnk"
        self._capture_countdown = 0

        self._create_widgets()
        self._create_layout()
        self._create_tray_icon()
        self._connect_signals()
        self._apply_styles()
        self._setup_status_bar(is_admin)
        self._load_snippets()
        self._load_settings()
        if hasattr(self, "autostart_tray_action"):
            self.autostart_tray_action.blockSignals(True)
            self.autostart_tray_action.setChecked(self.autostart_check.isChecked())
            self.autostart_tray_action.blockSignals(False)
        self.set_autostart(self.autostart_check.isChecked(), silent=True)
        self._start_listener_thread()
        self._schedule_post_boot_listener_restarts()

        # Если включен запуск свернутым - прячем окно через небольшую задержку
        if self.start_minimized_check.isChecked():
            QTimer.singleShot(100, self.hide_to_tray)
