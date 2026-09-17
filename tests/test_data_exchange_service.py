from __future__ import annotations

import pytest

from app.services.data_exchange_service import (
    COMBINED_BACKUP_FORMAT,
    COMBINED_BACKUP_VERSION,
    JsonDocumentError,
    build_combined_backup_payload,
    ensure_json_mapping,
    load_json_document,
    save_json_document,
    validate_combined_backup_payload,
    validate_settings_payload,
)


def test_save_and_load_json_document_roundtrip(tmp_path):
    file_path = tmp_path / "payload.json"
    payload = {"name": "Text Expander", "enabled": True}

    save_json_document(file_path, payload)

    assert load_json_document(file_path) == payload


def test_save_json_document_creates_parent_directory(tmp_path):
    file_path = tmp_path / "nested" / "config.json"

    save_json_document(file_path, {"ok": True})

    assert file_path.exists()


def test_ensure_json_mapping_rejects_non_object_payload():
    with pytest.raises(JsonDocumentError):
        ensure_json_mapping(["not", "an", "object"], "Тестовый документ")


def test_validate_settings_payload_accepts_supported_fields():
    payload = {
        "geometry": "abc",
        "splitter_state": "def",
        "expanded_categories": [["Общее"]],
        "autostart_enabled": True,
        "start_minimized": False,
        "window_filter_collapsed": True,
        "ui_scale_mode": "auto",
        "ui_scale_delta_percent": 20,
        "ui_scale_percent": 120,
    }

    assert validate_settings_payload(payload) == payload


def test_validate_settings_payload_rejects_invalid_field_type():
    with pytest.raises(JsonDocumentError):
        validate_settings_payload({"autostart_enabled": "yes"})


def test_validate_settings_payload_rejects_invalid_window_filter_collapsed_type():
    with pytest.raises(JsonDocumentError):
        validate_settings_payload({"window_filter_collapsed": "yes"})


def test_validate_settings_payload_rejects_invalid_ui_scale_range():
    with pytest.raises(JsonDocumentError):
        validate_settings_payload({"ui_scale_delta_percent": 80})


def test_load_json_document_rejects_invalid_json(tmp_path):
    file_path = tmp_path / "broken.json"
    file_path.write_text("{broken", encoding="utf-8")

    with pytest.raises(JsonDocumentError):
        load_json_document(file_path)


def test_build_combined_backup_payload_contains_required_sections():
    payload = build_combined_backup_payload(
        {"Общее": {"enabled": True, "snippets": {}, "categories": {}}},
        {"autostart_enabled": True},
    )

    assert payload == {
        "format": COMBINED_BACKUP_FORMAT,
        "version": COMBINED_BACKUP_VERSION,
        "snippets": {"Общее": {"enabled": True, "snippets": {}, "categories": {}}},
        "settings": {"autostart_enabled": True},
    }


def test_validate_combined_backup_payload_rejects_missing_sections():
    with pytest.raises(JsonDocumentError):
        validate_combined_backup_payload({"format": COMBINED_BACKUP_FORMAT})


def test_validate_combined_backup_payload_accepts_valid_payload():
    payload = {
        "format": COMBINED_BACKUP_FORMAT,
        "version": COMBINED_BACKUP_VERSION,
        "snippets": {"Общее": {"enabled": True, "snippets": {}, "categories": {}}},
        "settings": {"start_minimized": False},
    }

    assert validate_combined_backup_payload(payload) == payload
