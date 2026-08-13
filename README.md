# FolderNotes

**Lightweight folder-attached notes for Windows.**

FolderNotes is a native Windows desktop utility that attaches exactly one persistent note to each folder. Whenever that folder is opened in Windows Explorer, a small floating note automatically appears, visually anchored to the Explorer window.

## Why?

Windows has no native way to attach contextual notes to folders. FolderNotes fills that gap with lightweight, offline annotations that belong to folders — not a notebook or productivity suite.

**Examples:**
- *Move PDFs here later.*
- *Legacy code. Don't modify `Parser.cpp`.*
- *Watch these films first.*
- *Contains archived invoices.*

## Features

- **One note per folder** — Simple, focused, no clutter
- **Auto-detection** — Notes appear automatically when you open the folder in Explorer
- **Rich text** — Bold, italic, underline, bullet lists, numbered lists
- **Auto-save** — Every keystroke is saved instantly
- **System tray** — Runs quietly in the background
- **Snooze** — Temporarily hide a note (1, 2, 3, 5, or 8 hours)
- **Session dismiss** — Close a note until you restart the app
- **Zero modification** — Does not inject into or modify Explorer in any way
- **SQLite storage** — All data stored locally in `%LOCALAPPDATA%\FolderNotes\`

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.10+ |
| UI Framework | PySide6 (Qt 6) |
| Database | SQLite (built-in) |
| Win32 Integration | pywin32 + ctypes |
| Explorer Detection | Shell COM Automation |

## Quick Start

### Prerequisites
- Python 3.10 or later
- Windows 10 or 11

### Installation

```powershell
# Clone or download the project
cd FolderNotes

# Install dependencies
pip install -r requirements.txt

# Run
python main.py
```

When started this way, FolderNotes detaches from the terminal after launch,
so the terminal can be closed without closing the app. Use
`python main.py --foreground` while debugging to keep it attached.

Closing the FolderNotes manager window hides it to the system tray and leaves
the floating note running. Use the tray menu's **Quit** command to exit the
application completely.

### Usage

1. **Start the app** — A yellow "FN" icon appears in the system tray
2. **Open a folder** in Windows Explorer
3. **Right-click the tray icon** → "Create note for current folder"
4. **Type your note** — it auto-saves on every keystroke
5. **Navigate away and back** — the note reappears automatically!

### Controls

| Action | How |
|--------|-----|
| Create a note | Right-click tray icon → "Create note" |
| Edit | Click on the note and type |
| Format text | Use toolbar buttons or Ctrl+B/I/U |
| Dismiss (session) | Click ✕ on the note |
| Snooze | Click 💤 → choose duration |
| Delete permanently | Click ⋮ → "Delete note permanently" |
| Quit | Right-click tray icon → "Quit" |

## Architecture

```
Explorer Monitor → Folder Resolver → SQLite Layer → Note Manager →
Floating Window → Rich Text Editor → System Tray → Settings
```

- **Explorer Monitor** — Detects active Explorer windows via Shell COM + Win32 hooks
- **Folder Resolver** — Normalizes paths, filters virtual folders
- **Note Manager** — Business logic (CRUD, snooze, dismiss)
- **Overlay Window** — Borderless floating Qt window, docked to Explorer
- **Rich Editor** — QTextEdit with formatting toolbar
- **System Tray** — Background app with context menu

## Project Structure

```
FolderNotes/
├── main.py                    # Entry point
├── requirements.txt           # Dependencies
├── README.md
├── src/
│   ├── app.py                 # Application controller
│   ├── explorer_monitor.py    # Explorer detection
│   ├── folder_resolver.py     # Path normalization
│   ├── database.py            # SQLite layer
│   ├── note_manager.py        # Business logic
│   ├── overlay_window.py      # Floating note window
│   ├── rich_editor.py         # Rich text editor
│   ├── system_tray.py         # System tray
│   ├── settings.py            # Settings manager
│   └── constants.py           # App constants
└── tests/
    ├── test_database.py
    ├── test_folder_resolver.py
    └── test_note_manager.py
```

## Building an Installer

```powershell
# Install PyInstaller
pip install pyinstaller

# Build
pyinstaller --onefile --noconsole --name FolderNotes --icon=resources/icon.ico main.py
```

## License

MIT

---

*One lightweight note attached to one folder.*
