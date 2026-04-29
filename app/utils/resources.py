"""Helpers for locating source-tree and PyInstaller-bundled resources."""

import sys
from pathlib import Path


def resource_path(relative_path):
    """Return an absolute path for a project resource in source or frozen mode."""
    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
    return base_path / relative_path


def resource_string(relative_path):
    """Return a resource path as a string suitable for Qt APIs."""
    return str(resource_path(relative_path))


def load_stylesheet(relative_path):
    """Load QSS and rewrite bundled icon URLs to absolute filesystem paths."""
    stylesheet_path = resource_path(relative_path)
    if not stylesheet_path.exists():
        return ""

    stylesheet = stylesheet_path.read_text(encoding="utf-8")
    assets_path = resource_path("app/assets").as_posix()
    return stylesheet.replace("url(app/assets/", f"url({assets_path}/")
