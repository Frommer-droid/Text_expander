from __future__ import annotations

import os
import re
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QPushButton

from app.ui.theme import (
    DERIVED_COLORS,
    THEME_COLORS,
    apply_theme,
    build_global_stylesheet,
    enforce_button_proportions,
)


def _all_stylesheet_hex(value: str) -> set[str]:
    return {match.group(0).upper() for match in re.finditer(r"#[0-9A-Fa-f]{6}", value)}


def test_build_global_stylesheet_uses_only_theme_palette():
    base = build_global_stylesheet(THEME_COLORS, 1.0)
    enlarged = build_global_stylesheet(THEME_COLORS, 1.5)

    allowed = {v.upper() for v in {**DERIVED_COLORS, **THEME_COLORS}.values()}
    found = _all_stylesheet_hex(base) | _all_stylesheet_hex(enlarged)
    assert found, "в stylesheet нет hex-цветов темы"
    assert found <= allowed, f"hex мимо палитры: {sorted(found - allowed)}"

    # Tahoma первым, запасные Segoe UI/Aptos.
    assert '"Tahoma"' in base
    assert base.index('"Tahoma"') < base.index('"Segoe UI"')

    # Ролевая система кнопок присутствует.
    for role in (
        "QPushButton",
        "QPushButton#primaryButton",
        "QPushButton#start_btn",
        "QPushButton#danger_btn",
        "QPushButton#success_btn",
        "QPushButton#warning_btn",
    ):
        assert role in base, f"нет селектора {role}"

    # Масштаб меняет размеры.
    assert "min-height: 30px" in base
    assert "min-height: 45px" in enlarged


def test_apply_theme_sets_tahoma_and_enforces_proportions():
    app = QApplication.instance() or QApplication(sys.argv[:1])
    apply_theme(app, scale_factor=1.0)

    families = app.font().families() if hasattr(app.font(), "families") else []
    if families:
        assert families[0] == "Tahoma"

    button = QPushButton("Тест")
    button.setFixedHeight(40)
    button.ensurePolished()
    enforce_button_proportions([button])
    assert button.minimumWidth() >= button.sizeHint().height()
