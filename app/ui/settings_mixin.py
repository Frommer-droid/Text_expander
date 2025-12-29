import base64
import json
import os
import subprocess
import sys
import tempfile
import traceback

from PySide6.QtWidgets import QApplication

from app.services.paths import get_project_root


class SettingsMixin:
    def on_autostart_changed(self, state):
        """Обрабатывает изменение состояния чекбокса автозапуска."""
        enabled = bool(state)
        if hasattr(self, "autostart_tray_action"):
            self.autostart_tray_action.blockSignals(True)
            self.autostart_tray_action.setChecked(enabled)
            self.autostart_tray_action.blockSignals(False)
        self._save_specific_setting("autostart_enabled", enabled)
        QApplication.processEvents()
        self.set_autostart(enabled)
        status = "включен" if enabled else "выключен"
        self.statusBar().showMessage(f"Автозапуск {status}", 3000)

    def on_start_minimized_changed(self, state):
        """Обрабатывает изменение состояния чекбокса 'запускать свернутым'."""
        enabled = bool(state)
        self._save_specific_setting("start_minimized", enabled)
        status = "включен" if enabled else "выключен"
        self.statusBar().showMessage(f"Запуск свернутым {status}", 3000)

    def _tray_autostart_toggled(self, checked):
        """
        Обрабатывает переключение автозапуска из меню трея,
        синхронизируя состояние с чекбоксом настроек.
        """
        if self.autostart_check.isChecked() != checked:
            self.autostart_check.setChecked(checked)

    def _save_specific_setting(self, key, value):
        try:
            settings = {}
            if os.path.exists(self.settings_file):
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    settings = json.load(f)
            settings[key] = value
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
        except (IOError, json.JSONDecodeError) as e:
            print(f"Ошибка при сохранении настройки '{key}': {e}")

    def _load_settings(self):
        if not os.path.exists(self.settings_file):
            return
        try:
            with open(self.settings_file, "r", encoding="utf-8") as f:
                settings = json.load(f)
            if "geometry" in settings:
                self.restoreGeometry(base64.b64decode(settings["geometry"]))
            if "splitter_state" in settings:
                self.splitter.restoreState(
                    base64.b64decode(settings["splitter_state"])
                )

            autostart_enabled = settings.get("autostart_enabled")
            if autostart_enabled is not None:
                self.autostart_check.blockSignals(True)
                self.autostart_check.setChecked(bool(autostart_enabled))
                self.autostart_check.blockSignals(False)

            start_minimized = settings.get("start_minimized")
            if start_minimized is not None:
                self.start_minimized_check.blockSignals(True)
                self.start_minimized_check.setChecked(bool(start_minimized))
                self.start_minimized_check.blockSignals(False)

            expanded = settings.get("expanded_categories", [])
            self._restore_tree_expanded_state(expanded)
        except (IOError, json.JSONDecodeError):
            pass

    def _save_settings(self):
        """Собирает данные из виджетов и сохраняет их в JSON-файл."""
        settings = {
            "geometry": base64.b64encode(self.saveGeometry().data()).decode("utf-8"),
            "splitter_state": base64.b64encode(self.splitter.saveState().data()).decode(
                "utf-8"
            ),
            "expanded_categories": self._save_tree_expanded_state(),
            "autostart_enabled": self.autostart_check.isChecked(),
            "start_minimized": self.start_minimized_check.isChecked(),
        }

        try:
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Ошибка при сохранении настроек: {e}")

    def closeEvent(self, event):
        """Перехватывает стандартное событие закрытия окна."""
        if not self.is_closing:
            event.ignore()
        else:
            event.accept()

    def set_autostart(self, enabled, silent=False):
        """
        Настраивает запуск программы вместе с Windows.
        """
        try:
            target_path = self._resolve_autostart_target()
            if not target_path:
                return

            task_name = "Text_expander"
            subprocess.run(
                ["schtasks", "/Delete", "/TN", task_name, "/F"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
                creationflags=subprocess.CREATE_NO_WINDOW,
                check=False,
            )

            if enabled:
                created = False
                for folder in self.startup_locations:
                    if not folder:
                        continue
                    try:
                        os.makedirs(folder, exist_ok=True)
                    except OSError:
                        continue
                    shortcut_path = os.path.join(folder, self.autostart_shortcut_name)
                    if self._create_shortcut(shortcut_path, target_path):
                        created = True
                        if not silent:
                            self.statusBar().showMessage("Автозапуск включен", 4000)
                        break

                if not created:
                    if not silent:
                        self.statusBar().showMessage(
                            "Не удалось создать ярлык", 5000
                        )

            else:
                removed = False
                for folder in self.startup_locations:
                    if not folder:
                        continue
                    shortcut_path = os.path.join(folder, self.autostart_shortcut_name)
                    if os.path.exists(shortcut_path):
                        try:
                            os.remove(shortcut_path)
                            removed = True
                        except Exception as err:
                            print(f"Ошибка удаления ярлыка '{shortcut_path}': {err}")
                            traceback.print_exc()

                if removed and not silent:
                    self.statusBar().showMessage("Автозапуск отключен", 4000)

        except Exception as e:
            print(f"Критическая ошибка в set_autostart: {e}")
            traceback.print_exc()
            if not silent:
                self.statusBar().showMessage("Критическая ошибка автозапуска", 5000)

    def _resolve_autostart_target(self):
        if getattr(sys, "frozen", False):
            target_path = sys.executable
        else:
            target_path = os.path.join(get_project_root(), "Text_expander.pyw")

        target_path = os.path.normpath(target_path)
        if not os.path.exists(target_path):
            self.statusBar().showMessage(
                "Ошибка создания ярлыка: целевой файл не найден", 5000
            )
            return None
        return target_path

    def _create_shortcut(self, shortcut_path, target_path):
        vbs_script = f"""
Set oWS = WScript.CreateObject("WScript.Shell")
sLinkFile = "{shortcut_path}"
Set oLink = oWS.CreateShortcut(sLinkFile)
oLink.TargetPath = "{target_path}"
oLink.WorkingDirectory = "{os.path.dirname(target_path)}"
oLink.Description = "Text expander"
oLink.Save
"""
        tmp_file = None
        try:
            with tempfile.NamedTemporaryFile(
                "w", delete=False, suffix=".vbs", encoding="utf-8"
            ) as tmp:
                tmp.write(vbs_script)
                tmp_file = tmp.name

            subprocess.run(
                ["cscript", "//Nologo", tmp_file],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                check=False,
            )
            if not os.path.exists(shortcut_path):
                self.statusBar().showMessage("Ошибка создания ярлыка", 5000)
                return False
            return True
        except Exception as err:
            print(f"Ошибка при создании ярлыка: {err}")
            traceback.print_exc()
            self.statusBar().showMessage("Ошибка создания ярлыка", 5000)
            return False
        finally:
            if tmp_file and os.path.exists(tmp_file):
                try:
                    os.remove(tmp_file)
                except OSError:
                    pass
