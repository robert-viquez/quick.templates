from pathlib import Path
from PySide6.QtWidgets import QDialog, QInputDialog, QListWidget
from core.folder_manager import FolderService
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QInputDialog,
    QListWidget,
    QVBoxLayout,
)
from qfluentwidgets import (
    InfoBar,
    MessageBox,
    PrimaryPushButton,
    PushButton,
)

class FolderManagerDialog(QDialog):
    def __init__(self, base_directory: Path, parent=None) -> None:
        super().__init__(parent)

        self.folder_service = FolderService(base_directory)

        self.build_ui()
        self.connect_signals()
        self.load_folders()

    def build_ui(self) -> None:
        self.folder_list = QListWidget(self)

        self.create_button = PrimaryPushButton(
            "Crear carpeta",
            self,
        )

        self.delete_button = PushButton(
            "Eliminar carpeta",
            self,
        )

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.create_button)
        button_layout.addWidget(self.delete_button)

        layout = QVBoxLayout(self)
        layout.addWidget(self.folder_list)
        layout.addLayout(button_layout)

    def connect_signals(self) -> None:
        self.create_button.clicked.connect(
            self.create_folder
        )

        self.delete_button.clicked.connect(
            self.delete_selected_folder
        )

    def load_folders(self) -> None:
        self.folder_list.clear()

        base_directory = self.folder_service.base_directory

        for folder in self.folder_service.get_folders():
            relative_path = folder.relative_to(base_directory)

            self.folder_list.addItem(str(relative_path))

    def get_selected_folder(self) -> Path | None:
            item = self.folder_list.currentItem()

            if item is None:
                return None

            return (
                self.folder_service.base_directory
                / item.text()
            )

    def create_folder(self) -> None:
        name, accepted = QInputDialog.getText(
            self,
            "Nueva carpeta",
            "Nombre de la carpeta:",
        )

        if not accepted:
            return

        try:
            folder_path = self.folder_service.create_folder(name)
        except (ValueError, FileExistsError, PermissionError, OSError) as error:
            InfoBar.error(
                title="No se pudo crear la carpeta",
                content=str(error),
                parent=self,
                duration=3000,
            )
            return

        InfoBar.success(
            title="Carpeta creada",
            content=folder_path.name,
            parent=self,
            duration=2000,
        )

        self.load_folders()

    def delete_selected_folder(self) -> None:
            folder_path = self.get_selected_folder()

            if folder_path is None:
                return

            dialog = MessageBox(
                "Eliminar carpeta",
                f"¿Deseas eliminar '{folder_path.name}'?",
                self,
            )

            dialog.yesButton.setText("Eliminar")
            dialog.cancelButton.setText("Cancelar")

            if not dialog.exec():
                return

            try:
                self.folder_service.delete_folder(
                    folder_path,
                    recursive=False,
                )
            except (
                ValueError,
                FileNotFoundError,
                PermissionError,
                OSError,
            ) as error:
                InfoBar.error(
                    title="No se pudo eliminar la carpeta",
                    content=str(error),
                    parent=self,
                    duration=3000,
                )
                return

            InfoBar.success(
                title="Carpeta eliminada",
                content=folder_path.name,
                parent=self,
                duration=2000,
            )

            self.load_folders()