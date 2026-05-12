@echo off
title SAFIYA Mahiru - Startup Manager
color 0b
cls

echo ======================================================
echo           SAFIYA Mahiru - AUTO SETUP & RUN
echo ======================================================
echo.

set "APP_DIR=%~dp0"
cd /d "%APP_DIR%"

:: Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python topilmadi! Iltimos, Python o'rnating.
    pause
    exit /b 1
)

:: Check for Virtual Environment
if not exist ".venv" (
    echo [INFO] Virtual muhit (.venv) yaratilmoqda...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERROR] Virtual muhit yaratib bo'lmadi.
        pause
        exit /b 1
    )
    echo [OK] Virtual muhit yaratildi.
)

:: Activate and Update
echo [INFO] Kutubxonalar tekshirilmoqda va o'rnatilmoqda...
call .venv\Scripts\activate
python -m pip install --upgrade pip >nul
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Kutubxonalarni o'rnatishda xatolik yuz berdi.
    pause
    exit /b 1
)

:: Check Playwright
python -m playwright install --help >nul 2>&1
if %errorlevel% == 0 (
    echo [INFO] Playwright brauzerlari tekshirilmoqda...
    python -m playwright install chromium
)

echo.
echo [OK] Hammasi tayyor! SAFIYA ishga tushmoqda...
echo.
echo ======================================================

:: Run the app
python main.py

if %errorlevel% neq 0 (
    echo.
    echo [!] Dastur to'xtadi. Xatolik borligini tekshiring.
    pause
)
