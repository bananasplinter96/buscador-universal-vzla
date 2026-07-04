#!/usr/bin/env bash
# Arranque rápido en Linux/macOS: crea el entorno si no existe, instala y lanza.
set -e
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  echo "Creando entorno virtual..."
  python3 -m venv .venv
fi
source .venv/bin/activate
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt

python app.py "$@"