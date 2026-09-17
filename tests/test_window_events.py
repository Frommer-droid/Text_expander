from __future__ import annotations

import os
import subprocess
import sys
from unittest.mock import patch

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QApplication, QMainWindow

from app.ui.window_events_mixin import WindowEventsMixin


@pytest.fixture(scope="module")
def app() -> QApplication:
    return QApplication.instance() or QApplication(sys.argv[:1])


def test_close_event_shuts_down_application_and_accepts_event(app):
    class TestWindow(WindowEventsMixin, QMainWindow):
        def __init__(self):
            super().__init__()
            self.is_closing = False
            self.shutdown_calls = 0

        def _shutdown_application(self):
            self.shutdown_calls += 1
            self.is_closing = True

    window = TestWindow()
    event = QCloseEvent()
    try:
        with patch.object(QApplication, "quit") as quit_application:
            window.closeEvent(event)
        assert window.shutdown_calls == 1
        assert event.isAccepted()
        quit_application.assert_called_once_with()
    finally:
        window.deleteLater()


def test_close_button_ends_qt_event_loop_when_tray_mode_is_enabled():
    """Закрытие не должно оставлять python-процесс работающим в трее."""
    script = """
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QMainWindow
from app.ui.window_events_mixin import WindowEventsMixin

class TestWindow(WindowEventsMixin, QMainWindow):
    def __init__(self):
        super().__init__()
        self.is_closing = False

    def _shutdown_application(self):
        self.is_closing = True

app = QApplication([])
app.setQuitOnLastWindowClosed(False)
window = TestWindow()
window.show()
QTimer.singleShot(0, window.close)
raise SystemExit(app.exec())
"""
    environment = os.environ.copy()
    environment["QT_QPA_PLATFORM"] = "offscreen"
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=os.getcwd(),
        env=environment,
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )

    assert result.returncode == 0, result.stderr
