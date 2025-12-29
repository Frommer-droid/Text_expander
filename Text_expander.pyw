import ctypes
import os
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QStyle

from app.services.paths import resource_path
from app.services.startup_service import apply_user_appdata_override, run_as_admin
from app.ui.main_window import TextExpanderApp


def main():
    apply_user_appdata_override()
    is_admin = run_as_admin()
    if not is_admin:
        sys.exit(0)

    myappid = "mycompany.myproduct.textexpander.19"
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

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
