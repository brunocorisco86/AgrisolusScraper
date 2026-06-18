import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
load_dotenv()

ID_USUARIO = os.getenv("ID_USUARIO")
SENHA = os.getenv("SENHA")
URL_ACESSO = os.getenv("URL_ACESSO")
LINK_LOTE = os.getenv("LINK")

session = requests.Session()

try:
    # 1. Carregar a página de login e obter o token anti-forgery
    print("Carregando página de login...")
    login_page = session.get(URL_ACESSO)
    soup_login = BeautifulSoup(login_page.text, 'lxml')
    
    token_input = soup_login.find("input", {"name": "__RequestVerificationToken"})
    if not token_input:
        print("Erro: __RequestVerificationToken não encontrado!")
        exit(1)
        
    token = token_input.get("value")
    print(f"Token anti-forgery extraído: {token[:20]}...")

    # 2. Executar o POST de login
    login_url = f"{URL_ACESSO.rstrip('/')}/Login?ReturnUrl=%2F"
    login_data = {
        "Login": ID_USUARIO,
        "Senha": SENHA,
        "__RequestVerificationToken": token
    }
    
    headers = {
        "Referer": URL_ACESSO,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    print("Enviando requisição de login (POST)...")
    response_login = session.post(login_url, data=login_data, headers=headers)
    print(f"Status do login: {response_login.status_code}")
    print(f"URL final após login: {response_login.url}")

    # 3. Acessar a página de detalhes do lote
    print(f"\nAcessando página de detalhes do lote: {LINK_LOTE}")
    response_lote = session.get(LINK_LOTE, headers=headers)
    print(f"Status do lote: {response_lote.status_code}")

    if response_lote.status_code == 200:
        output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "batch_details.html")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(response_lote.text)
        print(f"Sucesso! HTML da página de detalhes salvo em: {output_file}")
    else:
        print("Falha ao acessar detalhes do lote. Verifique se o login falhou ou se expirou.")

except Exception as e:
    print(f"Erro durante a execução do scraper de teste: {e}")
