@echo off
title DataVision AI — Setup ^& Launch
color 0A
echo.
echo  =============================================
echo   DataVision AI — Intelligent Analytics
echo   AI ^& Data Science Major Project
echo  =============================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Python not found. Install Python 3.10+ from python.org
    pause
    exit /b 1
)

echo  [1/3] Installing dependencies...
pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo  [ERROR] Failed to install packages. Check your internet connection.
    pause
    exit /b 1
)

echo  [2/3] Dependencies installed successfully!
echo  [3/3] Starting DataVision AI server...
echo.
echo  Open your browser at:  http://localhost:5000
echo  Press Ctrl+C to stop the server.
echo.

python app.py

pause
