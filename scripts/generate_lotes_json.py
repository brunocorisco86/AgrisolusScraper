import os
import sys
import json
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Garante que o Python encontre o pacote 'src'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.logger import setup_logger

logger = setup_logger(name="generate_lotes_json", log_file="test_run.log")

def main():
    load_dotenv()
    
    id_usuario = os.getenv("ID_USUARIO")
    senha = os.getenv("SENHA")
    url_acesso = os.getenv("URL_ACESSO")
    
    if not id_usuario or not senha or not url_acesso:
        logger.error("Credenciais da Agrisolus não configuradas no arquivo .env.")
        return
        
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        # 1. Login
        logger.info("Carregando página de login...")
        login_page = session.get(url_acesso)
        soup_login = BeautifulSoup(login_page.text, 'lxml')
        token_input = soup_login.find("input", {"name": "__RequestVerificationToken"})
        if not token_input:
            logger.error("Token __RequestVerificationToken não encontrado na página de login.")
            return
            
        token = token_input.get("value")
        
        login_url = f"{url_acesso.rstrip('/')}/Login?ReturnUrl=%2F"
        login_data = {
            "Login": id_usuario,
            "Senha": senha,
            "__RequestVerificationToken": token
        }
        
        logger.info("Realizando login...")
        response_login = session.post(login_url, data=login_data, headers=headers)
        logger.info(f"Status do login: {response_login.status_code}")

        # 2. Acessar Listagem de Lotes
        listagem_url = f"{url_acesso.rstrip('/')}/Home/Listagem"
        logger.info(f"Acessando listagem de lotes em: {listagem_url}")
        response_listagem = session.get(listagem_url, headers=headers)
        logger.info(f"Status da listagem: {response_listagem.status_code}")
        
        if response_listagem.status_code != 200:
            logger.error("Falha ao obter página de listagem.")
            return

        # Salvar o HTML para inspeção
        html_out = "/media/brunoconter/DOCUMENTOS3/11_AGRISOLUS_SCRAPER/scripts/listagem.html"
        with open(html_out, "w", encoding="utf-8") as f:
            f.write(response_listagem.text)
        logger.info(f"HTML da listagem salvo em: {html_out}")

        # 3. Parse da Tabela de Lotes
        soup = BeautifulSoup(response_listagem.text, 'lxml')
        
        # Procurar tabelas
        tables = soup.find_all("table")
        logger.info(f"Total de tabelas encontradas na listagem: {len(tables)}")
        
        # Vamos tentar mapear e extrair os dados da tabela
        # A listagem costuma conter colunas como: Empresa, Estabelecimento, Aviário, Lote, Linhagem, Idade, Link Detalhes
        lotes_mapeados = []
        
        # Se houver pelo menos uma tabela, vamos inspecionar as linhas dela
        if tables:
            table = tables[0]
            rows = table.find_all("tr")
            logger.info(f"Tabela 1 possui {len(rows)} linhas.")
            
            # Identificar cabeçalhos
            headers_cells = [th.text.strip() for th in rows[0].find_all(["th", "td"])]
            logger.info(f"Cabeçalhos da Tabela: {headers_cells}")
            
            for row in rows[1:]:
                cells = row.find_all("td")
                if len(cells) < 2:
                    continue
                
                # Extrai dados básicos baseados em posições aproximadas (vamos calibrar depois de ver o HTML)
                # Tenta localizar links com 'idLote' na célula
                detail_link = ""
                id_lote = ""
                for cell in cells:
                    link_tag = cell.find("a", href=True)
                    if link_tag and "idLote=" in link_tag["href"]:
                        detail_link = link_tag["href"]
                        # Se o link for relativo, constrói o absoluto
                        if detail_link.startswith("/"):
                            detail_link = f"{url_acesso.rstrip('/')}{detail_link}"
                        # Extrai o idLote da URL
                        id_lote_match = re_match = None
                        import re
                        match = re.search(r"idLote=(\d+)", detail_link)
                        if match:
                            id_lote = match.group(1)
                        break

                # Mapeamento provisório de colunas
                # Vamos extrair os textos de todas as células para podermos decidir os campos
                cell_texts = [c.text.strip().replace("\n", " ").replace("  ", " ") for c in cells]
                
                lote_info = {
                    "id_lote": id_lote,
                    "link": detail_link,
                    "dados_linha": cell_texts
                }
                lotes_mapeados.append(lote_info)

        # Salvar o JSON inicial de mapeamento
        json_out = "/media/brunoconter/DOCUMENTOS3/11_AGRISOLUS_SCRAPER/lotes_config.json"
        with open(json_out, "w", encoding="utf-8") as f:
            json.dump(lotes_mapeados, f, indent=4, ensure_ascii=False)
        logger.info(f"Mapeamento inicial salvo em: {json_out}")
        logger.info(f"Total de lotes mapeados: {len(lotes_mapeados)}")

    except Exception as e:
        logger.error(f"Erro durante geração do JSON de lotes: {e}")

if __name__ == "__main__":
    main()
