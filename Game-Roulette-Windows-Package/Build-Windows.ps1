$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot

Write-Host 'Game Roulette - Windows build' -ForegroundColor Cyan
Write-Host 'This builds a normal user-level app. It does not request administrator access.'

$python = Get-Command py -ErrorAction SilentlyContinue
if ($python) {
    & py -3 --version
    if ($LASTEXITCODE -ne 0) { throw 'Python 3 was not found. Install Python 3.10+ from https://www.python.org/downloads/windows/ and try again.' }
    & py -3 -m venv .venv
} else {
    $python = Get-Command python -ErrorAction SilentlyContinue
    if (-not $python) { throw 'Python was not found. Install Python 3.10+ from https://www.python.org/downloads/windows/ and try again.' }
    & python -m venv .venv
}
if ($LASTEXITCODE -ne 0) { throw 'Could not create the local Python environment.' }

$venvPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
& $venvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw 'Could not update pip.' }
& $venvPython -m pip install -r requirements.txt pyinstaller
if ($LASTEXITCODE -ne 0) { throw 'Could not install build dependencies. Check your internet connection.' }

if (Test-Path (Join-Path $PSScriptRoot 'build')) { Remove-Item (Join-Path $PSScriptRoot 'build') -Recurse -Force }
if (Test-Path (Join-Path $PSScriptRoot 'dist\Game Roulette')) { Remove-Item (Join-Path $PSScriptRoot 'dist\Game Roulette') -Recurse -Force }

& $venvPython -m PyInstaller --noconfirm --clean --windowed --onedir `
    --name 'Game Roulette' `
    --icon (Join-Path $PSScriptRoot 'game_roulette_icon.ico') `
    --add-data ((Join-Path $PSScriptRoot 'game_roulette_icon.png') + ';.') `
    --manifest (Join-Path $PSScriptRoot 'app.manifest') `
    --collect-all PySide6 --collect-all PIL `
    (Join-Path $PSScriptRoot 'game_roulette.py')
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller failed to build Game Roulette.' }

Write-Host ''
Write-Host 'Build successful.' -ForegroundColor Green
Write-Host ('Executable: ' + (Join-Path $PSScriptRoot 'dist\Game Roulette\Game Roulette.exe'))
Write-Host 'Copy the entire "dist\Game Roulette" folder to where you want to keep the app.'
