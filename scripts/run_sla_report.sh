#!/bin/bash
# Script utilitário para o relatório diário de SLA e Consumo dos silos
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR" || exit 1
source env/bin/activate
export PYTHONPATH="$PROJECT_DIR"
python scripts/run_sla_report.py
