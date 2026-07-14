# -*- coding: utf-8 -*-
import os
import tempfile
import pytest
import sqlite3
from src.database.connection import DatabaseConnection
from src.analysis.silo_analyzer import SiloAnalyzer

@pytest.fixture
def temp_db():
    # Cria arquivo temporário para o SQLite de testes
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    
    # Inicializa as tabelas
    db_conn = DatabaseConnection(sqlite_path=path)
    conn = db_conn.get_sqlite_connection()
    conn.close()
    
    yield path
    
    # Limpa arquivo temporário
    if os.path.exists(path):
        os.remove(path)

def test_insert_and_get_invoices(temp_db):
    analyzer = SiloAnalyzer(db_path=temp_db)
    
    # Teste de inserção bem-sucedida
    assert analyzer.insert_nota_fiscal("2026-07-14 12:00:00", "NF123", 5000.0) is True
    # Teste de inserção de duplicado (deve retornar False devido ao UNIQUE)
    assert analyzer.insert_nota_fiscal("2026-07-14 13:00:00", "NF123", 6000.0) is False
    
    # Teste de recuperação
    invoices = analyzer.get_invoices()
    assert len(invoices) == 1
    assert invoices[0]["numero_nf"] == "NF123"
    assert invoices[0]["quantidade_kg"] == 5000.0
    assert invoices[0]["data_nf"] == "2026-07-14 12:00:00"

def test_smooth_readings():
    analyzer = SiloAnalyzer(db_path=":memory:")
    
    readings = [
        {"data": "2026-07-14 10:00:00", "peso_bruto": 1000.0},
        {"data": "2026-07-14 11:00:00", "peso_bruto": 950.0},
        {"data": "2026-07-14 12:00:00", "peso_bruto": 900.0},
        {"data": "2026-07-14 13:00:00", "peso_bruto": 850.0},
    ]
    
    smoothed = analyzer.smooth_readings(readings, window_size=3)
    
    assert len(smoothed) == 4
    # Primeira leitura (janela size 1): (1000) / 1 = 1000
    assert smoothed[0]["peso_suavizado"] == 1000.0
    # Segunda leitura (janela size 2): (1000 + 950) / 2 = 975
    assert smoothed[1]["peso_suavizado"] == 975.0
    # Terceira leitura (janela size 3): (1000 + 950 + 900) / 3 = 950
    assert smoothed[2]["peso_suavizado"] == 950.0
    # Quarta leitura (janela size 3): (950 + 900 + 850) / 3 = 900
    assert smoothed[3]["peso_suavizado"] == 900.0

def test_analyze_silo_and_accuracy(temp_db):
    analyzer = SiloAnalyzer(db_path=temp_db)
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    
    # 1. Popula Lotes e Silos para satisfazer chaves estrangeiras
    cursor.execute("INSERT INTO lotes (id_lote, codigo_lote, aviario_lote) VALUES (85, 'LOTE85', 'Aviario85')")
    cursor.execute("INSERT INTO silos (id_silo, lote_id, capacidade_kg) VALUES ('Silo-819-01', 85, 10000.0)")
    
    # 2. Popula Leituras simulando consumo e carregamentos
    readings = [
        ("Silo-819-01", "2026-07-14T08:00:00", 5000.0, 5000.0, 0.0),
        ("Silo-819-01", "2026-07-14T09:00:00", 4900.0, 4900.0, 0.0),
        ("Silo-819-01", "2026-07-14T10:00:00", 4800.0, 4800.0, 0.0),
        # Carregamento de +3000 kg (de 4800 para 7800)
        ("Silo-819-01", "2026-07-14T11:00:00", 7800.0, 7800.0, 0.0),
        ("Silo-819-01", "2026-07-14T12:00:00", 7700.0, 7700.0, 0.0),
    ]
    cursor.executemany("""
        INSERT INTO leituras (silo_id, data_leitura, valor_racao_g, valor_racao_kg, consumo_kg)
        VALUES (?, ?, ?*1000, ?, ?)
    """, readings)
    conn.commit()
    cursor.close()
    conn.close()
    
    # 3. Analisa silo
    res = analyzer.analyze_silo("Silo-819-01", smoothing_window=1, load_threshold=500.0)
    
    assert len(res["loadings"]) == 1
    assert res["loadings"][0]["quantidade_carregada"] == 3000.0
    assert res["loadings"][0]["data"] == "2026-07-14T11:00:00"
    
    # Consumo diário (100 + 100 + 100 = 300 kg)
    assert res["daily_consumption"]["2026-07-14"] == 300.0
    
    # 4. Cadastra Nota Fiscal com valor ligeiramente diferente para avaliar acurácia (3100 kg carregados em nota)
    analyzer.insert_nota_fiscal("2026-07-14 11:15:00", "NF999", 3100.0)
    
    # 5. Avalia acurácia
    acc_report = analyzer.evaluate_sensor_accuracy("Silo-819-01", window_hours=2, smoothing_window=1, load_threshold=500.0)
    assert acc_report["status"] == "OK"
    assert acc_report["total_invoices"] == 1
    assert acc_report["matched_loadings"] == 1
    
    # Diferença: 3000 kg (sensor) - 3100 kg (nota) = -100 kg
    report_detail = acc_report["accuracy_report"][0]
    assert report_detail["diferenca_kg"] == -100.0
    # Erro = 100/3100 = 3.22%, Acurácia = 96.77%
    assert report_detail["acuracia_pct"] == 96.77
    assert acc_report["overall_accuracy_pct"] == 96.77
