#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script executado periodicamente (06h, 11h, 13h, 16h) para enviar o resumo de silos offline no Telegram.
Focado exclusivamente nos silos do 'Aviário 819'.
"""
import os
import sys
from datetime import datetime

# Garante que o Python encontre o pacote 'src'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database.connection import DatabaseConnection
from src.bot.notifier import TelegramNotifier
from src.utils.logger import setup_logger
from src.utils.datetime_parser import parse_iso_datetime

logger = setup_logger(name="run_periodic_summary", log_file="test_run.log")

def main():
    logger.info("Iniciando verificação para o resumo periódico de ocorrências...")
    
    db_conn = DatabaseConnection()
    notifier = TelegramNotifier()
    
    # Tenta conectar ao Supabase primeiro (banco de dados principal)
    client = db_conn.get_supabase_client()
    
    silos_data = []
    
    if client:
        try:
            logger.info("Buscando dados no Supabase para o relatório periódico...")
            # 1. Obter lotes ativos para 'Aviário 819'
            lotes_res = client.table("lotes").select("id_lote").ilike("aviario", "%Aviário 819%").execute()
            lote_ids = [l["id_lote"] for l in lotes_res.data]
            
            if not lote_ids:
                logger.warning("Nenhum lote para 'Aviário 819' encontrado no Supabase.")
            else:
                # 2. Obter silos para estes lotes
                silos_res = client.table("silos").select("id_silo").in_("lote_id", lote_ids).execute()
                silo_ids = [s["id_silo"] for s in silos_res.data]
                
                # 3. Obter a última leitura de cada silo
                for silo_id in silo_ids:
                    reading_res = client.table("leituras").select("data_leitura").eq("silo_id", silo_id).order("data_leitura", desc=True).limit(1).execute()
                    if reading_res.data:
                        silos_data.append({
                            "silo_id": silo_id,
                            "data_leitura": reading_res.data[0]["data_leitura"]
                        })
                    else:
                        logger.info(f"Nenhuma leitura encontrada para o silo {silo_id} no Supabase.")
        except Exception as e:
            logger.error(f"Erro ao buscar dados no Supabase: {e}. Iniciando fallback para SQLite local...")
            client = None

    # Se o cliente for None ou se ocorreu um erro na busca remota, tenta buscar localmente no SQLite
    if not client:
        try:
            logger.info("Buscando dados no SQLite local para o relatório periódico...")
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
                
                # 3. Obter a última leitura de cada silo
                for silo_id in silo_ids:
                    cursor.execute("SELECT data_leitura FROM leituras WHERE silo_id = ? ORDER BY data_leitura DESC LIMIT 1", (silo_id,))
                    row = cursor.fetchone()
                    if row:
                        silos_data.append({
                            "silo_id": silo_id,
                            "data_leitura": row[0]
                        })
                    else:
                        logger.info(f"Nenhuma leitura encontrada para o silo {silo_id} no SQLite local.")
            conn.close()
        except Exception as e:
            logger.error(f"Erro ao buscar dados no SQLite local: {e}")

    # Processamento dos silos offline
    occurrences = []
    now = datetime.now()
    
    for item in silos_data:
        silo_id = item["silo_id"]
        data_leitura_str = item["data_leitura"]
        
        try:
            dt_leitura = parse_iso_datetime(data_leitura_str)
            diff_seconds = (now - dt_leitura).total_seconds()
            diff_hours = diff_seconds / 3600.0
            
            if diff_hours > 3.0:
                logger.warning(f"Silo {silo_id} offline detectado: há {diff_hours:.1f} horas (Última leitura: {data_leitura_str}).")
                occurrences.append({
                    "silo_id": silo_id,
                    "offline_hours": diff_hours,
                    "last_datetime_str": data_leitura_str
                })
            else:
                logger.info(f"Silo {silo_id} online: {diff_hours:.1f}h desde a última leitura.")
        except Exception as e:
            logger.error(f"Erro ao calcular diferença de tempo para o silo {silo_id}: {e}")

    # Envia o resumo periódico
    logger.info(f"Enviando resumo com {len(occurrences)} ocorrências para o Telegram...")
    notifier.send_periodic_summary(occurrences)
    logger.info("Resumo periódico enviado.")

if __name__ == "__main__":
    main()
