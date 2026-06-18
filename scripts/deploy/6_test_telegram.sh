#!/bin/bash
# -----------------------------------------------------------------------------
# Script: 6_test_telegram.sh
# Descrição: Executa a validação de envio de mensagens do Telegram Bot.
# -----------------------------------------------------------------------------

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_DIR" || exit 1

LOG_FILE="$PROJECT_DIR/deploy_test_telegram.log"

echo "=================================================="
echo "      PASSO 6: COMISSIONAMENTO DO TELEGRAM BOT    "
echo "=================================================="
echo "Logs gravados em: $LOG_FILE"
echo ""

# Redireciona a execução para tela e arquivo de log
exec > >(tee -a "$LOG_FILE") 2>&1

# 1. Verifica se o ambiente virtual está disponível
if [ -d "env" ]; then
    echo "🚀 Rodando teste de envio de mensagens do Telegram..."
    ./env/bin/python scripts/test_telegram.py
else
    echo "❌ ERRO: Ambiente Python 'env' não encontrado. Execute o Passo 1 primeiro."
    exit 1
fi

echo "=================================================="
