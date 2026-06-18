#!/bin/bash
# -----------------------------------------------------------------------------
# Script: 3_test_db.sh
# Descrição: Executa o script de comissionamento de rede e conexão Supabase.
# -----------------------------------------------------------------------------

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_DIR" || exit 1

LOG_FILE="$PROJECT_DIR/deploy_test_db.log"

echo "=================================================="
echo "      PASSO 3: COMISSIONAMENTO DE REDE E BANCO    "
echo "=================================================="
echo "Logs gravados em: $LOG_FILE"
echo ""

# Redireciona a execução para tela e arquivo de log
exec > >(tee -a "$LOG_FILE") 2>&1

# 1. Verifica se o .env foi configurado
if [ ! -f ".env" ]; then
    echo "❌ ERRO: Arquivo .env não encontrado. Execute o Passo 2 primeiro."
    exit 1
fi

# 2. Executa o comissionamento do banco de dados
if [ -d "env" ]; then
    echo "🚀 Executando comissionamento do Supabase..."
    ./env/bin/python scripts/comissioning.py
else
    echo "❌ ERRO: Ambiente Python 'env' não encontrado. Execute o Passo 1 primeiro."
    exit 1
fi

echo "=================================================="
