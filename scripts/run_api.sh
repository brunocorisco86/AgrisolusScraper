#!/bin/bash
# Wrapper utilitário para iniciar o servidor API/Frontend do Silo Monitor (Porta 8090)

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR" || exit 1

# Ativa o ambiente virtual local
source env/bin/activate

# Configura o PYTHONPATH
export PYTHONPATH="$PROJECT_DIR"

# Executa o servidor FastAPI
echo "Iniciando servidor de Monitoramento na porta 8090..."
echo "Acesse o painel em: http://localhost:8090"
python src/api/main.py
