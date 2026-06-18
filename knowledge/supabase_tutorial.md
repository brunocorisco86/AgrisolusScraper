# Conectando ao Supabase com Python

Este tutorial descreve como conectar a aplicação Python ao Supabase utilizando a biblioteca oficial.

---

## 🔌 Opção Recomendada: SDK Oficial do Supabase

Para máxima compatibilidade, facilidade de autenticação e bypass de políticas RLS em ambiente administrativo/produção, utilizamos o SDK oficial `supabase-py`. Ela se comunica de forma transparente via requisições HTTPS e PostgREST.

**Instalação**:
```bash
pip install supabase
```

### Configurando o Cliente
O cliente é instanciado na classe `DatabaseConnection` localizada em [connection.py](file:///media/brunoconter/DOCUMENTOS3/11_AGRISOLUS_SCRAPER/src/database/connection.py):

```python
import os
from supabase import create_client, Client

url = os.getenv("SUPABASE_API_URL")
key = os.getenv("SECRET_KEY") # Service role/bypass RLS key
supabase: Client = create_client(url, key)
```

---

## 📥 Exemplos de Operações Comuns (CRUD)

### 1. Inserção / Upsert (Atualização em Conflito)
Para evitar falhas de chaves duplicadas (por exemplo, leituras com o mesmo timestamp), utilize o método `upsert` com a cláusula `on_conflict` especificando as colunas únicas:

```python
# Inserir ou Atualizar leituras garantindo unicidade
client.table("leituras").upsert(
    [
        {
            "silo_id": "Silo-819-01",
            "data_leitura": "2026-06-17T12:00:00",
            "valor_racao_kg": 5000.0,
            "consumo_kg": 15.2
        }
    ],
    on_conflict="silo_id,data_leitura"
).execute()
```

### 2. Seleção de Dados com Filtros
Para obter os registros de lotes específicos do seu aviário:

```python
# Seleciona todos os lotes do Aviário 819
response = client.table("lotes") \
    .select("id_lote") \
    .ilike("aviario", "%Aviário 819%") \
    .execute()

lote_ids = [row["id_lote"] for row in response.data]
```

### 3. Seleção Ordenada e Limitada
Para calcular alertas ou resumos baseados no último registro de envio do silo:

```python
response = client.table("leituras") \
    .select("data_leitura") \
    .eq("silo_id", "Silo-819-01") \
    .order("data_leitura", desc=True) \
    .limit(1) \
    .execute()

if response.data:
    ultima_data = response.data[0]["data_leitura"]
```

---

## 🔒 Boas Práticas de Segurança e Recursos

1. **Proteção das Chaves de API**: Mantenha as credenciais `SUPABASE_API_URL` e `SECRET_KEY` exclusivas do arquivo local `.env` (nunca comitadas no Git). O arquivo `.gitignore` já está pré-configurado para ignorar `.env`.
2. **Utilização da Key de Acesso Administrativo (Service Role)**: A chave `SECRET_KEY` (service role) é necessária em ambientes autônomos (como cron scraper no Raspberry Pi) para que o sistema consiga gravar os dados diretamente sem restrições de RLS.
3. **Consumo de Memória Zero**: Como a API funciona inteiramente via HTTP REST, as conexões são encerradas imediatamente após a requisição, eliminando o consumo contínuo de recursos ou limites de pooler de conexões PostgreSQL.
