from __future__ import annotations

from app.ui.styles import build_app_stylesheet


def test_build_app_stylesheet_scales_fonts_and_control_sizes():
    base = build_app_stylesheet(1.0)
    enlarged = build_app_stylesheet(1.5)

    assert "font-size: 15pt" in base
    assert "font-size: 22.5pt" in enlarged
    assert "min-height: 40px" in base
    assert "min-height: 60px" in enlarged
    assert "QTreeWidget QCheckBox" in base
    assert "background-color: transparent" in base
