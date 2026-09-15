# -*- coding: utf-8 -*-
"""Общие правила упаковки релиза."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Iterable, Sequence


# Приложение импортирует только QtCore, QtGui и QtWidgets. Этот набор
# появляется из-за QtGui platforminputcontexts/VirtualKeyboard и не нужен в
# релизе; Qt Virtual Keyboard у Qt 6 распространяется под GPLv3 для open-source.
EXCLUDED_QT_RUNTIME_FILENAMES = frozenset(
    {
        "qt6virtualkeyboard.dll",
        "qt6qml.dll",
        "qt6qmlmeta.dll",
        "qt6qmlmodels.dll",
        "qt6qmlworkerscript.dll",
        "qt6quick.dll",
        "qtvirtualkeyboardplugin.dll",
    }
)

GPL_ONLY_QT_RUNTIME_FILENAMES = frozenset(
    {
        "qt6virtualkeyboard.dll",
        "qtvirtualkeyboardplugin.dll",
    }
)

EXCLUDED_QT_RUNTIME_MARKERS = frozenset(
    {
        "pyside6/plugins/platforminputcontexts/qtvirtualkeyboardplugin.dll",
        "pyside6/plugins/virtualkeyboard/",
        "pyside6/qml/qtquick/virtualkeyboard/",
    }
)

BINARY_TOC_TYPE_CODES = frozenset({"BINARY", "EXTENSION"})


def normalize_runtime_path(path: str | Path) -> str:
    return str(path).replace("\\", "/").strip().lower()


def runtime_filename(path: str | Path) -> str:
    return normalize_runtime_path(path).rsplit("/", 1)[-1]


def path_mentions_pyside6(path: str | Path) -> bool:
    normalized = f"/{normalize_runtime_path(path)}"
    return "/pyside6/" in normalized


def is_excluded_qt_runtime_path(path: str | Path) -> bool:
    normalized = normalize_runtime_path(path)
    name = runtime_filename(normalized)

    if path_mentions_pyside6(normalized) and name in EXCLUDED_QT_RUNTIME_FILENAMES:
        return True

    return any(marker in normalized for marker in EXCLUDED_QT_RUNTIME_MARKERS)


def is_gpl_only_qt_runtime_path(path: str | Path) -> bool:
    normalized = normalize_runtime_path(path)
    name = runtime_filename(normalized)

    if path_mentions_pyside6(normalized) and name in GPL_ONLY_QT_RUNTIME_FILENAMES:
        return True

    return any(
        marker in normalized
        for marker in (
            "pyside6/plugins/platforminputcontexts/qtvirtualkeyboardplugin.dll",
            "pyside6/plugins/virtualkeyboard/",
            "pyside6/qml/qtquick/virtualkeyboard/",
        )
    )


def filter_pyinstaller_toc(
    toc: Iterable[Sequence[object]],
) -> tuple[list[Sequence[object]], list[Sequence[object]]]:
    kept: list[Sequence[object]] = []
    removed: list[Sequence[object]] = []

    for entry in toc:
        candidates = entry[:2]
        if any(is_excluded_qt_runtime_path(str(candidate)) for candidate in candidates):
            removed.append(entry)
        else:
            kept.append(entry)

    return kept, removed


def _is_path_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def trusted_binary_roots(
    project_root: Path,
    additional_roots: Iterable[Path | str] = (),
) -> tuple[Path, ...]:
    """Возвращает единственный допустимый набор источников native-библиотек."""
    candidates: list[Path | str] = [
        project_root,
        sys.prefix,
        sys.base_prefix,
        os.environ.get("SystemRoot", r"C:\\Windows"),
        *additional_roots,
    ]
    roots: list[Path] = []
    for candidate in candidates:
        if not candidate:
            continue
        resolved = Path(candidate).resolve(strict=False)
        if resolved not in roots:
            roots.append(resolved)
    return tuple(roots)


def validate_pyinstaller_binary_origins(
    toc: Iterable[Sequence[object]],
    project_root: Path,
    additional_roots: Iterable[Path | str] = (),
) -> tuple[Path, ...]:
    """Прерывает сборку, если PyInstaller нашёл DLL вне доверенных корней."""
    roots = trusted_binary_roots(project_root, additional_roots)
    foreign_sources: list[Path] = []

    for entry in toc:
        if len(entry) < 2:
            continue
        type_code = str(entry[2]).upper() if len(entry) > 2 else "BINARY"
        if type_code not in BINARY_TOC_TYPE_CODES:
            continue

        source = Path(str(entry[1]))
        if not source.is_absolute():
            source = Path(project_root) / source
        source = source.resolve(strict=False)
        if not any(_is_path_within(source, root) for root in roots):
            foreign_sources.append(source)

    if foreign_sources:
        formatted_sources = "\n".join(
            f"  - {source}" for source in sorted(set(foreign_sources), key=str)
        )
        raise RuntimeError(
            "PyInstaller обнаружил native-библиотеки из недоверенных источников:\n"
            f"{formatted_sources}"
        )

    return roots


def iter_excluded_qt_runtime_files(runtime_root: Path) -> Iterable[Path]:
    if not runtime_root.exists():
        return

    for path in runtime_root.rglob("*"):
        if path.is_file() and is_excluded_qt_runtime_path(path):
            yield path


def iter_gpl_only_qt_runtime_files(runtime_root: Path) -> Iterable[Path]:
    if not runtime_root.exists():
        return

    for path in runtime_root.rglob("*"):
        if path.is_file() and is_gpl_only_qt_runtime_path(path):
            yield path


def prune_excluded_qt_runtime(runtime_root: Path) -> list[str]:
    removed: list[str] = []

    for path in sorted(iter_excluded_qt_runtime_files(runtime_root), key=str):
        removed.append(path.relative_to(runtime_root).as_posix())
        path.unlink(missing_ok=True)

    for directory in sorted(
        (path for path in runtime_root.rglob("*") if path.is_dir()),
        key=lambda path: len(path.parts),
        reverse=True,
    ):
        try:
            directory.rmdir()
        except OSError:
            pass

    return removed
