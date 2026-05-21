#!/usr/bin/env python3
"""Start desktop attendance GUI."""
import subprocess
import sys

if __name__ == "__main__":
    subprocess.run([sys.executable, "start_mysql_app.py"], check=False)
