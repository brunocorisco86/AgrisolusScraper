#!/bin/bash
# -----------------------------------------------------------------------------
# Script: 4_setup_cron.sh
# Descrição: Configura as tarefas de agendamento (Cron) nativas no Raspberry Pi.
# -----------------------------------------------------------------------------

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_DIR" || exit 1

echo "=================================================="
echo "      PASSO 4: CONFIGURAÇÃO DO AGENDADOR CRON     "
echo "=================================================="
echo "Configurando os horários de leituras e relatórios..."

# Define as tarefas cron absolutizadas
SCRAPER_CRON="30 * * * * $PROJECT_DIR/scripts/run_cron.sh >> $PROJECT_DIR/cron_exec.log 2>&1"
SUMMARY_CRON="45 6,11,13,16 * * * $PROJECT_DIR/scripts/run_periodic_summary.sh >> $PROJECT_DIR/cron_exec.log 2>&1"
SLA_CRON="0 18 * * * $PROJECT_DIR/scripts/run_sla_report.sh >> $PROJECT_DIR/cron_exec.log 2>&1"
HOUSEKEEP_CRON="0 3 * * * $PROJECT_DIR/env/bin/python $PROJECT_DIR/scripts/housekeep_logs.py >> $PROJECT_DIR/cron_exec.log 2>&1"

echo ""
echo "As seguintes linhas serão inseridas no seu crontab:"
echo "--------------------------------------------------"
echo "1. Scraper (minuto 30 de cada hora):"
echo "   $SCRAPER_CRON"
echo "2. Resumos offline (minuto 45 das 06h, 11h, 13h, 16h):"
echo "   $SUMMARY_CRON"
echo "3. Relatório diário de SLA (18:00h diariamente):"
echo "   $SLA_CRON"
echo "4. Housekeeping de Logs (03:00h diariamente):"
echo "   $HOUSEKEEP_CRON"
echo "--------------------------------------------------"
echo ""

# Pergunta ao usuário se deseja atualizar o crontab local automaticamente
read -p "Deseja instalar estas regras no crontab do seu usuário? (s/N): " CONFIRM

if [[ "$CONFIRM" =~ ^[sS]$ ]]; then
    # 1. Faz o dump do crontab existente (evita erro se não houver crontab antigo)
    TMP_CRON=$(mktemp)
    crontab -l 2>/dev/null | grep -v "$PROJECT_DIR" > "$TMP_CRON"
    
    # 2. Adiciona as novas regras ao arquivo temporário
    echo "# --- Agrisolus Silo Monitor ---" >> "$TMP_CRON"
    echo "$SCRAPER_CRON" >> "$TMP_CRON"
    echo "$SUMMARY_CRON" >> "$TMP_CRON"
    echo "$SLA_CRON" >> "$TMP_CRON"
    echo "$HOUSEKEEP_CRON" >> "$TMP_CRON"
    echo "# -------------------------------" >> "$TMP_CRON"
    
    # 3. Carrega o crontab do temporário
    crontab "$TMP_CRON"
    rm -f "$TMP_CRON"
    
    echo "✅ SUCESSO: Crontab atualizado com sucesso!"
    echo "Você pode conferir rodando o comando: crontab -l"
else
    echo "⚠️ Instalação cancelada. Copie as linhas acima e configure manualmente usando: crontab -e"
fi

echo "=================================================="
