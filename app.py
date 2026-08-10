import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication
from qfluentwidgets import Theme, setTheme

from ui.command_palette import CommandPalette


APP_ICON = Path(__file__).resolve().parent / "assets" / "case_templates_76.ico"


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("CaseTemplates")
    app.setApplicationDisplayName("Case Templates")
    app.setOrganizationName("CaseTemplates")
    app.setWindowIcon(QIcon(str(APP_ICON)))
    setTheme(Theme.AUTO)

    window = CommandPalette()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
