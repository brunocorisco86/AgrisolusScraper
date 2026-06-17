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
        INSERT INTO lotes (id_lote, codigo_lote, empresa, estabelecimento, aviario, linhagem, qtd_alojamento, data_alojamento, saldo_frangos)
        VALUES (12345, '85', 'Marcelo Fumagalli', 'Marcelo Fumagalli', 'Aviário 819', 'ROSS 308', 26800, '2026-06-05 11:00:00', 26800)
    """)
    # Inserir Silo
    cursor.execute("INSERT INTO silos (id_silo, lote_id, capacidade_kg) VALUES ('Silo-01', 12345, 18000.0)")
    # Inserir Leitura
    cursor.execute("""
        INSERT INTO leituras (silo_id, data_leitura, valor_racao_g, valor_racao_kg, consumo_kg)
        VALUES ('Silo-01', '2026-06-17 16:00:00', 2133650.0, 2133.65, 150.0)
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

    # 2. Mockar a conexão com o Supabase
    mock_pg_conn = MagicMock()
    mock_pg_cursor = MagicMock()
    mock_pg_conn.cursor.return_value = mock_pg_cursor
    
    # Faz o mock do método get_supabase_connection da conexão
    test_db.get_supabase_connection = MagicMock(return_value=mock_pg_conn)

    # 3. Executar o SyncService
    sync_service = SyncService(test_db)
    success = sync_service.sync_local_to_remote()
    
    assert success is True, "O serviço de sincronização falhou."

    # 4. Validar se os métodos do cursor PostgreSQL (Supabase) foram chamados com o SQL correto
    # Deve ter chamado execute para lotes, silos, leituras, alertas e calibrações
    calls = mock_pg_cursor.execute.call_args_list
    assert len(calls) == 5, f"Esperava 5 execuções SQL no Postgres, obteve {len(calls)}"

    # Verificar se as chamadas de SQL executaram as tabelas corretas
    inserted_tables = []
    for call in calls:
        sql = call[0][0].lower()
        if "insert into lotes" in sql:
            inserted_tables.append("lotes")
        elif "insert into silos" in sql:
            inserted_tables.append("silos")
        elif "insert into leituras" in sql:
            inserted_tables.append("leituras")
        elif "insert into alertas" in sql:
            inserted_tables.append("alertas")
        elif "insert into calibracoes" in sql:
            inserted_tables.append("calibracoes")

    assert "lotes" in inserted_tables
    assert "silos" in inserted_tables
    assert "leituras" in inserted_tables
    assert "alertas" in inserted_tables
    assert "calibracoes" in inserted_tables

    # 5. Validar que as tabelas de leituras, alertas e calibrações foram apagadas localmente no SQLite
    # enquanto lotes e silos persistem localmente como cache
    sqlite_conn2 = sqlite3.connect(TEST_DB_PATH)
    cursor2 = sqlite_conn2.cursor()
    
    cursor2.execute("SELECT COUNT(*) FROM lotes")
    assert cursor2.fetchone()[0] == 1, "A tabela de lotes local foi limpa incorretamente!"

    cursor2.execute("SELECT COUNT(*) FROM silos")
    assert cursor2.fetchone()[0] == 1, "A tabela de silos local foi limpa incorretamente!"

    cursor2.execute("SELECT COUNT(*) FROM leituras")
    assert cursor2.fetchone()[0] == 0, "A tabela de leituras local não foi limpa pós-sincronização!"

    cursor2.execute("SELECT COUNT(*) FROM alertas")
    assert cursor2.fetchone()[0] == 0, "A tabela de alertas local não foi limpa pós-sincronização!"

    cursor2.execute("SELECT COUNT(*) FROM calibracoes")
    assert cursor2.fetchone()[0] == 0, "A tabela de calibrações local não foi limpa pós-sincronização!"
    
    sqlite_conn2.close()
