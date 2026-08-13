# Application Category

FolderNotes is a **native Windows desktop utility**.

It runs as a lightweight **system tray application** and continuously monitors Windows Explorer.

When an Explorer window displaying a folder with an associated note becomes active, FolderNotes displays its own **borderless floating overlay window**, positioned to appear visually attached to that Explorer window.

The overlay is a completely independent window owned by FolderNotes.

FolderNotes **does not**:

- modify Windows Explorer
- inject code into Explorer
- implement a Shell Extension
- replace Explorer UI
- add Explorer toolbars or panes
- hook Explorer using unsupported techniques

Instead, it communicates with Explorer only through supported Windows APIs (such as Shell COM Automation, Win32 APIs, or other production-ready mechanisms) to determine the active folder and window position.

The design philosophy is to keep FolderNotes fully independent from Explorer while creating the illusion that the note naturally belongs to the currently open folder.

------------------------------------------------------------------------

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

# Snoozing Architecture (Core Feature)

## Purpose

Users may temporarily suppress a note that repeatedly appears while
navigating between folders. Snoozing is **folder-specific**, not global.

## Behavior

-   Snooze affects **only the selected folder**.
-   Other folders continue to display their notes normally.
-   When the snooze duration expires, the note automatically resumes
    appearing.
-   Snoozing never deletes or modifies the note's content.

### Supported Durations

-   1 hour
-   2 hours
-   3 hours
-   5 hours
-   8 hours

### Example

    Downloads     → Note appears ✓

    Films         → User clicks "Snooze for 3 hours"

    Downloads     → Note appears ✓

    Songs         → Note appears ✓

    Films         → No note appears (until the 3-hour timer expires)

    After 3 hours:

    Films         → Note appears again ✓

## Session Behavior

Snooze state is maintained independently for each folder. A snoozed
folder must not suppress notes belonging to any other folder.

## Suggested Database Fields

Add the following optional fields to the Notes table:

-   SnoozedUntil (nullable DateTime)
-   LastDismissedAt (optional)

When displaying a note, the application should first determine whether
the current folder has an active snooze period. If the current time is
earlier than `SnoozedUntil`, the overlay must remain hidden for that
folder only.

This check should be part of the Note Manager before instructing the
Floating Window to display the note.

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
