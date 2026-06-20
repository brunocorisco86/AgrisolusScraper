#!/bin/bash
# Script utilitário para a auditoria de logs do cron do scraper
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR" || exit 1
source env/bin/activate
export PYTHONPATH="$PROJECT_DIR"
python scripts/run_log_monitor.py
