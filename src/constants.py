"""
Application-wide constants for FolderNotes.
"""

import os

APP_NAME = "FolderNotes"
APP_VERSION = "1.0.0"

# Storage paths
LOCAL_APPDATA = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
APP_DATA_DIR = os.path.join(LOCAL_APPDATA, APP_NAME)
DATABASE_PATH = os.path.join(APP_DATA_DIR, "database.db")
SETTINGS_PATH = os.path.join(APP_DATA_DIR, "settings.json")
LOG_DIR = os.path.join(APP_DATA_DIR, "logs")
CACHE_DIR = os.path.join(APP_DATA_DIR, "cache")

# Overlay dimensions
OVERLAY_WIDTH = 320
OVERLAY_HEIGHT = 280
OVERLAY_MARGIN = 16  # pixels from Explorer edge

# Polling intervals (ms)
EXPLORER_POLL_INTERVAL = 500    # fallback polling for in-window navigation
POSITION_POLL_INTERVAL = 100    # overlay repositioning frequency

# Snooze durations (hours)
SNOOZE_DURATIONS = [1, 2, 3, 5, 8]

# Explorer window class name
EXPLORER_CLASS_NAME = "CabinetWClass"

# Colors
NOTE_BG_COLOR = "#FFF9C4"         # Light yellow paper
NOTE_BORDER_COLOR = "#F9E066"     # Warm yellow border accent
NOTE_TITLE_BG = "#FFEE58"        # Title bar yellow
NOTE_SHADOW_COLOR = "rgba(0, 0, 0, 40)"
TEXT_COLOR = "#3E2723"            # Dark brown text
TOOLBAR_BG = "#FFF3B0"           # Lighter yellow for toolbar
