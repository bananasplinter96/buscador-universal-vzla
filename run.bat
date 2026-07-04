@echo off
REM Arranque rapido en Windows: crea el entorno si no existe, instala y lanza.
setlocal
cd /d "%~dp0"

if not exist ".venv\" (
  echo Creando entorno virtual...
  python -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt

python app.py %*
