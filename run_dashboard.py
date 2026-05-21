#!/usr/bin/env python3
"""Start web attendance dashboard."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from web.dashboard_final import app

if __name__ == "__main__":
    print("Dashboard: http://127.0.0.1:5000")
    app.run(debug=True, host="0.0.0.0", port=5000)
