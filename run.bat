@echo off
cd /d "%~dp0"
echo ==============================================
echo   Iniciando Buscador Universal en Local
echo ==============================================

where python >nul 2>nul
if %errorlevel% EQU 0 (
    set PYTHON_CMD=python
    goto :python_ok
)

where py >nul 2>nul
if %errorlevel% EQU 0 (
    set PYTHON_CMD=py
    goto :python_ok
)

echo [ERROR] No se encontro Python en este equipo.
echo Instala Python desde https://www.python.org/ y marca la casilla "Add Python to PATH".
pause
exit /b 1

:python_ok
echo [INFO] Python detectado: %PYTHON_CMD%

if exist .venv\ (
    goto :venv_ok
)

echo [INFO] Creando entorno virtual...
%PYTHON_CMD% -m venv .venv
if %errorlevel% NEQ 0 (
    echo [ERROR] No se pudo crear el entorno virtual.
    pause
    exit /b 1
)

:venv_ok
echo [INFO] Activando entorno...
call .venv\Scripts\activate.bat
if %errorlevel% NEQ 0 (
    echo [ERROR] No se pudo activar el entorno.
    pause
    exit /b 1
)

echo [INFO] Actualizando dependencias...
python -m pip install -r requirements.txt
if %errorlevel% NEQ 0 (
    echo [ERROR] Error al instalar requirements.txt.
    pause
    exit /b 1
)

echo [INFO] Abriendo navegador...
start http://127.0.0.1:5000

echo [INFO] Iniciando app.py...
python app.py
if %errorlevel% NEQ 0 (
    echo [ERROR] La aplicacion se detuvo con un error.
    pause
)