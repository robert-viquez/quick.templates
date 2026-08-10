import json

def load_settings(self) -> dict:
    defaults = self.get_default_settings()

    if not self.settings_path.exists():
        self.save_settings(defaults)
        return defaults

    try:
        with self.settings_path.open("r", encoding="utf-8") as file:
            loaded = json.load(file)
    except (OSError, json.JSONDecodeError, TypeError):
        self.save_settings(defaults)
        return defaults

    if not isinstance(loaded, dict):
        loaded = {}

    settings = defaults.copy()
    settings.update(loaded)

    loaded_windows = loaded.get("window", {})
    if not isinstance(loaded_windows, dict):
        loaded_windows = {}

    # Migra versiones anteriores del archivo de configuración.
    legacy_window_keys = {
        "main_window": "main",
        "editor_window": "editor",
    }
    for legacy_key, current_key in legacy_window_keys.items():
        legacy_size = loaded.get(legacy_key)
        if (
            current_key not in loaded_windows
            and isinstance(legacy_size, dict)
        ):
            loaded_windows[current_key] = legacy_size

    settings["window"] = defaults["window"].copy()
    for name, default_size in defaults["window"].items():
        candidate = loaded_windows.get(name, {})
        if isinstance(candidate, dict):
            settings["window"][name] = {
                "width": candidate.get("width", default_size["width"]),
                "height": candidate.get("height", default_size["height"]),
            }

    if not isinstance(settings.get("favorites"), list):
        settings["favorites"] = []
    if not isinstance(settings.get("usage"), dict):
        settings["usage"] = {}

    self.save_settings(settings)
    return settings

def save_settings(self, settings: dict | None = None) -> None:
    data = self.settings if settings is None else settings

    try:
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.settings_path.with_suffix(".tmp")
        with temporary_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
        temporary_path.replace(self.settings_path)
    except OSError as error:
        print(f"Could not save settings: {error}")
