# تشغيل GUI باستخدام Python 3.11 (venv311)
$root = $PSScriptRoot
$py = Join-Path $root "venv311\Scripts\python.exe"
if (-not (Test-Path $py)) {
    Write-Host "venv311 not found. Run: .\setup_python311.ps1" -ForegroundColor Red
    exit 1
}
Set-Location $root
& $py start_mysql_app.py
