"""
Módulo responsável por sincronizar dados salvos no SQLite local com o Supabase
quando a conexão com a internet for restabelecida.
"""

class SyncService:
    def __init__(self, db_conn):
        self.db_conn = db_conn

    def sync_local_to_remote(self):
        """Busca leituras pendentes no SQLite e envia para o Supabase."""
        pass
