# Technical Overview

[Documentation home](index.md) · [Usage and configuration](USAGE.md) · [Contributing](../CONTRIBUTING.md)

## Architecture

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
