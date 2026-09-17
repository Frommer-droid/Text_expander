from __future__ import annotations

import pytest

from Build_Tools.release_packaging import (
    filter_pyinstaller_toc,
    is_excluded_qt_runtime_path,
    is_gpl_only_qt_runtime_path,
    prune_excluded_qt_runtime,
    validate_pyinstaller_binary_origins,
)


def test_excludes_qt_virtual_keyboard_runtime_paths():
    assert is_excluded_qt_runtime_path(
        r"PySide6\plugins\platforminputcontexts\qtvirtualkeyboardplugin.dll"
    )
    assert is_excluded_qt_runtime_path(r"PySide6\Qt6VirtualKeyboard.dll")
    assert is_excluded_qt_runtime_path(r"PySide6\Qt6Qml.dll")
    assert is_excluded_qt_runtime_path(r"PySide6\Qt6Quick.dll")


def test_gpl_only_qt_runtime_detection_is_narrow():
    assert is_gpl_only_qt_runtime_path(r"PySide6\Qt6VirtualKeyboard.dll")
    assert is_gpl_only_qt_runtime_path(
        r"PySide6\plugins\platforminputcontexts\qtvirtualkeyboardplugin.dll"
    )
    assert not is_gpl_only_qt_runtime_path(r"PySide6\Qt6Qml.dll")
    assert not is_gpl_only_qt_runtime_path(r"PySide6\Qt6Widgets.dll")


def test_filter_pyinstaller_toc_removes_unused_qt_runtime():
    toc = [
        ("PySide6/Qt6Core.dll", r"C:\pkg\PySide6\Qt6Core.dll", "BINARY"),
        (
            "PySide6/Qt6VirtualKeyboard.dll",
            r"C:\pkg\PySide6\Qt6VirtualKeyboard.dll",
            "BINARY",
        ),
    ]

    kept, removed = filter_pyinstaller_toc(toc)

    assert kept == [toc[0]]
    assert removed == [toc[1]]


def test_prune_excluded_qt_runtime_removes_empty_plugin_folder(tmp_path):
    runtime_root = tmp_path / "Text_expander"
    plugin_dir = runtime_root / "_internal" / "PySide6" / "plugins" / "platforminputcontexts"
    plugin_dir.mkdir(parents=True)
    plugin_file = plugin_dir / "qtvirtualkeyboardplugin.dll"
    plugin_file.write_bytes(b"not a real dll")
    kept_file = runtime_root / "_internal" / "PySide6" / "Qt6Core.dll"
    kept_file.write_bytes(b"not a real dll")

    removed = prune_excluded_qt_runtime(runtime_root)

    assert removed == [
        "_internal/PySide6/plugins/platforminputcontexts/qtvirtualkeyboardplugin.dll"
    ]
    assert not plugin_dir.exists()
    assert kept_file.exists()


def test_binary_origin_validation_allows_only_declared_roots(tmp_path):
    project_root = tmp_path / "project"
    venv_root = tmp_path / "venv"
    trusted_binary = venv_root / "Lib" / "site-packages" / "PySide6" / "Qt6Core.dll"
    trusted_binary.parent.mkdir(parents=True)
    trusted_binary.write_bytes(b"dll")

    roots = validate_pyinstaller_binary_origins(
        [("Qt6Core.dll", str(trusted_binary), "BINARY")],
        project_root,
        additional_roots=[venv_root],
    )

    assert venv_root.resolve() in roots


def test_binary_origin_validation_rejects_foreign_dll(tmp_path):
    project_root = tmp_path / "project"
    foreign_binary = tmp_path / "foreign" / "Qt6Core.dll"
    foreign_binary.parent.mkdir(parents=True)
    foreign_binary.write_bytes(b"dll")

    with pytest.raises(RuntimeError, match="недоверенных источников"):
        validate_pyinstaller_binary_origins(
            [("Qt6Core.dll", str(foreign_binary), "BINARY")],
            project_root,
        )
