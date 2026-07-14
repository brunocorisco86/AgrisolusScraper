# -*- coding: utf-8 -*-
"""
Helper CLI para o Agente Hermes na VPS.
Fornece resumos prontos para Telegram e comandos para registrar Notas Fiscais.
"""
import os
import sys
import argparse
from datetime import datetime

# Adiciona o diretório raiz ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.analysis.silo_analyzer import SiloAnalyzer
from src.database.connection import DatabaseConnection

def get_telemetry_summary():
    analyzer = SiloAnalyzer()
    db_conn = DatabaseConnection()
    conn = db_conn.get_sqlite_connection()
    cursor = conn.cursor()

    try:
        # 1. Dados de Silos e Ocupação
        cursor.execute("""
            SELECT s.id_silo, s.capacidade_kg, l.aviario
            FROM silos s
            JOIN lotes l ON s.lote_id = l.id_lote
        """)
        silos = cursor.fetchall()
        
        silo_lines = []
        total_capacity = 0.0
        total_weight = 0.0
        latest_reading_dt = None
        aviario_nome = "Aviário"

        for s_id, cap, av in silos:
            aviario_nome = av
            total_capacity += cap
            
            # Pega última leitura
            cursor.execute("""
                SELECT valor_racao_kg, data_leitura
                FROM leituras
                WHERE silo_id = ?
                ORDER BY data_leitura DESC
                LIMIT 1
            """, (s_id,))
            row = cursor.fetchone()
            
            weight = row[0] if row else 0.0
            total_weight += weight
            
            dt_str = row[1] if row else None
            if dt_str:
                clean_dt_str = dt_str.split('.')[0].replace('T', ' ')
                dt = datetime.strptime(clean_dt_str, "%Y-%m-%d %H:%M:%S")
                if not latest_reading_dt or dt > latest_reading_dt:
                    latest_reading_dt = dt
            
            pct = (weight / cap * 100) if cap > 0 else 0.0
            silo_lines.append(f"  • *{s_id}:* {pct:.1f}% ({weight:,.0f} kg / {cap:,.0f} kg)")

        total_pct = (total_weight / total_capacity * 100) if total_capacity > 0 else 0.0

        # 2. SLA de Comunicação (Últimos 7 dias)
        cursor.execute("""
            SELECT SUM(CASE WHEN sucesso_conexao = 1 THEN 1 ELSE 0 END),
                   MIN(data_tentativa)
            FROM historico_scraping
            WHERE data_tentativa >= datetime('now', '-7 days')
              AND silo_id = (SELECT id_silo FROM silos LIMIT 1)
        """)
        sla_row = cursor.fetchone()
        success_attempts = sla_row[0] if sla_row and sla_row[0] is not None else 0
        min_date_str = sla_row[1] if sla_row and sla_row[1] is not None else None

        if min_date_str:
            try:
                clean_date_str = min_date_str.split('.')[0].replace('T', ' ')
                min_date = datetime.strptime(clean_date_str, "%Y-%m-%d %H:%M:%S")
                delta_hours = int((datetime.now() - min_date).total_seconds() / 3600) + 1
                expected_attempts = min(168, max(1, delta_hours))
            except Exception:
                expected_attempts = 168
        else:
            expected_attempts = 168

        sla_pct = (success_attempts / expected_attempts * 100) if expected_attempts > 0 else 0.0

        # 3. Consumo diário e Forecast (Usando análise combinada)
        comb = analyzer.get_combined_analysis()
        daily_cons = comb.get("daily_consumption", {})
        
        days_sorted = sorted(daily_cons.keys())
        last_7_days = days_sorted[-7:] if len(days_sorted) >= 7 else days_sorted
        avg_cons = 0.0
        if last_7_days:
            avg_cons = sum(daily_cons[d] for d in last_7_days) / len(last_7_days)
            
        days_remaining = "N/A"
        forecast_date = "Sem consumo"
        if avg_cons > 5.0 and total_weight > 0.0:
            days_num = total_weight / avg_cons
            days_remaining = f"{days_num:.1f} dias"
            est_dt = datetime.now().date() + argparse.Namespace(days=days_num).days
            # Utilizar um cálculo simples de soma de dias para o datetime
            from datetime import timedelta
            est_dt = datetime.now() + timedelta(days=days_num)
            forecast_date = est_dt.strftime("%d/%m/%Y")

        # 4. Alertas Recentes
        cursor.execute("SELECT data_alerta, tipo_alerta_str, mensagem FROM alertas ORDER BY data_alerta DESC LIMIT 3")
        alerts = cursor.fetchall()
        alert_lines = []
        for dt_a, tipo, msg in alerts:
            # Formata data
            try:
                clean_dt = dt_a.split('.')[0].replace('T', ' ')
                dt_obj = datetime.strptime(clean_dt, "%Y-%m-%d %H:%M:%S")
                dt_formatted = dt_obj.strftime("%d/%m %H:%M")
            except Exception:
                dt_formatted = dt_a
            alert_lines.append(f"  ⚠️ [{dt_formatted}] {msg}")

        # Monta a mensagem final no formato Markdown do Telegram
        last_read_str = latest_reading_dt.strftime("%d/%m/%Y %H:%M") if latest_reading_dt else "N/A"
        diff_hours = (datetime.now() - latest_reading_dt).total_seconds() / 3600 if latest_reading_dt else 999.0
        
        status_sinal = "🟢 Conectado" if diff_hours <= 2 else f"🔴 Inativo ({diff_hours:.1f}h sem dados)"

        msg = (
            f"🌾 *Silo Monitor - {aviario_nome}* 🌾\n\n"
            f"Status do Sensor: {status_sinal}\n"
            f"Última Leitura: `{last_read_str}`\n"
            f"SLA de Comunicação (7d): `{sla_pct:.1f}%`\n\n"
            f"📊 *Nível dos Silos:*\n"
            + "\n".join(silo_lines) + "\n"
            f"  *Total:* {total_pct:.1f}% ({total_weight:,.0f} kg / {total_capacity:,.0f} kg)\n\n"
            f"📈 *Estimativas:*\n"
            f"  • Consumo Médio (7d): `{avg_cons:,.0f} kg/dia`\n"
            f"  • Duração Restante: `{days_remaining}`\n"
            f"  • Previsão Esvaziamento: `{forecast_date}`\n"
        )
        
        if alert_lines:
            msg += "\n🚨 *Alertas Recentes:*\n" + "\n".join(alert_lines)
            
        return msg
        
    except Exception as e:
        return f"❌ Erro ao gerar sumário de telemetria: {e}"
    finally:
        cursor.close()
        conn.close()

def add_invoice(nf_number, qty_kg, date_str):
    analyzer = SiloAnalyzer()
    # Tenta parsear a data
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        formatted_date = dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        # Tenta data simples
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            formatted_date = dt.strftime("%Y-%m-%d 12:00:00")
        except Exception:
            return f"❌ Erro: Formato de data inválido. Use YYYY-MM-DD HH:MM:SS."
            
    success, msg = analyzer.register_invoice(formatted_date, nf_number, qty_kg)
    if success:
        return f"✅ Nota Fiscal *{nf_number}* de *{qty_kg:,.0f} kg* registrada com sucesso em {formatted_date}!"
    else:
        return f"❌ Falha ao registrar Nota Fiscal: {msg}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hermes Agent Helper CLI")
    parser.add_argument("--status", action="store_true", help="Gera um sumário Markdown ideal para Telegram.")
    parser.add_argument("--add-invoice", action="store_true", help="Adiciona uma nova Nota Fiscal.")
    parser.add_argument("--nf", type=str, help="Número da Nota Fiscal.")
    parser.add_argument("--qty", type=float, help="Quantidade de ração em kg.")
    parser.add_argument("--date", type=str, default=None, help="Data da entrega (YYYY-MM-DD HH:MM:SS). Se omitida, usa agora.")
    
    args = parser.parse_args()
    
    if args.status:
        print(get_telemetry_summary())
    elif args.add_invoice:
        if not args.nf or not args.qty:
            print("❌ Erro: Parâmetros --nf e --qty são obrigatórios para registrar Nota Fiscal.")
            sys.exit(1)
        dt_str = args.date if args.date else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(add_invoice(args.nf, args.qty, dt_str))
    else:
        parser.print_help()
