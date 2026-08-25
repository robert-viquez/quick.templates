from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QEvent, Qt, QTimer
from PySide6.QtGui import QCloseEvent, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView, QApplication, QFileDialog, QHBoxLayout, QHeaderView,
    QLabel, QMainWindow, QMessageBox, QSplitter, QTableWidgetItem, QTabWidget,
    QVBoxLayout, QWidget,
)
from qfluentwidgets import (
    BodyLabel, CheckBox, ComboBox, FluentIcon, FluentWindow, PlainTextEdit,
    PrimaryPushButton, PushButton, SearchLineEdit, TableWidget, Theme, setTheme,
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
        self._allow_close = False
        self._save_timer = QTimer(self, interval=400, singleShot=True)
        self._save_timer.timeout.connect(self.save_window_size)

        size = self.settings.data.get("window", {}).get("main", {})
        self.setWindowTitle("Quick Templates")
        if sys.platform == "win32":
            self.setMicaEffectEnabled(True)
        self.resize(int(size.get("width", 920)), int(size.get("height", 620)))
        self.setMinimumSize(700, 460)

        self.templates_page = self._build_templates_page(False)
        self.templates_page.setObjectName("templatesPage")
        self.favorites_page = self._build_templates_page(True)
        self.favorites_page.setObjectName("favoritesPage")
        self.folders_page = self._build_folders_page()
        self.folders_page.setObjectName("foldersPage")
        self.settings_page = self._build_settings_page()
        self.settings_page.setObjectName("settingsPage")
        self._install_navigation()

        QShortcut(QKeySequence("Escape"), self, activated=self.hide)
        QShortcut(QKeySequence("Ctrl+N"), self, activated=self.new_template)
        QShortcut(QKeySequence("Ctrl+E"), self, activated=self.edit_template)
        QShortcut(QKeySequence("Ctrl+F"), self, activated=self.focus_search)
        self.refresh_templates()
        self.focus_search()

    def _build_templates_page(self, favorites_only: bool) -> QWidget:
        page = QWidget(self)
        title = BodyLabel("Favorites" if favorites_only else "Templates", page)
        search = SearchLineEdit(page)
        search.setPlaceholderText("Search templates...")
        search.setClearButtonEnabled(True)
        search.installEventFilter(self)
        table = TableWidget(page)
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Name", "Path", "Uses"])
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        preview = PlainTextEdit(page)
        preview.setReadOnly(True)
        preview.setPlaceholderText("Template preview")
        status = BodyLabel(page)

        new_button = PrimaryPushButton(FluentIcon.ADD, "New", page)
        edit_button = PushButton(FluentIcon.EDIT, "Edit", page)
        delete_button = PushButton(FluentIcon.DELETE, "Delete", page)
        favorite_button = PushButton(FluentIcon.HEART, "Favorite", page)
        header = QHBoxLayout()
        header.addWidget(title)
        header.addStretch()
        for button in (new_button, edit_button, delete_button, favorite_button):
            header.addWidget(button)
        splitter = QSplitter(Qt.Orientation.Vertical, page)
        splitter.addWidget(table)
        splitter.addWidget(preview)
        splitter.setSizes([370, 170])
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 16)
        layout.addLayout(header)
        layout.addWidget(search)
        layout.addWidget(splitter, 1)
        layout.addWidget(status)

        page.search_input = search
        page.template_table = table
        page.preview = preview
        page.status_label = status
        page.templates = []
        page.favorites_only = favorites_only
        search.textChanged.connect(self.refresh_templates)
        search.returnPressed.connect(self.copy_selected_template)
        table.currentCellChanged.connect(lambda *_: self.update_preview())
        table.cellDoubleClicked.connect(lambda *_: self.edit_template())
        table.cellActivated.connect(lambda *_: self.copy_selected_template())
        new_button.clicked.connect(self.new_template)
        edit_button.clicked.connect(self.edit_template)
        delete_button.clicked.connect(self.delete_template)
        favorite_button.clicked.connect(self.toggle_favorite)
        QShortcut(QKeySequence("Delete"), table, activated=self.delete_template)
        return page

    def _build_folders_page(self) -> QWidget:
        page = QWidget(self)
        self.location_label = QLabel(str(self.templates_dir), page)
        self.location_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        manage = PrimaryPushButton(FluentIcon.FOLDER, "Manage folders", page)
        change = PushButton(FluentIcon.FOLDER_ADD, "Change template location", page)
        manage.clicked.connect(self.open_folder_manager)
        change.clicked.connect(self.choose_directory)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.addWidget(BodyLabel("Folders", page))
        layout.addWidget(BodyLabel("Organize the folders used to store your templates.", page))
        layout.addSpacing(16)
        layout.addWidget(BodyLabel("Current location", page))
        layout.addWidget(self.location_label)
        layout.addSpacing(12)
        layout.addWidget(manage, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(change, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addStretch()
        return page

    def _build_settings_page(self) -> QWidget:
        page = QWidget(self)
        self.usage_checkbox = CheckBox("Show template usage count", page)
        self.usage_checkbox.setChecked(bool(self.settings.data.get("show_usage_count", True)))
        self.theme_combo = ComboBox(page)
        self.theme_combo.addItems(["Use system setting", "Light", "Dark"])
        self.theme_combo.setCurrentIndex({"auto": 0, "light": 1, "dark": 2}.get(self.settings.data.get("theme", "auto"), 0))
        self.usage_checkbox.toggled.connect(self.set_usage_visibility)
        self.theme_combo.currentIndexChanged.connect(self.set_theme)
        row = QHBoxLayout()
        row.addWidget(BodyLabel("Color mode", page))
        row.addWidget(self.theme_combo)
        row.addStretch()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.addWidget(BodyLabel("Appearance", page))
        layout.addSpacing(16)
        layout.addWidget(self.usage_checkbox)
        layout.addLayout(row)
        layout.addStretch()
        return page

    def _install_navigation(self) -> None:
        pages = [
            (self.templates_page, FluentIcon.DOCUMENT, "Templates"),
            (self.favorites_page, FluentIcon.HEART, "Favorites"),
            (self.folders_page, FluentIcon.FOLDER, "Folders"),
            (self.settings_page, FluentIcon.SETTING, "Settings"),
        ]
        if sys.platform == "win32":
            for page, icon, label in pages:
                self.addSubInterface(page, icon, label)
        else:
            tabs = QTabWidget(self)
            for page, _icon, label in pages:
                tabs.addTab(page, label)
            tabs.currentChanged.connect(lambda _: self.refresh_templates())
            self.setCentralWidget(tabs)

    def active_page(self):
        current = self.stackedWidget.currentWidget() if sys.platform == "win32" else self.centralWidget().currentWidget()
        return current if current in (self.templates_page, self.favorites_page) else self.templates_page

    def template_key(self, template: Template) -> str:
        return template.path.relative_to(self.templates_dir).as_posix()

    def refresh_templates(self, _text: str = "") -> None:
        favorites = set(self.settings.data["favorites"])
        usage = self.settings.data["usage"]
        for page in (self.templates_page, self.favorites_page):
            templates = self.template_service.search_templates(page.search_input.text())
            if page.favorites_only:
                templates = [item for item in templates if self.template_key(item) in favorites]
            templates.sort(key=lambda item: (self.template_key(item) not in favorites, -int(usage.get(self.template_key(item), 0)), item.title.casefold()))
            page.templates = templates
            page.template_table.setRowCount(len(templates))
            page.template_table.setColumnHidden(2, not self.settings.data.get("show_usage_count", True))
            for row, template in enumerate(templates):
                key = self.template_key(template)
                name = f"★ {template.title}" if key in favorites else template.title
                relative_parent = template.path.parent.relative_to(self.templates_dir).as_posix()
                relative_path = "Root" if relative_parent == "." else relative_parent
                page.template_table.setItem(row, 0, QTableWidgetItem(name))
                page.template_table.setItem(row, 1, QTableWidgetItem(relative_path))
                page.template_table.setItem(row, 2, QTableWidgetItem(str(int(usage.get(key, 0)))))
            if templates:
                page.template_table.selectRow(0)
            else:
                page.preview.clear()
            page.status_label.setText(f"{len(templates)} template(s) · Enter to copy · Esc to hide")

    def selected_template(self) -> Template | None:
        page = self.active_page()
        row = page.template_table.currentRow()
        return page.templates[row] if 0 <= row < len(page.templates) else None

    def update_preview(self) -> None:
        page = self.active_page()
        template = self.selected_template()
        page.preview.setPlainText(template.content if template else "")

    def copy_selected_template(self) -> None:
        template = self.selected_template()
        if not template or not self.clipboard_service.copy_text(template.content):
            return
        key = self.template_key(template)
        self.settings.data["usage"][key] = int(self.settings.data["usage"].get(key, 0)) + 1
        self.settings.save()
        self.hide()

    def new_template(self) -> None:
        if TemplateEditor(self.templates_dir, parent=self).exec():
            self.refresh_templates()

    def edit_template(self) -> None:
        template = self.selected_template()
        if template and TemplateEditor(self.templates_dir, template.path, self).exec():
            self.refresh_templates()

    def delete_template(self) -> None:
        template = self.selected_template()
        if not template or QMessageBox.question(self, "Delete template", f"Delete '{template.title}'?") != QMessageBox.StandardButton.Yes:
            return
        try:
            template.path.unlink()
        except OSError as error:
            QMessageBox.critical(self, "Could not delete template", str(error))
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
        selected = QFileDialog.getExistingDirectory(self, "Select template location", str(self.templates_dir))
        if not selected:
            return
        self.templates_dir = Path(selected)
        self.template_service = TemplateService(self.templates_dir)
        self.settings.data["templates_directory"] = str(self.templates_dir)
        self.settings.save()
        self.location_label.setText(str(self.templates_dir))
        self.refresh_templates()

    def set_usage_visibility(self, visible: bool) -> None:
        self.settings.data["show_usage_count"] = visible
        self.settings.save()
        self.refresh_templates()

    def set_theme(self, index: int) -> None:
        keys = ["auto", "light", "dark"]
        themes = [Theme.AUTO, Theme.LIGHT, Theme.DARK]
        self.settings.data["theme"] = keys[index]
        self.settings.save()
        setTheme(themes[index])

    def eventFilter(self, watched, event) -> bool:
        if watched in (self.templates_page.search_input, self.favorites_page.search_input) and event.type() == QEvent.Type.KeyPress:
            if event.key() in (Qt.Key.Key_Down, Qt.Key.Key_Tab):
                page = self.templates_page if watched is self.templates_page.search_input else self.favorites_page
                if page.template_table.rowCount():
                    page.template_table.setFocus()
                    page.template_table.selectRow(max(0, page.template_table.currentRow()))
                return True
        return super().eventFilter(watched, event)

    def focus_search(self) -> None:
        page = self.active_page()
        page.search_input.setFocus()
        page.search_input.selectAll()

    def activate_from_external_request(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()
        self.focus_search()

    def resizeEvent(self, event):
        super().resizeEvent(event)

        if hasattr(self, "_save_timer"):
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
