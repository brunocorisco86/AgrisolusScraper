#!/bin/bash
# Script utilitário para o resumo consolidado diário dos silos às 19h
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR" || exit 1
source env/bin/activate
export PYTHONPATH="$PROJECT_DIR"
python scripts/run_daily_summary_telegram.py
