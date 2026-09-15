from __future__ import annotations

from app.services.ui_scale_service import (
    DEFAULT_UI_SCALE_PERCENT,
    calculate_auto_percent,
    calculate_final_percent,
    normalize_ui_scale_delta_percent,
    normalize_ui_scale_settings,
    resolve_ui_scale_from_values,
    scale_px,
)


def test_calculate_auto_percent_uses_reference_screen_as_100_percent():
    assert calculate_auto_percent(2560, 1440, 96) == 100


def test_calculate_auto_percent_clamps_small_screens():
    assert calculate_auto_percent(1366, 768, 96) == 70


def test_calculate_auto_percent_uses_logical_dpi():
    assert calculate_auto_percent(3840, 2160, 96) == 150
    assert calculate_auto_percent(3840, 2160, 144) == 200


def test_calculate_final_percent_uses_manual_delta_from_auto_reference():
    assert calculate_final_percent(100, 20) == 120
    assert calculate_final_percent(80, 20) == 100
    assert calculate_final_percent(150, -20) == 120


def test_normalize_ui_scale_delta_clamps_and_rounds():
    assert normalize_ui_scale_delta_percent(14) == 10
    assert normalize_ui_scale_delta_percent(16) == 20
    assert normalize_ui_scale_delta_percent(200) == 50
    assert normalize_ui_scale_delta_percent(True) == 0


def test_normalize_settings_migrates_legacy_percent_to_delta():
    settings = normalize_ui_scale_settings({"ui_scale_percent": 130})

    assert settings["ui_scale_mode"] == "auto"
    assert settings["ui_scale_delta_percent"] == 30
    assert settings["ui_scale_percent"] == 130


def test_resolve_ui_scale_from_values_returns_full_state():
    state = resolve_ui_scale_from_values(2560, 1440, 96, 10)

    assert state.auto_percent == DEFAULT_UI_SCALE_PERCENT
    assert state.delta_percent == 10
    assert state.final_percent == 110
    assert state.scale_factor == 1.1


def test_scale_px_preserves_zero_and_respects_minimum():
    assert scale_px(0, 1.5, minimum=1) == 0
    assert scale_px(1, 0.25, minimum=1) == 1
    assert scale_px(10, 1.5) == 15
