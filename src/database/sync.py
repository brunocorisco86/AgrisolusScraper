import sqlite3
import psycopg2
from src.utils.logger import setup_logger

logger = setup_logger(name="sync_service", log_file="test_run.log")

class SyncService:
    """
    Sincroniza os dados coletados localmente no SQLite (durante falhas de internet)
    com o banco de dados principal no Supabase.
    """
    def __init__(self, db_conn):
        self.db_conn = db_conn

    def sync_local_to_remote(self):
        """
        Executa o fluxo de sincronização do SQLite local para o Supabase.
        Retorna True se a sincronização ocorrer com sucesso ou se não houver dados,
        e False se houver falha de rede/conexão com o Supabase.
        """
        # 1. Verifica se conseguimos conectar ao Supabase
        pg_conn = self.db_conn.get_supabase_connection()
        if not pg_conn:
            logger.warning("Supabase inacessível no momento. Sincronização cancelada. Os dados permanecem salvos localmente.")
            return False

        sqlite_conn = self.db_conn.get_sqlite_connection()
        sqlite_cursor = sqlite_conn.cursor()
        pg_cursor = pg_conn.cursor()

        try:
            logger.info("Iniciando sincronização local -> remota...")
            
            # --- 1. Sincronizar Lotes (Upsert) ---
            sqlite_cursor.execute("SELECT id_lote, codigo_lote, empresa, estabelecimento, aviario, linhagem, qtd_alojamento, data_alojamento, saldo_frangos FROM lotes")
            lotes = sqlite_cursor.fetchall()
            if lotes:
                logger.info(f"Sincronizando {len(lotes)} lotes...")
                for lote in lotes:
                    pg_cursor.execute("""
                        INSERT INTO lotes (id_lote, codigo_lote, empresa, estabelecimento, aviario, linhagem, qtd_alojamento, data_alojamento, saldo_frangos, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                        ON CONFLICT (id_lote) 
                        DO UPDATE SET 
                            codigo_lote = EXCLUDED.codigo_lote,
                            empresa = EXCLUDED.empresa,
                            estabelecimento = EXCLUDED.estabelecimento,
                            aviario = EXCLUDED.aviario,
                            linhagem = EXCLUDED.linhagem,
                            qtd_alojamento = EXCLUDED.qtd_alojamento,
                            data_alojamento = EXCLUDED.data_alojamento,
                            saldo_frangos = EXCLUDED.saldo_frangos,
                            updated_at = NOW();
                    """, lote)

            # --- 2. Sincronizar Silos (Upsert) ---
            sqlite_cursor.execute("SELECT id_silo, lote_id, capacidade_kg FROM silos")
            silos = sqlite_cursor.fetchall()
            if silos:
                logger.info(f"Sincronizando {len(silos)} silos...")
                for silo in silos:
                    pg_cursor.execute("""
                        INSERT INTO silos (id_silo, lote_id, capacidade_kg)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (id_silo)
                        DO UPDATE SET 
                            lote_id = EXCLUDED.lote_id,
                            capacidade_kg = EXCLUDED.capacidade_kg;
                    """, silo)

            # --- 3. Sincronizar Leituras (Insert + Delete local após sucesso) ---
            sqlite_cursor.execute("SELECT id, silo_id, data_leitura, valor_racao_g, valor_racao_kg, consumo_kg FROM leituras")
            leituras = sqlite_cursor.fetchall()
            if leituras:
                logger.info(f"Sincronizando {len(leituras)} leituras...")
                for leitura in leituras:
                    # leitura[0] é o ID local (do SQLite)
                    pg_cursor.execute("""
                        INSERT INTO leituras (silo_id, data_leitura, valor_racao_g, valor_racao_kg, consumo_kg)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (silo_id, data_leitura) DO NOTHING;
                    """, (leitura[1], leitura[2], leitura[3], leitura[4], leitura[5]))
                
                # Após inserir tudo no Supabase com sucesso, limpamos do SQLite
                sqlite_cursor.execute("DELETE FROM leituras")
                logger.info("Leituras locais removidas pós-sincronização.")

            # --- 4. Sincronizar Alertas (Insert + Delete local após sucesso) ---
            sqlite_cursor.execute("SELECT id, lote_id, tipo_alerta, tipo_alerta_str, data_alerta, mensagem FROM alertas")
            alertas = sqlite_cursor.fetchall()
            if alertas:
                logger.info(f"Sincronizando {len(alertas)} alertas...")
                for alerta in alertas:
                    pg_cursor.execute("""
                        INSERT INTO alertas (lote_id, tipo_alerta, tipo_alerta_str, data_alerta, mensagem)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (lote_id, data_alerta) DO NOTHING;
                    """, (alerta[1], alerta[2], alerta[3], alerta[4], alerta[5]))
                
                sqlite_cursor.execute("DELETE FROM alertas")
                logger.info("Alertas locais removidos pós-sincronização.")

            # --- 5. Sincronizar Calibrações (Insert + Delete local após sucesso) ---
            sqlite_cursor.execute("SELECT id, lote_id, numero_serial, zona, zona_str, data_calibracao, idade FROM calibracoes")
            calibracoes = sqlite_cursor.fetchall()
            if calibracoes:
                logger.info(f"Sincronizando {len(calibracoes)} calibrações...")
                for cal in calibracoes:
                    pg_cursor.execute("""
                        INSERT INTO calibracoes (lote_id, numero_serial, zona, zona_str, data_calibracao, idade)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (lote_id, data_calibracao) DO NOTHING;
                    """, (cal[1], cal[2], cal[3], cal[4], cal[5], cal[6]))
                
                sqlite_cursor.execute("DELETE FROM calibracoes")
                logger.info("Calibrações locais removidas pós-sincronização.")

            # Comita transações em ambos os bancos
            pg_conn.commit()
            sqlite_conn.commit()
            
            logger.info("Sincronização concluída com sucesso!")
            return True

        except Exception as e:
            pg_conn.rollback()
            sqlite_conn.rollback()
            logger.error(f"Erro durante o processo de sincronização: {e}")
            return False

        finally:
            pg_cursor.close()
            pg_conn.close()
            sqlite_cursor.close()
            sqlite_conn.close()
