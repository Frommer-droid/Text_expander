from __future__ import annotations

from pathlib import Path

from app.services import paths


def test_get_project_root_from_source():
    assert paths.get_project_root() == Path(__file__).resolve().parents[1]


def test_get_project_root_from_frozen_runtime(monkeypatch):
    fake_executable = Path(r"D:\Apps\Text_expander\Text_expander.exe")

    monkeypatch.setattr(paths.sys, "frozen", True, raising=False)
    monkeypatch.setattr(paths.sys, "executable", str(fake_executable))

    assert paths.get_project_root() == fake_executable.parent


def test_resource_path_uses_project_root():
    expected = Path(__file__).resolve().parents[1] / "logo.ico"

    assert Path(paths.resource_path("logo.ico")) == expected
