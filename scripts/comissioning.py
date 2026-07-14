# -*- coding: utf-8 -*-
"""
Script de Comissionamento para validação em tempo real das credenciais de acesso,
da estrutura do banco de dados local SQLite e da conectividade com o portal Agrisolus.
"""
import os
import sys
import sqlite3
from dotenv import load_dotenv

# Garante que o Python encontre o pacote 'src'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database.connection import DatabaseConnection
from src.scraper.extractor import AgrisolusScraper

def run_comissioning():
    print("==================================================")
    print("      INICIANDO COMISSIONAMENTO DO SISTEMA        ")
    print("==================================================")
    
    # 1. Carrega as variáveis de ambiente
    load_dotenv()
    db_path = os.getenv("SQLITE_PATH", "local_fallback.db")
    username = os.getenv("ID_USUARIO")
    password = os.getenv("SENHA")
    
    print(f"\n1. Validando arquivo .env...")
    if not username or not password:
        print("❌ FALHA: Credenciais do portal (ID_USUARIO / SENHA) ausentes no .env.")
        return
    print(f"   - Usuário configurado: {username}")
    print(f"   - Banco de dados SQLite configurado: {db_path}")

    # 2. Valida conexão e tabelas locais do SQLite
    print(f"\n2. Verificando estrutura e permissão de escrita no SQLite local...")
    try:
        db = DatabaseConnection()
        conn = db.get_sqlite_connection()
        cursor = conn.cursor()
        
        # Teste de inserção e exclusão (Permissão de escrita)
        test_id = 999999
        cursor.execute("INSERT OR REPLACE INTO lotes (id_lote, codigo_lote, aviario_lote) VALUES (?, 'TEST-99', 'Test-Aviary')", (test_id,))
        print("   - Inserção de Lote de teste: OK")
        
        cursor.execute("INSERT OR REPLACE INTO silos (id_silo, lote_id, capacidade_kg) VALUES ('Silo-Test-Commission', ?, 18000.0)", (test_id,))
        print("   - Inserção de Silo de teste: OK")
        
        cursor.execute("DELETE FROM silos WHERE lote_id = ?", (test_id,))
        cursor.execute("DELETE FROM lotes WHERE id_lote = ?", (test_id,))
        conn.commit()
        print("   - Remoção dos dados de teste: OK")
        
        # Valida existência de todas as tabelas requeridas
        required_tables = ["lotes", "silos", "leituras", "alertas", "calibracoes", "historico_scraping", "notas_fiscais"]
        for table in required_tables:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (table,))
            if not cursor.fetchone():
                print(f"❌ FALHA: A tabela obrigatória '{table}' está ausente no banco SQLite local.")
                return
            print(f"   - Tabela '{table}': Validada")
            
        cursor.close()
        conn.close()
        print("✅ SQLite local está 100% íntegro e operacional!")
        
    except Exception as e:
        print(f"❌ FALHA no banco SQLite local: {e}")
        return

    # 3. Testa conectividade e login no portal Agrisolus
    print("\n3. Testando login no portal s2.agrisolus.com.br...")
    try:
        scraper = AgrisolusScraper()
        # Tenta obter o token e fazer login
        token = scraper._get_antiforgery_token()
        if not token:
            print("❌ FALHA: Não foi possível carregar a página de login do portal (Sem conexão ou portal offline).")
            return
        print("   - Acesso à página de login: OK (token antiforgery obtido)")
        
        session = scraper._login(token)
        if not session:
            print("❌ FALHA: Login rejeitado pelo portal. Verifique se o ID_USUARIO e SENHA no seu .env estão corretos.")
            return
        print("✅ Login realizado com sucesso no portal Agrisolus!")
        
    except Exception as e:
        print(f"❌ FALHA de conectividade com o portal: {e}")
        return

    print("\n==================================================")
    print("🎉 COMISSIONAMENTO CONCLUÍDO COM SUCESSO!")
    print("O sistema está pronto para produção e deploy na VPS.")
    print("==================================================")

if __name__ == "__main__":
    run_comissioning()
