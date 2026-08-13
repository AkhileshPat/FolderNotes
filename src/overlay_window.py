"""
Floating Overlay Window for FolderNotes.

A borderless, frameless Qt window that visually resembles a sticky note.
Docks to the bottom-right of the active Explorer window and follows
its movement, resize, maximize, and restore operations.
"""

import ctypes
import ctypes.wintypes
import logging

from PySide6.QtCore import Qt, QTimer, Signal, QPoint
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMenu
)
from PySide6.QtGui import (
    QColor, QFont, QCursor, QPainter, QBrush, QPen, QRegion, QGuiApplication
)

from src.rich_editor import RichEditor
from src.constants import (
    OVERLAY_WIDTH, OVERLAY_HEIGHT, OVERLAY_MARGIN,
    NOTE_BG_COLOR, NOTE_BORDER_COLOR, NOTE_TITLE_BG,
    TEXT_COLOR, SNOOZE_DURATIONS,
    POSITION_POLL_INTERVAL
)

logger = logging.getLogger(__name__)

user32 = ctypes.windll.user32
dwmapi = ctypes.windll.dwmapi
DWMWA_EXTENDED_FRAME_BOUNDS = 9

# Proper Win32 function signatures
user32.IsWindow.restype = ctypes.wintypes.BOOL
user32.IsWindow.argtypes = [ctypes.wintypes.HWND]
user32.IsIconic.restype = ctypes.wintypes.BOOL
user32.IsIconic.argtypes = [ctypes.wintypes.HWND]
user32.GetWindowRect.restype = ctypes.wintypes.BOOL
user32.GetWindowRect.argtypes = [ctypes.wintypes.HWND, ctypes.POINTER(ctypes.wintypes.RECT)]


class OverlayWindow(QWidget):
    """
    Floating borderless overlay that displays a note.

    Signals:
        content_saved(str):    Content changed (for auto-save).
        title_saved(str):      Title changed.
        close_requested():     User clicked close (dismiss for session).
        delete_requested():    User chose to delete the note.
        snooze_requested(int): User chose to snooze for N hours.
    """

    content_saved = Signal(str)
    title_saved = Signal(str)
    close_requested = Signal()
    delete_requested = Signal()
    snooze_requested = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._explorer_hwnd: int = 0
        self._is_dragging = False
        self._drag_offset = QPoint()
        self._current_folder_name = ""
        self._manual_offset_x = 0
        self._manual_offset_y = 0

        self._setup_window()
        self._setup_ui()
        self._setup_position_tracker()

    # ── Window Setup ─────────────────────────────────────────────────

    def _setup_window(self):
        """Configure the overlay as a borderless, always-on-top window."""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        # No WA_TranslucentBackground — it causes rendering issues on many
        # Windows systems when combined with drop shadows and Tool windows.
        # No WA_ShowWithoutActivating — we WANT the note to be interactive.
        self.setFixedSize(OVERLAY_WIDTH, OVERLAY_HEIGHT)

        # Rounded corner styling on the entire widget
        self.setStyleSheet(f"""
            OverlayWindow {{
                background-color: {NOTE_BG_COLOR};
                border: 2px solid {NOTE_BORDER_COLOR};
                border-radius: 10px;
            }}
        """)

    def _setup_ui(self):
        """Build the sticky-note-style UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(0)

        # ── Title Bar ────────────────────────────────────────────────
        title_bar = QWidget()
        title_bar.setObjectName("titleBar")
        title_bar.setFixedHeight(32)
        title_bar.setStyleSheet(f"""
            QWidget#titleBar {{
                background-color: {NOTE_TITLE_BG};
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                border-bottom: 1px solid #E8D44D;
            }}
        """)

        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 0, 6, 0)
        title_layout.setSpacing(4)

        # Folder icon + name
        self._folder_label = QLabel("Note")
        self._folder_label.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_COLOR};
                font-family: 'Segoe UI', sans-serif;
                font-size: 12px;
                font-weight: bold;
                background: transparent;
                border: none;
            }}
        """)

        # Snooze button
        self._btn_snooze = self._make_title_btn("Zz", "Snooze this note")
        self._btn_snooze.clicked.connect(self._show_snooze_menu)

        # More actions button
        self._btn_more = self._make_title_btn("...", "More actions")
        self._btn_more.clicked.connect(self._show_more_menu)

        # Close button
        self._btn_close = self._make_title_btn("X", "Dismiss for this session")
        self._btn_close.clicked.connect(self.close_requested.emit)

        title_layout.addWidget(self._folder_label, 1)
        title_layout.addWidget(self._btn_snooze)
        title_layout.addWidget(self._btn_more)
        title_layout.addWidget(self._btn_close)

        # ── Rich Text Editor ─────────────────────────────────────────
        self._editor = RichEditor()
        self._editor.content_changed.connect(self.content_saved.emit)

        main_layout.addWidget(title_bar)
        main_layout.addWidget(self._editor, 1)

    def _make_title_btn(self, text: str, tooltip: str) -> QPushButton:
        """Create a compact title bar button."""
        btn = QPushButton(text)
        btn.setToolTip(tooltip)
        btn.setFixedSize(26, 22)
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 3px;
                font-size: 11px;
                font-weight: bold;
                color: {TEXT_COLOR};
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: rgba(0, 0, 0, 0.1);
                border-color: #D4C44A;
            }}
            QPushButton:pressed {{
                background-color: rgba(0, 0, 0, 0.2);
            }}
        """)
        return btn

    # ── Position Tracking ────────────────────────────────────────────

    def _setup_position_tracker(self):
        """Timer to follow the Explorer window's position."""
        self._position_timer = QTimer(self)
        self._position_timer.setInterval(POSITION_POLL_INTERVAL)
        self._position_timer.timeout.connect(self._update_position)

    def _update_position(self):
        """Reposition the overlay relative to the Explorer window."""
        if not self._explorer_hwnd:
            return

        # Check if Explorer window still exists
        if not user32.IsWindow(self._explorer_hwnd):
            logger.debug("Overlay: Explorer window gone - hiding")
            self.hide()
            self._position_timer.stop()
            return

        # Check if Explorer is minimized
        if user32.IsIconic(self._explorer_hwnd):
            if self.isVisible():
                self.hide()
            return

        rect = self._get_explorer_rect()
        if not rect:
            return

        ex, ey, ew, eh = rect

        # Get work area (excludes taskbar)
        work_area = ctypes.wintypes.RECT()
        user32.SystemParametersInfoW(
            0x0030,  # SPI_GETWORKAREA
            0,
            ctypes.byref(work_area),
            0
        )

        # Calculate position: bottom-right of Explorer, inside the window
        target_x = ex + ew - self.width() - OVERLAY_MARGIN + self._manual_offset_x
        target_y = ey + eh - self.height() - OVERLAY_MARGIN + self._manual_offset_y

        # Clamp to work area
        target_x = max(work_area.left, min(target_x, work_area.right - self.width()))
        target_y = max(work_area.top, min(target_y, work_area.bottom - self.height()))

        self.move(target_x, target_y)

        if not self.isVisible():
            logger.info("Overlay: showing at (%d, %d)", target_x, target_y)
            self.show()
            self.raise_()

    def _get_explorer_rect(self):
        """Get Explorer window bounds using DWM API."""
        rect = ctypes.wintypes.RECT()
        result = dwmapi.DwmGetWindowAttribute(
            self._explorer_hwnd,
            DWMWA_EXTENDED_FRAME_BOUNDS,
            ctypes.byref(rect),
            ctypes.sizeof(rect)
        )
        if result != 0:
            user32.GetWindowRect(self._explorer_hwnd, ctypes.byref(rect))

        x = rect.left
        y = rect.top
        w = rect.right - rect.left
        h = rect.bottom - rect.top

        if w <= 0 or h <= 0:
            return None
        return (x, y, w, h)

    # ── Public API ───────────────────────────────────────────────────

    def show_note(self, note_data: dict, explorer_hwnd: int):
        """Display a note attached to the given Explorer window."""
        logger.info("Overlay: show_note called, hwnd=%s", explorer_hwnd)

        # A cached Explorer HWND can become invalid while the tray menu has
        # focus.  Do not start the position tracker for such a handle: it
        # would hide this window again on its next timer tick.
        has_live_explorer = bool(
            explorer_hwnd
            and user32.IsWindow(explorer_hwnd)
            and not user32.IsIconic(explorer_hwnd)
        )
        self._explorer_hwnd = explorer_hwnd if has_live_explorer else 0
        self._manual_offset_x = 0
        self._manual_offset_y = 0

        # Set folder name in title
        folder_path = note_data.get("folder_path", "")
        parts = folder_path.rstrip("/").split("/")
        folder_name = parts[-1] if parts else folder_path
        self._folder_label.setText(folder_name)
        self._current_folder_name = folder_name

        # Set content
        content = note_data.get("content", "")
        self._editor.set_content(content)

        # Position and show immediately.  Explorer may not have a foreground
        # handle while a tray-menu action is being processed; in that case,
        # show a usable standalone note instead of silently dropping it.
        if self._explorer_hwnd:
            self._update_position()
            self._position_timer.start()
        else:
            self._position_timer.stop()
            screen = QGuiApplication.primaryScreen()
            if screen:
                available = screen.availableGeometry()
                self.move(available.center() - self.rect().center())
            logger.warning("Overlay: no Explorer hwnd; showing centered fallback")

        # Force visibility
        if not self.isVisible():
            self.show()
        self.raise_()
        self.activateWindow()
        self._editor.setFocus()

        logger.info("Overlay: show complete, visible=%s, geom=(%d,%d,%dx%d)",
                     self.isVisible(), self.x(), self.y(), self.width(), self.height())

    def hide_note(self):
        """Hide the overlay and stop tracking."""
        self._position_timer.stop()
        self.hide()

    def get_editor(self) -> RichEditor:
        """Access the rich text editor."""
        return self._editor

    # ── Snooze Menu ──────────────────────────────────────────────────

    def _show_snooze_menu(self):
        """Show snooze duration options."""
        menu = QMenu(self)
        menu.setStyleSheet(self._menu_style())

        for hours in SNOOZE_DURATIONS:
            label = f"Snooze for {hours} hour{'s' if hours > 1 else ''}"
            action = menu.addAction(label)
            action.triggered.connect(lambda checked, h=hours: self.snooze_requested.emit(h))

        menu.exec(self._btn_snooze.mapToGlobal(
            QPoint(0, self._btn_snooze.height())
        ))

    def _show_more_menu(self):
        """Show additional actions menu."""
        menu = QMenu(self)
        menu.setStyleSheet(self._menu_style())

        delete_action = menu.addAction("Delete note permanently")
        delete_action.triggered.connect(self.delete_requested.emit)

        menu.exec(self._btn_more.mapToGlobal(
            QPoint(0, self._btn_more.height())
        ))

    @staticmethod
    def _menu_style() -> str:
        return f"""
            QMenu {{
                background-color: #FFFDE7;
                border: 1px solid {NOTE_BORDER_COLOR};
                border-radius: 6px;
                padding: 4px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 12px;
                color: {TEXT_COLOR};
            }}
            QMenu::item {{
                padding: 6px 16px;
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background-color: #FFF59D;
            }}
        """

    # ── Dragging ─────────────────────────────────────────────────────

    def mousePressEvent(self, event):
        """Begin drag on the title bar area."""
        if event.button() == Qt.MouseButton.LeftButton and event.position().y() < 40:
            self._is_dragging = True
            self._drag_offset = event.globalPosition().toPoint() - self.pos()

    def mouseMoveEvent(self, event):
        """Handle drag movement."""
        if self._is_dragging:
            new_pos = event.globalPosition().toPoint() - self._drag_offset
            self.move(new_pos)

            # Update manual offset so position tracker preserves user's drag
            if self._explorer_hwnd:
                rect = self._get_explorer_rect()
                if rect:
                    ex, ey, ew, eh = rect
                    default_x = ex + ew - self.width() - OVERLAY_MARGIN
                    default_y = ey + eh - self.height() - OVERLAY_MARGIN
                    self._manual_offset_x = new_pos.x() - default_x
                    self._manual_offset_y = new_pos.y() - default_y

    def mouseReleaseEvent(self, event):
        """End drag."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = False
