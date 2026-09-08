# Quick Templates

Quick Templates is a Windows desktop application for creating, organizing, and quickly copying reusable text templates for repetitive workflows.

## Overview

Quick Templates keeps frequently used text in a searchable local library. It is useful for email follow-ups, status updates, support responses, checklists, meeting notes, and other repeated content.

Templates can be organized into folders, marked as favorites, previewed, and copied directly to the clipboard. The application stays available from the system tray and can be opened globally with `Ctrl+Alt+V`.

## Features

- Create, edit, and delete reusable templates
- Organize templates with nested folders
- Search template names, content, and folders
- Mark frequently used templates as favorites
- Preview and copy a template with Enter
- Track and optionally hide usage counts
- Use system, light, or dark appearance
- Choose where the template library is stored
- Store templates as local, human-readable Markdown files

## Screenshots

| Screenshot | Details | Screenshot | Details |
| --- | --- | --- | --- |
| ![Template Library](docs/screenshots/templates.png) | **Template Library**<br>Search, preview, and manage all templates. | ![Favorites](docs/screenshots/favorites.png) | **Favorites**<br>Keep frequently used templates in a focused view. |
| ![Create Template](docs/screenshots/new-template.png) | **Create Template**<br>Add content and select its destination folder. | ![Edit Template](docs/screenshots/edit-template.png) | **Edit Template**<br>Update a template's name, folder, or content. |
| ![Folder Management](docs/screenshots/folders.png) | **Folder Management**<br>Manage folders and choose the library location. | ![Settings](docs/screenshots/settings.png) | **Settings**<br>Control usage counts and color mode. |

Each screenshot is stored as an individual image under `docs/screenshots/`.

## How It Works

1. Create a reusable template.
2. Save it in the root library or a folder.
3. Find it through search or Favorites.
4. Select it and press Enter to copy its content.

Press `Ctrl+Alt+V` to show Quick Templates and `Esc` to hide it.

## Template Storage and Backup

Each template is a UTF-8 `.md` file: the filename is its name, the directory is its category, and the file body is its content. Favorites, usage counters, theme, window size, and the selected library location are stored in `%APPDATA%\Case Templates\settings.json`.

The template location is configurable from the Folders page. It can point to a locally synchronized cloud directory—such as a OneDrive folder—to keep an automatic backup and make the template files available through that provider's synchronization. Quick Templates itself remains local-first and does not connect directly to a cloud service.

## Technical Overview

- **Language and UI:** Python, PySide6, and PySide6-Fluent-Widgets
- **Templates:** Local Markdown files managed by services in `core/`
- **Configuration:** JSON stored in the user's application-data directory
- **Clipboard:** Qt clipboard integration
- **Desktop integration:** Global shortcut and system tray
- **Packaging:** PyInstaller support for a standalone Windows executable

## Project Structure

```text
quick.templates/
├── app.py                 # Application entry point
├── core/                  # Storage, search, clipboard, and settings
├── models/                # Template data model
├── ui/                    # Main window and dialogs
├── assets/                # Application icons
├── docs/screenshots/      # Sanitized screenshots
├── install.ps1            # Windows installer script
└── requirements.txt       # Runtime and build dependencies
```

## Use Cases

- Customer support responses
- Repeated email follow-ups
- Project and operational status updates
- Development or operations runbook snippets
- Meeting-note templates
- Administrative and other repetitive text

## Open Source and Contributions

Quick Templates is open to community feedback and contributions. You can:

- Open an issue to report a bug
- Suggest an improvement or new feature
- Submit a pull request with a focused change
- Improve documentation or test coverage

Before submitting a pull request, install the dependencies with `python -m pip install -r requirements.txt`, run the application with `python app.py`, and describe how the change was verified.

## License

This project is released under the MIT License.
