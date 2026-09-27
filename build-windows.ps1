param([string]$Python = "python")
$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    & $Python -c "import sys,ssl; assert sys.version_info >= (3,13) and ssl.HAS_PSK, 'Python 3.13+ with TLS-PSK is required'"
    if ($LASTEXITCODE) { throw 'Python prerequisite check failed' }
    & $Python -m venv .venv-win
    if ($LASTEXITCODE) { throw 'Virtual environment creation failed' }
    $buildPython = Join-Path $PSScriptRoot '.venv-win\Scripts\python.exe'
    & $buildPython -m pip install -r requirements-windows.lock
    if ($LASTEXITCODE) { throw 'Dependency installation failed' }
    & $buildPython tests\test_secure_link.py
    if ($LASTEXITCODE) { throw 'TLS regression checks failed' }
    & $buildPython -m PyInstaller --noconfirm --distpath dist --workpath build win_app\build.spec
    if ($LASTEXITCODE) { throw 'Build failed' }
    Write-Output (Join-Path $PSScriptRoot 'dist\SideBySide.exe')
} finally { Pop-Location }
