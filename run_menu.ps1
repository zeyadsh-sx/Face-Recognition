# Activate venv and run Menu
& "$PSScriptRoot/.venv/Scripts/Activate.ps1"
Write-Host "Starting Main Menu..." -ForegroundColor Green
python start_mysql_app.py
