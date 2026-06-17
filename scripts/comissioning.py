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
        print("\n1. Tentando INSERIR um registro de teste no Supabase...")
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
        
        # Insere/Upserta o lote no Supabase
        response = client.table("lotes").upsert(test_data).execute()
        
        print("✅ SUCESSO: Registro de teste inserido com sucesso!")
        print("\n==================================================")
        print("💻 COMO CONFERIR NO SEU PAINEL DO SUPABASE:")
        print("1. Acesse seu projeto no Supabase.")
        print("2. Clique no ícone 'Table Editor' (Editor de Tabelas) no menu lateral esquerdo.")
        print("3. Selecione a tabela 'lotes'.")
        print(f"4. Você deve ver uma linha com o id_lote '{test_id}' e empresa '{test_data['empresa']}'!")
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
