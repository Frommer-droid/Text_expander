from __future__ import annotations

import copy
import os

from PySide6.QtWidgets import QFileDialog, QMessageBox

from app.services.data_exchange_service import (
    JsonDocumentError,
    build_combined_backup_payload,
    ensure_json_mapping,
    load_json_document,
    save_json_document,
    validate_combined_backup_payload,
    validate_settings_payload,
)
from app.services.paths import get_application_path


class ImportExportMixin:
    def _default_exchange_directory(self):
        return get_application_path()

    def _prompt_export_json_path(self, title, default_filename):
        default_path = os.path.join(self._default_exchange_directory(), default_filename)
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            title,
            default_path,
            "JSON files (*.json)",
        )
        if file_path and not file_path.lower().endswith(".json"):
            file_path = f"{file_path}.json"
        return file_path

    def _prompt_import_json_path(self, title):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            title,
            self._default_exchange_directory(),
            "JSON files (*.json)",
        )
        return file_path

    def _confirm_import(self, title, message):
        reply = QMessageBox.question(
            self,
            title,
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return reply == QMessageBox.StandardButton.Yes

    def _show_exchange_error(self, title, error):
        QMessageBox.critical(self, title, str(error))

    def _sync_autostart_tray_action(self):
        if hasattr(self, "autostart_tray_action"):
            self.autostart_tray_action.blockSignals(True)
            self.autostart_tray_action.setChecked(self.autostart_check.isChecked())
            self.autostart_tray_action.blockSignals(False)

    def _collect_settings_payload(self):
        self._save_settings()
        if not os.path.exists(self.settings_file):
            return {}
        return validate_settings_payload(load_json_document(self.settings_file))

    def _normalize_imported_snippets(self, payload, document_name):
        imported_payload = ensure_json_mapping(payload, document_name)
        normalized_snippets, _ = self._normalize_snippet_store(imported_payload)
        if not normalized_snippets:
            normalized_snippets = {"Общее": self._new_category_payload()}
        return normalized_snippets

    def _apply_snippets_payload(self, snippets_payload):
        self.snippets_data = snippets_payload
        save_json_document(self.snippets_file, self.snippets_data)
        self._load_snippets()
        self._clear_fields_for_new_snippet()
        if self.worker:
            self.worker.reload_snippets()

    def _apply_settings_payload(self, settings_payload):
        save_json_document(self.settings_file, settings_payload)
        self._load_settings()
        if hasattr(self, "apply_ui_scale"):
            self.apply_ui_scale(allow_window_resize=True, reason="manual-delta")
        self._sync_autostart_tray_action()
        self.set_autostart(self.autostart_check.isChecked(), silent=True)

    def _restore_snippets_payload(self, snippets_payload):
        self._apply_snippets_payload(copy.deepcopy(snippets_payload))

    def _restore_settings_payload(self, settings_payload):
        self._apply_settings_payload(copy.deepcopy(settings_payload))

    def export_snippets_to_json(self):
        file_path = self._prompt_export_json_path(
            "Экспорт сниппетов",
            "Text_expander_snippets.json",
        )
        if not file_path:
            return

        try:
            save_json_document(file_path, self.snippets_data)
        except JsonDocumentError as error:
            self._show_exchange_error("Ошибка экспорта сниппетов", error)
            return

        self.statusBar().showMessage(
            f"Сниппеты экспортированы: {file_path}",
            4000,
        )

    def import_snippets_from_json(self):
        file_path = self._prompt_import_json_path("Импорт сниппетов")
        if not file_path:
            return

        if not self._confirm_import(
            "Импорт сниппетов",
            "Импорт заменит текущие сниппеты. Несохраненные изменения в редакторе будут потеряны. Продолжить?",
        ):
            return

        try:
            normalized_snippets = self._normalize_imported_snippets(
                load_json_document(file_path),
                "Файл сниппетов",
            )
        except JsonDocumentError as error:
            self._show_exchange_error("Ошибка импорта сниппетов", error)
            return

        previous_snippets = copy.deepcopy(self.snippets_data)
        try:
            self._apply_snippets_payload(normalized_snippets)
        except Exception as error:  # pragma: no cover - defensive Qt/runtime branch
            try:
                self._restore_snippets_payload(previous_snippets)
            except Exception:
                pass
            self._show_exchange_error(
                "Ошибка импорта сниппетов",
                JsonDocumentError(
                    f"Не удалось применить импортированные сниппеты: {error}"
                ),
            )
            return

        self.statusBar().showMessage(
            f"Сниппеты импортированы из файла: {file_path}",
            4000,
        )

    def export_settings_to_json(self):
        file_path = self._prompt_export_json_path(
            "Экспорт настроек",
            "Text_expander_settings.json",
        )
        if not file_path:
            return

        try:
            settings_payload = self._collect_settings_payload()
            save_json_document(file_path, settings_payload)
        except JsonDocumentError as error:
            self._show_exchange_error("Ошибка экспорта настроек", error)
            return

        self.statusBar().showMessage(
            f"Настройки экспортированы: {file_path}",
            4000,
        )

    def import_settings_from_json(self):
        file_path = self._prompt_import_json_path("Импорт настроек")
        if not file_path:
            return

        if not self._confirm_import(
            "Импорт настроек",
            "Импорт заменит текущие настройки окна и системные параметры программы. Продолжить?",
        ):
            return

        try:
            imported_settings = validate_settings_payload(load_json_document(file_path))
        except JsonDocumentError as error:
            self._show_exchange_error("Ошибка импорта настроек", error)
            return

        previous_settings = self._collect_settings_payload()
        try:
            self._apply_settings_payload(imported_settings)
        except Exception as error:  # pragma: no cover - defensive Qt/runtime branch
            try:
                self._restore_settings_payload(previous_settings)
            except Exception:
                pass
            self._show_exchange_error(
                "Ошибка применения настроек",
                JsonDocumentError(
                    f"Не удалось применить импортированные настройки: {error}"
                ),
            )
            return

        self.statusBar().showMessage(
            f"Настройки импортированы из файла: {file_path}",
            4000,
        )

    def export_all_data_to_json(self):
        file_path = self._prompt_export_json_path(
            "Экспорт сниппетов и настроек",
            "Text_expander_backup.json",
        )
        if not file_path:
            return

        try:
            settings_payload = self._collect_settings_payload()
            backup_payload = build_combined_backup_payload(
                copy.deepcopy(self.snippets_data),
                settings_payload,
            )
            save_json_document(file_path, backup_payload)
        except JsonDocumentError as error:
            self._show_exchange_error(
                "Ошибка экспорта данных программы",
                error,
            )
            return

        self.statusBar().showMessage(
            f"Сниппеты и настройки экспортированы: {file_path}",
            4000,
        )

    def import_all_data_from_json(self):
        file_path = self._prompt_import_json_path("Импорт сниппетов и настроек")
        if not file_path:
            return

        if not self._confirm_import(
            "Импорт сниппетов и настроек",
            "Импорт заменит и текущие сниппеты, и текущие настройки программы. Продолжить?",
        ):
            return

        try:
            backup_payload = validate_combined_backup_payload(
                load_json_document(file_path)
            )
            normalized_snippets = self._normalize_imported_snippets(
                backup_payload["snippets"],
                "Раздел snippets",
            )
            imported_settings = backup_payload["settings"]
        except JsonDocumentError as error:
            self._show_exchange_error(
                "Ошибка импорта данных программы",
                error,
            )
            return

        previous_snippets = copy.deepcopy(self.snippets_data)
        previous_settings = self._collect_settings_payload()
        try:
            self._apply_snippets_payload(normalized_snippets)
            self._apply_settings_payload(imported_settings)
        except Exception as error:  # pragma: no cover - defensive Qt/runtime branch
            try:
                self._restore_snippets_payload(previous_snippets)
                self._restore_settings_payload(previous_settings)
            except Exception:
                pass
            self._show_exchange_error(
                "Ошибка импорта данных программы",
                JsonDocumentError(
                    f"Не удалось применить импортированные данные: {error}"
                ),
            )
            return

        self.statusBar().showMessage(
            f"Сниппеты и настройки импортированы из файла: {file_path}",
            4000,
        )
