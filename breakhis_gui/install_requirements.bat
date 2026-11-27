@echo off
rem ======================================================================
rem  Double-click this file once to install the libraries the GUI needs.
rem ======================================================================
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if not errorlevel 1 (
    set "PY=py"
) else (
    set "PY=python"
)

%PY% -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo Installation failed. Read the messages above.
    echo If Python is not installed, get it from https://www.python.org/downloads/
) else (
    echo.
    echo Done. Now double-click start_gui.bat to open the program.
)
echo.
pause
