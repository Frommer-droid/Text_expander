import importlib.util
import json
from pathlib import Path

from app.services.data_exchange_service import validate_settings_payload


def test_public_packaging_replaces_stale_private_data(tmp_path, monkeypatch):
    tools_dir = Path(__file__).resolve().parents[1] / "Build_Tools"
    monkeypatch.syspath_prepend(str(tools_dir))
    spec = importlib.util.spec_from_file_location("public_post_build", tools_dir / "post_build.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    source = tmp_path / "project"
    target = source / "dist"
    target.mkdir(parents=True)
    for directory in (source, target):
        (directory / "snippets.json").write_text('{"private-example": "do not publish"}')
        (directory / "expander_settings.json").write_text('{"autostart_enabled": true}')
    before = {p.name: p.read_bytes() for p in source.glob("*.json")}

    module.prepare_public_data(target)

    assert json.loads((target / "snippets.json").read_text()) == {}
    settings = validate_settings_payload(json.loads((target / "expander_settings.json").read_text()))
    assert settings["autostart_enabled"] is False
    assert settings["start_minimized"] is False
    assert {p.name: p.read_bytes() for p in source.glob("*.json")} == before
    assert not {"snippets.json", "expander_settings.json"}.intersection(module.EXTRA_ROOT_FILES)
