import os
import re
import json
import requests
import sqlite3
from bs4 import BeautifulSoup
from datetime import datetime
from src.database.connection import DatabaseConnection
from src.database.sync import SyncService
from src.utils.logger import setup_logger
from src.utils.datetime_parser import parse_iso_datetime

logger = setup_logger(name="agrisolus_scraper", log_file="test_run.log")

class AgrisolusScraper:
    """
    Scraper oficial para o portal Agrisolus.
    Realiza o login, navegação, extração das variáveis do silo/lotes,
    calcula o consumo e faz a persistência resiliente (Supabase -> SQLite fallback).
    """
    def __init__(self, db_conn: DatabaseConnection = None):
        self.db_conn = db_conn or DatabaseConnection()
        self.session = requests.Session()
        
        # Credenciais
        self.id_usuario = os.getenv("ID_USUARIO")
        self.senha = os.getenv("SENHA")
        self.url_acesso = os.getenv("URL_ACESSO", "https://s2.agrisolus.com.br/")
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def login(self) -> bool:
        """
        Realiza a autenticação no portal Agrisolus.
        Retorna True se autenticado com sucesso, senão False.
        """
        try:
            logger.info("Acessando página de login para obter o token anti-forgery...")
            response = self.session.get(self.url_acesso, headers=self.headers)
            if response.status_code != 200:
                logger.error(f"Erro ao carregar página de login. Status: {response.status_code}")
                return False
                
            soup = BeautifulSoup(response.text, "lxml")
            token_input = soup.find("input", {"name": "__RequestVerificationToken"})
            if not token_input:
                logger.error("Token __RequestVerificationToken não encontrado na página de login.")
                return False
                
            token = token_input.get("value")
            
            login_url = f"{self.url_acesso.rstrip('/')}/Login?ReturnUrl=%2F"
            login_data = {
                "Login": self.id_usuario,
                "Senha": self.senha,
                "__RequestVerificationToken": token
            }
            
            logger.info("Enviando requisição de login (POST)...")
            response_login = self.session.post(login_url, data=login_data, headers=self.headers)
            
            # O login redireciona para /Login/Portal em caso de sucesso
            if response_login.status_code == 200 and ("Login/Portal" in response_login.url or "ReturnUrl" not in response_login.url):
                logger.info("Login realizado com sucesso!")
                return True

            else:
                logger.error("Falha no login. Verifique o usuário e a senha no arquivo .env.")
                return False
                
        except Exception as e:
            logger.error(f"Erro inesperado durante o login: {e}")
            return False

    def generate_lotes_config(self, output_path="lotes_config.json") -> int:
        """
        Busca os lotes ativos na listagem (/Home/Listagem) e atualiza o arquivo de configuração json.
        Retorna o número de lotes mapeados.
        """
        listagem_url = f"{self.url_acesso.rstrip('/')}/Home/Listagem"
        logger.info(f"Acessando listagem de lotes em: {listagem_url}")
        
        try:
            response = self.session.get(listagem_url, headers=self.headers)
            if response.status_code != 200:
                logger.error(f"Falha ao carregar listagem de lotes. Status: {response.status_code}")
                return 0
                
            # Extrai a variável 'lotes' declarada no Javascript da página
            pattern = r'var\s+lotes\s*=\s*([\[\{].*?[\]\}]);'
            match = re.search(pattern, response.text, re.DOTALL)
            if not match:
                logger.warning("Variável 'lotes' não encontrada na página de listagem.")
                return 0
                
            lotes_data = json.loads(match.group(1))
            lotes_formatados = []
            
            for lote in lotes_data:
                aviario = lote.get("Aviario")
                # Foca somente no 'Aviário 819' e ignora os demais
                if not aviario or "Aviário 819" not in aviario:
                    continue

                id_lote = lote.get("IdLote")
                link_detalhes = f"{self.url_acesso.rstrip('/')}/Home/Detalhes?idLote={id_lote}"
                
                lotes_formatados.append({
                    "EMPRESA": lote.get("Empresa"),
                    "ESTABELECIMENTO": lote.get("Estabelecimento"),
                    "AVIARIO": aviario,
                    "LOTE": int(lote.get("CodigoLote", 0)) if lote.get("CodigoLote") else None,
                    "LINHAGEM": lote.get("Linhagem"),
                    "LINK": link_detalhes
                })

                
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(lotes_formatados, f, indent=4, ensure_ascii=False)
                
            logger.info(f"Configuração {output_path} atualizada com {len(lotes_formatados)} lotes.")
            return len(lotes_formatados)
            
        except Exception as e:
            logger.error(f"Erro ao gerar lotes_config: {e}")
            return 0

    def scrape_and_persist(self, config_path="lotes_config.json"):
        """
        Lê a lista de lotes configurados, executa o scraping detalhado de cada um,
        calcula o consumo dos silos e persiste no banco (Supabase com SQLite fallback).
        """
        if not os.path.exists(config_path):
            logger.warning(f"Arquivo de configuração {config_path} não encontrado. Mapeando lotes...")
            self.generate_lotes_config(config_path)
            
        if not os.path.exists(config_path):
            logger.error("Impossível prosseguir sem lotes_config.json.")
            return

        with open(config_path, "r", encoding="utf-8") as f:
            lotes_config = json.load(f)

        logger.info(f"Iniciando processamento de {len(lotes_config)} lotes...")
        
        for idx, config in enumerate(lotes_config):
            link = config.get("LINK")
            logger.info(f"[{idx+1}/{len(lotes_config)}] Scraping lote: {config.get('AVIARIO')} - {config.get('EMPRESA')}")
            
            try:
                response = self.session.get(link, headers=self.headers)
                if response.status_code != 200:
                    logger.error(f"Erro ao carregar detalhes do lote. Status: {response.status_code}")
                    continue
                
                # Executa o parse e extração dos dados
                self._process_lote_html(response.text, link)
                
            except Exception as e:
                logger.error(f"Erro ao processar lote {config.get('AVIARIO')}: {e}")

        # Tenta sincronizar dados locais acumulados se houver internet
        logger.info("Tentando executar serviço de sincronização pós-execução do scraper...")
        sync = SyncService(self.db_conn)
        sync.sync_local_to_remote()

    def _process_lote_html(self, html_content: str, link: str):
        """
        Faz o parse do HTML de detalhes do lote, extrai as variáveis JS
        e decide onde salvar.
        """
        soup = BeautifulSoup(html_content, "lxml")
        
        # 1. Extrair ID do Lote a partir do link
        match_id = re.search(r"idLote=(\d+)", link)
        if not match_id:
            logger.error(f"Não foi possível extrair o id_lote do link: {link}")
            return
        id_lote = int(match_id.group(1))

        # 2. Extrair dados da Tabela 1 (HTML)
        table1_data = self._parse_html_table1(soup)

        # 3. Extrair variáveis JS
        lotes_js = self._extract_js_var("lotes", html_content)
        saldo_racao_js = self._extract_js_var("saldoRacao", html_content)
        alertas_js = self._extract_js_var("alertas", html_content)
        calibracoes_js = self._extract_js_var("calibracoes", html_content)

        # 4. Estruturar Lote
        # Mescla informações do JSON 'lotes' (da listagem/detalhes) com a Tabela 1
        lote_info = {}
        if lotes_js and len(lotes_js) > 0:
            lote_data = lotes_js[0]
            codigo_lote = lote_data.get("CodigoLote")
            aviario = lote_data.get("Aviario")
            lote_info = {
                "id_lote": id_lote,
                "codigo_lote": codigo_lote,
                "empresa": lote_data.get("Empresa"),
                "estabelecimento": lote_data.get("Estabelecimento"),
                "aviario": aviario,
                "linhagem": lote_data.get("Linhagem"),
                "qtd_alojamento": table1_data.get("qtd_alojamento", lote_data.get("QtdAlojamento", 0)),
                "data_alojamento": table1_data.get("data_alojamento"),
                "saldo_frangos": table1_data.get("saldo_frangos", lote_data.get("QtdAlojamento", 0)),
                "aviario_lote": f"{codigo_lote}-{aviario}" if codigo_lote and aviario else None
            }
        else:
            # Fallback se não achar a variável lotes no JS
            lote_info = {
                "id_lote": id_lote,
                "codigo_lote": None,
                "empresa": None,
                "estabelecimento": None,
                "aviario": None,
                "linhagem": None,
                "qtd_alojamento": table1_data.get("qtd_alojamento", 0),
                "data_alojamento": table1_data.get("data_alojamento"),
                "saldo_frangos": table1_data.get("saldo_frangos", 0),
                "aviario_lote": None
            }


        # 5. Estruturar Silos e Leituras (Calculando consumo)
        silos_list = []
        leituras_list = []
        if saldo_racao_js:
            for item in saldo_racao_js:
                silo_id = item.get("Descricao")
                capacidade = item.get("Capacidade", 0.0)
                qty_g = item.get("Quantidade", 0.0)
                qty_kg = qty_g / 1000.0  # O valor retornado em 'Quantidade' está em gramas
                data_leitura = item.get("Data")

                if not silo_id or not data_leitura:
                    continue

                # Estrutura Silo
                silos_list.append({
                    "id_silo": silo_id,
                    "lote_id": id_lote,
                    "capacidade_kg": capacidade
                })

                # Calcula o consumo de ração
                consumo = self._calculate_consumo(silo_id, qty_kg, data_leitura)

                # Estrutura Leitura
                leituras_list.append({
                    "silo_id": silo_id,
                    "data_leitura": data_leitura,
                    "valor_racao_g": qty_g,
                    "valor_racao_kg": qty_kg,
                    "consumo_kg": consumo
                })

        # 6. Estruturar Alertas
        alertas_list = []
        if alertas_js:
            for item in alertas_js:
                alertas_list.append({
                    "lote_id": id_lote,
                    "tipo_alerta": item.get("TipoAlerta"),
                    "tipo_alerta_str": item.get("TipoAlertaStr"),
                    "data_alerta": item.get("Data"),
                    "mensagem": item.get("Mensagem")
                })

        # 7. Estruturar Calibrações
        calibracoes_list = []
        if calibracoes_js:
            for item in calibracoes_js:
                calibracoes_list.append({
                    "lote_id": id_lote,
                    "numero_serial": item.get("NumeroSerial"),
                    "zona": item.get("Zona"),
                    "zona_str": item.get("ZonaStr"),
                    "data_calibracao": item.get("DataCalibracao"),
                    "idade": item.get("Idade")
                })

        # Checagem de Silo Offline (>2 horas)
        for lei in leituras_list:
            silo_id = lei["silo_id"]
            data_leitura_str = lei["data_leitura"]
            
            try:
                dt_leitura = parse_iso_datetime(data_leitura_str)
                
                now = datetime.now()
                diff_seconds = (now - dt_leitura).total_seconds()
                diff_hours = diff_seconds / 3600.0
                
                if diff_hours > 2.0:
                    logger.info(f"Silo {silo_id} offline há {diff_hours:.1f} horas. Verificando se alerta já foi enviado...")
                    
                    if not self._alert_already_sent(id_lote, silo_id, data_leitura_str):
                        logger.warning(f"Silo {silo_id} offline recém-detectado. Enviando alerta no Telegram...")
                        
                        alertas_list.append({
                            "lote_id": id_lote,
                            "tipo_alerta": 99,
                            "tipo_alerta_str": "Silo Offline",
                            "data_alerta": data_leitura_str,
                            "mensagem": f"O {silo_id} está sem enviar dados há {diff_hours:.1f} horas. Último envio: {data_leitura_str}"
                        })
                        
                        # Dispara Telegram
                        from src.bot.notifier import TelegramNotifier
                        notifier = TelegramNotifier()
                        notifier.send_immediate_alert(silo_id, data_leitura_str, diff_hours)
                    else:
                        logger.info(f"Alerta de offline para {silo_id} na data {data_leitura_str} já foi enviado.")
            except Exception as e:
                logger.error(f"Erro ao checar status offline de {silo_id}: {e}")


        # Filtra duplicados em leituras_list (silo_id, data_leitura)
        unique_leituras = {}
        for item in leituras_list:
            key = (item["silo_id"], item["data_leitura"])
            unique_leituras[key] = item
        leituras_list = list(unique_leituras.values())

        # Filtra duplicados em alertas_list (lote_id, data_alerta)
        unique_alertas = {}
        for item in alertas_list:
            key = (item["lote_id"], item["data_alerta"])
            unique_alertas[key] = item
        alertas_list = list(unique_alertas.values())

        # Filtra duplicados em calibracoes_list (lote_id, data_calibracao)
        unique_calibracoes = {}
        for item in calibracoes_list:
            key = (item["lote_id"], item["data_calibracao"])
            unique_calibracoes[key] = item
        calibracoes_list = list(unique_calibracoes.values())

        # 8. Persistir de forma Resiliente
        self._persist_all(lote_info, silos_list, leituras_list, alertas_list, calibracoes_list)


    def _calculate_consumo(self, silo_id: str, current_weight_kg: float, current_date_str: str) -> float:
        """
        Busca o último peso salvo para o silo localmente (ou remotamente se possível)
        e calcula o consumo.
        Retorna consumo_kg (float).
        """
        # Como o SQLite é nosso fallback local e sempre armazena as leituras recentes,
        # buscar no SQLite local é a forma mais rápida, estável e offline-friendly
        # de obter a leitura anterior de forma confiável.
        try:
            sqlite_conn = self.db_conn.get_sqlite_connection()
            cursor = sqlite_conn.cursor()
            
            # Busca a última leitura do silo que seja anterior à data atual
            cursor.execute("""
                SELECT valor_racao_kg, data_leitura FROM leituras 
                WHERE silo_id = ? AND data_leitura < ?
                ORDER BY data_leitura DESC LIMIT 1
            """, (silo_id, current_date_str))
            
            row = cursor.fetchone()
            sqlite_conn.close()

            if row:
                prev_weight = row[0]
                prev_date = row[1]
                
                # Se o peso anterior for maior que o atual, a diferença é o consumo
                if prev_weight > current_weight_kg:
                    consumo = prev_weight - current_weight_kg
                    logger.info(f"Consumo calculado para {silo_id}: {consumo:.2f} kg (Peso anterior: {prev_weight:.2f} kg em {prev_date} -> Atual: {current_weight_kg:.2f} kg)")
                    return round(consumo, 4)
                else:
                    # Se o peso atual for maior ou igual, indica abastecimento de ração
                    logger.info(f"Abastecimento detectado para {silo_id} (Peso anterior: {prev_weight:.2f} kg -> Atual: {current_weight_kg:.2f} kg). Consumo definido como 0.")
                    return 0.0
            else:
                logger.info(f"Nenhuma leitura anterior encontrada para o silo {silo_id}. Consumo definido como 0.")
                return 0.0
                
        except Exception as e:
            logger.error(f"Erro ao calcular consumo para {silo_id}: {e}")
            return 0.0

    def _persist_all(self, lote, silos, leituras, alertas, calibracoes):
        """
        Salva os dados extraídos no Supabase. Se falhar, faz o fallback para o SQLite local.
        """
        # Tenta salvar no Supabase
        client = self.db_conn.get_supabase_client()
        if client:
            try:
                logger.info("Persistindo dados no Supabase...")
                
                # Lotes
                client.table("lotes").upsert(lote).execute()
                
                # Silos
                if silos:
                    client.table("silos").upsert(silos).execute()
                
                # Leituras
                if leituras:
                    client.table("leituras").upsert(leituras, on_conflict="silo_id,data_leitura").execute()
                
                # Alertas
                if alertas:
                    client.table("alertas").upsert(alertas, on_conflict="lote_id,data_alerta").execute()
                
                # Calibrações
                if calibracoes:
                    client.table("calibracoes").upsert(calibracoes, on_conflict="lote_id,data_calibracao").execute()
                
                logger.info("Dados persistidos com sucesso no Supabase!")
                
                # Importante: Como o método _calculate_consumo lê o histórico de leituras do SQLite local
                # para calcular a diferença e consumo, precisamos gravar as leituras no SQLite local
                # mesmo que o envio ao Supabase funcione, para servir de histórico local para a próxima execução.
                self._save_to_sqlite(lote, silos, leituras, alertas=[], calibracoes=[])
                return
                
            except Exception as e:
                logger.error(f"Falha ao persistir no Supabase (iniciando fallback local): {e}")

        # Se não houver cliente ou a chamada do Supabase falhou, salva tudo localmente no SQLite
        logger.warning("Salvando dados no buffer local do SQLite...")
        self._save_to_sqlite(lote, silos, leituras, alertas, calibracoes)

    def _save_to_sqlite(self, lote, silos, leituras, alertas, calibracoes):
        """
        Grava os dados no banco local SQLite utilizando sintaxe ON CONFLICT / INSERT OR IGNORE.
        """
        try:
            conn = self.db_conn.get_sqlite_connection()
            cursor = conn.cursor()

            # 1. Salvar Lote (Upsert)
            cursor.execute("""
                INSERT INTO lotes (id_lote, codigo_lote, empresa, estabelecimento, aviario, linhagem, qtd_alojamento, data_alojamento, saldo_frangos, aviario_lote)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (id_lote) DO UPDATE SET
                    codigo_lote = EXCLUDED.codigo_lote,
                    empresa = EXCLUDED.empresa,
                    estabelecimento = EXCLUDED.estabelecimento,
                    aviario = EXCLUDED.aviario,
                    linhagem = EXCLUDED.linhagem,
                    qtd_alojamento = EXCLUDED.qtd_alojamento,
                    data_alojamento = EXCLUDED.data_alojamento,
                    saldo_frangos = EXCLUDED.saldo_frangos,
                    aviario_lote = EXCLUDED.aviario_lote,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                lote.get("id_lote"), lote.get("codigo_lote"), lote.get("empresa"),
                lote.get("estabelecimento"), lote.get("aviario"), lote.get("linhagem"),
                lote.get("qtd_alojamento"), lote.get("data_alojamento"), lote.get("saldo_frangos"),
                lote.get("aviario_lote")
            ))


            # 2. Salvar Silos (Upsert)
            for silo in silos:
                cursor.execute("""
                    INSERT INTO silos (id_silo, lote_id, capacidade_kg)
                    VALUES (?, ?, ?)
                    ON CONFLICT (id_silo) DO UPDATE SET
                        lote_id = EXCLUDED.lote_id,
                        capacidade_kg = EXCLUDED.capacidade_kg
                """, (silo.get("id_silo"), silo.get("lote_id"), silo.get("capacidade_kg")))

            # 3. Salvar Leituras (Insert or Ignore)
            for lei in leituras:
                cursor.execute("""
                    INSERT INTO leituras (silo_id, data_leitura, valor_racao_g, valor_racao_kg, consumo_kg)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT (silo_id, data_leitura) DO NOTHING
                """, (lei.get("silo_id"), lei.get("data_leitura"), lei.get("valor_racao_g"), lei.get("valor_racao_kg"), lei.get("consumo_kg")))

            # 4. Salvar Alertas (Insert or Ignore)
            for al in alertas:
                cursor.execute("""
                    INSERT INTO alertas (lote_id, tipo_alerta, tipo_alerta_str, data_alerta, mensagem)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT (lote_id, data_alerta) DO NOTHING
                """, (al.get("lote_id"), al.get("tipo_alerta"), al.get("tipo_alerta_str"), al.get("data_alerta"), al.get("mensagem")))

            # 5. Salvar Calibrações (Insert or Ignore)
            for cal in calibracoes:
                cursor.execute("""
                    INSERT INTO calibracoes (lote_id, numero_serial, zona, zona_str, data_calibracao, idade)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT (lote_id, data_calibracao) DO NOTHING
                """, (cal.get("lote_id"), cal.get("numero_serial"), cal.get("zona"), cal.get("zona_str"), cal.get("data_calibracao"), cal.get("idade")))

            conn.commit()
            conn.close()
            logger.info("Dados salvos no SQLite local com sucesso!")
        except Exception as e:
            logger.error(f"Erro ao salvar dados no SQLite local: {e}")

    def _parse_html_table1(self, soup) -> dict:
        """
        Faz o parse da Tabela 1 (dados gerais do lote) no HTML.
        """
        table1 = soup.find("table", class_=lambda x: x and "col-lg-12" in x)
        data = {}
        if table1:
            for row in table1.find_all("tr"):
                text = row.text.strip().replace("\xa0", " ").replace("\n", " ").replace("  ", " ")
                if "Data Alojamento" in text:
                    # Pega apenas a data e a hora correspondente (ex: '05/06/2026 11:00:00')
                    val = text.replace("Data Alojamento", "").strip()
                    try:
                        # Tenta parsear no formato 'dd/mm/aaaa hh:mm:ss'
                        dt_obj = datetime.strptime(val, "%d/%m/%Y %H:%M:%S")
                        data["data_alojamento"] = dt_obj.strftime("%Y-%m-%dT%H:%M:%S")
                    except Exception:
                        data["data_alojamento"] = val
                elif "Qtd. Alojamento" in text:
                    val = text.replace("Qtd. Alojamento", "").strip()
                    data["qtd_alojamento"] = int(val) if val.isdigit() else 0
                elif "Saldo de Frangos" in text:
                    val = text.replace("Saldo de Frangos", "").strip()
                    data["saldo_frangos"] = int(val) if val.isdigit() else 0
        return data

    def _extract_js_var(self, var_name: str, html: str):
        """
        Extrai variáveis declaradas no script inline em formato JSON.
        """
        pattern = r'var\s+' + re.escape(var_name) + r'\s*=\s*([\[\{].*?[\]\}]);'
        match = re.search(pattern, html, re.DOTALL)
        if match:
            var_content = match.group(1)
            try:
                return json.loads(var_content)
            except Exception as e:
                logger.error(f"Falha ao decodificar JSON de '{var_name}': {e}")
                return None
        return None

    def _alert_already_sent(self, lote_id: int, silo_id: str, data_leitura: str) -> bool:
        """
        Verifica se o alerta de silo offline para este silo e data de leitura já existe localmente no SQLite.
        """
        try:
            conn = self.db_conn.get_sqlite_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM alertas 
                WHERE lote_id = ? AND data_alerta = ? AND tipo_alerta = 99 AND mensagem LIKE ?
            """, (lote_id, data_leitura, f"%{silo_id}%"))
            count = cursor.fetchone()[0]
            conn.close()
            return count > 0
        except Exception as e:
            logger.error(f"Erro ao verificar alertas antigos no SQLite: {e}")
            return False

