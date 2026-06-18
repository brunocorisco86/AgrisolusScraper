import os
import sqlite3
import pytest
from unittest.mock import MagicMock
from bs4 import BeautifulSoup
from src.database.connection import DatabaseConnection
from src.scraper.extractor import AgrisolusScraper

TEST_DB_PATH = "local_scraper_test.db"

@pytest.fixture
def test_db(monkeypatch):
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    monkeypatch.setenv("SQLITE_PATH", TEST_DB_PATH)
    
    db_conn = DatabaseConnection()
    conn = db_conn.get_sqlite_connection()
    conn.close()
    
    yield db_conn
    
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

def test_parse_html_table1():
    scraper = AgrisolusScraper()
    
    # Simula HTML da Tabela 1
    html = """
    <table class="table col-lg-12">
        <tr><td>Data Alojamento05/06/2026 11:00:00</td></tr>
        <tr><td>Qtd. Alojamento26800</td></tr>
        <tr><td>Saldo de Frangos26800</td></tr>
    </table>
    """
    soup = BeautifulSoup(html, "lxml")
    data = scraper._parse_html_table1(soup)
    
    assert data.get("data_alojamento") == "2026-06-05T11:00:00"
    assert data.get("qtd_alojamento") == 26800
    assert data.get("saldo_frangos") == 26800

def test_calculate_consumo(test_db):
    scraper = AgrisolusScraper(db_conn=test_db)
    
    # 1. Inserir uma leitura inicial no SQLite local
    conn = test_db.get_sqlite_connection()
    cursor = conn.cursor()
    
    # Prepara Lote e Silo para evitar violação de Foreign Key
    cursor.execute("INSERT INTO lotes (id_lote) VALUES (11111)")
    cursor.execute("INSERT INTO silos (id_silo, lote_id, capacidade_kg) VALUES ('Silo-Test', 11111, 10000.0)")
    
    # Leitura anterior (Peso: 5000 kg, Data: 12:00:00)
    cursor.execute("""
        INSERT INTO leituras (silo_id, data_leitura, valor_racao_g, valor_racao_kg, consumo_kg)
        VALUES ('Silo-Test', '2026-06-17T12:00:00', 5000000.0, 5000.0, 0.0)
    """)
    conn.commit()
    conn.close()
    
    # 2. Testar Consumo (Caso de queda de ração: peso atual = 4800 kg)
    # consumo esperado = 5000 - 4800 = 200 kg
    consumo_normal = scraper._calculate_consumo("Silo-Test", 4800.0, "2026-06-17T13:00:00")
    assert consumo_normal == 200.0
    
    # 3. Testar Abastecimento (Caso de aumento de ração: peso atual = 8000 kg)
    # consumo esperado = 0.0
    consumo_abastecimento = scraper._calculate_consumo("Silo-Test", 8000.0, "2026-06-17T13:00:00")
    assert consumo_abastecimento == 0.0

def test_process_lote_html_resilience(test_db, monkeypatch):
    scraper = AgrisolusScraper(db_conn=test_db)
    
    # Força o mock do Supabase client para None (simula offline)
    test_db.get_supabase_client = MagicMock(return_value=None)
    
    # Mock do envio de alertas do Telegram para evitar disparos reais nos testes
    mock_send_alert = MagicMock()
    monkeypatch.setattr("src.bot.notifier.TelegramNotifier.send_immediate_alert", mock_send_alert)
    
    # Carrega o HTML real do dump
    dump_path = "scripts/batch_details.html"
    assert os.path.exists(dump_path), "O dump scripts/batch_details.html é necessário para rodar este teste."
    
    with open(dump_path, "r", encoding="utf-8") as f:
        html_content = f.read()
        
    # Executa o processamento do HTML do lote
    link_lote = "https://s2.agrisolus.com.br/Home/Detalhes?idLote=4200000019"
    scraper._process_lote_html(html_content, link_lote)
    
    # Verifica se os alertas de Telegram foram de fato disparados para os dois silos offline
    assert mock_send_alert.call_count == 2
    
    # Verifica se os dados foram persistidos no SQLite local devido ao fallback do Supabase
    conn = test_db.get_sqlite_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id_lote, empresa, aviario, aviario_lote FROM lotes WHERE id_lote = 4200000019")
    lote = cursor.fetchone()
    assert lote is not None
    assert lote[1] == "Marcelo Fumagalli"
    assert lote[2] == "Aviário 819"
    assert lote[3] == "85-Aviário 819"

    
    cursor.execute("SELECT id_silo, capacidade_kg FROM silos WHERE lote_id = 4200000019")
    silos = cursor.fetchall()
    assert len(silos) == 2
    assert silos[0][0] in ["Silo-819-01", "Silo-819-02"]
    
    # Leituras, alertas e calibrações devem ter sido salvas no SQLite buffer local
    cursor.execute("SELECT COUNT(*) FROM leituras")
    assert cursor.fetchone()[0] == 2
    
    cursor.execute("SELECT COUNT(*) FROM alertas")
    assert cursor.fetchone()[0] == 231

    
    cursor.execute("SELECT COUNT(*) FROM calibracoes")
    assert cursor.fetchone()[0] == 16
    
    conn.close()
