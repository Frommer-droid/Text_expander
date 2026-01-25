"""Помощник для чтения версии."""

from __future__ import annotations

import sys
from pathlib import Path

FROZEN_VERSION = "5.14.2"


def _read_version() -> str:
    # В frozen (скомпилированном) режиме используем хардкод
    if getattr(sys, "frozen", False):
        return FROZEN_VERSION

    # В режиме разработки читаем из файла VERSION в корне проекта
    version_file = Path(__file__).resolve().parent.parent / "VERSION"
    if version_file.exists():
        value = version_file.read_text(encoding="utf-8").strip()
        if value:
            return value
    return "0.0.0"


__version__ = _read_version()
