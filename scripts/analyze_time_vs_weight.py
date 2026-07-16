# -*- coding: utf-8 -*-
"""
Script utilitário para analisar se a data de leitura da plataforma Agrisolus
permanece estática enquanto o peso mensurado flutua ao longo do tempo.
"""
import os
import sys
from collections import defaultdict

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.database.connection import DatabaseConnection

def analyze():
    db_conn = DatabaseConnection()
    conn = db_conn.get_sqlite_connection()
    cursor = conn.cursor()
    
    try:
        # Busca todas as tentativas de scraping com sucesso
        cursor.execute("""
            SELECT data_leitura, data_tentativa, peso_kg, silo_id
            FROM historico_scraping
            WHERE sucesso_conexao = 1 AND peso_kg IS NOT NULL
            ORDER BY silo_id, data_leitura, data_tentativa
        """)
        rows = cursor.fetchall()
        
        if not rows:
            print("Nenhum registro de scraping encontrado no histórico para analisar.")
            return
            
        print(f"Total de registros de tentativas encontrados: {len(rows)}")
        
        # Agrupa por silo e data_leitura
        grouped = defaultdict(list)
        for data_leitura, data_tentativa, peso, silo_id in rows:
            grouped[(silo_id, data_leitura)].append((data_tentativa, peso))
            
        # Procura por flutuações de peso para a mesma data de leitura
        issues_found = False
        print("\n=== Relatório de Auditoria de Telemetria (Data de Leitura vs Peso) ===\n")
        
        for (silo_id, data_leitura), attempts in grouped.items():
            pesos = [attempt[1] for attempt in attempts]
            unique_pesos = set(pesos)
            
            print(f"Silo: {silo_id} | Data de Leitura da Plataforma: {data_leitura}")
            print(f"  - Total de tentativas registradas para esta data: {len(attempts)}")
            print(f"  - Variações de peso detectadas: {list(unique_pesos)}")
            
            if len(unique_pesos) > 1:
                issues_found = True
                print("  ⚠️ ALERTA: O peso variou enquanto a data do portal se manteve estática!")
                print("  Linha do tempo das tentativas:")
                for data_tentativa, peso in attempts:
                    print(f"    • Tentativa em {data_tentativa} | Peso lido: {peso:.2f} kg")
            else:
                print("  \u2705 Estável: Peso permaneceu constante para esta data de leitura.")
            print("-" * 50)
            
        if not issues_found:
            print("\nResultado: Não foram detectadas flutuações de peso para a mesma data de leitura nos registros atuais.")
            print("Nota: Como o cronie estava desativado, o histórico possui poucos registros. Deixe o cronie executar as coletas de hora em hora para acumular dados intradia de análise.")
            
    except Exception as e:
        print(f"Erro ao executar análise: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    analyze()
