@echo off
REM Run Flask Dashboard
cd /d "%~dp0"
echo Starting Flask Dashboard...
echo Open your browser at: http://localhost:5000
.\venv\Scripts\python.exe dashboard_final.py
pause
