"""Непосредственно проверяет PyInstaller TOC, MSVC runtime и frozen smoke."""

from __future__ import annotations

import argparse
import hashlib
import subprocess
from pathlib import Path

from PyInstaller.utils.misc import load_py_data_struct

from release_packaging import validate_pyinstaller_binary_origins


FORBIDDEN_OUTPUT_MARKERS = (
    "Traceback",
    "ImportError",
    "DLL load failed",
    "[PYI-",
)
MSVC_RUNTIME_PREFIXES = ("concrt140", "msvcp140", "vcruntime140")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_collect_toc(toc_path: Path, project_root: Path) -> None:
    if not toc_path.is_file():
        raise RuntimeError(f"Не найден COLLECT-00.toc: {toc_path}")
    toc = load_py_data_struct(str(toc_path))
    validate_pyinstaller_binary_origins(toc, project_root)
    print(f"[OK] COLLECT-00.toc: native origins проверены ({toc_path})")


def verify_msvc_runtime(app_dir: Path) -> None:
    runtime_root = app_dir / "_internal"
    pyside_root = Path(__import__("PySide6").__file__).resolve().parent
    expected = {
        path.name.lower(): path
        for path in pyside_root.glob("*.dll")
        if path.name.lower().startswith(MSVC_RUNTIME_PREFIXES)
    }
    actual = {
        path.name.lower(): path
        for path in runtime_root.glob("*.dll")
        if path.name.lower().startswith(MSVC_RUNTIME_PREFIXES)
    }

    missing = sorted(set(expected) - set(actual))
    mismatched = sorted(
        name for name in expected.keys() & actual.keys() if _sha256(expected[name]) != _sha256(actual[name])
    )
    if missing or mismatched:
        details = [
            *(f"не найден {name}" for name in missing),
            *(f"не совпадает с PySide6 {name}" for name in mismatched),
        ]
        raise RuntimeError("Неконсистентный MSVC runtime:\n  - " + "\n  - ".join(details))
    print(f"[OK] MSVC runtime согласован с PySide6 ({len(expected)} DLL)")


def verify_frozen_smoke(executable: Path) -> None:
    if not executable.is_file():
        raise RuntimeError(f"Не найден frozen executable: {executable}")
    completed = subprocess.run(
        [str(executable), "--frozen-smoke"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    output = f"{completed.stdout}\n{completed.stderr}"
    if completed.returncode != 0 or any(marker in output for marker in FORBIDDEN_OUTPUT_MARKERS):
        raise RuntimeError(
            "Frozen smoke завершился с ошибкой "
            f"(exit={completed.returncode}):\n{output.strip()}"
        )
    print("[OK] Frozen import/runtime smoke завершён без ошибок")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path)
    parser.add_argument("--toc", type=Path)
    parser.add_argument("--app-dir", type=Path)
    args = parser.parse_args()

    if bool(args.project_root) != bool(args.toc):
        parser.error("--project-root и --toc указываются вместе")
    if not args.toc and not args.app_dir:
        parser.error("укажите --toc или --app-dir")

    if args.toc:
        verify_collect_toc(args.toc, args.project_root)
    if args.app_dir:
        verify_msvc_runtime(args.app_dir)
        verify_frozen_smoke(args.app_dir / "Text_expander.exe")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
