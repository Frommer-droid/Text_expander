from __future__ import annotations

import os
import sys

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from app.ui.main_window import TextExpanderApp
from app.ui.settings_mixin import SettingsMixin
from app.ui.ui_setup_mixin import UiSetupMixin
from app.ui.ui_scale_mixin import UiScaleMixin
from PySide6.QtWidgets import QApplication, QMainWindow


@pytest.fixture(scope="module")
def app() -> QApplication:
    if QApplication.instance() is None:
        app = QApplication(sys.argv[:1])
    else:
        app = QApplication.instance()
    yield app


def test_window_minimum_size_is_small_and_defined_as_constant():
    assert TextExpanderApp.MINIMUM_WINDOW_SIZE == (360, 240)


def test_window_with_minimum_size_can_shrink_below_legacy_900(app):
    class StubWindow(QMainWindow, UiSetupMixin, UiScaleMixin):
        def __init__(self):
            super().__init__()
            self.settings_file = "stub_unused.json"
            self.setMinimumSize(*TextExpanderApp.MINIMUM_WINDOW_SIZE)
            self.statusBar()
            self._init_ui_scale_runtime()
            self._create_widgets()
            self._create_layout()
            self._apply_styles(1.0)

    window = StubWindow()
    try:
        window.resize(1400, 900)
        window.show()
        app.processEvents()
        assert window.minimumSize().width() <= 400
        assert window.minimumSize().height() <= 400

        window.splitter.moveSplitter(360, 1)
        app.processEvents()
        splitter_position = window.splitter.sizes()[0]
        window.resize(900, 500)
        app.processEvents()
        assert abs(window.splitter.sizes()[0] - splitter_position) <= 1

        window.resize(700, 500)
        app.processEvents()
        assert window.size().width() == 700
        assert window.size().height() == 500
    finally:
        window.close()
        app.processEvents()


def test_first_start_uses_readable_size_and_gives_editor_more_space(app, tmp_path):
    class StubWindow(QMainWindow, UiSetupMixin, SettingsMixin, UiScaleMixin):
        def __init__(self):
            super().__init__()
            self.settings_file = str(tmp_path / "missing_settings.json")
            self.setMinimumSize(*TextExpanderApp.MINIMUM_WINDOW_SIZE)
            self.statusBar()
            self._init_ui_scale_runtime()
            self._create_widgets()
            self._create_layout()

    window = StubWindow()
    try:
        window._load_settings()
        window.show()
        app.processEvents()
        available = app.primaryScreen().availableGeometry()
        assert window.width() >= min(800, available.width())
        assert window.height() >= min(600, available.height())
        assert window.splitter.sizes()[1] > window.splitter.sizes()[0]
    finally:
        window.close()
        app.processEvents()
