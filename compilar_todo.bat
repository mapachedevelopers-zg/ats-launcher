@echo off
chcp 65001 >nul
echo ===================================================
echo   Compilador y Empaquetador Launcher de Chasis
echo ===================================================
python compilar_todo.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] La compilacion ha fallado.
    pause
    exit /b %ERRORLEVEL%
)
echo.
pause
