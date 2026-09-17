"""Единый набор контурных иконок для действий интерфейса."""

from __future__ import annotations

from functools import lru_cache

from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QIcon, QImage, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer


_ICON_BODIES = {
    "archive": '<path d="M4 5h16v16H4z"/><path d="M3 5h18V2H3zM9 11h6"/>',
    "capture": '<rect x="3" y="4" width="18" height="14" rx="1"/><path d="M9 21h6M12 18v3"/>',
    "document": '<path d="M6 2h8l4 4v16H6zM14 2v5h4M9 12h6M9 16h6"/>',
    "download": '<path d="M12 3v12M8 11l4 4 4-4M4 19h16v2H4z"/>',
    "edit": '<path d="m5 16-1 5 5-1L20 9l-4-4zM16 5l4 4"/>',
    "folder": '<path d="M3 6h7l2 3h9v10H3z"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7h.01"/>',
    "list": '<path d="M7 6h12M7 12h12M7 18h12"/><circle cx="4" cy="6" r=".7" fill="#FFFFFF" stroke="none"/><circle cx="4" cy="12" r=".7" fill="#FFFFFF" stroke="none"/><circle cx="4" cy="18" r=".7" fill="#FFFFFF" stroke="none"/>',
    "save": '<path d="M5 3h13l2 2v16H4V3zM8 3v6h8V3M8 21v-7h8v7"/>',
    "system": '<path d="M4 5h16v11H4zM8 21h8M12 16v5"/><path d="M8 9h8M8 12h5"/>',
    "trash": '<path d="M5 7h14M10 3h4M8 7l1 14h6l1-14M11 11v6M14 11v6"/>',
    "upload": '<path d="M12 15V3M8 7l4-4 4 4M4 19h16v2H4z"/>',
}


def _svg_document(body: str) -> QByteArray:
    source = f"""
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
      <g transform="translate(0 1.5)" fill="none" stroke="#FFFFFF" stroke-width="2"
         stroke-linecap="round" stroke-linejoin="round">{body}</g>
    </svg>
    """
    return QByteArray(source.encode("utf-8"))


@lru_cache(maxsize=None)
def action_icon(name: str) -> QIcon:
    """Возвращает резкую центрированную иконку во всех масштабах интерфейса."""
    body = _ICON_BODIES[name]
    renderer = QSvgRenderer(_svg_document(body))
    if not renderer.isValid():
        raise RuntimeError(f"Не удалось создать SVG-иконку '{name}'.")

    icon = QIcon()
    for size in (16, 18, 20, 24, 32, 48, 64):
        image = QImage(
            size,
            size,
            QImage.Format.Format_ARGB32_Premultiplied,
        )
        image.fill(Qt.GlobalColor.transparent)
        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        renderer.render(painter)
        painter.end()
        icon.addPixmap(QPixmap.fromImage(image))
    return icon
