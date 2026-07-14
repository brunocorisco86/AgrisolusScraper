#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script executado diariamente às 19:00 para enviar o resumo diário consolidado no Telegram.
Contém:
- Quantidade de scrapings executados no dia.
- Quantidade de novos dados (leituras exclusivas) coletados.
- Métricas de SLA de conectividade, Consumo de ração e Saldo atual de cada silo do 'Aviário 819'.
- Resumo de alertas gerados no dia ou silos offline.
"""
import os
import sys
import sqlite3
from datetime import datetime, timedelta

# Garante que o Python encontre o pacote 'src'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database.connection import DatabaseConnection
from src.bot.notifier import TelegramNotifier
from src.utils.logger import setup_logger
from src.utils.datetime_parser import parse_iso_datetime
from src.utils.log_monitor import CronLogMonitor

logger = setup_logger(name="run_daily_summary_telegram", log_file="test_run.log")

def main():
    logger.info("==================================================")
    logger.info("INICIANDO GERAÇÃO DO RESUMO DIÁRIO TELEGRAM às 19h")
    logger.info("==================================================")
    
    db_conn = DatabaseConnection()
    notifier = TelegramNotifier()
    
    # 1. Definir os períodos
    now = datetime.now()
    
    # Período do dia civil (00:00 até agora) para scrapings e novos dados
    start_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    start_today_str = start_today.strftime("%Y-%m-%dT%H:%M:%S")
    end_today_str = now.strftime("%Y-%m-%dT%H:%M:%S")
    
    # Período de 24 horas (das 19h de ontem às 19h de hoje) para SLA, Consumo e Saldo
    end_24h = now.replace(hour=19, minute=0, second=0, microsecond=0)
    start_24h = end_24h - timedelta(days=1)
    start_24h_str = start_24h.strftime("%Y-%m-%dT%H:%M:%S")
    end_24h_str = end_24h.strftime("%Y-%m-%dT%H:%M:%S")
    
    logger.info(f"Período hoje: de {start_today_str} até {end_today_str}")
    logger.info(f"Período 24h (SLA/Consumo): de {start_24h_str} até {end_24h_str}")
    
    silo_ids = []
    lote_ids = []
    
    # Variáveis consolidadas
    total_scrapings = 0
    successful_scrapings = 0
    new_readings_count = 0
    readings_24h = []
    alertas_today = []
    
    try:
        logger.info("Buscando dados no SQLite local para o resumo consolidado...")
        conn = db_conn.get_sqlite_connection()
        cursor = conn.cursor()
        
        # A. Obter lotes ativos para 'Aviário 819'
        cursor.execute("SELECT id_lote FROM lotes WHERE aviario LIKE '%Aviário 819%'")
        lote_ids = [row[0] for row in cursor.fetchall()]
        
        if lote_ids:
            # B. Obter silos para estes lotes
            placeholders = ",".join("?" for _ in lote_ids)
            cursor.execute(f"SELECT id_silo FROM silos WHERE lote_id IN ({placeholders})", lote_ids)
            silo_ids = [row[0] for row in cursor.fetchall()]
            
            # C. Total de scrapings e bem sucedidos no dia civil
            cursor.execute(f"""
                SELECT sucesso_conexao, achou_dados_novos FROM historico_scraping
                WHERE data_tentativa >= ? AND data_tentativa <= ?
            """, (start_today_str, end_today_str))
            rows_hist = cursor.fetchall()
            total_scrapings = len(rows_hist)
            successful_scrapings = sum(1 for r in rows_hist if r[0] == 1)
            new_readings_count = sum(1 for r in rows_hist if r[1] == 1)
            
            # D. Obter todas as leituras no período de 24 horas
            if silo_ids:
                silos_placeholders = ",".join("?" for _ in silo_ids)
                cursor.execute(f"""
                    SELECT silo_id, data_leitura, consumo_kg, valor_racao_kg FROM leituras
                    WHERE silo_id IN ({silos_placeholders}) AND data_leitura >= ? AND data_leitura <= ?
                """, silo_ids + [start_24h_str, end_24h_str])
                rows_read = cursor.fetchall()
                for r in rows_read:
                    readings_24h.append({
                        "silo_id": r[0],
                        "data_leitura": r[1],
                        "consumo_kg": r[2],
                        "valor_racao_kg": r[3]
                    })
            
            # E. Obter alertas registrados no dia de hoje
            cursor.execute(f"""
                SELECT tipo_alerta_str, mensagem, data_alerta FROM alertas
                WHERE lote_id IN ({placeholders}) AND data_alerta >= ? AND data_alerta <= ?
            """, lote_ids + [start_today_str, end_today_str])
            rows_al = cursor.fetchall()
            for r in rows_al:
                alertas_today.append({
                    "tipo_alerta_str": r[0],
                    "mensagem": r[1],
                    "data_alerta": r[2]
                })
        conn.close()
    except Exception as e:
        logger.error(f"Erro ao buscar dados no SQLite local: {e}")

    # 3. Processar métricas por silo
    silos_metrics = []
    silos_offline_report = []
    
    for silo_id in silo_ids:
        silo_readings = [r for r in readings_24h if r["silo_id"] == silo_id]
        
        # SLA de Conectividade (esperado 1 leitura por hora nas últimas 24 horas, ou seja, 24 leituras)
        unique_times = set(r["data_leitura"] for r in silo_readings)
        num_readings = len(unique_times)
        sla_percentage = min(100.0, (num_readings / 24.0) * 100.0)
        
        # Consumo total de ração nas últimas 24 horas
        total_consumed = sum(float(r["consumo_kg"] or 0) for r in silo_readings)
        
        # Saldo atual de ração (última leitura registrada)
        current_balance = 0.0
        last_datetime_str = "Sem registros recentes"
        if silo_readings:
            silo_readings_sorted = sorted(silo_readings, key=lambda x: parse_iso_datetime(x["data_leitura"]))
            current_balance = float(silo_readings_sorted[-1]["valor_racao_kg"] or 0)
            last_datetime_str = silo_readings_sorted[-1]["data_leitura"]
            
            # Verifica se o silo está atualmente offline (última leitura há mais de 3 horas)
            try:
                dt_leitura = parse_iso_datetime(last_datetime_str)
                diff_hours = (now - dt_leitura).total_seconds() / 3600.0
                if diff_hours > 3.0:
                    silos_offline_report.append({
                        "silo_id": silo_id,
                        "offline_hours": diff_hours,
                        "last_datetime_str": last_datetime_str
                    })
            except Exception as e:
                logger.error(f"Erro ao calcular offline para {silo_id}: {e}")
        else:
            # Se não houver leituras nas últimas 24h, tentamos buscar a última leitura de todas no banco local
            try:
                conn_last = db_conn.get_sqlite_connection()
                cursor_last = conn_last.cursor()
                cursor_last.execute("SELECT valor_racao_kg, data_leitura FROM leituras WHERE silo_id = ? ORDER BY data_leitura DESC LIMIT 1", (silo_id,))
                row_last = cursor_last.fetchone()
                if row_last:
                    current_balance = float(row_last[0] or 0)
                    last_datetime_str = row_last[1]
                    dt_leitura = parse_iso_datetime(last_datetime_str)
                    diff_hours = (now - dt_leitura).total_seconds() / 3600.0
                    silos_offline_report.append({
                        "silo_id": silo_id,
                        "offline_hours": diff_hours,
                        "last_datetime_str": last_datetime_str
                    })
                else:
                    silos_offline_report.append({
                        "silo_id": silo_id,
                        "offline_hours": 24.0,
                        "last_datetime_str": "Nunca enviado"
                    })
                conn_last.close()
            except Exception as e:
                logger.error(f"Erro ao buscar última leitura histórica para {silo_id}: {e}")
                
        silos_metrics.append({
            "silo_id": silo_id,
            "sla_percentage": sla_percentage,
            "total_consumed_kg": total_consumed,
            "current_balance_kg": current_balance,
            "last_datetime_str": last_datetime_str
        })

    # 4. Formatar a mensagem do Telegram
    emoji_summary = "📊"
    emoji_check = "✅"
    emoji_warn = "⚠️"
    
    date_str = now.strftime("%d/%m/%Y")
    
    message = f"{emoji_summary} <b>RESUMO DIÁRIO AGRISOLUS - {date_str}</b>\n"
    message += f"<i>Relatório consolidado gerado às {now.strftime('%H:%M:%S')}</i>\n\n"
    
    # A. Execução do Scraper no dia
    message += f"🤖 <b>Status do Sistema de Scraping:</b>\n"
    message += f"• Tentativas de scraping hoje: <b>{total_scrapings}</b>\n"
    message += f"• Sucessos de conexão: <b>{successful_scrapings}</b>\n"
    message += f"• Dados novos/exclusivos: <b>{new_readings_count} leituras</b>\n\n"
    
    # B. Resumo dos Silos (Aviário 819)
    message += f"🔋 <b>Status e Consumo dos Silos:</b>\n"
    for item in silos_metrics:
        sla = item["sla_percentage"]
        sla_emoji = "🟢" if sla >= 95.0 else ("🟡" if sla >= 85.0 else "🔴")
        
        message += (
            f"• <b>{item['silo_id']}</b>:\n"
            f"  {sla_emoji} SLA de Conexão: <b>{sla:.1f}%</b>\n"
            f"  📉 Consumo 24h: <b>{item['total_consumed_kg']:.2f} kg</b>\n"
            f"  📦 Saldo de Ração: <b>{item['current_balance_kg']:.2f} kg</b>\n"
            f"  🕒 Última leitura: {item['last_datetime_str']}\n\n"
        )
        
    # C. Silos Offline ou Ocorrências Críticas
    if silos_offline_report:
        message += f"{emoji_warn} <b>Silos Offline Detectados (>3 horas):</b>\n"
        for occ in silos_offline_report:
            message += (
                f"• <b>{occ['silo_id']}</b> está sem enviar dados há <b>{occ['offline_hours']:.1f}h</b>\n"
                f"  (Último envio: {occ['last_datetime_str']})\n"
            )
        message += "\n"
    else:
        message += f"{emoji_check} <b>Conectividade Silos:</b> Todos os silos operando e transmitindo normalmente!\n\n"
        
    # D. Resumo de Alertas adicionais
    alertas_filtrados = [a for a in alertas_today if a.get("tipo_alerta_str") != "Silo Offline"]
    if alertas_filtrados:
        message += f"🔔 <b>Alertas e Eventos do Dia:</b>\n"
        for al in alertas_filtrados[:5]:  # limita aos 5 primeiros
            message += f"• [{al['tipo_alerta_str']}] {al['mensagem']} ({al['data_alerta']})\n"
        message += "\n"
        
    # E. Auditoria de Logs do Cron
    logger.info("Executando auditoria de logs do cron...")
    log_monitor = CronLogMonitor()
    audit_res = log_monitor.analyze_logs(hours_back=24)
    
    message += f"📋 <b>Auditoria do Sistema e Logs (24h):</b>\n"
    if audit_res["cron_active"]:
        message += f"• Status do Cron: {emoji_check} <b>Ativo</b> (última execução: {audit_res['last_execution_time']})\n"
    else:
        message += f"• Status do Cron: {emoji_warn} <b>Inativo / Travado!</b> (última execução: {audit_res['last_execution_time']})\n"
        
    audit_errors = audit_res["errors"]
    if audit_errors:
        message += f"• Erros/Exceções detectados: {emoji_warn} <b>{len(audit_errors)} ocorrências</b>\n"
        message += f"  <i>Exemplo:</i> <code>{audit_errors[0][:100]}...</code>\n\n"
    else:
        message += f"• Erros/Exceções detectados: {emoji_check} <b>Nenhum erro encontrado</b>\n\n"
        
    message += "<i>Pilares Agrisolus: Comunicação Eficiente, Processos Otimizados & Tecnologia Habilitadora.</i>"
    
    # Envia a mensagem consolidada
    logger.info("Enviando o Resumo Consolidado do Dia para o Telegram...")
    success = notifier.send_message(message)
    if success:
        logger.info("Resumo Diário enviado ao Telegram com sucesso!")
    else:
        logger.error("Falha ao enviar o Resumo Diário ao Telegram.")

if __name__ == "__main__":
    main()
