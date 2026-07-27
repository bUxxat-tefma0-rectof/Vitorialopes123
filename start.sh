#!/bin/bash

echo "🐕 DOGUINHA STORE BOT"
echo "====================="
echo ""

if [ ! -f .env ]; then
    echo "❌ Arquivo .env nao encontrado!"
    echo "📝 Crie o arquivo .env com:"
    echo "BOT_TOKEN=SEU_TOKEN"
    echo "ADMIN_ID=SEU_ID"
    echo "MERCADO_PAGO_ACCESS_TOKEN=SEU_TOKEN"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 nao encontrado!"
    exit 1
fi

echo "📦 Instalando dependencias..."
pip3 install -r requirements.txt

echo ""
echo "🚀 Iniciando bot..."
python3 run.py
