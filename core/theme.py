from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QGuiApplication, QPalette
from PySide6.QtWidgets import QApplication
from qfluentwidgets import Theme, setTheme


THEME_KEYS = ("auto", "light", "dark")


def _set_colors(
    palette: QPalette,
    group: QPalette.ColorGroup,
    colors: dict[QPalette.ColorRole, str],
) -> None:
    for role, color in colors.items():
        palette.setColor(group, role, QColor(color))


def create_application_palette(dark: bool) -> QPalette:
    palette = QPalette()
    if dark:
        active = {
            QPalette.ColorRole.Window: "#202020",
            QPalette.ColorRole.WindowText: "#f5f5f5",
            QPalette.ColorRole.Base: "#1e1e1e",
            QPalette.ColorRole.AlternateBase: "#2b2b2b",
            QPalette.ColorRole.ToolTipBase: "#2b2b2b",
            QPalette.ColorRole.ToolTipText: "#f5f5f5",
            QPalette.ColorRole.Text: "#f5f5f5",
            QPalette.ColorRole.Button: "#2d2d2d",
            QPalette.ColorRole.ButtonText: "#f5f5f5",
            QPalette.ColorRole.BrightText: "#ffffff",
            QPalette.ColorRole.Link: "#60cdff",
            QPalette.ColorRole.Highlight: "#4cc2ff",
            QPalette.ColorRole.HighlightedText: "#111111",
            QPalette.ColorRole.PlaceholderText: "#a0a0a0",
        }
        disabled_text = "#777777"
    else:
        active = {
            QPalette.ColorRole.Window: "#f9f9f9",
            QPalette.ColorRole.WindowText: "#1f1f1f",
            QPalette.ColorRole.Base: "#ffffff",
            QPalette.ColorRole.AlternateBase: "#f3f3f3",
            QPalette.ColorRole.ToolTipBase: "#ffffff",
            QPalette.ColorRole.ToolTipText: "#1f1f1f",
            QPalette.ColorRole.Text: "#1f1f1f",
            QPalette.ColorRole.Button: "#fbfbfb",
            QPalette.ColorRole.ButtonText: "#1f1f1f",
            QPalette.ColorRole.BrightText: "#ffffff",
            QPalette.ColorRole.Link: "#0067c0",
            QPalette.ColorRole.Highlight: "#0078d4",
            QPalette.ColorRole.HighlightedText: "#ffffff",
            QPalette.ColorRole.PlaceholderText: "#6b6b6b",
        }
        disabled_text = "#9a9a9a"

    _set_colors(palette, QPalette.ColorGroup.Active, active)
    _set_colors(palette, QPalette.ColorGroup.Inactive, active)
    disabled = active | {
        QPalette.ColorRole.WindowText: disabled_text,
        QPalette.ColorRole.Text: disabled_text,
        QPalette.ColorRole.ButtonText: disabled_text,
        QPalette.ColorRole.PlaceholderText: disabled_text,
    }
    _set_colors(palette, QPalette.ColorGroup.Disabled, disabled)
    return palette


def system_uses_dark_theme() -> bool:
    return QGuiApplication.styleHints().colorScheme() == Qt.ColorScheme.Dark


def apply_application_theme(theme_key: str) -> None:
    if theme_key not in THEME_KEYS:
        theme_key = "auto"

    dark = system_uses_dark_theme() if theme_key == "auto" else theme_key == "dark"
    fluent_theme = {
        "auto": Theme.AUTO,
        "light": Theme.LIGHT,
        "dark": Theme.DARK,
    }[theme_key]
    setTheme(fluent_theme)

    app = QApplication.instance()
    if app is not None:
        app.setPalette(create_application_palette(dark))
