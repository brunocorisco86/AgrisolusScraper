import os
import sqlite3
import pytest
from unittest.mock import MagicMock
from src.database.connection import DatabaseConnection
from src.database.sync import SyncService

TEST_DB_PATH = "local_sync_test.db"

@pytest.fixture
def test_db(monkeypatch):
    # Força o caminho do SQLite de teste
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    monkeypatch.setenv("SQLITE_PATH", TEST_DB_PATH)
    
    db_conn = DatabaseConnection()
    # Abre conexão SQLite para criar tabelas
    conn = db_conn.get_sqlite_connection()
    conn.close()
    
    yield db_conn
    
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

def test_sync_process(test_db):
    # 1. Inserir dados fictícios no SQLite local para simular dados offline pendentes
    sqlite_conn = sqlite3.connect(TEST_DB_PATH)
    cursor = sqlite_conn.cursor()
    
    # Inserir Lote
    cursor.execute("""
        INSERT INTO lotes (id_lote, codigo_lote, empresa, estabelecimento, aviario, linhagem, qtd_alojamento, data_alojamento, saldo_frangos, aviario_lote)
        VALUES (12345, '85', 'Marcelo Fumagalli', 'Marcelo Fumagalli', 'Aviário 819', 'ROSS 308', 26800, '2026-06-05 11:00:00', 26800, '85-Aviário 819')
    """)

    # Inserir Silo
    cursor.execute("INSERT INTO silos (id_silo, lote_id, capacidade_kg) VALUES ('Silo-01', 12345, 18000.0)")
    # Inserir Leitura 1 (mais antiga)
    cursor.execute("""
        INSERT INTO leituras (silo_id, data_leitura, valor_racao_g, valor_racao_kg, consumo_kg)
        VALUES ('Silo-01', '2026-06-17 15:00:00', 2200000.0, 2200.0, 50.0)
    """)
    # Inserir Leitura 2 (mais recente)
    cursor.execute("""
        INSERT INTO leituras (silo_id, data_leitura, valor_racao_g, valor_racao_kg, consumo_kg)
        VALUES ('Silo-01', '2026-06-17 16:00:00', 2133650.0, 2133.65, 66.35)
    """)
    # Inserir Alerta
    cursor.execute("""
        INSERT INTO alertas (lote_id, tipo_alerta, tipo_alerta_str, data_alerta, mensagem)
        VALUES (12345, 11, 'Energia', '2026-06-10 10:28:22', 'Queda de energia detectada')
    """)
    # Inserir Calibração
    cursor.execute("""
        INSERT INTO calibracoes (lote_id, numero_serial, zona, zona_str, data_calibracao, idade)
        VALUES (12345, '00012665', 2, 'Centro', '2026-06-10 09:44:16', 4)
    """)
    sqlite_conn.commit()
    sqlite_conn.close()

    # 2. Mockar o cliente Supabase
    mock_client = MagicMock()
    mock_table = MagicMock()
    mock_client.table.return_value = mock_table
    mock_table.upsert.return_value = mock_table
    mock_table.execute.return_value = MagicMock()
    
    # Faz o mock do método get_supabase_client
    test_db.get_supabase_client = MagicMock(return_value=mock_client)

    # 3. Executar o SyncService
    sync_service = SyncService(test_db)
    success = sync_service.sync_local_to_remote()
    
    assert success is True, "O serviço de sincronização falhou."

    # 4. Validar se os métodos do cliente Supabase foram chamados para as tabelas corretas
    table_calls = [call[0][0] for call in mock_client.table.call_args_list]
    assert len(table_calls) == 5, f"Esperava 5 chamadas de tabela, obteve {len(table_calls)}"
    assert "lotes" in table_calls
    assert "silos" in table_calls
    assert "leituras" in table_calls
    assert "alertas" in table_calls
    assert "calibracoes" in table_calls


    # 5. Validar que as tabelas de leituras, alertas e calibrações foram apagadas localmente no SQLite
    # enquanto lotes e silos persistem localmente como cache
    sqlite_conn2 = sqlite3.connect(TEST_DB_PATH)
    cursor2 = sqlite_conn2.cursor()
    
    cursor2.execute("SELECT COUNT(*) FROM lotes")
    assert cursor2.fetchone()[0] == 1, "A tabela de lotes local foi limpa incorretamente!"

    cursor2.execute("SELECT COUNT(*) FROM silos")
    assert cursor2.fetchone()[0] == 1, "A tabela de silos local foi limpa incorretamente!"

    cursor2.execute("SELECT COUNT(*) FROM leituras")
    assert cursor2.fetchone()[0] == 1, "A tabela de leituras local deveria preservar o último registro de cada silo pós-sincronização!"
    
    cursor2.execute("SELECT data_leitura FROM leituras LIMIT 1")
    assert cursor2.fetchone()[0] == '2026-06-17 16:00:00', "A leitura preservada localmente deveria ser a mais recente!"

    cursor2.execute("SELECT COUNT(*) FROM alertas")
    assert cursor2.fetchone()[0] == 0, "A tabela de alertas local não foi limpa pós-sincronização!"

    cursor2.execute("SELECT COUNT(*) FROM calibracoes")
    assert cursor2.fetchone()[0] == 0, "A tabela de calibrações local não foi limpa pós-sincronização!"
    
    sqlite_conn2.close()
