import sys
from pathlib import Path
from uuid import uuid4

from app.utils.resources import load_stylesheet, resource_path


def _runtime_tmp_path():
    path = Path("data/dynamic/tmp") / f"resource-test-{uuid4().hex}"
    path.mkdir(parents=True, exist_ok=True)
    return path.resolve()


def test_resource_path_uses_pyinstaller_meipass(monkeypatch):
    bundle_root = _runtime_tmp_path()
    monkeypatch.setattr(sys, "_MEIPASS", str(bundle_root), raising=False)

    assert resource_path("app/assets/styles/styles.qss") == (
        bundle_root / "app/assets/styles/styles.qss"
    )


def test_load_stylesheet_rewrites_asset_urls_for_frozen_bundle(monkeypatch):
    bundle_root = _runtime_tmp_path()
    monkeypatch.setattr(sys, "_MEIPASS", str(bundle_root), raising=False)
    stylesheet_path = bundle_root / "app/assets/styles/styles.qss"
    stylesheet_path.parent.mkdir(parents=True)
    stylesheet_path.write_text(
        "QComboBox::down-arrow { image: url(app/assets/icons/arrow-down.svg); }",
        encoding="utf-8",
    )

    stylesheet = load_stylesheet("app/assets/styles/styles.qss")

    assert "url(app/assets/icons/arrow-down.svg)" not in stylesheet
    assert (bundle_root / "app/assets/icons/arrow-down.svg").as_posix() in stylesheet
