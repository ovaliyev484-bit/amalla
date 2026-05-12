@echo off
set "SCRIPT_PATH=%~dp0RUN_APP.bat"
set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT_NAME=Malik_AI.lnk"

echo Creating startup shortcut...
powershell -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%STARTUP_FOLDER%\%SHORTCUT_NAME%');$s.TargetPath='%SCRIPT_PATH%';$s.WorkingDirectory='%~dp0';$s.Save()"

if %errorlevel% equ 0 (
    echo [SUCCESS] Malik AI endi kompyuter yonishi bilan avtomatik ishga tushadi.
) else (
    echo [ERROR] Avtomatik ishga tushirishni sozlashda xatolik yuz berdi.
)
pause
