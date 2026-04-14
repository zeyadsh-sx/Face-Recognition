@echo off
REM Run Main Menu Launcher
cd /d "%~dp0"
echo Starting Main Menu...
.\venv\Scripts\python.exe start_mysql_app.py
pause
