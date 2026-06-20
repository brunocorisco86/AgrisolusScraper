import os
import sqlite3
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from src.database.connection import DatabaseConnection
from scripts.run_daily_summary_telegram import main as run_daily_main

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
@patch("src.utils.log_monitor.CronLogMonitor.analyze_logs")
@patch("src.bot.notifier.TelegramNotifier.send_message")
def test_daily_summary_telegram_script(mock_send_message, mock_analyze_logs, mock_get_supabase, setup_test_db):
    # Mock do analisador de logs para retornar dados limpos nos testes
    mock_analyze_logs.return_value = {
        "cron_active": True,
        "last_execution_time": "2026-06-20 11:30:00",
        "errors": [],
        "warnings": []
    }
    conn = setup_test_db.get_sqlite_connection()
    cursor = conn.cursor()
    
    # 1. Inserir histórico de scraping fictício para o dia de hoje
    today_str = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("""
        INSERT INTO historico_scraping (silo_id, data_tentativa, sucesso_conexao, achou_dados_novos, peso_kg, data_leitura)
        VALUES ('Silo-Test-819', ?, 1, 1, 5000.0, ?)
    """, (f"{today_str}T10:00:00", f"{today_str}T10:00:00"))
    cursor.execute("""
        INSERT INTO historico_scraping (silo_id, data_tentativa, sucesso_conexao, achou_dados_novos, peso_kg, data_leitura)
        VALUES ('Silo-Test-819', ?, 1, 0, 5000.0, ?)
    """, (f"{today_str}T11:00:00", f"{today_str}T10:00:00"))
    
    # Inserir leituras para o período de SLA
    # Período é de 24 horas anteriores à execução (das 19h de ontem às 19h de hoje)
    now = datetime.now()
    end_24h = now.replace(hour=19, minute=0, second=0, microsecond=0)
    start_24h = end_24h - timedelta(days=1)
    
    # Vamos gerar exatamente 12 leituras de hora em hora a partir do início do período de 24h
    for i in range(12):
        leitura_time = (start_24h + timedelta(hours=i+1)).strftime("%Y-%m-%dT%H:%M:%S")
        cursor.execute("""
            INSERT INTO leituras (silo_id, data_leitura, valor_racao_g, valor_racao_kg, consumo_kg)
            VALUES ('Silo-Test-819', ?, 4000000.0, ?, 10.0)
        """, (leitura_time, 4000.0 - i * 10.0))
        
    conn.commit()
    conn.close()
    
    # Executa o novo script de resumo consolidado diário
    run_daily_main()
    
    # Valida se send_message foi chamado
    assert mock_send_message.call_count == 1
    sent_text = mock_send_message.call_args[0][0]
    
    # Validações do texto consolidado
    assert "RESUMO DIÁRIO AGRISOLUS" in sent_text
    assert "Tentativas de scraping hoje: <b>2</b>" in sent_text
    assert "Sucessos de conexão: <b>2</b>" in sent_text
    assert "Dados novos/exclusivos: <b>1 leituras</b>" in sent_text
    assert "Silo-Test-819" in sent_text
    assert "SLA de Conexão: <b>50.0%</b>" in sent_text  # 12 leituras de 24h esperadas
    assert "Consumo 24h: <b>120.00 kg</b>" in sent_text
    assert "Saldo de Ração: <b>3890.00 kg</b>" in sent_text  # 4000.0 - 110.0
    
    # Validações da seção de Auditoria de Logs
    assert "Auditoria do Sistema e Logs (24h)" in sent_text
    assert "Status do Cron: ✅ <b>Ativo</b>" in sent_text
    assert "Erros/Exceções detectados: ✅ <b>Nenhum erro encontrado</b>" in sent_text
