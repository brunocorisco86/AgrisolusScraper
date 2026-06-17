import os
import pytest
from src.database.connection import DatabaseConnection

TEST_DB_PATH = "local_fallback_test.db"

@pytest.fixture(autouse=True)
def cleanup_test_db():
    # Garante que o banco de teste antigo é apagado antes de iniciar e depois de finalizar
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    yield
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

def test_sqlite_initialization(monkeypatch):
    # Força a variável SQLITE_PATH a apontar para o banco de teste
    monkeypatch.setenv("SQLITE_PATH", TEST_DB_PATH)
    
    db = DatabaseConnection()
    assert db.sqlite_path == TEST_DB_PATH

    # Tenta conectar e criar as tabelas
    conn = db.get_sqlite_connection()
    assert conn is not None
    assert os.path.exists(TEST_DB_PATH), "O arquivo SQLite de teste não foi criado."

    # Verifica se as tabelas existem no SQLite
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    
    expected_tables = ["lotes", "silos", "leituras", "alertas", "calibracoes"]
    for table in expected_tables:
        assert table in tables, f"A tabela '{table}' não foi criada no SQLite."

    # Verifica se a tabela 'silos' possui a coluna capacidade_kg e lote_id
    cursor.execute("PRAGMA table_info(silos);")
    columns = [col[1] for col in cursor.fetchall()]
    assert "id_silo" in columns
    assert "lote_id" in columns
    assert "capacidade_kg" in columns

    conn.close()

def test_supabase_connection_without_url(monkeypatch):
    # Remove a DATABASE_URL para testar o comportamento resiliente da classe
    monkeypatch.delenv("DATABASE_URL", raising=False)
    
    db = DatabaseConnection()
    conn = db.get_supabase_connection()
    
    # Deve retornar None amigavelmente sem levantar exceção
    assert conn is None
