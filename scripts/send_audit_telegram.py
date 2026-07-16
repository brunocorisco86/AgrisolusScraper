# -*- coding: utf-8 -*-
"""
Script que gera a análise de consistência tempo vs peso
e envia o relatório formatado para o usuário via Telegram.
Possui data de expiração para rodar apenas por uma semana.
"""
import os
import sys
from datetime import datetime, date
from collections import defaultdict

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.database.connection import DatabaseConnection
from src.bot.notifier import TelegramNotifier

# Data limite de expiração (UTC): 24 de Julho de 2026 inclusive
EXPIRATION_DATE = date(2026, 7, 24)

def run():
    # Verifica expiração
    if date.today() >= EXPIRATION_DATE:
        print("Script de auditoria temporária expirado. Encerrando sem enviar.")
        sys.exit(0)
        
    db_conn = DatabaseConnection()
    conn = db_conn.get_sqlite_connection()
    cursor = conn.cursor()
    
    try:
        # Busca todas as tentativas nas últimas 24 horas para o relatório diário
        cursor.execute("""
            SELECT data_leitura, data_tentativa, peso_kg, silo_id
            FROM historico_scraping
            WHERE sucesso_conexao = 1 AND peso_kg IS NOT NULL
              AND data_tentativa >= datetime('now', '-24 hours')
            ORDER BY silo_id, data_leitura, data_tentativa
        """)
        rows = cursor.fetchall()
        
        notifier = TelegramNotifier()
        
        if not rows:
            msg = (
                "🔌 <b>Auditoria de Telemetria (Tempo vs Peso)</b>\n"
                "<i>Relatório diário de consistência dos silos</i>\n\n"
                "❌ Nenhum registro de scraping com sucesso foi encontrado nas últimas 24 horas para análise."
            )
            notifier.send_message(msg)
            return

        # Agrupa por silo e data_leitura
        grouped = defaultdict(list)
        for data_leitura, data_tentativa, peso, silo_id in rows:
            grouped[(silo_id, data_leitura)].append((data_tentativa, peso))
            
        msg = (
            "🔌 <b>Auditoria de Telemetria (Tempo vs Peso)</b>\n"
            "<i>Relatório diário de consistência dos silos (24h)</i>\n\n"
        )
        
        issues_detected = False
        for (silo_id, data_leitura), attempts in grouped.items():
            pesos = [attempt[1] for attempt in attempts]
            unique_pesos = list(set(pesos))
            
            # Formata a data de leitura para melhor exibição
            clean_date = data_leitura.replace('T', ' ').split('.')[0]
            try:
                dt_obj = datetime.strptime(clean_date, "%Y-%m-%d %H:%M:%S")
                date_formatted = dt_obj.strftime("%d/%m/%Y %H:%M")
            except Exception:
                date_formatted = data_leitura

            msg += f"🔋 <b>{silo_id}</b>\n"
            msg += f"• Data Portal: <code>{date_formatted}</code>\n"
            msg += f"• Tentativas nas últimas 24h: {len(attempts)}\n"
            
            if len(unique_pesos) > 1:
                issues_detected = True
                msg += "• Estado: ⚠️ <b>ALERTA: Peso variando com data estática!</b>\n"
                msg += "• Flutuações de peso detectadas (kg):\n"
                for data_tentativa, peso in attempts:
                    try:
                        dt_tent = datetime.strptime(data_tentativa.split('.')[0].replace('T', ' '), "%Y-%m-%d %H:%M:%S")
                        tent_formatted = dt_tent.strftime("%d/%m %H:%M")
                    except Exception:
                        tent_formatted = data_tentativa
                    msg += f"   - {tent_formatted}: <b>{peso:,.1f} kg</b>\n"
            else:
                msg += f"• Peso Estável: <b>{unique_pesos[0]:,.1f} kg</b>\n"
                msg += "• Estado: \u2705 Estável\n"
            msg += "\n"
            
        if issues_detected:
            msg += "<i>Nota: Foi detectado que o peso flutua enquanto a estampa de tempo do portal fica fixa.</i>\n\n"
        else:
            msg += "<i>Nota: Peso e data de leitura consistentes nas últimas 24 horas.</i>\n\n"
            
        # Adiciona informação de data de expiração do monitoramento temporário
        days_left = (EXPIRATION_DATE - date.today()).days
        msg += f"<i>Auditoria temporária ativa por mais {days_left} dias.</i>"
        
        notifier.send_message(msg)
        print("Relatório enviado com sucesso via Telegram.")
        
    except Exception as e:
        print(f"Erro ao gerar e enviar relatório do Telegram: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    run()
