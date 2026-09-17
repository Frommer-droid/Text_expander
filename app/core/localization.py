"""Загрузка русских переводов Qt."""

from __future__ import annotations

import sys
from pathlib import Path

import PySide6
from PySide6.QtCore import QLibraryInfo, QLocale, QTranslator
from PySide6.QtWidgets import QApplication

RUSSIAN_LOCALE = QLocale("ru_RU")


def _iter_translation_paths() -> list[str]:
    paths: list[str] = []

    qt_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    if qt_path:
        paths.append(qt_path)

    pyside_path = Path(PySide6.__file__).resolve().parent / "translations"
    if pyside_path.exists():
        paths.append(str(pyside_path))

    if getattr(sys, "frozen", False):
        frozen_path = (
            Path(sys.executable).resolve().parent
            / "_internal"
            / "PySide6"
            / "translations"
        )
        if frozen_path.exists():
            paths.append(str(frozen_path))

    unique_paths: list[str] = []
    for path in paths:
        if path and path not in unique_paths:
            unique_paths.append(path)
    return unique_paths


def install_qt_base_russian_translation(
    app: QApplication,
) -> QTranslator | None:
    """Подключает qtbase_ru.qm до создания окон."""

    QLocale.setDefault(RUSSIAN_LOCALE)

    for translation_path in _iter_translation_paths():
        translator = QTranslator(app)
        if translator.load(
            RUSSIAN_LOCALE,
            "qtbase",
            "_",
            translation_path,
        ) or translator.load("qtbase_ru", translation_path):
            app.installTranslator(translator)
            return translator

    return None
