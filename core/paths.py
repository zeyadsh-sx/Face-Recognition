"""Central project paths for attendance face recognition system."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CORE_DIR = PROJECT_ROOT / "core"
GUI_DIR = PROJECT_ROOT / "gui"
WEB_DIR = PROJECT_ROOT / "web"
DATA_DIR = PROJECT_ROOT / "data"
CONFIG_DIR = PROJECT_ROOT / "config"

KNOWN_FACES_DIR = DATA_DIR / "known_faces"
UNKNOWN_FACES_DIR = DATA_DIR / "unknown_faces"
ATTENDANCE_IMAGES_DIR = DATA_DIR / "attendance_images"

UNKNOWN_COUNTER_FILE = DATA_DIR / ".unknown_counter.json"
SYSTEM_SETTINGS_FILE = CONFIG_DIR / "system_settings.json"

# Legacy paths at project root (for older scripts)
LEGACY_KNOWN_FACES = PROJECT_ROOT / "known_faces"
LEGACY_UNKNOWN_FACES = PROJECT_ROOT / "unknown_faces"
LEGACY_ATTENDANCE_IMAGES = PROJECT_ROOT / "attendance_images"


def ensure_data_dirs() -> None:
    """Create data and face storage directories."""
    for path in (
        DATA_DIR,
        KNOWN_FACES_DIR,
        UNKNOWN_FACES_DIR,
        ATTENDANCE_IMAGES_DIR,
        CONFIG_DIR,
    ):
        path.mkdir(parents=True, exist_ok=True)
