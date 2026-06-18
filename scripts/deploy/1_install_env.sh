#!/bin/bash
# -----------------------------------------------------------------------------
# Script: 1_install_env.sh
# Descrição: Cria o ambiente virtual Python e instala as dependências.
# -----------------------------------------------------------------------------

# Determina o diretório raiz do projeto (um nível acima de scripts/deploy)
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_DIR" || exit 1

LOG_FILE="$PROJECT_DIR/deploy_install.log"

echo "=================================================="
echo "      PASSO 1: INSTALAÇÃO DO AMBIENTE PYTHON      "
echo "=================================================="
echo "Diretório do projeto: $PROJECT_DIR"
echo "Logs gravados em: $LOG_FILE"
echo ""

# Redireciona stdout e stderr para o terminal e para o arquivo de log
exec > >(tee -a "$LOG_FILE") 2>&1

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Iniciando instalação..."

# 1. Verifica se o Python 3 está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ ERRO: python3 não está instalado no sistema."
    exit 1
fi

# 2. Cria o ambiente virtual 'env'
if [ -d "env" ]; then
    echo "⚠️ Pasta 'env' já existe. Atualizando pacotes..."
else
    echo "📦 Criando ambiente virtual Python ('env')..."
    python3 -m venv env
    if [ $? -ne 0 ]; then
        echo "❌ ERRO ao criar venv. Certifique-se de que python3-venv está instalado."
        exit 1
    fi
fi

# 3. Ativa o ambiente virtual
echo "🔌 Ativando o ambiente virtual..."
source env/bin/activate

# 4. Atualiza o pip
echo "🚀 Atualizando pip..."
pip install --upgrade pip

# 5. Instala os requisitos
if [ -f "requirements.txt" ]; then
    echo "📥 Instalando dependências do requirements.txt..."
    pip install -r requirements.txt
    if [ $? -eq 0 ]; then
        echo "✅ SUCESSO: Ambiente Python instalado com sucesso!"
    else
        echo "❌ ERRO na instalação das dependências Python."
        exit 1
    fi
else
    echo "❌ ERRO: requirements.txt não encontrado."
    exit 1
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Passo 1 Concluído!"
echo "=================================================="
