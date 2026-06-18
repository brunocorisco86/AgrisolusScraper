#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script executado diariamente às 18:00 para enviar o Relatório de SLA e Consumo Diário de ração no Telegram.
Focado exclusivamente no 'Aviário 819' no período das 17h do dia anterior às 17h do dia atual.
"""
import os
import sys
from datetime import datetime, timedelta

# Garante que o Python encontre o pacote 'src'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database.connection import DatabaseConnection
from src.bot.notifier import TelegramNotifier
from src.utils.logger import setup_logger
from src.utils.datetime_parser import parse_iso_datetime

logger = setup_logger(name="run_sla_report", log_file="test_run.log")

def main():
    logger.info("Iniciando geração do Relatório Diário de SLA...")
    
    db_conn = DatabaseConnection()
    notifier = TelegramNotifier()
    
    # 1. Definir o período (17h de ontem às 17h de hoje)
    now = datetime.now()
    end_dt = now.replace(hour=17, minute=0, second=0, microsecond=0)
    start_dt = end_dt - timedelta(days=1)
    
    # Se o script for executado por algum motivo antes das 17h, ajustamos
    # para usar as 17h do dia anterior até as 17h de hoje mesmo.
    start_str = start_dt.strftime("%Y-%m-%dT%H:%M:%S")
    end_str = end_dt.strftime("%Y-%m-%dT%H:%M:%S")
    
    logger.info(f"Período de SLA: de {start_str} até {end_str}")
    
    # Tenta conectar ao Supabase primeiro
    client = db_conn.get_supabase_client()
    
    silo_ids = []
    readings = []
    
    if client:
        try:
            logger.info("Buscando dados no Supabase para o relatório de SLA...")
            # 1. Obter lotes ativos para 'Aviário 819'
            lotes_res = client.table("lotes").select("id_lote").ilike("aviario", "%Aviário 819%").execute()
            lote_ids = [l["id_lote"] for l in lotes_res.data]
            
            if not lote_ids:
                logger.warning("Nenhum lote para 'Aviário 819' encontrado no Supabase.")
            else:
                # 2. Obter silos para estes lotes
                silos_res = client.table("silos").select("id_silo").in_("lote_id", lote_ids).execute()
                silo_ids = [s["id_silo"] for s in silos_res.data]
                
                if silo_ids:
                    # 3. Obter todas as leituras no período
                    readings_res = client.table("leituras") \
                        .select("silo_id,data_leitura,consumo_kg,valor_racao_kg") \
                        .in_("silo_id", silo_ids) \
                        .gte("data_leitura", start_str) \
                        .lte("data_leitura", end_str) \
                        .execute()
                    
                    readings = readings_res.data
        except Exception as e:
            logger.error(f"Erro ao buscar dados no Supabase: {e}. Iniciando fallback para SQLite local...")
            client = None

    # Se o cliente for None ou se ocorreu um erro na busca remota, tenta buscar localmente no SQLite
    if not client:
        try:
            logger.info("Buscando dados no SQLite local para o relatório de SLA...")
            conn = db_conn.get_sqlite_connection()
            cursor = conn.cursor()
            
            # 1. Obter lotes ativos para 'Aviário 819'
            cursor.execute("SELECT id_lote FROM lotes WHERE aviario LIKE '%Aviário 819%'")
            lote_ids = [row[0] for row in cursor.fetchall()]
            
            if not lote_ids:
                logger.warning("Nenhum lote para 'Aviário 819' encontrado no SQLite local.")
            else:
                # 2. Obter silos para estes lotes
                placeholders = ",".join("?" for _ in lote_ids)
                cursor.execute(f"SELECT id_silo FROM silos WHERE lote_id IN ({placeholders})", lote_ids)
                silo_ids = [row[0] for row in cursor.fetchall()]
                
                if silo_ids:
                    # 3. Obter leituras no período
                    silos_placeholders = ",".join("?" for _ in silo_ids)
                    cursor.execute(f"""
                        SELECT silo_id, data_leitura, consumo_kg, valor_racao_kg FROM leituras
                        WHERE silo_id IN ({silos_placeholders}) AND data_leitura >= ? AND data_leitura <= ?
                    """, silo_ids + [start_str, end_str])
                    rows = cursor.fetchall()
                    
                    for row in rows:
                        readings.append({
                            "silo_id": row[0],
                            "data_leitura": row[1],
                            "consumo_kg": row[2],
                            "valor_racao_kg": row[3]
                        })
            conn.close()
        except Exception as e:
            logger.error(f"Erro ao buscar dados no SQLite local: {e}")

    # Processar métricas por silo
    silos_sla = []
    
    for silo_id in silo_ids:
        # Filtrar leituras deste silo
        silo_readings = [r for r in readings if r["silo_id"] == silo_id]
        
        # 1. SLA de Conectividade (1 leitura por hora esperada, total 24h)
        unique_times = set(r["data_leitura"] for r in silo_readings)
        num_readings = len(unique_times)
        sla_percentage = min(100.0, (num_readings / 24.0) * 100.0)
        
        # 2. Consumo Total de Ração no período
        total_consumed = sum(float(r["consumo_kg"] or 0) for r in silo_readings)
        
        # 3. Saldo de Ração Atual (última leitura dentro do período)
        if silo_readings:
            # Ordenar por data_leitura parsed
            silo_readings_sorted = sorted(silo_readings, key=lambda x: parse_iso_datetime(x["data_leitura"]))
            current_balance = float(silo_readings_sorted[-1]["valor_racao_kg"] or 0)
        else:
            current_balance = 0.0
            
        logger.info(f"Silo {silo_id} - Leituras: {num_readings}/24, SLA: {sla_percentage:.1f}%, Consumo: {total_consumed:.2f} kg, Saldo: {current_balance:.2f} kg")
        
        silos_sla.append({
            "silo_id": silo_id,
            "sla_percentage": sla_percentage,
            "total_consumed_kg": total_consumed,
            "current_balance_kg": current_balance
        })

    # Envia o relatório diário
    if silos_sla:
        date_str = now.strftime("%d/%m/%Y")
        logger.info(f"Enviando Relatório Diário de SLA para o Telegram...")
        notifier.send_daily_sla_report(date_str, silos_sla)
        logger.info("Relatório Diário enviado com sucesso.")
    else:
        logger.warning("Nenhum dado encontrado para gerar o relatório de SLA.")

if __name__ == "__main__":
    main()
