import sqlite3
from src.utils.logger import setup_logger

logger = setup_logger(name="sync_service", log_file="test_run.log")

class SyncService:
    """
    Sincroniza os dados coletados localmente no SQLite (durante falhas de internet)
    com o banco de dados principal no Supabase via API HTTP (Supabase Client).
    """
    def __init__(self, db_conn):
        self.db_conn = db_conn

    def sync_local_to_remote(self):
        """
        Executa o fluxo de sincronização do SQLite local para o Supabase.
        Retorna True se a sincronização ocorrer com sucesso ou se não houver dados,
        e False se houver falha de rede/conexão com a API do Supabase.
        """
        # 1. Verifica se conseguimos conectar ao cliente Supabase
        client = self.db_conn.get_supabase_client()
        if not client:
            logger.warning("Supabase inacessível no momento. Sincronização cancelada. Os dados permanecem salvos localmente.")
            return False

        sqlite_conn = self.db_conn.get_sqlite_connection()
        sqlite_cursor = sqlite_conn.cursor()

        try:
            logger.info("Iniciando sincronização local -> remota via Supabase SDK...")
            
            # --- 1. Sincronizar Lotes (Upsert) ---
            sqlite_cursor.execute("SELECT id_lote, codigo_lote, empresa, estabelecimento, aviario, linhagem, qtd_alojamento, data_alojamento, saldo_frangos FROM lotes")
            lotes = sqlite_cursor.fetchall()
            if lotes:
                logger.info(f"Sincronizando {len(lotes)} lotes...")
                data_lotes = []
                for row in lotes:
                    data_lotes.append({
                        "id_lote": row[0],
                        "codigo_lote": row[1],
                        "empresa": row[2],
                        "estabelecimento": row[3],
                        "aviario": row[4],
                        "linhagem": row[5],
                        "qtd_alojamento": row[6],
                        "data_alojamento": row[7],
                        "saldo_frangos": row[8]
                    })
                # Executa o upsert no Supabase
                client.table("lotes").upsert(data_lotes).execute()

            # --- 2. Sincronizar Silos (Upsert) ---
            sqlite_cursor.execute("SELECT id_silo, lote_id, capacidade_kg FROM silos")
            silos = sqlite_cursor.fetchall()
            if silos:
                logger.info(f"Sincronizando {len(silos)} silos...")
                data_silos = []
                for row in silos:
                    data_silos.append({
                        "id_silo": row[0],
                        "lote_id": row[1],
                        "capacidade_kg": row[2]
                    })
                client.table("silos").upsert(data_silos).execute()

            # --- 3. Sincronizar Leituras (Insert/Upsert + Delete local após sucesso) ---
            sqlite_cursor.execute("SELECT id, silo_id, data_leitura, valor_racao_g, valor_racao_kg, consumo_kg FROM leituras")
            leituras = sqlite_cursor.fetchall()
            if leituras:
                logger.info(f"Sincronizando {len(leituras)} leituras...")
                data_leituras = []
                for row in leituras:
                    data_leituras.append({
                        "silo_id": row[1],
                        "data_leitura": row[2],
                        "valor_racao_g": row[3],
                        "valor_racao_kg": row[4],
                        "consumo_kg": row[5]
                    })
                # Upsert especificando on_conflict para garantir unicidade da leitura por silo/data
                client.table("leituras").upsert(data_leituras, on_conflict="silo_id,data_leitura").execute()
                
                # Após sucesso no Supabase, limpamos as leituras no SQLite
                sqlite_cursor.execute("DELETE FROM leituras")
                logger.info("Leituras locais removidas pós-sincronização.")

            # --- 4. Sincronizar Alertas (Insert/Upsert + Delete local após sucesso) ---
            sqlite_cursor.execute("SELECT id, lote_id, tipo_alerta, tipo_alerta_str, data_alerta, mensagem FROM alertas")
            alertas = sqlite_cursor.fetchall()
            if alertas:
                logger.info(f"Sincronizando {len(alertas)} alertas...")
                data_alertas = []
                for row in alertas:
                    data_alertas.append({
                        "lote_id": row[1],
                        "tipo_alerta": row[2],
                        "tipo_alerta_str": row[3],
                        "data_alerta": row[4],
                        "mensagem": row[5]
                    })
                client.table("alertas").upsert(data_alertas, on_conflict="lote_id,data_alerta").execute()
                
                sqlite_cursor.execute("DELETE FROM alertas")
                logger.info("Alertas locais removidos pós-sincronização.")

            # --- 5. Sincronizar Calibrações (Insert/Upsert + Delete local após sucesso) ---
            sqlite_cursor.execute("SELECT id, lote_id, numero_serial, zona, zona_str, data_calibracao, idade FROM calibracoes")
            calibracoes = sqlite_cursor.fetchall()
            if calibracoes:
                logger.info(f"Sincronizando {len(calibracoes)} calibrações...")
                data_calibracoes = []
                for row in calibracoes:
                    data_calibracoes.append({
                        "lote_id": row[1],
                        "numero_serial": row[2],
                        "zona": row[3],
                        "zona_str": row[4],
                        "data_calibracao": row[5],
                        "idade": row[6]
                    })
                client.table("calibracoes").upsert(data_calibracoes, on_conflict="lote_id,data_calibracao").execute()
                
                sqlite_cursor.execute("DELETE FROM calibracoes")
                logger.info("Calibrações locais removidas pós-sincronização.")

            # Comita as deleções no SQLite local
            sqlite_conn.commit()
            logger.info("Sincronização concluída com sucesso via Supabase SDK!")
            return True

        except Exception as e:
            sqlite_conn.rollback()
            logger.error(f"Erro durante o processo de sincronização: {e}")
            return False

        finally:
            sqlite_cursor.close()
            sqlite_conn.close()
