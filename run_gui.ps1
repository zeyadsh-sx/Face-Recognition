# Activate venv and run GUI
& "$PSScriptRoot/.venv/Scripts/Activate.ps1"
Write-Host "Starting GUI Application..." -ForegroundColor Green
python gui_basic_mysql.py
