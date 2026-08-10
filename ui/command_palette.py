from pathlib import Path
from ui.folder_manager import FolderManagerDialog
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QListWidgetItem, QWidget

from qfluentwidgets import BodyLabel, PushButton, StrongBodyLabel, PushButton
# from qfluentwidgets import InfoBar, InfoBarPosition
from models.template import Template

from core.templates import TemplateService
from core.clipboard import ClipboardService

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent, QShortcut, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from qfluentwidgets import (
    BodyLabel,
    FluentWindow,
    SearchLineEdit,
    StrongBodyLabel,
)


class CommandPalette(FluentWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Case Templates")
        self.resize(820, 560)
        self.setMinimumSize(620, 420)

        self.interface = QWidget(self)
        self.interface.setObjectName("commandPaletteInterface")

        self.search_input = SearchLineEdit(self.interface)
        self.search_input.setPlaceholderText("Buscar plantillas...")
        self.search_input.setClearButtonEnabled(True)

        self.template_list = QListWidget(self.interface)
        self.template_list.setAlternatingRowColors(False)
        self.template_list.setUniformItemSizes(True)

        self.status_label = BodyLabel(
            "↑↓ Navegar   Enter Copiar   Esc Cerrar",
            self.interface,
        )

        self.manage_folders_button = PushButton(
            "Manage Folders",
            self,
        )

        layout = QVBoxLayout(self.interface)
        layout.setContentsMargins(24, 24, 24, 16)
        layout.setSpacing(12)
        layout.addWidget(self.search_input)
        layout.addWidget(self.template_list, 1)
        layout.addWidget(self.status_label)
        layout.addWidget(self.manage_folders_button)

        self.addSubInterface(
            self.interface,
            icon=None,
            text="Plantillas",
        )

        self.template_service = TemplateService(
            Path.home() / "Documents" / "Templates"
        )

        self.all_templates: list[Template] = []
        self.visible_templates: list[Template] = []

        self.load_templates()
        self._connect_signals()
        self._configure_shortcuts()

        self.search_input.setFocus()
        
        self.clipboard_service = ClipboardService()


    def _connect_signals(self) -> None:
        self.search_input.textChanged.connect(self.filter_templates)
        self.search_input.returnPressed.connect(self.copy_selected_template)
        self.template_list.itemActivated.connect(
            lambda _: self.copy_selected_template()
        )
        self.manage_folders_button.clicked.connect(
            self.open_folder_manager
        ) 

    def open_folder_manager(self) -> None:
        dialog = FolderManagerDialog(
            base_directory=self.template_service.base_directory,
            parent=self,
        )

        dialog.exec()

        self.load_templates()

    def _configure_shortcuts(self) -> None:
        QShortcut(
            QKeySequence("Escape"),
            self,
            activated=self.hide,
        )

        QShortcut(
            QKeySequence("Ctrl+K"),
            self,
            activated=self.focus_search,
        )

    def load_templates(self) -> None:
        self.all_templates = self.template_service.get_templates()
        self.show_templates(self.all_templates)

    def focus_search(self) -> None:
        self.search_input.setFocus()
        self.search_input.selectAll()

    def filter_templates(self, text: str) -> None:
        results = self.template_service.search_templates(
            text,
            self.all_templates,
        )

        self.show_templates(results)

    def select_first_visible_item(self) -> None:
        for row in range(self.template_list.count()):
            item = self.template_list.item(row)

            if not item.isHidden():
                self.template_list.setCurrentRow(row)
                return

    def copy_selected_template(self) -> None:
        item = self.template_list.currentItem()

        if item is None:
            return

        content = item.data(Qt.ItemDataRole.UserRole)

        clipboard = QApplication.clipboard()
        clipboard.setText(content)

        self.hide()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Down:
            self.template_list.setFocus()

            if self.template_list.currentRow() < 0:
                self.select_first_visible_item()

            return

        super().keyPressEvent(event)

    def show_templates(self, templates: list[Template]) -> None:
        self.template_list.clear()
        self.visible_templates = templates

        for template in templates:
            item = QListWidgetItem()

            item.setData(
                Qt.ItemDataRole.UserRole,
                str(template.path),
            )

            widget = self.create_template_item(template)

            self.template_list.addItem(item)
            self.template_list.setItemWidget(item, widget)
            item.setSizeHint(widget.sizeHint())

        if self.template_list.count() > 0:
            self.template_list.setCurrentRow(0)

    def create_template_item(self, template: Template) -> QWidget:
        widget = QWidget()

        title_label = StrongBodyLabel(template.title, widget)

        preview = template.content.replace("\n", " ").strip()

        if len(preview) > 90:
            preview = preview[:87] + "..."

        preview_label = BodyLabel(preview, widget)

        from PySide6.QtWidgets import QVBoxLayout

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(2)
        layout.addWidget(title_label)
        layout.addWidget(preview_label)

        return widget

    def get_selected_template(self) -> Template | None:
        row = self.template_list.currentRow()

        if row < 0:
            return None

        if row >= len(self.visible_templates):
            return None

        return self.visible_templates[row]

    def copy_selected_template(self) -> None:
        template = self.get_selected_template()

        if template is None:
            return

        copied = self.clipboard_service.copy_text(template.content)

        if not copied:
            return

        self.hide()