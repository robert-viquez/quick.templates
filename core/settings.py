from __future__ import annotations

import json
import os
import sys
from pathlib import Path


APP_NAME = "Case Templates"


def app_data_directory() -> Path:
    if appdata := os.getenv("APPDATA"):
        return Path(appdata) / APP_NAME
    return Path.home() / ".case_templates"


def default_templates_directory() -> Path:
    if getattr(sys, "frozen", False):
        return app_data_directory() / "templates"
    return Path(__file__).resolve().parents[1] / "templates"


class SettingsService:
    def __init__(self) -> None:
        self.path = app_data_directory() / "settings.json"
        self.data = self.load()

    @staticmethod
    def defaults() -> dict:
        return {
            "templates_directory": str(default_templates_directory()),
            "favorites": [],
            "usage": {},
            "show_usage_count": True,
            "theme": "auto",
            "window": {"main": {"width": 920, "height": 620}},
        }

    def load(self) -> dict:
        defaults = self.defaults()
        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            loaded = {}
        if not isinstance(loaded, dict):
            loaded = {}
        result = defaults | loaded
        result["favorites"] = loaded.get("favorites", []) if isinstance(loaded.get("favorites", []), list) else []
        result["usage"] = loaded.get("usage", {}) if isinstance(loaded.get("usage", {}), dict) else {}
        result["window"] = defaults["window"] | (loaded.get("window", {}) if isinstance(loaded.get("window"), dict) else {})
        return result

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(self.data, indent=2, ensure_ascii=False), encoding="utf-8")
        temporary.replace(self.path)
