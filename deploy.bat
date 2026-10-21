@echo off
title DataVision AI — Deploy to Render (Public)
color 0B
echo.
echo  ============================================================
echo   DataVision AI — Public Deployment Script
echo   Deploys to Render.com via GitHub (FREE)
echo  ============================================================
echo.

:: ── STEP 1: Check Git ────────────────────────────────────────
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [!] Git is NOT installed.
    echo.
    echo  Please install Git from: https://git-scm.com/download/win
    echo  After installing, re-run this script.
    echo.
    start https://git-scm.com/download/win
    pause
    exit /b 1
)
echo  [✓] Git found.

:: ── STEP 2: Ask for GitHub repo URL ──────────────────────────
echo.
echo  ──────────────────────────────────────────────────────────
echo   STEP 1: Create a GitHub repository
echo  ──────────────────────────────────────────────────────────
echo   1. Go to https://github.com/new
echo   2. Name it: datavision-ai
echo   3. Set to PUBLIC
echo   4. Do NOT add README (leave blank)
echo   5. Click "Create repository"
echo   6. Copy the HTTPS URL (looks like: https://github.com/YourName/datavision-ai.git)
echo  ──────────────────────────────────────────────────────────
echo.
set /p REPO_URL="  Paste your GitHub repo URL here: "

if "%REPO_URL%"=="" (
    echo  [ERROR] No URL entered. Exiting.
    pause
    exit /b 1
)

:: ── STEP 3: Git init + push ───────────────────────────────────
echo.
echo  [2/4] Initialising Git and pushing code...

git init
git config user.email "datavision@project.com"
git config user.name "DataVision AI"
git add .
git commit -m "Initial commit: DataVision AI Major Project"
git branch -M main
git remote add origin %REPO_URL%
git push -u origin main

if %errorlevel% neq 0 (
    echo.
    echo  [ERROR] Push failed. Common fixes:
    echo    - Make sure the GitHub URL is correct
    echo    - Make sure you're logged into GitHub in your browser
    echo    - Try: git remote remove origin ^& re-run
    pause
    exit /b 1
)

echo.
echo  [✓] Code pushed to GitHub successfully!

:: ── STEP 4: Open Render deploy page ──────────────────────────
echo.
echo  ──────────────────────────────────────────────────────────
echo   STEP 3: Deploy on Render.com (FREE)
echo  ──────────────────────────────────────────────────────────
echo   Opening Render.com for you...
echo.
echo   Follow these steps on Render:
echo    1. Sign up / Log in at render.com (use GitHub login)
echo    2. Click "New" → "Web Service"
echo    3. Connect your GitHub account
echo    4. Select: datavision-ai
echo    5. Settings auto-fill from render.yaml ✓
echo    6. Click "Create Web Service"
echo    7. Wait ~3 minutes — your live URL appears at the top!
echo  ──────────────────────────────────────────────────────────
echo.
start https://dashboard.render.com/select-repo?type=web

echo.
echo  ============================================================
echo   ALL DONE! Your app will be live at:
echo   https://datavision-ai.onrender.com  (or similar URL)
echo  ============================================================
echo.
pause
