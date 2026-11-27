@echo off
rem ======================================================================
rem  Double-click this file to start the BreaKHis Classifier on Windows.
rem  Run install_requirements.bat once before the first start.
rem ======================================================================
setlocal
cd /d "%~dp0"

rem --- Find Python: the "py" launcher from python.org, or "python" ---------
where py >nul 2>nul
if not errorlevel 1 (
    set "PY=py"
    set "PYW=pyw"
    goto check
)
where python >nul 2>nul
if not errorlevel 1 (
    set "PY=python"
    set "PYW=pythonw"
    goto check
)
goto no_python

:check
rem --- Make sure Python really runs and the libraries are installed -------
%PY% --version >nul 2>nul
if errorlevel 1 goto no_python
%PY% -c "import tkinter, PIL.ImageTk" >nul 2>nul
if errorlevel 1 goto missing_libraries

rem --- Start the GUI without a black console window -------------------------
where %PYW% >nul 2>nul
if errorlevel 1 set "PYW=%PY%"
start "" %PYW% gui.py
exit /b 0

:no_python
echo Python was not found on this computer.
echo Please install Python 3.9 or newer from https://www.python.org/downloads/
echo and tick "Add python.exe to PATH" on the first screen of the installer.
echo.
pause
exit /b 1

:missing_libraries
echo Python is installed, but the libraries this program needs are missing.
echo Please double-click install_requirements.bat first, then start this file again.
echo.
pause
exit /b 1
