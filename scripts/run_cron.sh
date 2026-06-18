#!/bin/bash
# Script utilitário para ser chamado pelo cron
# Ele garante que o ambiente virtual python 'env' seja ativado e o script executado no diretório correto.

# Caminho absoluto da pasta do projeto dinâmico
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$PROJECT_DIR" || exit 1

# Ativa o ambiente virtual
source env/bin/activate

# Define PYTHONPATH para garantir que os módulos sejam encontrados
export PYTHONPATH="$PROJECT_DIR"

# Executa o scraper principal
python src/main.py
