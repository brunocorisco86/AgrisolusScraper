import os
import sqlite3
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from src.database.connection import DatabaseConnection
from scripts.run_periodic_summary import main as run_summary_main
from scripts.run_sla_report import main as run_sla_main

TEST_DB_PATH = "local_periodic_test.db"

@pytest.fixture
def setup_test_db(monkeypatch):
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    monkeypatch.setenv("SQLITE_PATH", TEST_DB_PATH)
    
    # Supress Telegram keys
    monkeypatch.setenv("TELEGRAM_TOKEN", "fake_token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "fake_chat_id")
    
    db_conn = DatabaseConnection()
    conn = db_conn.get_sqlite_connection()
    
    # Insere lote e silos de teste para o Aviário 819
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO lotes (id_lote, codigo_lote, empresa, estabelecimento, aviario, linhagem, qtd_alojamento, data_alojamento, saldo_frangos, aviario_lote)
        VALUES (819001, '85', 'Test Farm', 'Test Estab', 'Aviário 819', 'ROSS', 25000, '2026-06-05T11:00:00', 25000, '85-Aviário 819')
    """)
    cursor.execute("""
        INSERT INTO silos (id_silo, lote_id, capacidade_kg)
        VALUES ('Silo-Test-819', 819001, 10000.0)
    """)
    conn.commit()
    conn.close()
    
    yield db_conn
    
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

@patch("src.database.connection.DatabaseConnection.get_supabase_client", return_value=None)
@patch("src.bot.notifier.TelegramNotifier.send_periodic_summary")
def test_periodic_summary_script(mock_send_summary, mock_get_supabase, setup_test_db):
    conn = setup_test_db.get_sqlite_connection()
    cursor = conn.cursor()
    
    # 1. Caso de silo ONLINE (última leitura há 1 hora)
    last_leitura_online = (datetime.now() - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S")
    cursor.execute("""
        INSERT INTO leituras (silo_id, data_leitura, valor_racao_g, valor_racao_kg, consumo_kg)
        VALUES ('Silo-Test-819', ?, 5000000.0, 5000.0, 10.0)
    """, (last_leitura_online,))
    conn.commit()
    conn.close()
    
    # Executa o script de resumo
    run_summary_main()
    
    # O silo está online, logo occurrences deve estar vazia []
    mock_send_summary.assert_called_once_with([])
    
    # 2. Caso de silo OFFLINE (última leitura há 5 horas)
    conn = setup_test_db.get_sqlite_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM leituras") # Limpa leituras anteriores
    
    last_leitura_offline = (datetime.now() - timedelta(hours=5)).strftime("%Y-%m-%dT%H:%M:%S")
    cursor.execute("""
        INSERT INTO leituras (silo_id, data_leitura, valor_racao_g, valor_racao_kg, consumo_kg)
        VALUES ('Silo-Test-819', ?, 5000000.0, 5000.0, 10.0)
    """, (last_leitura_offline,))
    conn.commit()
    conn.close()
    
    mock_send_summary.reset_mock()
    run_summary_main()
    
    # Deve disparar o resumo periódico com a ocorrência do silo offline
    assert mock_send_summary.call_count == 1
    call_args = mock_send_summary.call_args[0][0]
    assert len(call_args) == 1
    assert call_args[0]["silo_id"] == "Silo-Test-819"
    assert call_args[0]["offline_hours"] >= 4.9

@patch("src.database.connection.DatabaseConnection.get_supabase_client", return_value=None)
@patch("src.bot.notifier.TelegramNotifier.send_daily_sla_report")
def test_sla_report_script(mock_send_sla, mock_get_supabase, setup_test_db):
    # Inserir leituras para o período de SLA
    # Período é das 17h de ontem às 17h de hoje.
    now = datetime.now()
    end_dt = now.replace(hour=17, minute=0, second=0, microsecond=0)
    start_dt = end_dt - timedelta(days=1)
    
    # Vamos gerar exatamente 12 leituras de hora em hora
    conn = setup_test_db.get_sqlite_connection()
    cursor = conn.cursor()
    
    for i in range(12):
        leitura_time = (start_dt + timedelta(hours=i)).strftime("%Y-%m-%dT%H:%M:%S")
        cursor.execute("""
            INSERT INTO leituras (silo_id, data_leitura, valor_racao_g, valor_racao_kg, consumo_kg)
            VALUES ('Silo-Test-819', ?, 4000000.0, ?, 10.0)
        """, (leitura_time, 4000.0 - i * 10.0))
        
    conn.commit()
    conn.close()
    
    # Executa o script de SLA
    run_sla_main()
    
    # Esperamos que send_daily_sla_report tenha sido chamado
    assert mock_send_sla.call_count == 1
    silos_sla = mock_send_sla.call_args[0][1]
    
    assert len(silos_sla) == 1
    silo_metrics = silos_sla[0]
    assert silo_metrics["silo_id"] == "Silo-Test-819"
    # SLA deve ser de 50.0% (12 leituras das 24 esperadas)
    assert silo_metrics["sla_percentage"] == 50.0
    # Consumo total deve ser 12 leituras * 10 kg = 120 kg
    assert silo_metrics["total_consumed_kg"] == 120.0
    # Saldo atual de ração (última das leituras) deve ser 4000.0 - 11 * 10 = 3890.0 kg
    assert silo_metrics["current_balance_kg"] == 3890.0
