# Face Recognition — إعداد Python 3.11 (مطلوب للتعرف على الوجه)
# شغّل:  powershell -ExecutionPolicy Bypass -File setup_python311.ps1

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
Set-Location $ProjectRoot

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Face Recognition - Python 3.11 Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# تحقق من وجود Python 3.11
$py311 = $null
try {
    $out = & py -3.11 -c "import sys; print(sys.version)" 2>&1
    if ($LASTEXITCODE -eq 0) {
        $py311 = "py -3.11"
        Write-Host "[OK] Python 3.11 found: $out" -ForegroundColor Green
    }
} catch {}

if (-not $py311) {
    Write-Host "[X] Python 3.11 NOT installed on this PC." -ForegroundColor Red
    Write-Host ""
    Write-Host "You only have Python 3.14 (face_recognition does NOT work on 3.14)." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Steps:" -ForegroundColor White
    Write-Host "  1. Download Python 3.11.9 from:" -ForegroundColor White
    Write-Host "     https://www.python.org/downloads/release/python-3119/" -ForegroundColor Gray
    Write-Host "  2. Run installer -> check 'Add python.exe to PATH'" -ForegroundColor White
    Write-Host "  3. Run this script again" -ForegroundColor White
    Write-Host ""
    Write-Host "Current interpreters:" -ForegroundColor White
    & py -0p
    exit 1
}

$venvPath = Join-Path $ProjectRoot "venv311"
if (-not (Test-Path (Join-Path $venvPath "Scripts\python.exe"))) {
    Write-Host "[*] Creating venv311 ..." -ForegroundColor Yellow
    & py -3.11 -m venv $venvPath
}

$python = Join-Path $venvPath "Scripts\python.exe"
$pip = Join-Path $venvPath "Scripts\pip.exe"

Write-Host "[*] Upgrading pip ..." -ForegroundColor Yellow
& $python -m pip install --upgrade pip

Write-Host "[*] Installing requirements ..." -ForegroundColor Yellow
& $pip install -r (Join-Path $ProjectRoot "requirements.txt")

Write-Host "[*] Installing dlib (face recognition) ..." -ForegroundColor Yellow
& $pip install cmake
$dlibOk = $false
try {
    & $pip install dlib-bin 2>$null
    & $python -c "import dlib; print('dlib', dlib.__version__)"
    $dlibOk = ($LASTEXITCODE -eq 0)
} catch {}

if (-not $dlibOk) {
    Write-Host "[*] Trying pip install dlib (may need Visual Studio Build Tools) ..." -ForegroundColor Yellow
    & $pip install dlib
}

Write-Host "[*] Installing face-recognition ..." -ForegroundColor Yellow
& $pip install face-recognition

Write-Host ""
Write-Host "[*] Verification ..." -ForegroundColor Yellow
& $python -c @"
import sys
print('Python:', sys.version)
try:
    import face_recognition
    import dlib
    print('face_recognition: OK')
    print('dlib:', dlib.__version__)
except ImportError as e:
    print('FAIL:', e)
    sys.exit(1)
"@

if ($LASTEXITCODE -ne 0) {
    Write-Host "[X] Face recognition libraries failed." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Setup complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Always activate before running the app:" -ForegroundColor White
Write-Host "  .\venv311\Scripts\Activate.ps1" -ForegroundColor Cyan
Write-Host "  python start_mysql_app.py" -ForegroundColor Cyan
Write-Host ""
Write-Host "Or use:" -ForegroundColor White
Write-Host "  .\run_gui_311.ps1" -ForegroundColor Cyan
