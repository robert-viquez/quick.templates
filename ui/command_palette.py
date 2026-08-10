from __future__ import annotations

from pathlib import Path
import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QCloseEvent, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QHBoxLayout, QListWidget, QListWidgetItem,
    QMainWindow, QMessageBox, QSplitter, QVBoxLayout, QWidget,
)
from qfluentwidgets import (
    BodyLabel, FluentIcon, FluentWindow, PlainTextEdit, PrimaryPushButton,
    PushButton, SearchLineEdit,
)

from core.clipboard import ClipboardService
from core.settings import SettingsService
from core.templates import TemplateService
from models.template import Template
from ui.editor import TemplateEditor
from ui.folder_manager import FolderManagerDialog


WindowBase = FluentWindow if sys.platform == "win32" else QMainWindow


class CommandPalette(WindowBase):
    def __init__(self) -> None:
        super().__init__()
        self.settings = SettingsService()
        self.templates_dir = Path(self.settings.data["templates_directory"]).expanduser()
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.template_service = TemplateService(self.templates_dir)
        self.clipboard_service = ClipboardService()
        self.visible_templates: list[Template] = []
        self._allow_close = False
        self._save_timer = QTimer(self, interval=400, singleShot=True)
        self._save_timer.timeout.connect(self.save_window_size)

        size = self.settings.data.get("window", {}).get("main", {})
        self.setWindowTitle("Case Templates")
        if sys.platform == "win32":
            self.setMicaEffectEnabled(True)
        self.resize(int(size.get("width", 820)), int(size.get("height", 560)))
        self.setMinimumSize(620, 420)
        self.interface = QWidget(self)
        self.interface.setObjectName("commandPaletteInterface")
        self.search_input = SearchLineEdit(self.interface)
        self.search_input.setPlaceholderText("Buscar plantillas...")
        self.search_input.setClearButtonEnabled(True)
        self.path_label = BodyLabel(str(self.templates_dir), self.interface)
        self.path_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.template_list = QListWidget(self.interface)
        self.preview = PlainTextEdit(self.interface)
        self.preview.setReadOnly(True)
        self.preview.setPlaceholderText("Vista previa")
        self.status_label = BodyLabel(self.interface)

        new_button = PrimaryPushButton(FluentIcon.ADD, "Nueva", self.interface)
        edit_button = PushButton(FluentIcon.EDIT, "Editar", self.interface)
        delete_button = PushButton(FluentIcon.DELETE, "Eliminar", self.interface)
        favorite_button = PushButton(FluentIcon.HEART, "Favorita", self.interface)
        folders_button = PushButton(FluentIcon.FOLDER, "Carpetas", self.interface)
        choose_button = PushButton(FluentIcon.FOLDER_ADD, "Ubicación", self.interface)
        header = QHBoxLayout()
        for button in (new_button, edit_button, delete_button, favorite_button, folders_button, choose_button):
            header.addWidget(button)
        splitter = QSplitter(Qt.Orientation.Vertical, self.interface)
        splitter.addWidget(self.template_list)
        splitter.addWidget(self.preview)
        splitter.setSizes([340, 160])
        layout = QVBoxLayout(self.interface)
        layout.setContentsMargins(20, 20, 20, 14)
        layout.addLayout(header)
        layout.addWidget(self.path_label)
        layout.addWidget(self.search_input)
        layout.addWidget(splitter, 1)
        layout.addWidget(self.status_label)
        if sys.platform == "win32":
            self.addSubInterface(self.interface, FluentIcon.DOCUMENT, "Plantillas")
        else:
            self.setCentralWidget(self.interface)

        self.search_input.textChanged.connect(self.refresh_templates)
        self.search_input.returnPressed.connect(self.copy_selected_template)
        self.template_list.currentRowChanged.connect(self.update_preview)
        self.template_list.itemActivated.connect(lambda _: self.copy_selected_template())
        self.template_list.itemDoubleClicked.connect(lambda _: self.edit_template())
        new_button.clicked.connect(self.new_template)
        edit_button.clicked.connect(self.edit_template)
        delete_button.clicked.connect(self.delete_template)
        favorite_button.clicked.connect(self.toggle_favorite)
        folders_button.clicked.connect(self.open_folder_manager)
        choose_button.clicked.connect(self.choose_directory)
        QShortcut(QKeySequence("Escape"), self, activated=self.hide)
        QShortcut(QKeySequence("Ctrl+N"), self, activated=self.new_template)
        QShortcut(QKeySequence("Ctrl+E"), self, activated=self.edit_template)
        QShortcut(QKeySequence("Delete"), self.template_list, activated=self.delete_template)
        QShortcut(QKeySequence("Ctrl+F"), self, activated=self.focus_search)
        self.refresh_templates()
        self.focus_search()

    def template_key(self, template: Template) -> str:
        return template.path.relative_to(self.templates_dir).as_posix()

    def refresh_templates(self, _text: str = "") -> None:
        templates = self.template_service.search_templates(self.search_input.text())
        favorites = set(self.settings.data["favorites"])
        usage = self.settings.data["usage"]
        templates.sort(key=lambda t: (self.template_key(t) not in favorites, -int(usage.get(self.template_key(t), 0)), t.title.casefold()))
        self.visible_templates = templates
        self.template_list.clear()
        for template in templates:
            key = self.template_key(template)
            folder = str(template.path.parent.relative_to(self.templates_dir))
            location = "" if folder == "." else f" — {folder}"
            count = int(usage.get(key, 0))
            suffix = f"  ({count})" if count else ""
            self.template_list.addItem(QListWidgetItem(f"{'★ ' if key in favorites else ''}{template.title}{location}{suffix}"))
        if templates:
            self.template_list.setCurrentRow(0)
        else:
            self.preview.clear()
        self.status_label.setText(f"{len(templates)} plantilla(s) · Enter copia · Esc oculta")

    def selected_template(self) -> Template | None:
        row = self.template_list.currentRow()
        return self.visible_templates[row] if 0 <= row < len(self.visible_templates) else None

    def update_preview(self, _row: int) -> None:
        template = self.selected_template()
        self.preview.setPlainText(template.content if template else "")

    def copy_selected_template(self) -> None:
        template = self.selected_template()
        if not template or not self.clipboard_service.copy_text(template.content):
            return
        key = self.template_key(template)
        self.settings.data["usage"][key] = int(self.settings.data["usage"].get(key, 0)) + 1
        self.settings.save()
        self.hide()

    def new_template(self) -> None:
        editor = TemplateEditor(self.templates_dir, parent=self)
        if editor.exec():
            self.refresh_templates()

    def edit_template(self) -> None:
        template = self.selected_template()
        if not template:
            return
        editor = TemplateEditor(self.templates_dir, template.path, self)
        if editor.exec():
            self.refresh_templates()

    def delete_template(self) -> None:
        template = self.selected_template()
        if not template or QMessageBox.question(self, "Eliminar", f"¿Eliminar '{template.title}'?") != QMessageBox.StandardButton.Yes:
            return
        try:
            template.path.unlink()
        except OSError as error:
            QMessageBox.critical(self, "Error", str(error))
        self.refresh_templates()

    def toggle_favorite(self) -> None:
        template = self.selected_template()
        if not template:
            return
        key = self.template_key(template)
        favorites = self.settings.data["favorites"]
        favorites.remove(key) if key in favorites else favorites.append(key)
        self.settings.save()
        self.refresh_templates()

    def open_folder_manager(self) -> None:
        FolderManagerDialog(self.templates_dir, self).exec()
        self.refresh_templates()

    def choose_directory(self) -> None:
        selected = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta de plantillas", str(self.templates_dir))
        if not selected:
            return
        self.templates_dir = Path(selected)
        self.template_service = TemplateService(self.templates_dir)
        self.settings.data["templates_directory"] = str(self.templates_dir)
        self.settings.save()
        self.path_label.setText(str(self.templates_dir))
        self.refresh_templates()

    def focus_search(self) -> None:
        self.search_input.setFocus()
        self.search_input.selectAll()

    def activate_from_external_request(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()
        self.focus_search()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._save_timer.start()

    def save_window_size(self) -> None:
        if not self.isMaximized():
            self.settings.data["window"]["main"] = {"width": self.width(), "height": self.height()}
            self.settings.save()

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._allow_close:
            event.accept()
        else:
            event.ignore()
            self.hide()

    def quit(self) -> None:
        self._allow_close = True
        QApplication.quit()
