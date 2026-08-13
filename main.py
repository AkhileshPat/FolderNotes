"""
FolderNotes — Lightweight folder-attached notes for Windows.

Entry point: Run this script to start the application.
"""

import sys
import os
import subprocess

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.app import FolderNotesApp


def _run_detached_from_console() -> bool:
    """Start the GUI in its own Windows process when launched with ``python``.

    A process started by a terminal can receive a close signal when that
    terminal exits. Relaunching with ``pythonw.exe`` gives FolderNotes its
    own GUI-process lifetime, so closing the terminal does not close notes.
    """
    if os.name != "nt" or "--background" in sys.argv or "--foreground" in sys.argv:
        return False

    pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    if not os.path.exists(pythonw):
        return False

    creationflags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    subprocess.Popen(
        [pythonw, os.path.abspath(__file__), "--background"],
        close_fds=True,
        creationflags=creationflags,
    )
    return True


def main():
    if _run_detached_from_console():
        return 0

    app = FolderNotesApp()
    return app.run()


if __name__ == "__main__":
    sys.exit(main())
