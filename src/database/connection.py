import os
import sqlite3
import psycopg2
from dotenv import load_dotenv
from src.utils.logger import setup_logger

# Configura o logger do módulo
logger = setup_logger(name="database_connection", log_file="test_run.log")

class DatabaseConnection:
    """
    Gerencia as conexões com o banco de dados remoto (Supabase PostgreSQL)
    e o banco de dados local (SQLite Fallback).
    """
    def __init__(self):
        # Carrega variáveis de ambiente
        load_dotenv()
        self.database_url = os.getenv("DATABASE_URL")
        self.sqlite_path = os.getenv("SQLITE_PATH", "local_fallback.db")
        
        logger.info(f"Classe DatabaseConnection inicializada.")
        logger.info(f"Caminho do SQLite configurado: {self.sqlite_path}")
        if not self.database_url:
            logger.warning("DATABASE_URL não configurada no arquivo .env. Conexão remota com o Supabase falhará.")

    def get_supabase_connection(self):
        """
        Tenta abrir e retornar uma conexão direta com o PostgreSQL do Supabase.
        Retorna:
            psycopg2.connection ou None se a conexão falhar (ex: sem internet ou credenciais incorretas).
        """
        if not self.database_url:
            logger.error("Tentativa de conexão com Supabase sem DATABASE_URL configurada.")
            return None
        
        try:
            logger.info("Tentando conectar ao banco de dados do Supabase...")
            conn = psycopg2.connect(self.database_url)
            logger.info("Conexão com o Supabase estabelecida com sucesso!")
            return conn
        except psycopg2.OperationalError as e:
            logger.error(f"Erro de conexão com o Supabase (banco offline ou sem internet): {e}")
            return None
        except Exception as e:
            logger.error(f"Erro inesperado ao conectar ao Supabase: {e}")
            return None

    def get_sqlite_connection(self):
        """
        Abre e retorna uma conexão com o SQLite local, garantindo que as tabelas estejam criadas.
        Retorna:
            sqlite3.Connection
        """
        try:
            logger.info(f"Conectando ao banco SQLite local: {self.sqlite_path}")
            conn = sqlite3.connect(self.sqlite_path)
            
            # Habilita suporte a chaves estrangeiras no SQLite (desativado por padrão)
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

            conn.commit()
            logger.info("Estrutura do SQLite local validada com sucesso.")
        except Exception as e:
            conn.rollback()
            logger.error(f"Erro ao inicializar tabelas do SQLite: {e}")
            raise
