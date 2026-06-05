#!/bin/bash
# Cria/usa um ambiente virtual, instala as dependências e abre a interface gráfica.
set -e

cd "$(dirname "$0")"

if [ ! -d venv ]; then
    echo "🐍 Criando ambiente virtual..."
    python3 -m venv venv
fi

echo "📦 Instalando dependências..."
venv/bin/pip install --quiet --upgrade pip
venv/bin/pip install --quiet -r requirements.txt

echo "🚀 Abrindo o FileConverter..."
venv/bin/python gui.py
