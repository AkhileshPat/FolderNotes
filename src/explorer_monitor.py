"""
Explorer Monitor for FolderNotes.

Detects the active Windows Explorer window and its current folder path
using Shell COM Automation and Win32 APIs.

Strategy:
  1. QTimer polling at 500ms — checks if foreground is Explorer and
     queries Shell COM for the current folder path.
  2. Shell.Application.Windows() — enumerate Explorer windows via COM.
  3. Match by HWND with fallback to "any Explorer window that is foreground".

Note: We dropped SetWinEventHook because it races with Shell COM registration.
A new Explorer window fires the foreground event BEFORE Shell.Application
adds it to its Windows() collection, causing silent HWND match failures.
Polling at 500ms is reliable and lightweight.
"""

import ctypes
import ctypes.wintypes
import os
import logging
from typing import Optional, Tuple

from PySide6.QtCore import QObject, Signal, QTimer

logger = logging.getLogger(__name__)

# ── Win32 Constants ──────────────────────────────────────────────────
DWMWA_EXTENDED_FRAME_BOUNDS = 9

user32 = ctypes.windll.user32
dwmapi = ctypes.windll.dwmapi

# ── Set proper return/arg types for Win32 functions ──────────────────
user32.GetForegroundWindow.restype = ctypes.wintypes.HWND
user32.GetForegroundWindow.argtypes = []

user32.GetClassNameW.restype = ctypes.c_int
user32.GetClassNameW.argtypes = [ctypes.wintypes.HWND, ctypes.c_wchar_p, ctypes.c_int]

user32.IsWindow.restype = ctypes.wintypes.BOOL
user32.IsWindow.argtypes = [ctypes.wintypes.HWND]

user32.IsIconic.restype = ctypes.wintypes.BOOL
user32.IsIconic.argtypes = [ctypes.wintypes.HWND]

user32.GetWindowRect.restype = ctypes.wintypes.BOOL
user32.GetWindowRect.argtypes = [ctypes.wintypes.HWND, ctypes.POINTER(ctypes.wintypes.RECT)]

user32.GetWindowThreadProcessId.restype = ctypes.wintypes.DWORD
user32.GetWindowThreadProcessId.argtypes = [ctypes.wintypes.HWND, ctypes.POINTER(ctypes.wintypes.DWORD)]

OUR_PID = os.getpid()


class ExplorerMonitor(QObject):
    """
    Monitors Windows Explorer windows and emits signals when the
    active folder changes.

    Signals:
        folder_changed(str, int, tuple):
            Emitted with (folder_path, explorer_hwnd, (x, y, w, h))
        explorer_lost():
            Emitted when the foreground window is no longer Explorer.
    """

    folder_changed = Signal(str, int, tuple)  # path, hwnd, rect
    explorer_lost = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._last_folder: str = ""
        self._last_hwnd: int = 0
        # Persists across focus-loss so the tray menu can use it
        self._last_known_folder: str = ""
        self._last_known_hwnd: int = 0
        self._explorer_is_active: bool = False

        # Main polling timer
        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(400)
        self._poll_timer.timeout.connect(self._poll)

    # ── Public API ───────────────────────────────────────────────────

    def start(self):
        """Begin monitoring Explorer windows."""
        self._poll_timer.start()
        logger.info("Explorer monitor started (polling at %dms).",
                     self._poll_timer.interval())

    def stop(self):
        """Stop monitoring."""
        self._poll_timer.stop()
        logger.info("Explorer monitor stopped.")

    # ── Polling ──────────────────────────────────────────────────────

    def _poll(self):
        """
        Check the foreground window every tick.
        If it's Explorer, resolve the folder via COM.
        """
        try:
            raw_hwnd = user32.GetForegroundWindow()
            hwnd = int(raw_hwnd) if raw_hwnd else 0

            if not hwnd:
                return

            if self._is_explorer_window(hwnd):
                self._handle_explorer_foreground(hwnd)
            elif self._is_our_process(hwnd) or self._is_shell_ui(hwnd):
                # User is interacting with our overlay or with the Windows
                # tray menu.  The latter briefly owns foreground focus after
                # a tray action; treating it as Explorer-loss immediately
                # hides a note just after it has been created.
                pass
            else:
                # Some other app is in front
                if self._explorer_is_active:
                    self._explorer_is_active = False
                    self._last_hwnd = 0
                    self._last_folder = ""
                    self.explorer_lost.emit()

        except Exception as e:
            logger.debug("Poll error: %s", e)

    def _handle_explorer_foreground(self, hwnd: int):
        """Explorer is the foreground window — resolve folder via COM."""
        self._explorer_is_active = True

        try:
            import win32com.client
            shell = win32com.client.Dispatch("Shell.Application")
            windows = shell.Windows()
            count = windows.Count

            # Try to match by HWND first
            for i in range(count):
                try:
                    window = windows.Item(i)
                    if window is None:
                        continue
                    com_hwnd = int(window.HWND)
                    if com_hwnd == hwnd:
                        self._process_matched_window(window, hwnd)
                        return
                except Exception:
                    continue

            # HWND match failed (COM race condition on new windows).
            # Fall back: find any COM window whose HWND is an Explorer
            # class window that matches our foreground.
            # This handles the case where Shell.Application hasn't
            # registered the new window yet.
            logger.debug("COM: No direct HWND match for %s in %d windows. "
                         "Trying fallback...", hwnd, count)

            # Try all COM windows — if any is an Explorer window AND
            # is currently the foreground, use it.
            for i in range(count):
                try:
                    window = windows.Item(i)
                    if window is None:
                        continue
                    com_hwnd = int(window.HWND)
                    if self._is_explorer_window(com_hwnd):
                        # Check if this COM window is actually foreground
                        fg = int(user32.GetForegroundWindow() or 0)
                        if com_hwnd == fg:
                            self._process_matched_window(window, com_hwnd)
                            return
                except Exception:
                    continue

            logger.debug("COM: Could not resolve folder for hwnd=%s "
                         "(likely new window not yet in COM collection)", hwnd)

        except Exception as e:
            logger.error("COM Shell enumeration failed: %s", e)

    def _process_matched_window(self, window, hwnd: int):
        """Extract folder path from a matched COM window object."""
        try:
            folder_path = window.Document.Folder.Self.Path
        except AttributeError:
            try:
                folder_path = window.LocationURL
            except Exception:
                folder_path = ""

        if not folder_path:
            return

        # Always update last-known (survives focus loss)
        self._last_known_folder = folder_path
        self._last_known_hwnd = hwnd

        # Only emit signal if folder or window changed
        if folder_path != self._last_folder or hwnd != self._last_hwnd:
            self._last_folder = folder_path
            self._last_hwnd = hwnd
            rect = self._get_window_rect(hwnd)
            logger.info("Folder changed: '%s' (hwnd=%s)", folder_path, hwnd)
            self.folder_changed.emit(folder_path, hwnd, rect)

    # ── Window Identification ────────────────────────────────────────

    @staticmethod
    def _is_explorer_window(hwnd: int) -> bool:
        """Check if a window handle belongs to Windows Explorer."""
        if not hwnd:
            return False

        try:
            class_name = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, class_name, 256)
            return class_name.value == "CabinetWClass"
        except Exception:
            return False

    @staticmethod
    def _is_shell_ui(hwnd: int) -> bool:
        """Return True for Windows taskbar/tray UI that should not hide notes."""
        if not hwnd:
            return False
        try:
            class_name = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, class_name, 256)
            return class_name.value in {
                "Shell_TrayWnd", "NotifyIconOverflowWindow", "#32768"
            }
        except Exception:
            return False

    @staticmethod
    def _is_our_process(hwnd: int) -> bool:
        """Check if a window belongs to our own application process."""
        if not hwnd:
            return False
        try:
            pid = ctypes.wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            return pid.value == OUR_PID
        except Exception:
            return False

    # ── Window Geometry ──────────────────────────────────────────────

    @staticmethod
    def _get_window_rect(hwnd: int) -> Tuple[int, int, int, int]:
        """
        Get the true visible bounds of a window using DWM API.
        Returns (x, y, width, height).
        """
        rect = ctypes.wintypes.RECT()

        # Try DWM extended frame bounds first (more accurate on Win10/11)
        result = dwmapi.DwmGetWindowAttribute(
            hwnd,
            DWMWA_EXTENDED_FRAME_BOUNDS,
            ctypes.byref(rect),
            ctypes.sizeof(rect)
        )

        if result != 0:
            # Fallback to GetWindowRect
            user32.GetWindowRect(hwnd, ctypes.byref(rect))

        x = rect.left
        y = rect.top
        w = rect.right - rect.left
        h = rect.bottom - rect.top
        return (x, y, w, h)

    def get_current_explorer_rect(self) -> Optional[Tuple[int, int, int, int]]:
        """Get the current rect of the tracked Explorer window."""
        if self._last_hwnd and self._is_explorer_window(self._last_hwnd):
            return self._get_window_rect(self._last_hwnd)
        return None

    def get_current_hwnd(self) -> int:
        """Get the current tracked Explorer HWND."""
        return self._last_hwnd

    def get_active_explorer_folder(self) -> str:
        """Get the most recently active Explorer folder, even if focus was lost."""
        return self._last_known_folder

    def get_active_explorer_hwnd(self) -> int:
        """Get the most recently active Explorer HWND, even if focus was lost."""
        return self._last_known_hwnd

    def get_note_target(self) -> Tuple[str, int]:
        """Resolve a usable folder and HWND for a tray-menu note action.

        A system-tray menu becomes the foreground window before its action is
        emitted, so foreground-window polling alone cannot identify Explorer
        at that point.  Query Shell.Application directly, preferring the
        last tracked Explorer window and otherwise using an open Explorer
        window with a real filesystem folder.
        """
        if self._last_known_folder and self._last_known_hwnd:
            if user32.IsWindow(self._last_known_hwnd):
                return self._last_known_folder, self._last_known_hwnd

        try:
            import win32com.client

            shell = win32com.client.Dispatch("Shell.Application")
            windows = shell.Windows()
            fallback = ("", 0)

            for i in range(windows.Count):
                try:
                    window = windows.Item(i)
                    hwnd = int(window.HWND)
                    if not self._is_explorer_window(hwnd):
                        continue
                    path = window.Document.Folder.Self.Path
                    if path:
                        # Keep this cache populated for later overlay updates.
                        self._last_known_folder = path
                        self._last_known_hwnd = hwnd
                        fallback = (path, hwnd)
                except Exception:
                    continue

            return fallback
        except Exception as e:
            logger.warning("Could not resolve Explorer folder for tray action: %s", e)
            return "", 0
