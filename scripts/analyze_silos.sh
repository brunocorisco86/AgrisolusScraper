#!/bin/bash
# Wrapper utilitário para o Silo Analyzer (destinado ao tool calling do agente Hermes)

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR" || exit 1

# Ativa o ambiente virtual local
source env/bin/activate

# Configura o PYTHONPATH
export PYTHONPATH="$PROJECT_DIR"

# Executa o analisador repassando todos os argumentos recebidos
python src/analysis/silo_analyzer.py "$@"
