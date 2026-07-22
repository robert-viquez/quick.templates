# Case Templates

A lightweight desktop application built with **Python** and **Tkinter** for creating, organizing, searching, and copying reusable text templates. The application is designed to improve productivity by reducing repetitive typing and providing instant access to frequently used texts.

---

## Features

- Fast template search
- Copy templates to clipboard with one click
- Create, edit, and delete templates
- Keyboard shortcuts
- No internet connection required
- Standalone executable support (PyInstaller)

---

## Screenshots

> Add screenshots here.

```
/screenshots
    main-window.png
    editor.png
    settings.png
```

---

## Project Structure

```
CaseTemplates/
│
├── app.py                 # Main application
├── templates/             # Templates
├── settings.json          # User settings
├── README.md
├── assets/
└── dist/                  # Generated executable
```

---

## Requirements

- Python 3.11+
- Windows 10/11

Required packages:

```
tkinter
pyperclip
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Running the Application

```bash
python app.py
```

---

## Building the Executable

Using PyInstaller:

```bash
pyinstaller ^
    --onefile ^
    --windowed ^
    --icon=icon.ico ^
    app.py
```

The executable will be generated inside:

```
dist/
```

---

## Settings

Application settings are automatically stored in:

```
%APPDATA%/CaseTemplates/settings.json
```

The application saves:

- Window size
- Last selected category
- User preferences

---

## Template Storage

Templates are stored locally in Markdown format.

Example:

```json
[
    {
        "title": "Password Reset",
        "category": "Accounts",
        "content": "Please reset your password using the following link...",
        "favorite": true
    }
]
```

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl + N | New template |
| Ctrl + E | Edit template |
| Delete | Delete selected template |
| Ctrl + F | Focus search |
| Ctrl + C | Copy template |
| Esc | Close dialog |

---

## Technologies

- Python
- Tkinter
- ttk
- JSON
- PyInstaller

---

## Future Improvements

- Markdown support
- Rich text editor
- Import / Export templates
- Cloud synchronization
- Multiple databases
- Template tags
- Advanced filtering
- Dark mode
- Auto-update support
- Cross-platform builds (macOS/Linux)

---

## License

This project is released under the MIT License.

---

## Author

**Robert Viquez Santos**

Engineering Student • Software Developer

GitHub:
https://github.com/robert-viquez

---

## Contributing

Contributions, feature requests, and bug reports are welcome.

1. Fork the repository
2. Create a feature branch

```bash
git checkout -b feature/new-feature
```

3. Commit your changes

```bash
git commit -m "Add new feature"
```

4. Push the branch

```bash
git push origin feature/new-feature
```

5. Open a Pull Request.

---

## Why Case Templates?

Many professionals repeatedly type the same responses every day. Case Templates centralizes those responses into a fast, searchable desktop application that reduces repetitive work, improves consistency, and increases productivity.