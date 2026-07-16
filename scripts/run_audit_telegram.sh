#!/bin/bash
# Script wrapper para o agendamento cron que dispara o relatório diário de auditoria por Telegram

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR" || exit 1

source env/bin/activate
export PYTHONPATH="$PROJECT_DIR"

python scripts/send_audit_telegram.py
