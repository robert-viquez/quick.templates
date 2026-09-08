# Quick Templates

Quick Templates is a Windows desktop application for creating, organizing, and quickly copying reusable text templates for repetitive workflows.

## Overview

Quick Templates keeps frequently reused text in a searchable local library. Templates can be grouped into folders, marked as favorites, previewed before use, and copied directly to the clipboard without opening or editing the underlying files.

The application is designed to reduce repetitive writing across common tasks such as email follow-ups, status updates, customer support responses, checklists, meeting notes, and other canned responses. Its compact interface, keyboard shortcuts, system-tray behavior, and global show shortcut keep the library close at hand without requiring an internet connection.

## Features

- Create, edit, and delete reusable text templates
- Organize templates with nested folders
- Mark frequently used templates as favorites
- Search across template names, content, and folders
- Preview a template before copying it
- Copy the selected template with Enter
- Track usage counts and optionally hide the usage column
- Choose a custom local template directory
- Follow the system theme or select light or dark mode
- Show the application with the global `Ctrl+Alt+V` shortcut
- Keep the application available from the system tray
- Prevent duplicate application instances
- Store templates locally as human-readable Markdown files

## Screenshots

### Template Library

![Template Library](docs/screenshots/templates.png)

Browse, search, preview, and manage the complete local template collection.

### Favorites

![Favorites](docs/screenshots/favorites.png)

Keep the most frequently used templates in a focused view.

### Create Template

![Create Template](docs/screenshots/new-template.png)

Create a template and place it in the appropriate folder.

### Edit Template

![Edit Template](docs/screenshots/edit-template.png)

Update a template's name, folder, or content in a dedicated editor.

### Folder Management

![Folder Management](docs/screenshots/folders.png)

Manage the folder hierarchy or move the template library to another local directory.

### Settings

![Settings](docs/screenshots/settings.png)

Control usage-count visibility and select the application's color mode.

## How It Works

1. Create a reusable template and enter its content.
2. Save it in the root library or organize it into a folder.
3. Find it with instant search or open the Favorites view.
4. Select the template and review its content in the preview pane.
5. Press Enter to copy the content to the clipboard; the window hides automatically after a successful copy.

Press `Ctrl+Alt+V` from anywhere to show the application again. `Esc` hides the window while keeping the application available in the system tray.

## Keyboard Shortcuts

| Shortcut | Action |
| --- | --- |
| `Ctrl+Alt+V` | Show the application globally |
| `Ctrl+N` | Create a template |
| `Ctrl+E` | Edit the selected template |
| `Ctrl+F` | Focus template search |
| `Enter` | Copy the selected template and hide the window |
| `Delete` | Delete the selected template |
| `Esc` | Hide the application window |

## Architecture and Technical Overview

Quick Templates is implemented in Python with PySide6 and PySide6-Fluent-Widgets:

- `app.py` initializes Qt, enforces a single running instance, registers the global shortcut, and manages the system tray.
- `ui/` contains the main template browser, editor, settings pages, and folder-management dialog.
- `core/` provides template discovery and search, clipboard integration, folder operations, and JSON-backed settings.
- `models/` contains the immutable template data model used by the UI and services.

Each template is stored as a UTF-8 `.md` file. Its filename becomes the template name, its parent directories define its path, and the file body is the copied content. Favorites, usage counters, theme selection, window size, and the configured template directory are stored in `%APPDATA%\Case Templates\settings.json` on Windows. File and directory operations remain local; the application does not require a network service.

## Running Locally

### Prerequisites

- Windows 10 or Windows 11
- Python 3.11 or later
- Git

Clone the repository and enter the project directory:

```powershell
git clone https://github.com/robert-viquez/quick.templates.git
cd quick.templates
```

Create and activate a virtual environment:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the dependencies and run the application:

```powershell
python -m pip install -r requirements.txt
python app.py
```

During development, templates default to the repository's `templates/` directory. Packaged builds default to `%APPDATA%\Case Templates\templates`; the location can be changed from the Folders page.

## Building a Windows Executable

PyInstaller is included in the development dependencies. From the activated virtual environment, run:

```powershell
python -m PyInstaller --onefile --windowed --name QuickTemplates --icon assets/case_templates_76.ico app.py
```

The executable is written to `dist\QuickTemplates.exe`.

The repository also includes `install.ps1`, which installs the `QuickTemplates.exe` asset from the latest GitHub release into the current user's local Programs directory and creates a Start menu shortcut.

## Project Structure

```text
quick.templates/
├── app.py                  # Application entry point and lifecycle
├── core/                   # Storage, search, clipboard, and settings services
├── models/                 # Template data model
├── ui/                     # Main window, editor, and folder-management UI
├── assets/                 # Windows application icons
├── docs/screenshots/       # Sanitized application screenshots
├── install.ps1             # Latest-release Windows installer script
├── requirements.txt        # Runtime and build dependencies
└── README.md
```

## Use Cases

- Customer support responses
- Repeated email follow-ups
- Project and operational status updates
- Development or operations runbook snippets
- Meeting-note templates
- Administrative and other repetitive text

## Roadmap

Potential future improvements include:

- Template variables and placeholders
- Template import and export
- Tags and advanced filtering
- Optional backup or synchronization workflows
- Cross-platform packaging

These items are ideas for future development and are not part of the current application.

## Contributing

Issues and pull requests are welcome. For a code contribution, create a focused branch, describe the behavior being changed, and include appropriate verification steps with the pull request.

## License

This project is released under the MIT License.

## Author

Robert Viquez Santos — Engineering Student and Software Developer

[GitHub profile](https://github.com/robert-viquez)
