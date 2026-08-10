import sys

from PySide6.QtWidgets import QApplication
from qfluentwidgets import Path, Theme, setTheme

from ui.command_palette import CommandPalette


def main() -> int:
    app = QApplication(sys.argv)

    app.setApplicationName("CaseTemplates")
    app.setOrganizationName("CaseTemplates")

    setTheme(Theme.DARK)

    window = CommandPalette()
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())