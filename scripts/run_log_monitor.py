#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de Auditoria de Logs do Cron. Varre os logs da aplicação e do sistema
e dispara alertas no Telegram caso o cron esteja inativo ou ocorram erros graves.
"""
import os
import sys

# Garante que o Python encontre o pacote 'src'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.log_monitor import CronLogMonitor
from src.bot.notifier import TelegramNotifier
from src.utils.logger import setup_logger

logger = setup_logger(name="run_log_monitor", log_file="test_run.log")

def main():
    logger.info("Iniciando auditoria preventiva de logs do cron...")
    
    monitor = CronLogMonitor()
    result = monitor.analyze_logs(hours_back=24)
    
    cron_active = result["cron_active"]
    errors = result["errors"]
    last_exec = result["last_execution_time"]
    
    alert_triggered = False
    alert_message = ""
    
    # 1. Alerta crítico: Cron Inativo
    if not cron_active:
        alert_triggered = True
        alert_message += (
            f"⚠️ <b>ALERTA CRÍTICO: CRON INATIVO</b>\n"
            f"O agendamento automático do scraper parece estar inativo!\n"
            f"• <b>Última Execução Detectada:</b> {last_exec}\n"
            f"• <b>Status:</b> Silos sem atualizações horárias nas últimas 2 horas.\n\n"
        )
        
    # 2. Alerta de Erros Graves Detectados
    if errors:
        alert_triggered = True
        if not alert_message:
            alert_message += f"⚠️ <b>ALERTA: ERROS DE EXECUÇÃO DETECTADOS</b>\n"
        alert_message += f"Encontrados <b>{len(errors)} erros/exceções</b> nos logs nas últimas 24 horas:\n\n"
        
        # Limita a exibição dos 5 primeiros erros para não estourar limite do Telegram
        for idx, err in enumerate(errors[:5]):
            alert_message += f"<b>Erro {idx+1}:</b>\n<code>{err[:150]}...</code>\n\n"
            
        if len(errors) > 5:
            alert_message += f"• <i>E mais {len(errors) - 5} erros adicionais nos logs.</i>\n\n"
            
    if alert_triggered:
        alert_message += "<i>Pilares Agrisolus: Tecnologia Habilitadora & Processos Otimizados.</i>"
        logger.warning("Auditoria encontrou falhas. Disparando notificação no Telegram...")
        
        notifier = TelegramNotifier()
        success = notifier.send_message(alert_message)
        if success:
            logger.info("Notificação de falha de cron enviada com sucesso.")
        else:
            logger.error("Falha ao enviar notificação de falha de cron.")
    else:
        logger.info(f"Auditoria concluída com sucesso. Cron ativo (última execução: {last_exec}) e nenhum erro crítico encontrado.")

if __name__ == "__main__":
    main()
