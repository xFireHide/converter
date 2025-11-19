#!/bin/bash

# Script para matar processos na porta, ativar venv e rodar o app

# Define a porta (padrão: 8080)
PORT=${PORT:-8080}

echo "🔍 Procurando processos na porta $PORT..."

# Encontra e mata processos na porta especificada
# macOS/Linux
if command -v lsof &> /dev/null; then
    PID=$(lsof -ti:$PORT)
    if [ ! -z "$PID" ]; then
        echo "🛑 Matando processo(es) na porta $PORT (PID: $PID)..."
        kill -9 $PID 2>/dev/null
        sleep 1
        echo "✅ Processo(s) finalizado(s)"
    else
        echo "ℹ️  Nenhum processo encontrado na porta $PORT"
    fi
else
    echo "⚠️  lsof não encontrado. Tentando com fuser..."
    if command -v fuser &> /dev/null; then
        fuser -k $PORT/tcp 2>/dev/null
        echo "✅ Tentativa de finalizar processos na porta $PORT"
    else
        echo "⚠️  Não foi possível encontrar processos. Continuando..."
    fi
fi

echo ""
echo "🐍 Ativando ambiente virtual..."
source venv/bin/activate

echo ""
echo "🚀 Iniciando servidor Flask na porta $PORT..."
echo "📝 Acesse: http://localhost:$PORT"
echo "🛑 Para parar: Ctrl + C"
echo ""

python app.py


