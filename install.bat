@echo off
:: ─────────────────────────────────────────────────────────────────────────────
:: Portfolio Tracker — Installatie (Windows)
:: Gebruik: dubbelklik op install.bat
:: ─────────────────────────────────────────────────────────────────────────────

echo.
echo  ==========================================
echo        Portfolio Tracker Installatie
echo  ==========================================
echo.

:: ── Zoek Python ───────────────────────────────────────────────────────────────
python --version >nul 2>&1
if %errorlevel% neq 0 goto :install_python

python -c "import sys; sys.exit(0 if sys.version_info >= (3,9) else 1)" 2>nul
if %errorlevel% neq 0 goto :install_python

goto :python_ok

:install_python
echo  Python 3.9+ niet gevonden. Proberen te installeren via winget...
winget --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  Installeer Python handmatig: https://www.python.org/downloads/
    echo  Vink "Add Python to PATH" aan tijdens de installatie.
    echo.
    pause
    exit /b 1
)

echo  Python installeren via winget (even geduld)...
winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements
if %errorlevel% neq 0 (
    echo.
    echo  Automatische installatie mislukt.
    echo  Installeer Python handmatig: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

set "PATH=%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python312\Scripts;%PATH%"

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  Sluit dit venster, open een nieuw venster en start install.bat opnieuw.
    echo.
    pause
    exit /b 1
)

:python_ok
for /f "tokens=*" %%i in ('python --version') do set PYVER=%%i
echo  Gevonden: %PYVER%

:: ── Paden ─────────────────────────────────────────────────────────────────────
set "ROOT_DIR=%~dp0"
set "APP_DIR=%ROOT_DIR%app"
set "VENV_DIR=%APP_DIR%\.venv"

:: ── Virtualenv aanmaken ───────────────────────────────────────────────────────
if exist "%VENV_DIR%" (
    echo  Bestaande omgeving gevonden, wordt hergebruikt.
) else (
    echo  Virtuele omgeving aanmaken...
    python -m venv "%VENV_DIR%"
    echo  Virtuele omgeving aangemaakt.
)

:: ── Dependencies installeren ──────────────────────────────────────────────────
echo  Dependencies installeren (kan even duren)...
"%VENV_DIR%\Scripts\pip" install --quiet --upgrade pip
"%VENV_DIR%\Scripts\pip" install --quiet -r "%APP_DIR%\requirements.txt"
echo  Alle packages geinstalleerd.

:: ── Mappen aanmaken ───────────────────────────────────────────────────────────
if not exist "%APP_DIR%\cache" mkdir "%APP_DIR%\cache"
if not exist "%APP_DIR%\data"  mkdir "%APP_DIR%\data"

:: ── Launch-script aanmaken ────────────────────────────────────────────────────
(
echo @echo off
echo cd /d "%%~dp0app"
echo echo Portfolio Tracker starten...
echo echo Open je browser op: http://localhost:8501
echo echo Stoppen: sluit dit venster
echo echo.
echo .venv\Scripts\streamlit run app.py --server.headless true
echo pause
) > "%ROOT_DIR%start.bat"

echo.
echo  ==========================================
echo        Installatie geslaagd!
echo  ==========================================
echo.
echo  Starten: dubbelklik op start.bat
echo.
pause
