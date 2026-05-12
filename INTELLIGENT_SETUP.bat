@echo off
title SAFIYA Mahiru - Intelligent Setup Manager
color 0b
cls

echo ======================================================
echo       SAFIYA Mahiru - TIZIMNI TAYYORLASH VA O'RNATISH
echo ======================================================
echo.

:: 1. Pythonni tekshirish va o'rnatish
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Python topilmadi. O'rnatish boshlanmoqda...
    winget install Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements
    if %errorlevel% neq 0 (
        echo [X] Pythonni o'rnatib bo'lmadi. Iltimos, o'zingiz o'rnating.
        pause
        exit /b 1
    )
    echo [OK] Python muvaffaqiyatli o'rnatildi.
    echo [!] Iltimos, ushbu oynani yopib, qaytadan oching (Path yangilanishi uchun).
    pause
    exit /b 0
) else (
    echo [OK] Python topildi.
)

:: 2. VS Code ni tekshirish va o'rnatish
code --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [?] VS Code (Kod muharriri) topilmadi. O'rnatishni xohlaysizmi? (Y/N)
    set /p install_code=Choice: 
    if /i "%install_code%"=="Y" (
        echo [!] VS Code o'rnatilmoqda...
        winget install Microsoft.VisualStudioCode --silent --accept-package-agreements --accept-source-agreements
        echo [OK] VS Code o'rnatildi.
    )
) else (
    echo [OK] VS Code topildi.
)

:: 3. Virtual muhit va kutubxonalar
echo.
echo [INFO] Loyiha muhitini sozlash...
if not exist ".venv" (
    python -m venv .venv
)
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt

:: 4. Ruxsat so'rash va ishga tushirish
echo.
echo ======================================================
echo [?] Hamma narsa tayyor. Dasturni hozir ishga tushiraymi? (Y/N)
set /p run_now=Tanlovingiz: 

if /i "%run_now%"=="Y" (
    echo [!] Dastur ishga tushmoqda...
    python main.py
) else (
    echo [OK] Dastur ishga tushirilmadi. Uni keyinchalik 'RUN_APP.bat' orqali ochishingiz mumkin.
    pause
)
