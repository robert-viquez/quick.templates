import sys
import tempfile
from pathlib import Path

from PySide6.QtCore import QObject, QLockFile, Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon
from qfluentwidgets import Theme, setTheme

from ui.command_palette import CommandPalette

SERVER_NAME = "CaseTemplates-single-instance-v1"
APP_ICON = Path(__file__).resolve().parent / "assets" / "case_templates_76.ico"


class ActivationBridge(QObject):
    requested = Signal()


def notify_running_instance() -> bool:
    socket = QLocalSocket()
    socket.connectToServer(SERVER_NAME)
    if not socket.waitForConnected(350):
        return False
    socket.write(b"activate")
    socket.waitForBytesWritten(350)
    socket.disconnectFromServer()
    return True


def create_single_instance_server() -> QLocalServer | None:
    server = QLocalServer()
    if server.listen(SERVER_NAME):
        return server
    QLocalServer.removeServer(SERVER_NAME)
    return server if server.listen(SERVER_NAME) else None


def install_global_hotkey(bridge: ActivationBridge):
    try:
        import keyboard
        keyboard.add_hotkey("ctrl+alt+v", bridge.requested.emit)
        return keyboard
    except (ImportError, OSError, RuntimeError):
        return None


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("CaseTemplates")
    app.setApplicationDisplayName("Case Templates")
    app.setOrganizationName("CaseTemplates")
    app.setWindowIcon(QIcon(str(APP_ICON)))
    app.setQuitOnLastWindowClosed(False)

    instance_lock = QLockFile(str(Path(tempfile.gettempdir()) / "case-templates.lock"))
    instance_lock.setStaleLockTime(0)
    if not instance_lock.tryLock(0):
        notify_running_instance()
        return 0

    server = create_single_instance_server()
    if server is None:
        instance_lock.unlock()
        return 1

    setTheme(Theme.AUTO)
    window = CommandPalette()
    bridge = ActivationBridge(app)
    bridge.requested.connect(window.activate_from_external_request)

    def accept_connections() -> None:
        while server.hasPendingConnections():
            connection = server.nextPendingConnection()
            window.activate_from_external_request()
            connection.disconnectFromServer()

    server.newConnection.connect(accept_connections)

    tray = QSystemTrayIcon(QIcon(str(APP_ICON)), app)
    tray.setToolTip("Case Templates")
    menu = QMenu()
    show_action = QAction("Mostrar", menu)
    quit_action = QAction("Salir", menu)
    show_action.triggered.connect(window.activate_from_external_request)
    quit_action.triggered.connect(window.quit)
    menu.addAction(show_action)
    menu.addSeparator()
    menu.addAction(quit_action)
    tray.setContextMenu(menu)
    tray.activated.connect(
        lambda reason: window.activate_from_external_request()
        if reason == QSystemTrayIcon.ActivationReason.Trigger
        else None
    )
    if QSystemTrayIcon.isSystemTrayAvailable():
        tray.show()

    hotkey_module = install_global_hotkey(bridge)
    window.show()
    exit_code = app.exec()
    if hotkey_module is not None:
        hotkey_module.unhook_all_hotkeys()
    server.close()
    instance_lock.unlock()
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
