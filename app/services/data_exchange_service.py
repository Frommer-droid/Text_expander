from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from app.services.ui_scale_service import (
    MAX_DELTA_PERCENT,
    MAX_FINAL_SCALE_PERCENT,
    MIN_DELTA_PERCENT,
    MIN_FINAL_SCALE_PERCENT,
)


class JsonDocumentError(Exception):
    """Ошибка чтения, проверки или записи JSON-документа."""


COMBINED_BACKUP_FORMAT = "text_expander_backup"
COMBINED_BACKUP_VERSION = 1


def load_json_document(file_path):
    path = Path(file_path)
    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError as error:
        raise JsonDocumentError(f"Файл не найден: {path}") from error
    except json.JSONDecodeError as error:
        raise JsonDocumentError(
            f"Файл содержит некорректный JSON: {path}"
        ) from error
    except OSError as error:
        raise JsonDocumentError(f"Не удалось прочитать файл: {path}") from error


def save_json_document(file_path, payload):
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            delete=False,
            dir=path.parent,
            prefix=f".{path.stem}_",
            suffix=".tmp",
            encoding="utf-8",
        ) as temp_file:
            json.dump(payload, temp_file, indent=4, ensure_ascii=False)
            temp_path = temp_file.name

        os.replace(temp_path, path)
    except TypeError as error:
        raise JsonDocumentError(
            f"Не удалось сериализовать JSON для файла: {path}"
        ) from error
    except OSError as error:
        raise JsonDocumentError(f"Не удалось записать файл: {path}") from error
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


def ensure_json_mapping(payload, document_name):
    if not isinstance(payload, dict):
        raise JsonDocumentError(
            f"{document_name} должен содержать JSON-объект верхнего уровня."
        )
    return payload


def validate_settings_payload(payload):
    settings = ensure_json_mapping(payload, "Файл настроек")
    expected_types = {
        "geometry": str,
        "splitter_state": str,
        "expanded_categories": list,
        "autostart_enabled": bool,
        "start_minimized": bool,
        "window_filter_collapsed": bool,
        "ui_scale_mode": str,
    }

    for key, expected_type in expected_types.items():
        value = settings.get(key)
        if value is not None and not isinstance(value, expected_type):
            raise JsonDocumentError(
                f"Поле '{key}' в файле настроек имеет неверный тип."
            )

    int_ranges = {
        "ui_scale_delta_percent": (MIN_DELTA_PERCENT, MAX_DELTA_PERCENT),
        "ui_scale_percent": (MIN_FINAL_SCALE_PERCENT, MAX_FINAL_SCALE_PERCENT),
    }
    for key, (minimum, maximum) in int_ranges.items():
        value = settings.get(key)
        if value is None:
            continue
        if isinstance(value, bool) or not isinstance(value, int):
            raise JsonDocumentError(
                f"Поле '{key}' в файле настроек имеет неверный тип."
            )
        if not minimum <= value <= maximum:
            raise JsonDocumentError(
                f"Поле '{key}' в файле настроек выходит за допустимый диапазон."
            )

    return settings


def build_combined_backup_payload(snippets_payload, settings_payload):
    snippets = ensure_json_mapping(snippets_payload, "Данные сниппетов")
    settings = validate_settings_payload(settings_payload)
    return {
        "format": COMBINED_BACKUP_FORMAT,
        "version": COMBINED_BACKUP_VERSION,
        "snippets": snippets,
        "settings": settings,
    }


def validate_combined_backup_payload(payload):
    backup_payload = ensure_json_mapping(payload, "Файл единого экспорта")

    format_name = backup_payload.get("format")
    if format_name is not None and format_name != COMBINED_BACKUP_FORMAT:
        raise JsonDocumentError(
            "Файл единого экспорта имеет неподдерживаемый формат."
        )

    version = backup_payload.get("version")
    if version is not None and not isinstance(version, int):
        raise JsonDocumentError(
            "Поле 'version' в файле единого экспорта имеет неверный тип."
        )

    if "snippets" not in backup_payload:
        raise JsonDocumentError(
            "Файл единого экспорта не содержит раздел 'snippets'."
        )
    if "settings" not in backup_payload:
        raise JsonDocumentError(
            "Файл единого экспорта не содержит раздел 'settings'."
        )

    return {
        "format": format_name or COMBINED_BACKUP_FORMAT,
        "version": version if version is not None else COMBINED_BACKUP_VERSION,
        "snippets": ensure_json_mapping(
            backup_payload["snippets"],
            "Раздел snippets",
        ),
        "settings": validate_settings_payload(backup_payload["settings"]),
    }
