# -*- coding: utf-8 -*-
"""
Módulo de análise de série temporal do silo: suavização de ruído,
cálculo de consumo diário, detecção de carregamentos e cálculo de acurácia do sensor.
"""
import argparse
import sqlite3
from datetime import datetime, timedelta
from src.database.connection import DatabaseConnection
from src.utils.logger import setup_logger

logger = setup_logger(name="silo_analyzer", log_file="test_run.log")

class SiloAnalyzer:
    def __init__(self, db_path=None):
        self.db_conn = DatabaseConnection(sqlite_path=db_path)

    def insert_nota_fiscal(self, data_nf: str, numero_nf: str, quantidade_kg: float) -> bool:
        """
        Insere os dados de uma nota fiscal de entrada de ração no banco local.
        data_nf deve estar no formato YYYY-MM-DD HH:MM:SS ou YYYY-MM-DD.
        """
        # Valida formato da data
        try:
            # Tenta com hora
            dt = datetime.strptime(data_nf, "%Y-%m-%d %H:%M:%S")
            data_nf_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                # Tenta apenas com data
                dt = datetime.strptime(data_nf, "%Y-%m-%d")
                data_nf_str = dt.strftime("%Y-%m-%d 12:00:00")  # Meio-dia como padrão
            except ValueError:
                logger.error(f"Formato de data inválido para a Nota Fiscal: {data_nf}. Use YYYY-MM-DD HH:MM:SS ou YYYY-MM-DD.")
                return False

        conn = self.db_conn.get_sqlite_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO notas_fiscais (data_nf, numero_nf, quantidade_kg)
                VALUES (?, ?, ?)
            """, (data_nf_str, numero_nf, quantidade_kg))
            conn.commit()
            logger.info(f"Nota Fiscal nº {numero_nf} inserida com sucesso: {quantidade_kg} kg em {data_nf_str}.")
            return True
        except sqlite3.IntegrityError:
            logger.error(f"Nota Fiscal nº {numero_nf} já cadastrada no sistema.")
            return False
        except Exception as e:
            logger.error(f"Erro ao inserir nota fiscal: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

    def get_invoices(self):
        """Retorna todas as notas fiscais cadastradas no banco."""
        conn = self.db_conn.get_sqlite_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, data_nf, numero_nf, quantidade_kg, created_at FROM notas_fiscais ORDER BY data_nf DESC")
            rows = cursor.fetchall()
            return [
                {
                    "id": r[0],
                    "data_nf": r[1],
                    "numero_nf": r[2],
                    "quantidade_kg": r[3],
                    "created_at": r[4]
                }
                for r in rows
            ]
        finally:
            cursor.close()
            conn.close()

    def get_raw_readings(self, silo_id: str):
        """Retorna as leituras brutas de um determinado silo ordenadas por data."""
        conn = self.db_conn.get_sqlite_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT data_leitura, valor_racao_kg, consumo_kg
                FROM leituras
                WHERE silo_id = ?
                ORDER BY data_leitura ASC
            """, (silo_id,))
            rows = cursor.fetchall()
            return [
                {
                    "data": r[0],
                    "peso_bruto": r[1],
                    "consumo_original": r[2]
                }
                for r in rows
            ]
        finally:
            cursor.close()
            conn.close()

    def smooth_readings(self, readings, window_size=3):
        """
        Aplica média móvel simples na série temporal dos pesos dos silos para suavizar o ruído.
        """
        if not readings:
            return []
        
        smoothed = []
        pesos = [r["peso_bruto"] for r in readings]
        
        for i in range(len(pesos)):
            # Define a janela deslizante centrada ou apenas anterior se no início
            start = max(0, i - window_size + 1)
            end = i + 1
            window_weights = pesos[start:end]
            avg_weight = sum(window_weights) / len(window_weights)
            
            smoothed.append({
                "data": readings[i]["data"],
                "peso_bruto": readings[i]["peso_bruto"],
                "peso_suavizado": round(avg_weight, 3)
            })
            
        return smoothed

    def analyze_silo(self, silo_id: str, smoothing_window=3, load_threshold=400.0):
        """
        Analisa a série temporal do silo:
        1. Suaviza a série temporal.
        2. Detecta abastecimentos (carregamento de ração).
        3. Calcula consumo diário.
        """
        raw_readings = self.get_raw_readings(silo_id)
        if not raw_readings:
            return {"readings": [], "loadings": [], "daily_consumption": {}}

        # 1. Suavizar
        smoothed = self.smooth_readings(raw_readings, window_size=smoothing_window)

        # 2. Detectar abastecimentos e calcular consumo
        loadings = []
        daily_consumption = {}
        
        for i in range(len(smoothed)):
            current = smoothed[i]
            current_date_str = current["data"]
            current_dt = datetime.strptime(current_date_str, "%Y-%m-%d" + ("T%H:%M:%S" if "T" in current_date_str else " %H:%M:%S"))
            day_str = current_dt.strftime("%Y-%m-%d")

            if i == 0:
                current["consumo_calculado"] = 0.0
                current["abastecimento_detectado"] = 0.0
                continue

            prev = smoothed[i - 1]
            diff = current["peso_suavizado"] - prev["peso_suavizado"]

            # Se o peso aumentou significativamente acima do threshold, é um abastecimento
            if diff >= load_threshold:
                current["abastecimento_detectado"] = round(diff, 2)
                current["consumo_calculado"] = 0.0
                loadings.append({
                    "data": current_date_str,
                    "peso_anterior": prev["peso_suavizado"],
                    "peso_atual": current["peso_suavizado"],
                    "quantidade_carregada": round(diff, 2)
                })
                logger.info(f"Abastecimento detectado no silo {silo_id} em {current_date_str}: +{round(diff, 2)} kg.")
            else:
                current["abastecimento_detectado"] = 0.0
                # O consumo é a queda no nível do silo (se houver queda)
                # Se diff for negativo, consumiu -diff. Se for positivo (mas < threshold), assumimos consumo 0 ou pequena flutuação
                consumo = max(0.0, -diff)
                current["consumo_calculado"] = round(consumo, 2)

                # Acumula o consumo por dia
                daily_consumption[day_str] = round(daily_consumption.get(day_str, 0.0) + consumo, 2)

        return {
            "readings": smoothed,
            "loadings": loadings,
            "daily_consumption": daily_consumption
        }

    def evaluate_sensor_accuracy(self, silo_id: str, window_hours=24, smoothing_window=3, load_threshold=400.0):
        """
        Objetivo Épico: Calcula o nível de acurácia do sensor comparando as
        Notas Fiscais de Entrada com os carregamentos detectados pelo sensor no silo.
        """
        analysis = self.analyze_silo(silo_id, smoothing_window=smoothing_window, load_threshold=load_threshold)
        loadings = analysis["loadings"]
        invoices = self.get_invoices()

        if not invoices:
            return {"status": "Sem notas fiscais cadastradas para comparação.", "accuracy_report": []}
        if not loadings:
            return {"status": "Nenhum carregamento detectado pelo sensor no silo.", "accuracy_report": []}

        report = []
        matched_loadings_ids = set()

        for inv in invoices:
            inv_dt = datetime.strptime(inv["data_nf"], "%Y-%m-%d %H:%M:%S")
            inv_qty = inv["quantidade_kg"]
            
            # Encontra o melhor match de carregamento dentro da janela temporal de ±window_hours
            best_match = None
            min_time_diff = timedelta(hours=window_hours + 1)

            for idx, load in enumerate(loadings):
                load_date_str = load["data"]
                load_dt = datetime.strptime(load_date_str, "%Y-%m-%d" + ("T%H:%M:%S" if "T" in load_date_str else " %H:%M:%S"))
                
                time_diff = abs(load_dt - inv_dt)
                if time_diff <= timedelta(hours=window_hours) and time_diff < min_time_diff:
                    min_time_diff = time_diff
                    best_match = load
                    best_match_idx = idx

            if best_match:
                matched_loadings_ids.add(best_match_idx)
                diff_kg = best_match["quantidade_carregada"] - inv_qty
                # Calcula acurácia: 100% - erro percentual
                error_pct = (abs(diff_kg) / inv_qty) * 100 if inv_qty > 0 else 100
                accuracy_pct = max(0.0, 100.0 - error_pct)

                report.append({
                    "numero_nf": inv["numero_nf"],
                    "data_nf": inv["data_nf"],
                    "quantidade_nf": inv_qty,
                    "data_carregamento": best_match["data"],
                    "quantidade_sensor": best_match["quantidade_carregada"],
                    "diferenca_kg": round(diff_kg, 2),
                    "acuracia_pct": round(accuracy_pct, 2),
                    "status": "Combinado"
                })
            else:
                report.append({
                    "numero_nf": inv["numero_nf"],
                    "data_nf": inv["data_nf"],
                    "quantidade_nf": inv_qty,
                    "data_carregamento": None,
                    "quantidade_sensor": 0.0,
                    "diferenca_kg": round(-inv_qty, 2),
                    "acuracia_pct": 0.0,
                    "status": "Não encontrado no sensor (Silo)"
                })

        # Calcula a acurácia geral média dos registros combinados
        matched_accuracies = [r["acuracia_pct"] for r in report if r["status"] == "Combinado"]
        overall_accuracy = sum(matched_accuracies) / len(matched_accuracies) if matched_accuracies else 0.0

        return {
            "status": "OK",
            "overall_accuracy_pct": round(overall_accuracy, 2),
            "total_invoices": len(invoices),
            "matched_loadings": len(matched_accuracies),
            "accuracy_report": report
        }

    def get_combined_analysis(self, smoothing_window=3, load_threshold=400.0):
        """
        Calcula a série temporal do somatório de todos os silos combinados.
        Garante alinhamento temporal via preenchimento para frente (forward fill).
        """
        # Busca todas as chaves de silos no banco de dados
        conn = self.db_conn.get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id_silo FROM silos")
        silo_ids = [r[0] for r in cursor.fetchall()]
        cursor.close()
        conn.close()

        if not silo_ids:
            return {"readings": [], "loadings": [], "daily_consumption": {}}

        # Busca leituras brutas de cada silo e monta um mapa rápido
        silo_readings = {}
        all_timestamps = set()
        for s_id in silo_ids:
            raw = self.get_raw_readings(s_id)
            silo_readings[s_id] = {r["data"]: r["peso_bruto"] for r in raw}
            all_timestamps.update(r["data"] for r in raw)

        sorted_timestamps = sorted(list(all_timestamps))

        combined = []
        last_weights = {s_id: 0.0 for s_id in silo_ids}

        for ts in sorted_timestamps:
            for s_id in silo_ids:
                if ts in silo_readings[s_id]:
                    last_weights[s_id] = silo_readings[s_id][ts]

            total_weight = sum(last_weights.values())
            combined.append({
                "data": ts,
                "peso_bruto": total_weight
            })

        # Aplica suavização na série somada
        smoothed = self.smooth_readings(combined, window_size=smoothing_window)

        # Detecta carregamentos e calcula consumo na série combinada
        loadings = []
        daily_consumption = {}

        for i in range(len(smoothed)):
            current = smoothed[i]
            current_date_str = current["data"]
            current_dt = datetime.strptime(current_date_str, "%Y-%m-%d" + ("T%H:%M:%S" if "T" in current_date_str else " %H:%M:%S"))
            day_str = current_dt.strftime("%Y-%m-%d")

            if i == 0:
                current["consumo_calculado"] = 0.0
                current["abastecimento_detectado"] = 0.0
                continue

            prev = smoothed[i - 1]
            diff = current["peso_suavizado"] - prev["peso_suavizado"]

            if diff >= load_threshold:
                current["abastecimento_detectado"] = round(diff, 2)
                current["consumo_calculado"] = 0.0
                loadings.append({
                    "data": current_date_str,
                    "peso_anterior": prev["peso_suavizado"],
                    "peso_atual": current["peso_suavizado"],
                    "quantidade_carregada": round(diff, 2)
                })
                logger.info(f"Abastecimento detectado no conjunto de silos em {current_date_str}: +{round(diff, 2)} kg.")
            else:
                current["abastecimento_detectado"] = 0.0
                consumo = max(0.0, -diff)
                current["consumo_calculado"] = round(consumo, 2)
                daily_consumption[day_str] = round(daily_consumption.get(day_str, 0.0) + consumo, 2)

        return {
            "readings": smoothed,
            "loadings": loadings,
            "daily_consumption": daily_consumption
        }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Análise do Silo e Acurácia do Sensor (Agrisolus Scraper)")
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponíveis")

    # Comando add-invoice
    parser_add = subparsers.add_parser("add-invoice", help="Adiciona dados de nota fiscal")
    parser_add.add_argument("--data", required=True, help="Data da NF (YYYY-MM-DD HH:MM:SS ou YYYY-MM-DD)")
    parser_add.add_argument("--numero", required=True, help="Número da Nota Fiscal")
    parser_add.add_argument("--qtd", required=True, type=float, help="Quantidade em kg de ração entregue")
    parser_add.add_argument("--db", default=None, help="Caminho personalizado do SQLite")

    # Comando list-invoices
    parser_list = subparsers.add_parser("list-invoices", help="Lista todas as notas fiscais")
    parser_list.add_argument("--db", default=None, help="Caminho personalizado do SQLite")

    # Comando analyze
    parser_analyze = subparsers.add_parser("analyze", help="Analisa série temporal do silo, calculando consumo e carregamentos")
    parser_analyze.add_argument("--silo", required=True, help="ID do silo (ex: Silo-819-01)")
    parser_analyze.add_argument("--window", type=int, default=3, help="Janela de suavização (Média Móvel)")
    parser_analyze.add_argument("--threshold", type=float, default=400.0, help="Limite em kg para detectar abastecimento")
    parser_analyze.add_argument("--db", default=None, help="Caminho personalizado do SQLite")

    # Comando accuracy
    parser_accuracy = subparsers.add_parser("accuracy", help="Avalia acurácia do sensor contra as Notas Fiscais")
    parser_accuracy.add_argument("--silo", required=True, help="ID do silo (ex: Silo-819-01)")
    parser_accuracy.add_argument("--hours", type=int, default=24, help="Janela temporal de busca em horas")
    parser_accuracy.add_argument("--window", type=int, default=3, help="Janela de suavização (Média Móvel)")
    parser_accuracy.add_argument("--threshold", type=float, default=400.0, help="Limite em kg para detectar abastecimento")
    parser_accuracy.add_argument("--db", default=None, help="Caminho personalizado do SQLite")

    args = parser.parse_args()

    if args.command == "add-invoice":
        analyzer = SiloAnalyzer(db_path=args.db)
        success = analyzer.insert_nota_fiscal(args.data, args.numero, args.qtd)
        if success:
            print(f"SUCESSO: Nota Fiscal nº {args.numero} inserida.")
        else:
            print("ERRO: Falha ao inserir Nota Fiscal.")
            
    elif args.command == "list-invoices":
        analyzer = SiloAnalyzer(db_path=args.db)
        invoices = analyzer.get_invoices()
        if not invoices:
            print("Nenhuma nota fiscal encontrada no banco.")
        else:
            print(f"{'Data NF':<20} | {'Número NF':<12} | {'Quantidade (kg)':<15} | {'Criado em':<20}")
            print("-" * 75)
            for inv in invoices:
                print(f"{inv['data_nf']:<20} | {inv['numero_nf']:<12} | {inv['quantidade_kg']:<15.2f} | {inv['created_at']:<20}")

    elif args.command == "analyze":
        analyzer = SiloAnalyzer(db_path=args.db)
        res = analyzer.analyze_silo(args.silo, smoothing_window=args.window, load_threshold=args.threshold)
        
        print(f"\n=== ANÁLISE DO SILO: {args.silo} ===")
        print(f"Leituras processadas: {len(res['readings'])}")
        
        print("\n--- Carregamentos Detectados ---")
        if not res["loadings"]:
            print("Nenhum carregamento detectado.")
        else:
            for ld in res["loadings"]:
                print(f"Data: {ld['data']} | +{ld['quantidade_carregada']} kg (De {ld['peso_anterior']} para {ld['peso_atual']} kg)")
                
        print("\n--- Consumo Diário Calculado ---")
        if not res["daily_consumption"]:
            print("Nenhum consumo registrado.")
        else:
            for day, cons in sorted(res["daily_consumption"].items()):
                print(f"Data: {day} | Consumo: {cons:.2f} kg")

    elif args.command == "accuracy":
        analyzer = SiloAnalyzer(db_path=args.db)
        res = analyzer.evaluate_sensor_accuracy(args.silo, window_hours=args.hours, smoothing_window=args.window, load_threshold=args.threshold)
        
        print(f"\n=== RELATÓRIO DE ACURÁCIA DO SENSOR: {args.silo} ===")
        print(f"Status: {res['status']}")
        if res.get("status") == "OK":
            print(f"Acurácia Geral Média: {res['overall_accuracy_pct']}%")
            print(f"Total Notas Fiscais: {res['total_invoices']} | Notas Combinadas: {res['matched_loadings']}")
            print("\n--- Detalhes das Comparações ---")
            print(f"{'Número NF':<10} | {'Quantidade NF':<15} | {'Qtd Sensor':<12} | {'Diferença':<12} | {'Acurácia':<10} | {'Status':<15}")
            print("-" * 85)
            for r in res["accuracy_report"]:
                print(f"{r['numero_nf']:<10} | {r['quantidade_nf']:<15.1f} | {r['quantidade_sensor']:<12.1f} | {r['diferenca_kg']:<12.1f} | {r['acuracia_pct']:<9.1f}% | {r['status']:<15}")
    else:
        parser.print_help()
