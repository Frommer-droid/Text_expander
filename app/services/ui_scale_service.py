from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping


BASE_LOGICAL_DPI = 96.0
REFERENCE_WIDTH = 2560
REFERENCE_HEIGHT = 1440

MIN_AUTO_SCALE_PERCENT = 70
MAX_AUTO_SCALE_PERCENT = 200
AUTO_SCALE_STEP_PERCENT = 10

MIN_DELTA_PERCENT = -50
MAX_DELTA_PERCENT = 50
DELTA_STEP_PERCENT = 10

MIN_FINAL_SCALE_PERCENT = 35
MAX_FINAL_SCALE_PERCENT = 300
FINAL_SCALE_STEP_PERCENT = 5

MIN_MANUAL_SCALE_REFERENCE_PERCENT = 100
UI_SCALE_MODE_AUTO = "auto"
DEFAULT_UI_SCALE_DELTA_PERCENT = 0
DEFAULT_UI_SCALE_PERCENT = 100


@dataclass(frozen=True)
class UIScaleState:
    auto_percent: int
    delta_percent: int
    final_percent: int
    scale_factor: float


def clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, value))


def round_to_step(value: float, step: int) -> int:
    if step <= 0:
        raise ValueError("Шаг округления должен быть больше нуля.")
    ratio = value / step
    if ratio >= 0:
        return int(math.floor(ratio + 0.5)) * step
    return int(math.ceil(ratio - 0.5)) * step


def _coerce_number(value: Any, default: float) -> float:
    if isinstance(value, bool):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def normalize_ui_scale_mode(value: Any) -> str:
    return UI_SCALE_MODE_AUTO


def normalize_ui_scale_delta_percent(value: Any) -> int:
    number = _coerce_number(value, DEFAULT_UI_SCALE_DELTA_PERCENT)
    rounded = round_to_step(number, DELTA_STEP_PERCENT)
    return clamp(rounded, MIN_DELTA_PERCENT, MAX_DELTA_PERCENT)


def normalize_ui_scale_percent(value: Any) -> int:
    number = _coerce_number(value, DEFAULT_UI_SCALE_PERCENT)
    rounded = round_to_step(number, FINAL_SCALE_STEP_PERCENT)
    return clamp(rounded, MIN_FINAL_SCALE_PERCENT, MAX_FINAL_SCALE_PERCENT)


def normalize_ui_scale_settings(settings: Mapping[str, Any] | None) -> dict[str, Any]:
    normalized = dict(settings or {})
    legacy_percent = normalized.get("ui_scale_percent", DEFAULT_UI_SCALE_PERCENT)
    if "ui_scale_delta_percent" in normalized:
        delta_percent = normalize_ui_scale_delta_percent(
            normalized.get("ui_scale_delta_percent")
        )
    else:
        delta_percent = normalize_ui_scale_delta_percent(
            normalize_ui_scale_percent(legacy_percent) - DEFAULT_UI_SCALE_PERCENT
        )

    normalized["ui_scale_mode"] = normalize_ui_scale_mode(
        normalized.get("ui_scale_mode")
    )
    normalized["ui_scale_delta_percent"] = delta_percent
    normalized["ui_scale_percent"] = normalize_ui_scale_percent(legacy_percent)
    return normalized


def calculate_auto_percent(
    available_width: int,
    available_height: int,
    logical_dpi: float,
) -> int:
    dpi = _coerce_number(logical_dpi, BASE_LOGICAL_DPI)
    if dpi <= 0:
        dpi = BASE_LOGICAL_DPI

    width = max(0, int(available_width))
    height = max(0, int(available_height))
    if width <= 0 or height <= 0:
        return DEFAULT_UI_SCALE_PERCENT

    normalized_width = width * dpi / BASE_LOGICAL_DPI
    normalized_height = height * dpi / BASE_LOGICAL_DPI
    ratio = min(normalized_width / REFERENCE_WIDTH, normalized_height / REFERENCE_HEIGHT)
    rounded = round_to_step(ratio * 100, AUTO_SCALE_STEP_PERCENT)
    return clamp(rounded, MIN_AUTO_SCALE_PERCENT, MAX_AUTO_SCALE_PERCENT)


def calculate_final_percent(auto_percent: int, delta_percent: int) -> int:
    normalized_auto = clamp(
        round_to_step(auto_percent, AUTO_SCALE_STEP_PERCENT),
        MIN_AUTO_SCALE_PERCENT,
        MAX_AUTO_SCALE_PERCENT,
    )
    normalized_delta = normalize_ui_scale_delta_percent(delta_percent)
    delta_reference = max(normalized_auto, MIN_MANUAL_SCALE_REFERENCE_PERCENT)
    raw_final = normalized_auto + delta_reference * normalized_delta / 100
    rounded = round_to_step(raw_final, FINAL_SCALE_STEP_PERCENT)
    return clamp(rounded, MIN_FINAL_SCALE_PERCENT, MAX_FINAL_SCALE_PERCENT)


def calculate_scale_factor(final_percent: int) -> float:
    return normalize_ui_scale_percent(final_percent) / 100.0


def resolve_ui_scale_from_values(
    available_width: int,
    available_height: int,
    logical_dpi: float,
    delta_percent: int,
) -> UIScaleState:
    auto_percent = calculate_auto_percent(
        available_width,
        available_height,
        logical_dpi,
    )
    normalized_delta = normalize_ui_scale_delta_percent(delta_percent)
    final_percent = calculate_final_percent(auto_percent, normalized_delta)
    return UIScaleState(
        auto_percent=auto_percent,
        delta_percent=normalized_delta,
        final_percent=final_percent,
        scale_factor=calculate_scale_factor(final_percent),
    )


def resolve_ui_scale_from_screen(screen: Any, delta_percent: int) -> UIScaleState:
    if screen is None:
        return resolve_ui_scale_from_values(
            REFERENCE_WIDTH,
            REFERENCE_HEIGHT,
            BASE_LOGICAL_DPI,
            delta_percent,
        )

    geometry = screen.availableGeometry()
    return resolve_ui_scale_from_values(
        geometry.width(),
        geometry.height(),
        screen.logicalDotsPerInch(),
        delta_percent,
    )


def scale_px(value: int | float, scale_factor: float, minimum: int = 0) -> int:
    if value == 0:
        return 0
    scaled = int(round(float(value) * scale_factor))
    return max(minimum, scaled)


def scale_point_size(
    value: int | float,
    scale_factor: float,
    minimum: float = 1.0,
) -> float:
    scaled = round(float(value) * scale_factor, 2)
    return max(minimum, scaled)
