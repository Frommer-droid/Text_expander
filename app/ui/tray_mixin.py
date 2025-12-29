import os

from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import QMenu, QStyle, QSystemTrayIcon

from app.services.paths import resource_path
from app.version import __version__


class TrayMixin:
    def hide_to_tray(self):
        """Сворачивает окно в трей и показывает уведомление."""
        self.hide()
        self.show_hide_action.setText("Показать менеджер")
        self.tray_icon.showMessage(
            "Text expander",
            "Приложение запущено и свернуто в трей",
            QSystemTrayIcon.MessageIcon.Information,
            2000,
        )

    def _create_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        tray_icon_path = resource_path("logo.ico")
        tray_icon = QIcon(tray_icon_path) if os.path.exists(tray_icon_path) else QIcon()
        if tray_icon.isNull():
            print(
                f"[WARN] Не удалось загрузить '{tray_icon_path}', используем стандартную иконку трея."
            )
            tray_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        self.tray_icon.setIcon(tray_icon)
        self.tray_icon.setToolTip(f"Text expander v{__version__}")
        tray_menu = QMenu()
        self.show_hide_action = QAction("Показать менеджер", self)
        self.show_hide_action.triggered.connect(self.show_hide_window)
        tray_menu.addAction(self.show_hide_action)
        self.pause_resume_action = QAction("Приостановить", self)
        self.pause_resume_action.triggered.connect(self.toggle_listening)
        tray_menu.addAction(self.pause_resume_action)
        self.autostart_tray_action = QAction("Автозапуск", self)
        self.autostart_tray_action.setCheckable(True)
        self.autostart_tray_action.setChecked(self.autostart_check.isChecked())
        self.autostart_tray_action.toggled.connect(self._tray_autostart_toggled)
        tray_menu.addAction(self.autostart_tray_action)
        reload_action = QAction("Обновить сниппеты", self)
        reload_action.triggered.connect(self.reload_listener_snippets)
        tray_menu.addAction(reload_action)

        tray_menu.addSeparator()

        quit_action = QAction("Выход", self)
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_hide_window()

    def show_hide_window(self):
        if self.isVisible():
            self.hide()
            self.show_hide_action.setText("Показать менеджер")
        else:
            self.show()
            self.activateWindow()
            self.raise_()
            self.show_hide_action.setText("Скрыть менеджер")

    def toggle_listening(self):
        if not self.worker:
            self.statusBar().showMessage("Слушатель ещё не запущен", 3000)
            return
        self.worker.toggle_pause()
        status_text = "Возобновить" if self.worker.is_paused else "Приостановить"
        self.pause_resume_action.setText(status_text)
        message = (
            "Отслеживание ввода приостановлено."
            if self.worker.is_paused
            else "Отслеживание ввода снова активно."
        )
        self.tray_icon.showMessage(
            "Статус", message, QSystemTrayIcon.MessageIcon.Information, 500
        )

    def reload_listener_snippets(self):
        """Применяет изменения: сохраняет сниппеты в файл и перезагружает их в слушателе."""
        # Сохраняем текущее состояние сниппетов в файл перед перезагрузкой
        self._save_snippets_to_file()

        # Перезагружаем сниппеты в рабочем потоке слушателя
        if self.worker:
            self.worker.reload_snippets()

    def quit_application(self):
        """Полностью завершает приложение."""
        self.is_closing = True
        self._save_settings()
        self._stop_listener_thread()
        self.tray_icon.hide()
        self.close()
