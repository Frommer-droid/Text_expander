import ctypes
import logging
import os
import threading

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QSystemTrayIcon

from app.services.listener_worker import ListenerWorker


class ListenerMixin:
    def _start_listener_thread(self):
        """Создает и запускает поток клавиатурного слушателя."""
        if self.worker and self.listener_thread and self.listener_thread.is_alive():
            return
        self.worker = ListenerWorker(self.snippets_file)
        self.listener_thread = threading.Thread(
            target=self.worker.run, name="TextExpanderListener", daemon=True
        )
        self.listener_thread.start()
        logging.info("[RUN] Поток слушателя запущен")

    def _stop_listener_thread(self):
        """Останавливает поток слушателя, если он запущен."""
        worker = getattr(self, "worker", None)
        thread = getattr(self, "listener_thread", None)
        if worker:
            worker.stop()
        if thread:
            thread.join(timeout=2.0)
            if thread.is_alive():
                logging.warning("[WARN] Поток слушателя не остановился вовремя")
        self.worker = None
        self.listener_thread = None

    def _restart_listener_silent(self):
        """Перезапускает слушатель без уведомлений (для автозапуска)."""
        if self.is_closing:
            return
        logging.info("[INIT] Тихий перезапуск слушателя")
        self._stop_listener_thread()
        self._start_listener_thread()
        if hasattr(self, "pause_resume_action"):
            self.pause_resume_action.setText("Приостановить")

    def _schedule_post_boot_listener_restarts(self):
        """
        При автозапуске некоторые приложения/службы Windows могут позже подхватывать
        свои хуки ввода. Чтобы не требовать ручного перезапуска, делаем 1-2
        мягких перезапуска слушателя в первые минуты после загрузки.
        """
        if not getattr(self, "autostart_check", None):
            return
        if not self.autostart_check.isChecked():
            return
        try:
            uptime_ms = int(ctypes.windll.kernel32.GetTickCount64())
        except Exception:
            uptime_ms = None
        if uptime_ms is None or uptime_ms > 10 * 60 * 1000:
            return

        has_startup_shortcut = any(
            folder
            and os.path.exists(os.path.join(folder, self.autostart_shortcut_name))
            for folder in (self.startup_locations or [])
        )
        if not has_startup_shortcut:
            return

        QTimer.singleShot(60_000, self._restart_listener_silent)
        QTimer.singleShot(150_000, self._restart_listener_silent)

    def restart_listener(self):
        """Перезапускает слушатель вручную через меню трея."""
        self.statusBar().showMessage("Перезапускаем слушатель...", 3000)
        try:
            self._stop_listener_thread()
            self._start_listener_thread()
            if hasattr(self, "pause_resume_action"):
                self.pause_resume_action.setText("Приостановить")
        finally:
            if hasattr(self, "tray_icon"):
                self.tray_icon.showMessage(
                    "Статус",
                    "Слушатель перезапущен и отслеживает новые окна.",
                    QSystemTrayIcon.MessageIcon.Information,
                    1500,
                )
