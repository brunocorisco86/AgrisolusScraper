import os
import sqlite3
from dotenv import load_dotenv
from src.utils.logger import setup_logger

logger = setup_logger(name="database_connection", log_file="test_run.log")

class DatabaseConnection:
    """
    Gerencia as conexões com o banco de dados local (SQLite).
    """
    def __init__(self, sqlite_path=None):
        load_dotenv()
        self.sqlite_path = sqlite_path if sqlite_path is not None else os.getenv("SQLITE_PATH", "local_fallback.db")

        logger.info("DatabaseConnection inicializada.")
        logger.info(f"Caminho do SQLite: {self.sqlite_path}")

    def get_sqlite_connection(self) -> sqlite3.Connection:
        """
        Abre e retorna uma conexão com o SQLite local, garantindo que as tabelas estejam criadas.
        Retorna:
            sqlite3.Connection
        """
        try:
            logger.info(f"Conectando ao banco SQLite local: {self.sqlite_path}")
            conn = sqlite3.connect(self.sqlite_path)
            conn.execute("PRAGMA foreign_keys = ON;")
            
            # Inicializa a estrutura das tabelas localmente
            self._init_local_db(conn)
            
            return conn
        except Exception as e:
            logger.error(f"Erro ao conectar ou inicializar o SQLite local: {e}")
            raise

    def _init_local_db(self, conn):
        """
        Cria a estrutura de tabelas do MER definitivo no SQLite local.
        """
        cursor = conn.cursor()
        try:
            logger.info("Verificando/inicializando tabelas no SQLite local...")
            
            # 1. Tabela de Lotes
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS lotes (
                id_lote INTEGER PRIMARY KEY,
                codigo_lote TEXT,
                empresa TEXT,
                estabelecimento TEXT,
                aviario TEXT,
                linhagem TEXT,
                qtd_alojamento INTEGER,
                data_alojamento TEXT,
                saldo_frangos INTEGER,
                aviario_lote TEXT UNIQUE,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # 2. Tabela de Silos
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS silos (
                id_silo TEXT PRIMARY KEY,
                lote_id INTEGER,
                capacidade_kg REAL,
                FOREIGN KEY (lote_id) REFERENCES lotes(id_lote) ON DELETE CASCADE
            );
            """)

            # 3. Tabela de Leituras
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS leituras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                silo_id TEXT,
                data_leitura TEXT NOT NULL,
                valor_racao_g REAL,
                valor_racao_kg REAL,
                consumo_kg REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (silo_id) REFERENCES silos(id_silo) ON DELETE CASCADE,
                UNIQUE (silo_id, data_leitura)
            );
            """)

            # 4. Tabela de Alertas
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS alertas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lote_id INTEGER,
                tipo_alerta INTEGER,
                tipo_alerta_str TEXT,
                data_alerta TEXT NOT NULL,
                mensagem TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lote_id) REFERENCES lotes(id_lote) ON DELETE CASCADE,
                UNIQUE (lote_id, data_alerta)
            );
            """)

            # 5. Tabela de Calibrações
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS calibracoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lote_id INTEGER,
                numero_serial TEXT,
                zona INTEGER,
                zona_str TEXT,
                data_calibracao TEXT NOT NULL,
                idade INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lote_id) REFERENCES lotes(id_lote) ON DELETE CASCADE,
                UNIQUE (lote_id, data_calibracao)
            );
            """)

            # 6. Tabela de Histórico de Scraping (SLA)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS historico_scraping (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                silo_id TEXT NOT NULL,
                data_tentativa TEXT NOT NULL,
                sucesso_conexao INTEGER DEFAULT 1,
                achou_dados_novos INTEGER DEFAULT 0,
                peso_kg REAL,
                data_leitura TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (silo_id) REFERENCES silos(id_silo) ON DELETE CASCADE,
                UNIQUE (silo_id, data_tentativa)
            );
            """)

            # Garantir de forma incremental que a coluna data_leitura exista
            try:
                cursor.execute("ALTER TABLE historico_scraping ADD COLUMN data_leitura TEXT;")
            except sqlite3.OperationalError:
                # Se a coluna já existir, o SQLite lançará um erro operacional, ignoramos.
                pass

            # 7. Tabela de Notas Fiscais (Entrada de Ração)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS notas_fiscais (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_nf TEXT NOT NULL,
                numero_nf TEXT UNIQUE NOT NULL,
                quantidade_kg REAL NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """)

            conn.commit()
            logger.info("Estrutura do SQLite local validada com sucesso.")
        except Exception as e:
            conn.rollback()
            logger.error(f"Erro ao inicializar tabelas do SQLite: {e}")
            raise

