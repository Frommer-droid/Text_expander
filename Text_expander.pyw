import ctypes
import os
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QStyle

from app.core.localization import install_qt_base_russian_translation
from app.services.paths import resource_path
from app.services.startup_service import (
    apply_user_appdata_override,
    relaunch_in_windowed_mode,
    run_as_admin,
)
from app.ui.main_window import TextExpanderApp
from app.ui.theme import apply_theme


FROZEN_SMOKE_ARGUMENT = "--frozen-smoke"


def main():
    # Этот путь запускается только проверкой собранного файла. Он загружает
    # native-модули приложения, но не запрашивает UAC и не создаёт GUI.
    if FROZEN_SMOKE_ARGUMENT in sys.argv:
        return 0

    if relaunch_in_windowed_mode():
        sys.exit(0)

    apply_user_appdata_override()
    is_admin = run_as_admin()
    if not is_admin:
        sys.exit(0)

    myappid = "mycompany.myproduct.textexpander.19"
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    app = QApplication(sys.argv)
    apply_theme(app)
    app.setQuitOnLastWindowClosed(False)
    qt_translator = install_qt_base_russian_translation(app)
    if qt_translator is not None:
        app._qt_base_translator = qt_translator

    icon_path = resource_path("logo.ico")
    window_icon = QIcon(icon_path) if os.path.exists(icon_path) else QIcon()
    if window_icon.isNull():
        print(
            f"[WARN] Не удалось загрузить иконку окна '{icon_path}', используется стандартная."
        )
        window_icon = app.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
    app.setWindowIcon(window_icon)

    window = TextExpanderApp(is_admin=is_admin)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
