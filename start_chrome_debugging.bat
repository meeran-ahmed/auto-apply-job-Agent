@echo off
title Auto Job - Chrome Live Session Bridge
echo ============================================================
echo   AUTO JOB: Launching Chrome with Remote Debugging (9222)
echo   Profile: meeranahmed17@gmail.com
echo ============================================================
echo.
echo Closing existing background Chrome tabs to attach debugging port...
taskkill /F /IM chrome.exe >nul 2>&1
timeout /t 2 /nobreak >nul

set CHROME_PATH="C:\Program Files\Google\Chrome\Application\chrome.exe"
if not exist %CHROME_PATH% set CHROME_PATH="C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
if not exist %CHROME_PATH% set CHROME_PATH="%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"

set USER_DATA="%LOCALAPPDATA%\Google\Chrome\User Data"

echo Starting Chrome with debugging enabled...
start "" %CHROME_PATH% --remote-debugging-port=9222 --user-data-dir=%USER_DATA%

echo.
echo [SUCCESS] Chrome is now running in Agent Debugging Mode!
echo Your Auto Job multi-portal swarm can now automate LinkedIn, Naukri, Indeed, Cutshort, and Wellfound directly.
timeout /t 3
