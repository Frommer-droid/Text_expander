from __future__ import annotations

from PySide6.QtCore import QMargins, QSize
from PySide6.QtWidgets import QAbstractButton, QLayout, QWidget

from app.services.ui_scale_service import scale_px


_WIDGET_SIZE_MAX = 16777215
_PROP_PREFIX = "_text_expander_ui_scale_"


def _property_name(name: str) -> str:
    return f"{_PROP_PREFIX}{name}"


def _get_or_store(obj, name: str, value):
    prop_name = _property_name(name)
    stored = obj.property(prop_name)
    if stored is None:
        obj.setProperty(prop_name, value)
        return value
    return stored


def _scaled_margin(value: int, scale_factor: float) -> int:
    return scale_px(value, scale_factor, minimum=0)


def _scale_margins(margins: QMargins, scale_factor: float) -> QMargins:
    return QMargins(
        _scaled_margin(margins.left(), scale_factor),
        _scaled_margin(margins.top(), scale_factor),
        _scaled_margin(margins.right(), scale_factor),
        _scaled_margin(margins.bottom(), scale_factor),
    )


def _scale_size(size: QSize, scale_factor: float, minimum: int = 0) -> QSize:
    return QSize(
        scale_px(size.width(), scale_factor, minimum=minimum),
        scale_px(size.height(), scale_factor, minimum=minimum),
    )


def _scale_maximum_size(size: QSize, scale_factor: float) -> QSize:
    width = size.width()
    height = size.height()
    scaled_width = (
        _WIDGET_SIZE_MAX
        if width >= _WIDGET_SIZE_MAX
        else scale_px(width, scale_factor, minimum=0)
    )
    scaled_height = (
        _WIDGET_SIZE_MAX
        if height >= _WIDGET_SIZE_MAX
        else scale_px(height, scale_factor, minimum=0)
    )
    return QSize(scaled_width, scaled_height)


def apply_scaled_layout_metrics(layout: QLayout | None, scale_factor: float) -> None:
    if layout is None:
        return

    base_margins = _get_or_store(
        layout,
        "layout_margins",
        QMargins(layout.contentsMargins()),
    )
    layout.setContentsMargins(_scale_margins(base_margins, scale_factor))

    base_spacing = _get_or_store(layout, "layout_spacing", layout.spacing())
    if base_spacing >= 0:
        layout.setSpacing(scale_px(base_spacing, scale_factor, minimum=0))

    for index in range(layout.count()):
        item = layout.itemAt(index)
        if item.layout() is not None:
            apply_scaled_layout_metrics(item.layout(), scale_factor)
        if item.widget() is not None:
            apply_scaled_widget_metrics(item.widget(), scale_factor)


def apply_scaled_widget_metrics(root: QWidget, scale_factor: float) -> None:
    seen_widgets: set[int] = set()

    def apply_widget(widget: QWidget) -> None:
        widget_id = id(widget)
        if widget_id in seen_widgets:
            return
        seen_widgets.add(widget_id)

        base_margins = _get_or_store(
            widget,
            "widget_margins",
            QMargins(widget.contentsMargins()),
        )
        widget.setContentsMargins(_scale_margins(base_margins, scale_factor))

        base_min_size = _get_or_store(
            widget,
            "minimum_size",
            QSize(widget.minimumSize()),
        )
        widget.setMinimumSize(_scale_size(base_min_size, scale_factor, minimum=0))

        base_max_size = _get_or_store(
            widget,
            "maximum_size",
            QSize(widget.maximumSize()),
        )
        if (
            base_max_size.width() < _WIDGET_SIZE_MAX
            or base_max_size.height() < _WIDGET_SIZE_MAX
        ):
            widget.setMaximumSize(_scale_maximum_size(base_max_size, scale_factor))

        if isinstance(widget, QAbstractButton):
            base_icon_size = _get_or_store(
                widget,
                "icon_size",
                QSize(widget.iconSize()),
            )
            if not base_icon_size.isEmpty():
                widget.setIconSize(_scale_size(base_icon_size, scale_factor, minimum=1))

        apply_scaled_layout_metrics(widget.layout(), scale_factor)

    apply_widget(root)
    for widget in root.findChildren(QWidget):
        apply_widget(widget)
