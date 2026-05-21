"""Backward-compatible launcher — use gui.gui_simple_mysql or run_gui.py."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from gui.gui_simple_mysql import SimpleMySQLAttendanceGUI, main  # noqa: F401

if __name__ == "__main__":
    main()
