#!/bash
# -----------------------------------------------------------------------------
# Script: 5_test_offline.sh
# Descrição: Executa a simulação de perda de rede e salvamento no SQLite local.
# -----------------------------------------------------------------------------

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_DIR" || exit 1

LOG_FILE="$PROJECT_DIR/deploy_test_offline.log"

echo "=================================================="
echo "      PASSO 5: SIMULAÇÃO DE QUEDA DE REDE         "
echo "=================================================="
echo "Logs gravados em: $LOG_FILE"
echo ""

# Redireciona a execução para tela e arquivo de log
exec > >(tee -a "$LOG_FILE") 2>&1

# 1. Verifica se o ambiente virtual está disponível
if [ -d "env" ]; then
    echo "🚀 Rodando teste de simulação offline (fallback SQLite)..."
    ./env/bin/python scripts/simulate_offline.py
else
    echo "❌ ERRO: Ambiente Python 'env' não encontrado. Execute o Passo 1 primeiro."
    exit 1
fi

echo "=================================================="
