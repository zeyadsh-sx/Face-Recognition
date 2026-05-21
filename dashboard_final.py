"""Backward-compatible launcher — use web.dashboard_final or run_dashboard.py."""
from web.dashboard_final import app  # noqa: F401

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
