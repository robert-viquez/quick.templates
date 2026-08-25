from pathlib import Path

from PySide6.QtWidgets import QDialog, QHBoxLayout, QInputDialog, QListWidget, QMessageBox, QPushButton, QVBoxLayout

from core.folder_manager import FolderService


class FolderManagerDialog(QDialog):
    def __init__(self, base_directory: Path, parent=None) -> None:
        super().__init__(parent)
        self.folder_service = FolderService(base_directory)
        self.setWindowTitle("Manage Folders")
        self.resize(520, 500)
        self.folder_list = QListWidget(self)
        self.create_button = QPushButton("Create", self)
        self.rename_button = QPushButton("Rename", self)
        self.delete_button = QPushButton("Delete", self)
        buttons = QHBoxLayout()
        for button in (self.create_button, self.rename_button, self.delete_button):
            buttons.addWidget(button)
        layout = QVBoxLayout(self)
        layout.addWidget(self.folder_list)
        layout.addLayout(buttons)
        self.create_button.clicked.connect(self.create_folder)
        self.rename_button.clicked.connect(self.rename_folder)
        self.delete_button.clicked.connect(self.delete_folder)
        self.load_folders()

    def load_folders(self) -> None:
        self.folder_list.clear()
        self.folder_list.addItem("Root")
        self.folder_list.item(0).setData(256, self.folder_service.base_directory)
        for folder in self.folder_service.get_folders():
            item_text = str(folder.relative_to(self.folder_service.base_directory)).replace("/", " > ")
            self.folder_list.addItem(item_text)
            self.folder_list.item(self.folder_list.count() - 1).setData(256, folder)
        self.folder_list.setCurrentRow(0)

    def selected_folder(self) -> Path:
        item = self.folder_list.currentItem()
        return item.data(256) if item else self.folder_service.base_directory

    def create_folder(self) -> None:
        name, ok = QInputDialog.getText(self, "New Folder", "Name:")
        if not ok:
            return
        try:
            self.folder_service.create_folder(name, self.selected_folder())
        except (ValueError, FileExistsError, PermissionError, OSError) as error:
            QMessageBox.warning(self, "Could not create folder", str(error))
        self.load_folders()

    def rename_folder(self) -> None:
        folder = self.selected_folder()
        name, ok = QInputDialog.getText(self, "Rename Folder", "New name:", text=folder.name)
        if not ok:
            return
        try:
            self.folder_service.rename_folder(folder, name)
        except (ValueError, FileExistsError, PermissionError, OSError) as error:
            QMessageBox.warning(self, "Could not rename folder", str(error))
        self.load_folders()

    def delete_folder(self) -> None:
        folder = self.selected_folder()
        answer = QMessageBox.question(self, "Delete Folder", f"Delete '{folder.name}' and all of its contents?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self.folder_service.delete_folder(folder, recursive=True)
        except (ValueError, FileNotFoundError, PermissionError, OSError) as error:
            QMessageBox.warning(self, "Could not delete folder", str(error))
        self.load_folders()
