"""
Script de Comissionamento para validação em tempo real das credenciais e conexão com o Supabase.
"""
import os
import sys
from dotenv import load_dotenv

# Garante que o Python encontre o pacote 'src'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database.connection import DatabaseConnection

def run_comissioning():
    print("==================================================")
    print("      INICIANDO COMISSIONAMENTO DO SUPABASE       ")
    print("==================================================")
    
    # 1. Instancia o gerenciador de conexões
    db = DatabaseConnection()
    
    # 2. Tenta obter o cliente Supabase
    client = db.get_supabase_client()
    if not client:
        print("\n❌ FALHA: Não foi possível instanciar o cliente Supabase.")
        print("Verifique se as variáveis SUPABASE_API_URL e SECRET_KEY estão no seu arquivo .env.")
        return

    # ID fictício para o teste
    test_id = 999999
    
    try:
        print("\n1. Tentando INSERIR registros de teste no Supabase (Lote, Silo e Histórico)...")
        test_data = {
            "id_lote": test_id,
            "codigo_lote": "TEST-99",
            "empresa": "COMISSIONAMENTO TESTE",
            "estabelecimento": "TESTE SUPABASE",
            "aviario": "Avião de Teste",
            "linhagem": "Teste",
            "qtd_alojamento": 100,
            "saldo_frangos": 100
        }
        
        # 2a. Insere/Upserta o lote no Supabase
        client.table("lotes").upsert(test_data).execute()
        print("   - Lote de teste inserido.")

        # 2b. Insere/Upserta o silo no Supabase
        silo_id = "Silo-Test-Commission"
        silo_data = {
            "id_silo": silo_id,
            "lote_id": test_id,
            "capacidade_kg": 10000.0
        }
        client.table("silos").upsert(silo_data).execute()
        print("   - Silo de teste inserido.")

        # 2c. Insere/Upserta o historico_scraping no Supabase
        from datetime import datetime
        historico_data = {
            "silo_id": silo_id,
            "data_tentativa": datetime.now().isoformat(),
            "sucesso_conexao": True,
            "achou_dados_novos": True,
            "peso_kg": 5000.0,
            "data_leitura": datetime.now().isoformat()
        }
        client.table("historico_scraping").upsert(historico_data).execute()
        print("   - Registro de histórico de scraping (com data_leitura) inserido.")
        
        print("✅ SUCESSO: Todos os registros de teste foram inseridos com sucesso!")
        print("\n==================================================")
        print("💻 COMO CONFERIR NO SEU PAINEL DO SUPABASE:")
        print("1. Acesse seu projeto no Supabase.")
        print("2. Clique no ícone 'Table Editor' (Editor de Tabelas) no menu lateral esquerdo.")
        print("3. Selecione a tabela 'lotes'.")
        print(f"4. Você deve ver uma linha com o id_lote '{test_id}' e empresa '{test_data['empresa']}'!")
        print("5. Selecione a tabela 'historico_scraping' e verifique se a coluna 'data_leitura' foi populada!")
        print("==================================================")
        
        # Pede confirmação para o usuário deletar o registro e limpar o banco
        input("\nApós confirmar a presença do registro no painel, aperte [ENTER] para limpar o banco...")
        
        print(f"\n2. Limpando o banco (removendo o lote fictício {test_id})...")
        client.table("lotes").delete().eq("id_lote", test_id).execute()
        print("✅ SUCESSO: Banco limpo! O comissionamento foi concluído com êxito.")

    except Exception as e:
        print(f"\n❌ ERRO durante a comunicação com o Supabase: {e}")
        print("\nDicas de diagnóstico:")
        print("- Verifique se a sua internet está funcionando.")
        print("- Verifique se você executou o script SQL no editor do Supabase (as tabelas precisam existir).")
        print("- Verifique se a SECRET_KEY no seu .env está correta.")

if __name__ == "__main__":
    run_comissioning()
