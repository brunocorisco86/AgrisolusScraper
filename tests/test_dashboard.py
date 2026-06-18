import os
import pytest
from unittest.mock import MagicMock, patch
from src.database.connection import DatabaseConnection
from src.dashboard.app import load_dashboard_data

TEST_DB_PATH = "local_dashboard_test.db"

@pytest.fixture
def setup_test_db(monkeypatch):
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    monkeypatch.setenv("SQLITE_PATH", TEST_DB_PATH)
    
    db_conn = DatabaseConnection()
    conn = db_conn.get_sqlite_connection()
    
    # Insere lote e silos de teste para o Aviário 819
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO lotes (id_lote, codigo_lote, empresa, estabelecimento, aviario, linhagem, qtd_alojamento, data_alojamento, saldo_frangos, aviario_lote)
        VALUES (819002, '85', 'Test Farm', 'Test Estab', 'Aviário 819', 'ROSS', 25000, '2026-06-05T11:00:00', 25000, '85-Aviário 819')
    """)
    cursor.execute("""
        INSERT INTO silos (id_silo, lote_id, capacidade_kg)
        VALUES ('Silo-Test-819', 819002, 10000.0)
    """)
    cursor.execute("""
        INSERT INTO leituras (silo_id, data_leitura, valor_racao_g, valor_racao_kg, consumo_kg)
        VALUES ('Silo-Test-819', '2026-06-17T12:00:00', 5000000.0, 5000.0, 10.0)
    """)
    conn.commit()
    conn.close()
    
    yield db_conn
    
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

@patch("src.database.connection.DatabaseConnection.get_supabase_client", return_value=None)
def test_dashboard_loader_sqlite(mock_get_supabase, setup_test_db):
    """
    Testa se o carregador de dados do dashboard lê corretamente do SQLite local
    quando o Supabase está offline.
    """
    df_lotes, df_silos, df_readings, df_alertas, df_calibracoes, using_supabase = load_dashboard_data()
    
    assert using_supabase is False
    assert not df_lotes.empty
    assert df_lotes.iloc[0]["id_lote"] == 819002
    assert not df_silos.empty
    assert df_silos.iloc[0]["id_silo"] == "Silo-Test-819"
    assert not df_readings.empty
    assert df_readings.iloc[0]["silo_id"] == "Silo-Test-819"
    assert "data_leitura_dt" in df_readings.columns
