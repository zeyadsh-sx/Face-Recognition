@echo off
REM Run GUI Application
cd /d "%~dp0"
echo Starting GUI Application...
.\venv\Scripts\python.exe gui_basic_mysql.py
pause
