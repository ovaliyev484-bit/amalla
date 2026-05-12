@echo off
setlocal EnableExtensions

set "APP_DIR=%~dp0"
set "SOURCE=%APP_DIR%start_safiya_once.bat"
set "STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "TARGET=%STARTUP_DIR%\start_safiya_once.bat"

if not exist "%SOURCE%" (
    echo start_safiya_once.bat topilmadi.
    pause
    exit /b 1
)

if not exist "%STARTUP_DIR%" mkdir "%STARTUP_DIR%" >nul 2>&1
(
    echo @echo off
    echo call "%SOURCE%"
) > "%TARGET%"

echo Tayyor: SAFIYA kompyuter yoqilganda 1 marta avtomatik ishga tushadi.
echo Startup fayl: "%TARGET%"
pause
