"""
Ponto de entrada principal para a execução horária do scraper Agrisolus.
"""
import os
import sys
from dotenv import load_dotenv

# Garante que o Python encontre o pacote 'src'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database.connection import DatabaseConnection
from src.scraper.extractor import AgrisolusScraper
from src.utils.logger import setup_logger

# Configura o logger principal para a execução
logger = setup_logger(name="main_execution", log_file="test_run.log")

def run():
    logger.info("==================================================")
    # Exibe a data/hora local
    from datetime import datetime
    logger.info(f"INICIANDO EXECUÇÃO DO SCRAPER - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("==================================================")
    
    # 1. Carrega variáveis de ambiente
    load_dotenv()

    # 2. Inicializa conexão
    db_conn = DatabaseConnection()

    # 3. Inicializa Scraper
    scraper = AgrisolusScraper(db_conn=db_conn)

    # 4. Efetua Login
    if not scraper.login():
        logger.error("Falha ao efetuar login. A execução do scraper foi cancelada.")
        scraper.record_global_login_failure()
        return

    # 5. Mapeia e processa os lotes
    # Atualiza a lista de lotes no arquivo local lotes_config.json
    logger.info("Atualizando lote_config.json com lotes ativos da listagem...")
    lotes_count = scraper.generate_lotes_config()
    
    if lotes_count > 0:
        logger.info(f"Processando raspagem de dados para {lotes_count} lotes...")
        scraper.scrape_and_persist()
    else:
        logger.warning("Nenhum lote ativo encontrado para raspagem.")

    logger.info("==================================================")
    logger.info("EXECUÇÃO DO SCRAPER FINALIZADA COM SUCESSO!")
    logger.info("==================================================")

if __name__ == "__main__":
    run()
