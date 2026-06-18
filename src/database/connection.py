import os
import sqlite3
from supabase import create_client, Client
from dotenv import load_dotenv
from src.utils.logger import setup_logger

logger = setup_logger(name="database_connection", log_file="test_run.log")

class DatabaseConnection:
    """
    Gerencia as conexões com o banco de dados remoto (Supabase via HTTP Client)
    e o banco de dados local (SQLite Fallback).
    """
    def __init__(self, supabase_url=None, secret_key=None, sqlite_path=None):
        load_dotenv()
        self.api_url = supabase_url if supabase_url is not None else os.getenv("SUPABASE_API_URL")
        self.secret_key = secret_key if secret_key is not None else os.getenv("SECRET_KEY")
        self.sqlite_path = sqlite_path if sqlite_path is not None else os.getenv("SQLITE_PATH", "local_fallback.db")

        
        # Se a URL contiver o caminho REST do supabase (/rest/v1/), limpamos para obter a URL base
        if self.api_url and "/rest/v1" in self.api_url:
            self.supabase_url = self.api_url.split("/rest/v1")[0]
        else:
            self.supabase_url = self.api_url


        logger.info("DatabaseConnection inicializada.")
        logger.info(f"Caminho do SQLite: {self.sqlite_path}")
        if self.supabase_url:
            logger.info(f"URL base do Supabase resolvida: {self.supabase_url}")
        else:
            logger.warning("SUPABASE_API_URL não configurada no arquivo .env.")

    def get_supabase_client(self) -> Client:
        """
        Instancia e retorna o cliente oficial do Supabase utilizando a SECRET_KEY (acesso administrativo/bypass RLS).
        Retorna:
            supabase.Client ou None se falhar ou se credenciais estiverem ausentes.
        """
        if not self.supabase_url or not self.secret_key:
            logger.error("Tentativa de conexão com o Supabase sem credenciais completas (SUPABASE_API_URL e SECRET_KEY).")
            return None
        
        try:
            logger.info("Criando cliente do Supabase...")
            client: Client = create_client(self.supabase_url, self.secret_key)
            logger.info("Cliente Supabase criado com sucesso!")
            return client
        except Exception as e:
            logger.error(f"Erro inesperado ao conectar ao Supabase: {e}")
            return None

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
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (silo_id) REFERENCES silos(id_silo) ON DELETE CASCADE,
                UNIQUE (silo_id, data_tentativa)
            );
            """)

            conn.commit()
            logger.info("Estrutura do SQLite local validada com sucesso.")
        except Exception as e:
            conn.rollback()
            logger.error(f"Erro ao inicializar tabelas do SQLite: {e}")
            raise
