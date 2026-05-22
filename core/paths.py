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
REPORTS_DIR = DATA_DIR / "reports"

UNKNOWN_COUNTER_FILE = DATA_DIR / ".unknown_counter.json"
SYSTEM_SETTINGS_FILE = CONFIG_DIR / "system_settings.json"
EMAIL_CONFIG_FILE = CONFIG_DIR / "email_config.json"

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
        REPORTS_DIR,
        CONFIG_DIR,
    ):
        # If a non-directory file exists where we expect a directory, rename it safely
        if path.exists() and not path.is_dir():
            # create a unique backup name
            backup = path.with_name(path.name + '.bak')
            i = 1
            while backup.exists():
                backup = path.with_name(f"{path.name}.bak{i}")
                i += 1
            path.rename(backup)
            print(f"Warning: existing file '{path}' renamed to '{backup}' to create directory.")

        path.mkdir(parents=True, exist_ok=True)
