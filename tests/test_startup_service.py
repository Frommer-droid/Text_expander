from __future__ import annotations

import os
from pathlib import Path
import subprocess

from app.services import startup_service


def test_get_launch_executable_prefers_pythonw_for_pyw(monkeypatch, tmp_path):
    scripts_dir = tmp_path / "Scripts"
    scripts_dir.mkdir()
    python_exe = scripts_dir / "python.exe"
    pythonw_exe = scripts_dir / "pythonw.exe"
    script_path = tmp_path / "Text_expander.pyw"
    python_exe.write_text("", encoding="utf-8")
    pythonw_exe.write_text("", encoding="utf-8")
    script_path.write_text("", encoding="utf-8")

    monkeypatch.setattr(startup_service.sys, "executable", str(python_exe))
    monkeypatch.setattr(startup_service.sys, "argv", [str(script_path)])

    assert (
        startup_service.get_launch_executable(prefer_windowed=True)
        == str(pythonw_exe)
    )


def test_get_launch_executable_keeps_python_for_py(monkeypatch, tmp_path):
    scripts_dir = tmp_path / "Scripts"
    scripts_dir.mkdir()
    python_exe = scripts_dir / "python.exe"
    pythonw_exe = scripts_dir / "pythonw.exe"
    script_path = tmp_path / "tool.py"
    python_exe.write_text("", encoding="utf-8")
    pythonw_exe.write_text("", encoding="utf-8")
    script_path.write_text("", encoding="utf-8")

    monkeypatch.setattr(startup_service.sys, "executable", str(python_exe))
    monkeypatch.setattr(startup_service.sys, "argv", [str(script_path)])

    assert (
        startup_service.get_launch_executable(prefer_windowed=True)
        == str(python_exe)
    )


def test_get_launch_executable_keeps_current_when_pythonw_missing(
    monkeypatch, tmp_path
):
    scripts_dir = tmp_path / "Scripts"
    scripts_dir.mkdir()
    python_exe = scripts_dir / "python.exe"
    script_path = tmp_path / "Text_expander.pyw"
    python_exe.write_text("", encoding="utf-8")
    script_path.write_text("", encoding="utf-8")

    monkeypatch.setattr(startup_service.sys, "executable", str(python_exe))
    monkeypatch.setattr(startup_service.sys, "argv", [str(script_path)])

    assert (
        startup_service.get_launch_executable(prefer_windowed=True)
        == str(python_exe)
    )


def test_get_startup_locations_prefers_known_folders_and_deduplicates(
    monkeypatch, tmp_path
):
    user_appdata = tmp_path / "Roaming"
    common_appdata = tmp_path / "ProgramData"
    monkeypatch.setattr(startup_service, "get_effective_appdata", lambda: str(user_appdata))
    monkeypatch.setenv("PROGRAMDATA", str(common_appdata))

    known_user = str(tmp_path / "KnownUserStartup")
    fallback_common = os.path.normpath(
        str(common_appdata / Path(startup_service.STARTUP_RELATIVE_PATH))
    )

    def fake_known_folder_path(folder_id):
        if folder_id == startup_service.FOLDERID_STARTUP:
            return known_user
        if folder_id == startup_service.FOLDERID_COMMON_STARTUP:
            return fallback_common
        return None

    monkeypatch.setattr(startup_service, "get_known_folder_path", fake_known_folder_path)

    assert startup_service.get_startup_locations() == [
        known_user,
        fallback_common,
        os.path.normpath(str(user_appdata / Path(startup_service.STARTUP_RELATIVE_PATH))),
    ]


def test_get_autostart_launch_spec_uses_pythonw_and_script_argument(
    monkeypatch, tmp_path
):
    scripts_dir = tmp_path / "Scripts"
    app_dir = tmp_path / "appdir"
    scripts_dir.mkdir()
    app_dir.mkdir()
    python_exe = scripts_dir / "python.exe"
    pythonw_exe = scripts_dir / "pythonw.exe"
    script_path = app_dir / "Text_expander.pyw"
    icon_path = app_dir / "logo.ico"
    python_exe.write_text("", encoding="utf-8")
    pythonw_exe.write_text("", encoding="utf-8")
    script_path.write_text("", encoding="utf-8")
    icon_path.write_text("", encoding="utf-8")

    monkeypatch.setattr(startup_service.sys, "executable", str(python_exe))
    monkeypatch.setattr(startup_service.sys, "argv", [str(script_path)])

    spec = startup_service.get_autostart_launch_spec(str(script_path))

    resolved_script_path = str(script_path.resolve())
    assert spec.target_path == str(pythonw_exe)
    assert spec.arguments == subprocess.list2cmdline([resolved_script_path])
    assert spec.working_directory == str(app_dir.resolve())
    assert spec.icon_location == str(icon_path.resolve())


def test_get_autostart_launch_spec_uses_exe_when_frozen(monkeypatch, tmp_path):
    executable_path = tmp_path / "Text_expander.exe"
    executable_path.write_text("", encoding="utf-8")

    monkeypatch.setattr(startup_service.sys, "executable", str(executable_path))
    monkeypatch.setattr(startup_service.sys, "frozen", True, raising=False)

    spec = startup_service.get_autostart_launch_spec(str(executable_path))

    assert spec.target_path == str(executable_path.resolve())
    assert spec.arguments == ""
    assert spec.working_directory == str(tmp_path.resolve())
    assert spec.icon_location == str(executable_path.resolve())
