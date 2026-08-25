from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFormLayout, QLineEdit,
    QMessageBox, QPlainTextEdit, QVBoxLayout,
)


class TemplateEditor(QDialog):
    def __init__(self, base_directory: Path, template_path: Path | None = None, parent=None) -> None:
        super().__init__(parent)
        self.base_directory = base_directory.resolve()
        self.original_path = template_path
        self.saved_path: Path | None = None
        self.setWindowTitle("Edit Template" if template_path else "New Template")
        self.resize(700, 560)
        self.setMinimumSize(520, 420)

        self.name_input = QLineEdit(self)
        self.folder_input = QComboBox(self)
        self.content_input = QPlainTextEdit(self)
        self.content_input.setPlaceholderText("Template content...")
        self._load_folders(template_path.parent if template_path else self.base_directory)

        if template_path:
            self.name_input.setText(template_path.stem)
            try:
                self.content_input.setPlainText(template_path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError) as error:
                QMessageBox.critical(self, "Error", f"Could not open the template:\n{error}")

        form = QFormLayout()
        form.addRow("Name", self.name_input)
        form.addRow("Folder", self.folder_input)
        form.addRow("Content", self.content_input)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Save")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancel")
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)
        self.name_input.setFocus()

    def _load_folders(self, selected: Path) -> None:
        folders = [self.base_directory]
        if self.base_directory.exists():
            folders += sorted((p for p in self.base_directory.rglob("*") if p.is_dir()), key=lambda p: str(p).casefold())
        for folder in folders:
            label = "Root" if folder == self.base_directory else str(folder.relative_to(self.base_directory)).replace("/", " > ")
            self.folder_input.addItem(label, folder)
            if folder.resolve() == selected.resolve():
                self.folder_input.setCurrentIndex(self.folder_input.count() - 1)

    def save(self) -> None:
        name = self.name_input.text().strip()
        if not name or any(char in name for char in '<>:"/\\|?*') or name.endswith((".", " ")):
            QMessageBox.warning(self, "Invalid name", "Enter a valid name without reserved characters.")
            return
        content = self.content_input.toPlainText()
        if not content.strip():
            QMessageBox.warning(self, "Empty content", "The template must have content.")
            return
        folder: Path = self.folder_input.currentData()
        target = folder / f"{name}.md"
        if target.exists() and target != self.original_path:
            QMessageBox.warning(self, "Template already exists", "A template with that name already exists in this folder.")
            return
        try:
            folder.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            if self.original_path and target != self.original_path:
                self.original_path.unlink()
        except OSError as error:
            QMessageBox.critical(self, "Error", f"Could not save the template:\n{error}")
            return
        self.saved_path = target
        self.accept()
