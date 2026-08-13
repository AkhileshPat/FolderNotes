# FolderNotes --- AI Implementation Specification

## One-line Summary

**FolderNotes** is a lightweight Windows desktop utility that attaches
**exactly one persistent note to each folder**. Whenever that folder is
opened in Windows Explorer, a small floating note automatically appears,
visually anchored to the Explorer window.

------------------------------------------------------------------------

# Why This Exists

Windows has no native way to attach contextual notes to folders.
FolderNotes provides lightweight, offline annotations that belong to
folders---not to the desktop, a notebook, or a productivity suite.

Examples: - Move PDFs here later. - Legacy code. Don't modify
`Parser.cpp`. - Watch these films first. - Contains archived invoices.

------------------------------------------------------------------------

# Core Philosophy

This is **not**: - A notes app - A task manager - Sticky Notes clone -
Reminder app - Calendar - AI assistant

The application has one purpose:

> **One lightweight note attached to one folder.**

When in doubt, prefer **minimalism** over adding features.

------------------------------------------------------------------------

# Scope (Version 1)

-   Windows 10/11 only
-   Offline only
-   One note per folder
-   Auto-save
-   SQLite storage
-   Floating borderless overlay
-   System tray application
-   No Explorer modification/injection

------------------------------------------------------------------------

# Functional Requirements

1.  Exactly one note per folder.
2.  Automatic folder association.
3.  Detect active Explorer window and current folder.
4.  Update the same overlay instantly during navigation.
5.  Hide overlay when no note exists.
6.  Overlay follows Explorer movement, resize, maximize, restore and
    monitor changes.
7.  Dock near bottom-right without covering the taskbar.
8.  Close hides the note for the current session; deleting is explicit.
9.  Start with Windows and idle efficiently.

------------------------------------------------------------------------

# Editor

Supported: - Bold - Italic - Underline - Bullet list - Numbered list

Not supported: - Images - Tables - Markdown - Colors - Custom fonts -
Hyperlinks - AI - Spell checker

Every keystroke auto-saves.

------------------------------------------------------------------------

# Storage

Use SQLite under:

`%LOCALAPPDATA%\FolderNotes\`

Suggested layout:

``` text
FolderNotes/
    database.db
    settings.json
    logs/
    cache/
```

Suggested schema:

-   NoteID
-   FolderPath (unique)
-   Title
-   Content
-   CreatedAt
-   UpdatedAt
-   Hidden
-   Version

Never create hidden files or notes inside user folders.

------------------------------------------------------------------------

# UX

The overlay should resemble a modern sticky note: - Rounded corners -
Light yellow paper - Subtle shadow - Small title bar - Borderless

Actions: - Edit - Close - Delete (optional)

------------------------------------------------------------------------

# Architecture

Explorer Monitor → Folder Resolver → SQLite Layer → Note Manager →
Floating Window → Rich Text Editor → System Tray → Settings

Use clean modular boundaries.

------------------------------------------------------------------------

# Non-functional Requirements

-   RAM \<100 MB
-   Startup \<2 s
-   Near-zero idle CPU
-   Fast database lookup
-   Graceful handling of:
    -   Explorer restart
    -   Deleted folders
    -   Renamed folders
    -   Disconnected drives
    -   SQLite corruption/locks

------------------------------------------------------------------------

# Recommended Tech Stack

Preferred: - Language: C# - UI: WPF (MVVM) - Database: SQLite -
Packaging: MSIX or Installer

Alternative: - Python + PySide6 for faster prototyping.

Explain trade-offs before implementation.

------------------------------------------------------------------------

# Development Plan

Before writing production code, produce:

1.  Software architecture
2.  Folder structure
3.  Database schema
4.  UI mockups
5.  Class diagrams
6.  State diagrams
7.  Explorer detection strategy
8.  Window docking strategy
9.  Testing strategy
10. Milestone roadmap

------------------------------------------------------------------------

# Deliverables

-   Architecture
-   Tech-stack justification
-   Folder structure
-   Database schema
-   Incremental production-ready code
-   Unit tests
-   Build & packaging instructions
-   Installer
-   GitHub README
-   Future roadmap

------------------------------------------------------------------------

# Highest-Risk Component

Do **not** assume Explorer exposes its current folder trivially.

Before implementation:

-   Compare Shell COM Automation
-   Win32 APIs
-   UI Automation
-   Other production-ready techniques

Evaluate reliability, edge cases and limitations.

The entire architecture should be based on the most reliable
production-ready approach.
