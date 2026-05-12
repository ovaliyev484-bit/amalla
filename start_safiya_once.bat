@echo off
setlocal EnableExtensions

set "APP_DIR=%~dp0"
set "APP_NAME=SAFIYA Mahiru"
set "MAIN_PY=%APP_DIR%main.py"
set "LOCK_FILE=%TEMP%\safiya_mahiru_startup.lock"
set "LOG_DIR=%APP_DIR%logs"
set "LOG_FILE=%LOG_DIR%\startup.log"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%" >nul 2>&1

for /f "usebackq delims=" %%B in (`powershell -NoProfile -ExecutionPolicy Bypass -Command "(Get-CimInstance Win32_OperatingSystem).LastBootUpTime.ToString('yyyyMMddHHmmss')"`) do set "BOOT_ID=%%B"
if not defined BOOT_ID set "BOOT_ID=%DATE%_%TIME%"

set "IS_RUNNING=0"
for /f "usebackq delims=" %%R in (`powershell -NoProfile -ExecutionPolicy Bypass -Command "$app=(Resolve-Path '%MAIN_PY%').Path; $p=Get-CimInstance Win32_Process | Where-Object { $_.Name -in @('python.exe','pythonw.exe') -and $_.CommandLine -and $_.CommandLine -like ('*' + $app + '*') }; if($p){'1'}else{'0'}"`) do set "IS_RUNNING=%%R"

if exist "%LOCK_FILE%" (
    set /p LAST_BOOT=<"%LOCK_FILE%"
    if "%LAST_BOOT%"=="%BOOT_ID%" (
        if "%IS_RUNNING%"=="1" (
            echo [%DATE% %TIME%] Already started for this boot.>>"%LOG_FILE%"
            exit /b 0
        )
        echo [%DATE% %TIME%] Old lock found, but app is not running. Starting again.>>"%LOG_FILE%"
    )
)

set "PYTHON_EXE=%APP_DIR%.venv\Scripts\pythonw.exe"
if not exist "%PYTHON_EXE%" set "PYTHON_EXE=%APP_DIR%.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" set "PYTHON_EXE=pythonw.exe"

if "%IS_RUNNING%"=="1" (
    echo %BOOT_ID%>"%LOCK_FILE%"
    echo [%DATE% %TIME%] %APP_NAME% is already running.>>"%LOG_FILE%"
    exit /b 0
)

echo %BOOT_ID%>"%LOCK_FILE%"
echo [%DATE% %TIME%] Starting %APP_NAME%.>>"%LOG_FILE%"

cd /d "%APP_DIR%"
start "%APP_NAME%" "%PYTHON_EXE%" "%MAIN_PY%"

exit /b 0
