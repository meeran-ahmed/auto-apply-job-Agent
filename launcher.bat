@echo off
title Auto Job - Autonomous Application Agent
echo ======================================================================
echo             ⚡ AUTO JOB: APPLICATION AGENT
echo                      Free & Open Source Edition
echo ======================================================================
echo.

:: Check if .venv exists
if exist ".venv\Scripts\python.exe" (
    echo [INFO] Starting Auto Job with virtual environment...
    start "" ".venv\Scripts\pythonw.exe" gui_main.py
    if %errorlevel% neq 0 (
        ".venv\Scripts\python.exe" gui_main.py
    )
    exit /b 0
)

:: Fallback to system python
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] Starting OmniSwarm with system Python...
    start "" pythonw gui_main.py
    if %errorlevel% neq 0 (
        python gui_main.py
    )
    exit /b 0
)

echo [ERROR] Python was not found on your system!
echo Please install Python 3.10+ from https://www.python.org/downloads/
echo Make sure to check "Add Python to PATH" during installation.
pause
