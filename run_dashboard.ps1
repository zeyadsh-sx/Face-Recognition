# Activate venv and run Dashboard
& "$PSScriptRoot/.venv/Scripts/Activate.ps1"
Write-Host "Starting Flask Dashboard..."
Write-Host "Open your browser at: http://localhost:5000" -ForegroundColor Green
python dashboard_final.py
