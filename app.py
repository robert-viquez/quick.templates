from __future__ import annotations
import os
import json
import re
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import keyboard
import pyperclip


APP_DIR = Path(__file__).resolve().parent
APP_NAME = "Case Templates"


def get_app_data_dir() -> Path:
    appdata = os.getenv("APPDATA")
    if appdata:
        return Path(appdata) / APP_NAME
    return Path.home() / ".case_templates"


APP_DATA_DIR = get_app_data_dir()
DEFAULT_TEMPLATES_DIR = (
    APP_DATA_DIR / "templates"
    if getattr(sys, "frozen", False)
    else APP_DIR / "templates"
)

GLOBAL_HOTKEY = "ctrl+alt+v"

WINDOW_DEFAULT_SIZES = {
    "main": (720, 520),
    "editor": (900, 720),
    "folder_manager": (500, 550),
    "name_dialog": (420, 180),
}


class CaseTemplatesApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root

        # ----------------------------------------------------------
        # Runtime state
        # ----------------------------------------------------------

        self.settings_path = self.get_settings_path()
        self.settings = self.load_settings()
        self.filtered_templates: list[Path] = []
        
        # Guarda los trabajos pendientes del debounce de resize.
        self.resize_save_jobs: dict[str, str] = {}

        # ----------------------------------------------------------
        # Tkinter variables
        # ----------------------------------------------------------

        self.search_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready")
        self.path_var = tk.StringVar()

        self.colors: dict[str, str] = {}

        # ----------------------------------------------------------
        # Settings
        # ----------------------------------------------------------

        # La ruta se obtiene directamente de settings.json.
        stored_templates_directory = self.settings.get(
            "templates_directory",
            "",
        )

        if stored_templates_directory:
            self.templates_dir = Path(
                stored_templates_directory
            )
        else:
            self.templates_dir = DEFAULT_TEMPLATES_DIR

            self.settings["templates_directory"] = str(
                self.templates_dir
            )

            self.save_settings()

        # ----------------------------------------------------------
        # App configuration
        # ----------------------------------------------------------

        self.configure_window()
        self.configure_dark_theme()
        self.ensure_templates_directory()

        # Actualiza el texto mostrado en la interfaz.
        self.path_var.set(str(self.templates_dir))

        # ----------------------------------------------------------
        # UI
        # ----------------------------------------------------------

        self.build_ui()
        self.bind_shortcuts()

        self.refresh_templates()

        # Deja Search listo para escribir al iniciar.
        self.root.after(
            100,
            self.focus_search,
        )

        # ----------------------------------------------------------
        # Global hotkey
        # ----------------------------------------------------------

        keyboard.add_hotkey(
            GLOBAL_HOTKEY,
            lambda: self.root.after(
                0,
                self.show_window,
            ),
        )

        # Ocultar en vez de destruir al cerrar.
        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.hide_window,
        )

    # --------------------------------------------------------------
    # Window and theme
    # --------------------------------------------------------------

    def configure_window(self) -> None:
        self.root.title("Case Templates")
        self.root.configure(bg="#202020")

        width, height = self.get_window_size(
            window_name="main",
            default_width=720,
            default_height=520,
        )

        self.root.geometry(
            f"{width}x{height}"
        )

        self.root.minsize(
            600,
            420,
        )

        self.bind_window_size_persistence(
            self.root,
            "main",
        )

    def configure_dark_theme(self) -> None:
        style = ttk.Style(self.root)

        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        background = "#202020"
        panel = "#252526"
        panel_alt = "#2d2d30"
        input_bg = "#313131"
        foreground = "#f1f1f1"
        muted = "#aaaaaa"
        accent = "#4f9fee"
        selected = "#094771"
        border = "#3f3f46"

        self.colors = {
            "background": background,
            "panel": panel,
            "panel_alt": panel_alt,
            "input_bg": input_bg,
            "foreground": foreground,
            "muted": muted,
            "accent": accent,
            "selected": selected,
            "border": border,
        }
        
        style.configure(
            "TCombobox",
            foreground="#ffffff",
        )

        style.configure(
            ".",
            background=background,
            foreground=foreground,
            font=("Segoe UI", 10),
        )

        style.configure(
            "TFrame",
            background=background,
        )

        style.configure(
            "Panel.TFrame",
            background=panel,
        )

        style.configure(
            "TLabel",
            background=background,
            foreground=foreground,
        )

        style.configure(
            "Panel.TLabel",
            background=panel,
            foreground=foreground,
        )

        style.configure(
            "Muted.TLabel",
            background=background,
            foreground=muted,
        )

        style.configure(
            "Title.TLabel",
            background=background,
            foreground=foreground,
            font=("Segoe UI Semibold", 13),
        )

        style.configure(
            "TButton",
            background=panel_alt,
            foreground=foreground,
            bordercolor=border,
            padding=(10, 6),
            relief="flat",
        )

        style.map(
            "TButton",
            background=[
                ("active", "#3a3a3d"),
                ("pressed", "#454548"),
            ],
        )

        style.configure(
            "Accent.TButton",
            background=accent,
            foreground="#ffffff",
            bordercolor=accent,
        )

        style.map(
            "Accent.TButton",
            background=[
                ("active", "#63aaf0"),
                ("pressed", "#3788d8"),
            ],
        )

        style.configure(
            "TEntry",
            fieldbackground=input_bg,
            foreground=foreground,
            insertcolor=foreground,
            bordercolor=border,
            padding=7,
        )

        style.configure(
            "Treeview",
            background=panel,
            fieldbackground=panel,
            foreground=foreground,
            bordercolor=border,
            rowheight=32,
            relief="flat",
        )

        style.map(
            "Treeview",
            background=[("selected", selected)],
            foreground=[("selected", "#ffffff")],
        )

        style.configure(
            "Treeview.Heading",
            background=panel_alt,
            foreground=foreground,
            relief="flat",
            padding=7,
        )

        style.configure(
            "Vertical.TScrollbar",
            background=panel_alt,
            troughcolor=panel,
            arrowcolor=foreground,
            bordercolor=panel,
        )

    # --------------------------------------------------------------
    # Settings
    # --------------------------------------------------------------

    def focus_search(self) -> None:
        self.search_entry.focus_set()
        self.search_entry.select_range(0, tk.END)

    @staticmethod
    def get_settings_path() -> Path:
        APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
        return APP_DATA_DIR / "settings.json"

    @staticmethod
    def get_default_settings() -> dict:
        return {
            "templates_directory": str(DEFAULT_TEMPLATES_DIR),
            "favorites": [],
            "usage": {},
            "window": {
                name: {"width": size[0], "height": size[1]}
                for name, size in WINDOW_DEFAULT_SIZES.items()
            },
        }

    def load_settings(self) -> dict:
        defaults = self.get_default_settings()

        if not self.settings_path.exists():
            self.save_settings(defaults)
            return defaults

        try:
            with self.settings_path.open("r", encoding="utf-8") as file:
                loaded = json.load(file)
        except (OSError, json.JSONDecodeError, TypeError):
            self.save_settings(defaults)
            return defaults

        if not isinstance(loaded, dict):
            loaded = {}

        settings = defaults.copy()
        settings.update(loaded)

        loaded_windows = loaded.get("window", {})
        if not isinstance(loaded_windows, dict):
            loaded_windows = {}

        # Migra versiones anteriores del archivo de configuración.
        legacy_window_keys = {
            "main_window": "main",
            "editor_window": "editor",
        }
        for legacy_key, current_key in legacy_window_keys.items():
            legacy_size = loaded.get(legacy_key)
            if (
                current_key not in loaded_windows
                and isinstance(legacy_size, dict)
            ):
                loaded_windows[current_key] = legacy_size

        settings["window"] = defaults["window"].copy()
        for name, default_size in defaults["window"].items():
            candidate = loaded_windows.get(name, {})
            if isinstance(candidate, dict):
                settings["window"][name] = {
                    "width": candidate.get("width", default_size["width"]),
                    "height": candidate.get("height", default_size["height"]),
                }

        if not isinstance(settings.get("favorites"), list):
            settings["favorites"] = []
        if not isinstance(settings.get("usage"), dict):
            settings["usage"] = {}

        self.save_settings(settings)
        return settings

    def save_settings(self, settings: dict | None = None) -> None:
        data = self.settings if settings is None else settings

        try:
            self.settings_path.parent.mkdir(parents=True, exist_ok=True)
            temporary_path = self.settings_path.with_suffix(".tmp")
            with temporary_path.open("w", encoding="utf-8") as file:
                json.dump(data, file, indent=4, ensure_ascii=False)
            temporary_path.replace(self.settings_path)
        except OSError as error:
            print(f"Could not save settings: {error}")

    def get_template_key(self, path: Path) -> str:
        return path.relative_to(
            self.templates_dir
        ).as_posix()

    def ensure_templates_directory(self) -> None:
        try:
            self.templates_dir.mkdir(
                parents=True,
                exist_ok=True,
            )
        except OSError as error:
            messagebox.showerror(
                "Folder error",
                f"Could not create the templates folder:\n{error}",
                parent=self.root,
            )

            self.templates_dir = DEFAULT_TEMPLATES_DIR
            self.templates_dir.mkdir(
                parents=True,
                exist_ok=True,
            )

        self.path_var.set(str(self.templates_dir))

    def choose_templates_directory(self) -> None:
        selected = filedialog.askdirectory(
            title="Select templates folder",
            initialdir=str(self.templates_dir),
            parent=self.root,
        )

        if not selected:
            return

        selected_path = Path(selected)

        # Se crea una subcarpeta específica para la aplicación.
        new_templates_dir = selected_path / "Case Templates"

        try:
            new_templates_dir.mkdir(
                parents=True,
                exist_ok=True,
            )
        except OSError as error:
            messagebox.showerror(
                "Folder error",
                f"Could not create the templates folder:\n{error}",
                parent=self.root,
            )
            return

        self.templates_dir = new_templates_dir
        self.path_var.set(str(self.templates_dir))
        self.settings["templates_directory"] = str(self.templates_dir)

        self.save_settings()
        self.search_var.set("")
        self.refresh_templates()

        self.set_status(
            f"Templates folder: {self.templates_dir}"
        )

    def get_window_size(
        self,
        window_name: str,
        default_width: int | None = None,
        default_height: int | None = None,
    ) -> tuple[int, int]:
        
        if default_width is None or default_height is None:
            default_width, default_height = WINDOW_DEFAULT_SIZES.get(
                window_name,
                WINDOW_DEFAULT_SIZES["main"],
            )

        windows = self.settings.setdefault("window", {})
        size = windows.setdefault(
            window_name,
            {
                "width": default_width,
                "height": default_height,
            },
        )

        try:
            width = max(1, int(size.get("width", default_width)))
            height = max(1, int(size.get("height", default_height)))
        except (TypeError, ValueError, AttributeError):
            width, height = default_width, default_height

        size["width"] = width
        size["height"] = height
        return width, height

    def save_window_size(
        self,
        window_name: str,
        window: tk.Misc,
    ) -> None:
        try:
            if window.state() != "normal":
                return
            width = window.winfo_width()
            height = window.winfo_height()
        except tk.TclError:
            return

        if width <= 1 or height <= 1:
            return

        windows = self.settings.setdefault("window", {})
        previous = windows.get(window_name, {})
        if (
            previous.get("width") == width
            and previous.get("height") == height
        ):
            return

        windows[window_name] = {
            "width": width,
            "height": height,
        }
        self.save_settings()

    def apply_saved_window_size(
        self,
        window: tk.Misc,
        window_name: str,
    ) -> tuple[int, int]:
        width, height = self.get_window_size(window_name)
        window.geometry(f"{width}x{height}")
        return width, height

    def bind_window_size_persistence(
        self,
        window: tk.Misc,
        window_name: str,
    ) -> None:
        def save_size() -> None:
            self.resize_save_jobs.pop(window_name, None)
            self.save_window_size(window_name, window)

        def on_configure(event) -> None:
            if event.widget is not window:
                return

            try:
                if window.state() != "normal":
                    return
            except tk.TclError:
                return

            if event.width <= 1 or event.height <= 1:
                return

            previous_job = self.resize_save_jobs.get(window_name)
            if previous_job:
                try:
                    window.after_cancel(previous_job)
                except tk.TclError:
                    pass

            try:
                self.resize_save_jobs[window_name] = window.after(
                    400,
                    save_size,
                )
            except tk.TclError:
                pass

        window.bind("<Configure>", on_configure, add="+")

    # --------------------------------------------------------------
    # Main UI
    # --------------------------------------------------------------

    def build_ui(self) -> None:
        main = ttk.Frame(self.root, padding=14)
        main.pack(fill="both", expand=True)

        self.build_header(main)
        self.build_search(main)
        self.build_template_list(main)
        self.build_footer(main)

    def build_header(self, parent: ttk.Frame) -> None:
        header = ttk.Frame(parent)
        header.pack(fill="x")

        ttk.Label(
            header,
            text="Case Templates",
            style="Title.TLabel",
        ).pack(side="left")

        ttk.Button(
            header,
            text="Select folder",
            command=self.choose_templates_directory,
        ).pack(side="right")

        ttk.Button(
            header,
            text="New",
            style="Accent.TButton",
            command=self.open_new_template_window,
        ).pack(side="right", padx=(0, 7))

        ttk.Button(
            header,
            text="Manage folders",
            command=self.open_folder_manager,
        ).pack(side="right", padx=(0, 7))

        path_frame = ttk.Frame(parent)
        path_frame.pack(fill="x", pady=(8, 12))

        ttk.Label(
            path_frame,
            text="Folder:",
            style="Muted.TLabel",
        ).pack(side="left")

        ttk.Label(
            path_frame,
            textvariable=self.path_var,
            style="Muted.TLabel",
        ).pack(
            side="left",
            padx=(6, 0),
            fill="x",
            expand=True,
        )

    def build_search(self, parent: ttk.Frame) -> None:
        ttk.Label(
            parent,
            text="Search",
        ).pack(anchor="w")

        self.search_entry = ttk.Entry(
            parent,
            textvariable=self.search_var,
        )
        self.search_entry.pack(
            fill="x",
            pady=(6, 12),
        )

        self.search_var.trace_add(
            "write",
            self.on_search_changed,
        )

        self.search_entry.bind(
            "<Tab>",
            self.focus_first_template,
        )

        self.search_entry.bind(
            "<Down>",
            self.focus_first_template,
        )

        self.search_entry.bind(
            "<Return>",
            self.copy_first_template,
        )

    def build_template_list(self, parent: ttk.Frame) -> None:
        list_header = ttk.Frame(parent)
        list_header.pack(fill="x", pady=(0, 7))

        ttk.Label(
            list_header,
            text="Templates",
        ).pack(side="left")

        ttk.Button(
            list_header,
            text="Delete",
            command=self.delete_selected_template,
        ).pack(side="right")

        ttk.Button(
            list_header,
            text="Edit",
            command=self.open_edit_template_window,
        ).pack(side="right", padx=(0, 7))

        # Contenedor general de lista + preview
        templates_container = ttk.Panedwindow(
            parent,
            orient="vertical",
        )
        templates_container.pack(
            fill="both",
            expand=True,
        )

        # ----------------------------------------------------------
        # Template list
        # ----------------------------------------------------------

        list_frame = ttk.Frame(
            templates_container,
            style="Panel.TFrame",
        )

        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        self.template_tree = ttk.Treeview(
            list_frame,
            show="tree",
            selectmode="browse",
        )

        self.template_tree.heading(
            "#0",
            text="Template",
        )

        self.template_tree.column(
            "#0",
            width=500,
            minwidth=250,
        )

        self.template_tree.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        list_scrollbar = ttk.Scrollbar(
            list_frame,
            orient="vertical",
            command=self.template_tree.yview,
        )
        list_scrollbar.grid(
            row=0,
            column=1,
            sticky="ns",
        )

        self.template_tree.configure(
            yscrollcommand=list_scrollbar.set
        )

        # ----------------------------------------------------------
        # Preview
        # ----------------------------------------------------------

        preview_frame = ttk.Frame(
            templates_container,
            style="Panel.TFrame",
            padding=(10, 8),
        )

        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(1, weight=1)

        ttk.Label(
            preview_frame,
            text="Preview",
            style="Panel.TLabel",
            font=("Segoe UI Semibold", 10),
        ).grid(
            row=0,
            column=0,
            sticky="w",
            pady=(0, 6),
        )

        self.preview_text = tk.Text(
            preview_frame,
            wrap="word",
            height=8,
            font=("Segoe UI", 10),
            bg=self.colors["input_bg"],
            fg=self.colors["foreground"],
            insertbackground=self.colors["foreground"],
            selectbackground=self.colors["selected"],
            selectforeground="#ffffff",
            relief="flat",
            borderwidth=0,
            padx=10,
            pady=10,
            state="disabled",
            cursor="arrow",
        )

        self.preview_text.grid(
            row=1,
            column=0,
            sticky="nsew",
        )

        preview_scrollbar = ttk.Scrollbar(
            preview_frame,
            orient="vertical",
            command=self.preview_text.yview,
        )
        preview_scrollbar.grid(
            row=1,
            column=1,
            sticky="ns",
        )

        self.preview_text.configure(
            yscrollcommand=preview_scrollbar.set
        )

        templates_container.add(
            list_frame,
            weight=3,
        )

        templates_container.add(
            preview_frame,
            weight=2,
        )

        # ----------------------------------------------------------
        # Events
        # ----------------------------------------------------------

        self.template_tree.bind(
            "<<TreeviewSelect>>",
            self.on_template_selected,
        )

        self.template_tree.bind(
            "<Return>",
            lambda event: self.copy_selected_template(),
        )

        self.template_tree.bind(
            "<Double-Button-1>",
            lambda event: self.open_edit_template_window(),
        )

        self.template_tree.bind(
            "<Delete>",
            lambda event: self.delete_selected_template(),
        )

    def on_template_selected(self, event=None) -> None:
        template_path = self.get_selected_template()

        if template_path is None:
            self.clear_template_preview()
            return

        try:
            content = template_path.read_text(
                encoding="utf-8",
                errors="replace",
            )
        except OSError as error:
            content = f"Could not load template preview:\n{error}"

        self.set_template_preview(content)

    def set_template_preview(self, content: str) -> None:
        self.preview_text.configure(
            state="normal"
        )

        self.preview_text.delete(
            "1.0",
            tk.END,
        )

        self.preview_text.insert(
            "1.0",
            content,
        )

        self.preview_text.configure(
            state="disabled"
        )

        self.preview_text.yview_moveto(0)

    def clear_template_preview(self) -> None:
        self.preview_text.configure(
            state="normal"
        )

        self.preview_text.delete(
            "1.0",
            tk.END,
        )

        self.preview_text.configure(
            state="disabled"
        )

    def build_footer(self, parent: ttk.Frame) -> None:
        footer = ttk.Frame(parent)
        footer.pack(fill="x", pady=(8, 0))

        ttk.Label(
            footer,
            textvariable=self.status_var,
            style="Muted.TLabel",
        ).pack(side="left")

        ttk.Label(
            footer,
            text="Enter: copy  |  Tab: results  |  Esc: hide",
            style="Muted.TLabel",
        ).pack(side="right")

    def get_template_folders(self) -> list[Path]:
        """
        Returns the main templates directory and all its subfolders.
        """
        if not self.templates_dir.exists():
            return [self.templates_dir]

        folders = [
            path
            for path in self.templates_dir.rglob("*")
            if path.is_dir()
        ]

        return [
            self.templates_dir,
            *sorted(
                folders,
                key=lambda path: str(
                    path.relative_to(self.templates_dir)
                ).lower(),
            ),
        ]

    def get_folder_display_name(self, folder: Path) -> str:
        """
        Returns a user-friendly relative folder name.
        """
        if folder.resolve() == self.templates_dir.resolve():
            return "Root"

        return str(
            folder.relative_to(self.templates_dir)
        ).replace("\\", " > ")

    def open_folder_manager(
        self,
        on_close=None,
    ) -> None:
        manager = tk.Toplevel(self.root)
        manager.title("Manage folders")
        manager.geometry("500x520")
        manager.minsize(420, 400)
        manager.transient(self.root)
        manager.grab_set()
        manager.configure(
            bg=self.colors["background"]
        )

        self.center_child_window(
            manager,
            500,
            520,
        )

        self.apply_saved_window_size(
            manager,
            "folder_manager",
        )

        manager.minsize(
            420,
            400,
        )

        manager_width, manager_height = (
            self.get_window_size(
                "folder_manager"
            )
        )

        self.center_child_window(
            manager,
            manager_width,
            manager_height,
        )

        self.bind_window_size_persistence(
            manager,
            "folder_manager",
        )

        container = ttk.Frame(
            manager,
            padding=14,
        )
        container.pack(fill="both", expand=True)

        ttk.Label(
            container,
            text="Manage folders",
            style="Title.TLabel",
        ).pack(anchor="w")

        ttk.Label(
            container,
            text=(
                "Create, rename or delete folders used "
                "to organize your templates."
            ),
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(4, 12))

        tree_frame = ttk.Frame(
            container,
            style="Panel.TFrame",
        )
        tree_frame.pack(
            fill="both",
            expand=True,
        )

        folder_tree = ttk.Treeview(
            tree_frame,
            show="tree",
            selectmode="browse",
        )
        folder_tree.pack(
            side="left",
            fill="both",
            expand=True,
        )

        scrollbar = ttk.Scrollbar(
            tree_frame,
            orient="vertical",
            command=folder_tree.yview,
        )
        scrollbar.pack(side="right", fill="y")

        folder_tree.configure(
            yscrollcommand=scrollbar.set
        )

        tree_paths: dict[str, Path] = {}

        def insert_folder_nodes(
            parent_id: str,
            parent_path: Path,
        ) -> None:
            child_folders = sorted(
                [
                    path
                    for path in parent_path.iterdir()
                    if path.is_dir()
                ],
                key=lambda path: path.name.lower(),
            )

            for folder in child_folders:
                item_id = folder_tree.insert(
                    parent_id,
                    "end",
                    text=folder.name,
                    open=True,
                )

                tree_paths[item_id] = folder

                insert_folder_nodes(
                    item_id,
                    folder,
                )

        def refresh_tree(
            selected_path: Path | None = None,
        ) -> None:
            folder_tree.delete(
                *folder_tree.get_children()
            )
            tree_paths.clear()

            root_id = folder_tree.insert(
                "",
                "end",
                text="Root",
                open=True,
            )

            tree_paths[root_id] = self.templates_dir

            insert_folder_nodes(
                root_id,
                self.templates_dir,
            )

            target_path = (
                selected_path
                if selected_path is not None
                else self.templates_dir
            )

            for item_id, path in tree_paths.items():
                try:
                    matches = (
                        path.resolve()
                        == target_path.resolve()
                    )
                except OSError:
                    matches = False

                if matches:
                    folder_tree.selection_set(item_id)
                    folder_tree.focus(item_id)
                    folder_tree.see(item_id)
                    break

        def get_selected_folder() -> Path | None:
            selection = folder_tree.selection()

            if not selection:
                return None

            return tree_paths.get(selection[0])

        def create_folder() -> None:
            parent_folder = (
                get_selected_folder()
                or self.templates_dir
            )

            dialog = self.open_name_dialog(
                parent=manager,
                title="New folder",
                label="Folder name",
            )

            if dialog is None:
                return

            folder_name = dialog.strip()

            if not folder_name:
                return

            if not self.is_valid_name(folder_name):
                messagebox.showwarning(
                    "Invalid name",
                    'The name cannot contain: \\ / : * ? " < > |',
                    parent=manager,
                )
                return

            new_folder = parent_folder / folder_name

            if new_folder.exists():
                messagebox.showwarning(
                    "Folder exists",
                    "A folder with that name already exists.",
                    parent=manager,
                )
                return

            try:
                new_folder.mkdir(
                    parents=True,
                    exist_ok=False,
                )
            except OSError as error:
                messagebox.showerror(
                    "Create error",
                    f"Could not create the folder:\n{error}",
                    parent=manager,
                )
                return

            refresh_tree(new_folder)

        def rename_folder() -> None:
            folder = get_selected_folder()

            if folder is None:
                return

            if (
                folder.resolve()
                == self.templates_dir.resolve()
            ):
                messagebox.showinfo(
                    "Root folder",
                    "The root folder cannot be renamed here.",
                    parent=manager,
                )
                return

            new_name = self.open_name_dialog(
                parent=manager,
                title="Rename folder",
                label="New folder name",
                initial_value=folder.name,
            )

            if new_name is None:
                return

            new_name = new_name.strip()

            if not new_name:
                return

            if not self.is_valid_name(new_name):
                messagebox.showwarning(
                    "Invalid name",
                    'The name cannot contain: \\ / : * ? " < > |',
                    parent=manager,
                )
                return

            new_path = folder.with_name(new_name)

            if new_path.exists():
                messagebox.showwarning(
                    "Folder exists",
                    "A folder with that name already exists.",
                    parent=manager,
                )
                return

            try:
                folder.rename(new_path)
            except OSError as error:
                messagebox.showerror(
                    "Rename error",
                    f"Could not rename the folder:\n{error}",
                    parent=manager,
                )
                return

            refresh_tree(new_path)
            self.refresh_templates()

        def delete_folder() -> None:
            folder = get_selected_folder()

            if folder is None:
                return

            if (
                folder.resolve()
                == self.templates_dir.resolve()
            ):
                messagebox.showinfo(
                    "Root folder",
                    "The root folder cannot be deleted.",
                    parent=manager,
                )
                return

            templates_inside = list(
                folder.rglob("*.md")
            )

            confirmed = messagebox.askyesno(
                "Delete folder",
                (
                    f'Delete "{folder.name}"?\n\n'
                    f"It contains {len(templates_inside)} "
                    "template(s).\n\n"
                    "All templates and subfolders inside it "
                    "will also be deleted."
                ),
                parent=manager,
            )

            if not confirmed:
                return

            try:
                import shutil

                shutil.rmtree(folder)

            except PermissionError as error:
                messagebox.showerror(
                    "Access denied",
                    (
                        "Windows did not allow this folder "
                        "to be deleted.\n\n"
                        "Close any files from this folder that "
                        "may be open in another application.\n\n"
                        f"{error}"
                    ),
                    parent=manager,
                )
                return

            except OSError as error:
                messagebox.showerror(
                    "Delete error",
                    f"Could not delete the folder:\n{error}",
                    parent=manager,
                )
                return

            refresh_tree(folder.parent)
            self.refresh_templates()

        button_frame = ttk.Frame(container)
        button_frame.pack(
            fill="x",
            pady=(12, 0),
        )

        ttk.Button(
            button_frame,
            text="New folder",
            command=create_folder,
        ).pack(side="left")

        ttk.Button(
            button_frame,
            text="Rename",
            command=rename_folder,
        ).pack(side="left", padx=(7, 0))

        ttk.Button(
            button_frame,
            text="Delete",
            command=delete_folder,
        ).pack(side="left", padx=(7, 0))

        def close_manager() -> None:
            pending_job = self.resize_save_jobs.pop(
                "folder_manager",
                None,
            )
            if pending_job:
                try:
                    manager.after_cancel(pending_job)
                except tk.TclError:
                    pass
            self.save_window_size("folder_manager", manager)
            manager.destroy()

            if on_close is not None:
                on_close()

        ttk.Button(
            button_frame,
            text="Close",
            style="Accent.TButton",
            command=close_manager,
        ).pack(side="right")

        manager.protocol(
            "WM_DELETE_WINDOW",
            close_manager,
        )

        manager.bind(
            "<Escape>",
            lambda event: close_manager(),
        )

        refresh_tree()

    def open_name_dialog(
        self,
        parent: tk.Misc,
        title: str,
        label: str,
        initial_value: str = "",
    ) -> str | None:
        dialog = tk.Toplevel(parent)
        dialog.title(title)
        dialog.resizable(False, False)
        dialog.transient(parent)
        dialog.grab_set()
        dialog.configure(
            bg=self.colors["background"]
        )

        dialog_width, dialog_height = self.get_window_size(
            "name_dialog"
        )
        self.center_relative_window(
            dialog,
            parent,
            dialog_width,
            dialog_height,
        )

        result: dict[str, str | None] = {
            "value": None
        }

        container = ttk.Frame(
            dialog,
            padding=14,
        )
        container.pack(fill="both", expand=True)

        ttk.Label(
            container,
            text=title,
            style="Title.TLabel",
        ).pack(anchor="w")

        ttk.Label(
            container,
            text=label,
        ).pack(anchor="w", pady=(12, 0))

        value_var = tk.StringVar(
            value=initial_value
        )

        entry = ttk.Entry(
            container,
            textvariable=value_var,
        )
        entry.pack(fill="x", pady=(6, 14))

        buttons = ttk.Frame(container)
        buttons.pack(fill="x")

        def cancel() -> None:
            dialog.destroy()

        def confirm() -> None:
            result["value"] = value_var.get()
            dialog.destroy()

        ttk.Button(
            buttons,
            text="Cancel",
            command=cancel,
        ).pack(side="right")

        ttk.Button(
            buttons,
            text="Save",
            style="Accent.TButton",
            command=confirm,
        ).pack(side="right", padx=(0, 7))

        dialog.bind(
            "<Escape>",
            lambda event: cancel(),
        )

        dialog.bind(
            "<Return>",
            lambda event: confirm(),
        )

        entry.focus_set()
        entry.select_range(0, tk.END)

        dialog.wait_window()

        return result["value"]

    def toggle_selected_favorite(self) -> None:
        template_path = self.get_selected_template()

        if template_path is None:
            return

        key = self.get_template_key(
            template_path
        )

        favorites = self.settings.setdefault(
            "favorites",
            [],
        )

        if key in favorites:
            favorites.remove(key)

            self.set_status(
                f"Removed from favorites: {template_path.stem}"
            )
        else:
            favorites.append(key)

            self.set_status(
                f"Added to favorites: {template_path.stem}"
            )

        self.save_settings()
        self.refresh_templates()
        self.select_template(template_path)
        
    # --------------------------------------------------------------
    # Templates
    # --------------------------------------------------------------

    def get_templates(self) -> list[Path]:
        if not self.templates_dir.exists():
            return []

        templates = list(
            self.templates_dir.rglob("*.md")
        )

        favorites = set(
            self.settings.get("favorites", [])
        )

        usage = self.settings.get("usage", {})

        if not isinstance(usage, dict):
            usage = {}

        def sort_key(path: Path):
            key = self.get_template_key(path)

            is_favorite = key in favorites
            usage_count = usage.get(key, 0)

            try:
                usage_count = int(usage_count)
            except (TypeError, ValueError):
                usage_count = 0

            return (
                not is_favorite,
                -usage_count,
                str(
                    path.parent.relative_to(
                        self.templates_dir
                    )
                ).lower(),
                path.stem.lower(),
            )

        return sorted(
            templates,
            key=sort_key,
        )

    def refresh_templates(self) -> None:
        query = self.search_var.get().strip().lower()

        templates = self.get_templates()
        results: list[Path] = []

        for path in templates:
            try:
                content = path.read_text(
                    encoding="utf-8",
                    errors="replace",
                ).lower()
            except OSError:
                content = ""

            searchable = f"{path.stem.lower()} {content}"

            if query and query not in searchable:
                continue

            results.append(path)

        self.filtered_templates = results

        self.template_tree.delete(
            *self.template_tree.get_children()
        )

        for index, path in enumerate(results):
            relative_path = path.relative_to(
                self.templates_dir
            )

            display_name = " > ".join(
                relative_path.with_suffix("").parts
            )

            favorites = set(
            self.settings.get("favorites", [])
            )

            usage = self.settings.get("usage", {})

            key = self.get_template_key(path)
            usage_count = usage.get(key, 0)

            if key in favorites:
                display_name = f"★ {display_name}"

            if usage_count:
                display_name += f"  ({usage_count})"

            self.template_tree.insert(
                "",
                "end",
                iid=str(index),
                text=display_name,
            )
            
        if results:
            self.template_tree.selection_set("0")
            self.template_tree.focus("0")
            self.template_tree.see("0")

            self.on_template_selected()
        else:
            self.clear_template_preview()

        self.set_status(
            f"{len(results)} template(s)"
        )

    def on_search_changed(self, *args) -> None:
        self.refresh_templates()

    def get_selected_template(self) -> Path | None:
        selection = self.template_tree.selection()

        if not selection:
            return None

        try:
            index = int(selection[0])
            return self.filtered_templates[index]
        except (ValueError, IndexError):
            return None

    def open_new_template_window(self) -> None:
        self.open_template_editor()

    def open_edit_template_window(self) -> None:
        template_path = self.get_selected_template()

        if template_path is None:
            messagebox.showinfo(
                "Select a template",
                "Select a template to edit.",
                parent=self.root,
            )
            return

        self.open_template_editor(template_path)

    def open_template_editor(
        self,
        template_path: Path | None = None,
        ) -> None:
        is_editing = template_path is not None

        editor_window = tk.Toplevel(self.root)
        editor_window.title(
            "Edit Template" if is_editing else "New Template"
        )

        self.apply_saved_window_size(
            editor_window,
            "editor",
        )

        editor_window.minsize(
            600,
            500,
        )

        editor_width, editor_height = (
            self.get_window_size("editor")
        )

        self.center_child_window(
            editor_window,
            editor_width,
            editor_height,
        )

        self.bind_window_size_persistence(
            editor_window,
            "editor",
        )

        editor_window.minsize(600, 500)
        editor_window.transient(self.root)
        editor_window.grab_set()
        editor_window.configure(
            bg=self.colors["background"]
        )

        # El contenedor principal usa únicamente grid.
        container = ttk.Frame(
            editor_window,
            padding=14,
        )
        container.pack(fill="both", expand=True)

        container.columnconfigure(0, weight=1)

        # Solo la fila del editor debe expandirse.
        container.rowconfigure(6, weight=1)

        # ----------------------------------------------------------
        # Header
        # ----------------------------------------------------------

        header = ttk.Frame(container)
        header.grid(
            row=0,
            column=0,
            sticky="ew",
            pady=(0, 14),
        )

        header.columnconfigure(0, weight=1)

        ttk.Label(
            header,
            text=(
                "Edit Template"
                if is_editing
                else "New Template"
            ),
            style="Title.TLabel",
        ).grid(
            row=0,
            column=0,
            sticky="w",
        )

        # ----------------------------------------------------------
        # Template name
        # ----------------------------------------------------------

        name_var = tk.StringVar()

        ttk.Label(
            container,
            text="Template Name",
        ).grid(
            row=1,
            column=0,
            sticky="w",
        )

        name_entry = ttk.Entry(
            container,
            textvariable=name_var,
        )
        name_entry.grid(
            row=2,
            column=0,
            sticky="ew",
            pady=(6, 12),
        )

        # ----------------------------------------------------------
        # Folder selector header
        # ----------------------------------------------------------

        folder_header = ttk.Frame(container)
        folder_header.grid(
            row=3,
            column=0,
            sticky="ew",
        )

        folder_header.columnconfigure(0, weight=1)

        ttk.Label(
            folder_header,
            text="Folder",
        ).grid(
            row=0,
            column=0,
            sticky="w",
        )

        folder_var = tk.StringVar()
        folder_paths: list[Path] = []

        # ----------------------------------------------------------
        # Folder selector
        # ----------------------------------------------------------

        folder_combobox = ttk.Combobox(
            container,
            textvariable=folder_var,
            state="readonly",
        )
        folder_combobox.grid(
            row=4,
            column=0,
            sticky="ew",
            pady=(6, 12),
        )

    
        def refresh_folder_combobox(
            selected_folder: Path | None = None,
            ) -> None:
            nonlocal folder_paths

            folder_paths = self.get_template_folders()

            folder_paths = [
                folder
                for folder in folder_paths
                if folder.exists() and folder.is_dir()
            ]

            if not any(
                folder.resolve() == self.templates_dir.resolve()
                for folder in folder_paths
            ):
                folder_paths.insert(
                    0,
                    self.templates_dir,
                )

            display_names = [
                self.get_folder_display_name(folder)
                for folder in folder_paths
            ]

            folder_combobox.configure(
                values=display_names
            )

            target_folder = (
                selected_folder
                if selected_folder is not None
                else self.templates_dir
            )

            selected_index = 0

            try:
                target_resolved = target_folder.resolve()

                for index, folder in enumerate(folder_paths):
                    if folder.resolve() == target_resolved:
                        selected_index = index
                        break

            except OSError:
                selected_index = 0

            if display_names:
                folder_combobox.current(selected_index)
                folder_var.set(display_names[selected_index])

        def open_folder_manager_from_editor() -> None:
            selected_folder = self.templates_dir
            selected_index = folder_combobox.current()

            if 0 <= selected_index < len(folder_paths):
                selected_folder = folder_paths[
                    selected_index
                ]

            def reload_folders() -> None:
                # Si la carpeta fue eliminada, vuelve a Root.
                target = (
                    selected_folder
                    if selected_folder.exists()
                    else self.templates_dir
                )

                refresh_folder_combobox(target)

            self.open_folder_manager(
                on_close=reload_folders
            )

        ttk.Button(
            folder_header,
            text="Manage Folders",
            command=open_folder_manager_from_editor,
        ).grid(
            row=0,
            column=1,
            sticky="e",
        )

        # ----------------------------------------------------------
        # Content label
        # ----------------------------------------------------------

        ttk.Label(
            container,
            text="Content",
        ).grid(
            row=5,
            column=0,
            sticky="w",
        )

        # ----------------------------------------------------------
        # Content editor
        # ----------------------------------------------------------

        text_frame = ttk.Frame(
            container,
            style="Panel.TFrame",
        )
        text_frame.grid(
            row=6,
            column=0,
            sticky="nsew",
            pady=(6, 12),
        )

        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)

        content_editor = tk.Text(
            text_frame,
            wrap="word",
            undo=True,
            font=("Segoe UI", 11),
            bg=self.colors["input_bg"],
            fg=self.colors["foreground"],
            insertbackground=self.colors["foreground"],
            selectbackground=self.colors["selected"],
            selectforeground="#ffffff",
            relief="flat",
            borderwidth=0,
            padx=12,
            pady=12,
        )
        content_editor.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        scrollbar = ttk.Scrollbar(
            text_frame,
            orient="vertical",
            command=content_editor.yview,
        )
        scrollbar.grid(
            row=0,
            column=1,
            sticky="ns",
        )

        content_editor.configure(
            yscrollcommand=scrollbar.set
        )

        # ----------------------------------------------------------
        # Load folders and existing template
        # ----------------------------------------------------------

        initial_folder = self.templates_dir

        if template_path is not None:
            name_var.set(template_path.stem)
            initial_folder = template_path.parent

            try:
                content = template_path.read_text(
                    encoding="utf-8",
                    errors="replace",
                )
            except OSError as error:
                messagebox.showerror(
                    "Read Error",
                    f"Could not read the template:\n{error}",
                    parent=editor_window,
                )
                editor_window.destroy()
                return

            content_editor.insert(
                "1.0",
                content,
            )

        refresh_folder_combobox(initial_folder)

            # ----------------------------------------------------------
            # Save action
            # ----------------------------------------------------------

        def save_template() -> None:
            name = name_var.get().strip()
            content = content_editor.get(
                "1.0",
                "end-1c",
            )

            selected_index = folder_combobox.current()

            if not folder_paths:
                messagebox.showwarning(
                    "Missing Folder",
                    "No template folders are available.",
                    parent=editor_window,
                )
                return

            if not (
                0 <= selected_index < len(folder_paths)
            ):
                messagebox.showwarning(
                    "Missing Folder",
                    "Select a folder.",
                    parent=editor_window,
                )
                return

            selected_folder = folder_paths[
                selected_index
            ]

            if not name:
                messagebox.showwarning(
                    "Missing Name",
                    "Enter a template name.",
                    parent=editor_window,
                )
                name_entry.focus_set()
                return

            if not self.is_valid_name(name):
                messagebox.showwarning(
                    "Invalid Name",
                    'The name cannot contain: \\ / : * ? " < > |',
                    parent=editor_window,
                )
                name_entry.focus_set()
                return

            try:
                selected_folder.mkdir(
                    parents=True,
                    exist_ok=True,
                )
            except OSError as error:
                messagebox.showerror(
                    "Folder Error",
                    f"Could not create the folder:\n{error}",
                    parent=editor_window,
                )
                return

            new_path = selected_folder / f"{name}.md"

            try:
                is_same_file = (
                    template_path is not None
                    and template_path.resolve()
                    == new_path.resolve()
                )
            except OSError:
                is_same_file = False

            if new_path.exists() and not is_same_file:
                messagebox.showwarning(
                    "Template Exists",
                    (
                        "A template with that name already "
                        "exists in the selected folder."
                    ),
                    parent=editor_window,
                )
                return

            try:
                # Primero guarda el archivo nuevo.
                new_path.write_text(
                    content,
                    encoding="utf-8",
                )

                # Si cambió el nombre o la carpeta, elimina el anterior.
                if (
                    template_path is not None
                    and not is_same_file
                    and template_path.exists()
                ):
                    template_path.unlink()

            except OSError as error:
                messagebox.showerror(
                    "Save Error",
                    f"Could not save the template:\n{error}",
                    parent=editor_window,
                )
                return

            close_editor()

            self.refresh_templates()
            self.select_template(new_path)

            try:
                relative_path = new_path.relative_to(
                    self.templates_dir
                )
            except ValueError:
                relative_path = new_path

            self.set_status(
                f"Saved: {relative_path}"
            )

        def close_editor() -> None:
            pending_job = self.resize_save_jobs.pop("editor", None)
            if pending_job:
                try:
                    editor_window.after_cancel(pending_job)
                except tk.TclError:
                    pass
            self.save_window_size("editor", editor_window)
            editor_window.destroy()

        # ----------------------------------------------------------
        # Bottom buttons
        # ----------------------------------------------------------

        button_frame = ttk.Frame(container)
        button_frame.grid(
            row=7,
            column=0,
            sticky="ew",
        )

        button_frame.columnconfigure(0, weight=1)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=close_editor,
        ).grid(
            row=0,
            column=1,
            sticky="e",
        )

        ttk.Button(
            button_frame,
            text="Save",
            style="Accent.TButton",
            command=save_template,
        ).grid(
            row=0,
            column=2,
            sticky="e",
            padx=(7, 0),
        )

        # ----------------------------------------------------------
        # Keyboard shortcuts and focus
        # ----------------------------------------------------------

        editor_window.bind(
            "<Control-s>",
            lambda event: save_template(),
        )

        editor_window.bind(
            "<Escape>",
            lambda event: close_editor(),
        )

        editor_window.protocol("WM_DELETE_WINDOW", close_editor)

        if is_editing:
            content_editor.focus_set()
        else:
            name_entry.focus_set()

    def delete_selected_template(self) -> None:
        template_path = self.get_selected_template()

        if template_path is None:
            messagebox.showinfo(
                "Select a template",
                "Select a template to delete.",
                parent=self.root,
            )
            return

        confirmed = messagebox.askyesno(
            "Delete template",
            f'Delete "{template_path.stem}"?',
            parent=self.root,
        )

        if not confirmed:
            return

        try:
            template_path.unlink()
        except OSError as error:
            messagebox.showerror(
                "Delete error",
                f"Could not delete the template:\n{error}",
                parent=self.root,
            )
            return

        self.refresh_templates()
        self.set_status(
            f"Deleted: {template_path.stem}"
        )

    def select_template(self, target: Path) -> None:
            for index, path in enumerate(
                self.filtered_templates
            ):
                if path.resolve() == target.resolve():
                    item_id = str(index)

                    self.template_tree.selection_set(item_id)
                    self.template_tree.focus(item_id)
                    self.template_tree.see(item_id)
                    return

    def center_relative_window(
            self,
            window: tk.Toplevel,
            parent: tk.Misc,
            width: int,
            height: int,
        ) -> None:
            parent.update_idletasks()

            parent_x = parent.winfo_rootx()
            parent_y = parent.winfo_rooty()
            parent_width = parent.winfo_width()
            parent_height = parent.winfo_height()

            x = parent_x + max(
                0,
                (parent_width - width) // 2,
            )

            y = parent_y + max(
                0,
                (parent_height - height) // 2,
            )

            window.geometry(
                f"{width}x{height}+{x}+{y}"
            )
            
        # Clipboard and keyboard navigation
        # --------------------------------------------------------------
        
    def copy_selected_template(self) -> None:
        template_path = self.get_selected_template()

        if template_path is None:
            return

        try:
            content = template_path.read_text(
                encoding="utf-8",
                errors="replace",
            )
        except OSError as error:
            messagebox.showerror(
                "Read error",
                f"Could not read the template:\n{error}",
                parent=self.root,
            )
            return

        pyperclip.copy(content)
        self.set_status(f"Copied: {template_path.stem}")
        
        template_key = self.get_template_key(
            template_path
        )

        usage = self.settings.setdefault(
            "usage",
            {},
        )

        usage[template_key] = (
            usage.get(template_key, 0) + 1
        )

        self.save_settings()
        self.hide_window()

    def copy_first_template(self, event=None) -> str:
        children = self.template_tree.get_children()

        if not children:
            return "break"

        first_item = children[0]

        self.template_tree.selection_set(first_item)
        self.template_tree.focus(first_item)

        self.copy_selected_template()

        return "break"

    def focus_first_template(self, event=None) -> str:
            children = self.template_tree.get_children()

            if not children:
                return "break"

            first_item = children[0]

            self.template_tree.selection_set(first_item)
            self.template_tree.focus(first_item)
            self.template_tree.see(first_item)
            self.template_tree.focus_set()

            return "break"

        # Shortcuts and window behavior
        # --------------------------------------------------------------

    def bind_shortcuts(self) -> None:
        self.root.bind(
            "<Control-n>",
            lambda event: self.open_new_template_window(),
        )

        self.root.bind(
            "<Control-e>",
            lambda event: self.open_edit_template_window(),
        )

        self.root.bind(
            "<Control-f>",
            lambda event: self.focus_search(),
        )

        self.root.bind(
            "<Escape>",
            lambda event: self.hide_window(),
        )

    def focus_search(self) -> None:
        self.search_entry.focus_set()
        self.search_entry.select_range(0, tk.END)

    def show_window(self) -> None:
        self.root.deiconify()
        self.center_window()
        self.root.lift()

        self.root.attributes("-topmost", True)

        self.root.after(
            150,
            lambda: self.root.attributes(
                "-topmost",
                False,
            ),
        )

        self.focus_search()

    def hide_window(self) -> None:
        self.root.withdraw()

    def center_window(self) -> None:
        self.root.update_idletasks()

        width = self.root.winfo_width()
        height = self.root.winfo_height()

        if width <= 1:
            width = WINDOW_DEFAULT_SIZES["main"][0]

        if height <= 1:
            height = WINDOW_DEFAULT_SIZES["main"][1]

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        x = max(0, (screen_width - width) // 2)
        y = max(0, (screen_height - height) // 2)

        self.root.geometry(
            f"{width}x{height}+{x}+{y}"
        )

    def center_child_window(
            self,
            window: tk.Toplevel,
            width: int,
            height: int,
        ) -> None:
            self.root.update_idletasks()

            root_x = self.root.winfo_rootx()
            root_y = self.root.winfo_rooty()
            root_width = self.root.winfo_width()
            root_height = self.root.winfo_height()

            x = root_x + max(
                0,
                (root_width - width) // 2,
            )
            y = root_y + max(
                0,
                (root_height - height) // 2,
            )

            window.geometry(
                f"{width}x{height}+{x}+{y}"
            )


        # Utilities
        # --------------------------------------------------------------

    def set_status(self, message: str) -> None:
        self.status_var.set(message)

    @staticmethod
    def is_valid_name(name: str) -> bool:
        if not name:
            return False

        if name.endswith(".") or name.endswith(" "):
            return False

        return re.search(r'[\\/:*?"<>|]', name) is None

def main() -> None:
    root = tk.Tk()
    app = CaseTemplatesApp(root)

    try:
        root.mainloop()
    finally:
        keyboard.unhook_all_hotkeys()

if __name__ == "__main__":
    main()