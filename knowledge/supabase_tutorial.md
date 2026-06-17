# Conectando ao Supabase com Python

Este tutorial descreve como conectar a aplicação Python ao Supabase utilizando PostgreSQL diretamente ou através de SDKs.

---

## 🔌 Opções de Conectividade

Como o Supabase expõe um banco de dados PostgreSQL padrão, temos duas opções principais para nos conectar a ele em Python:

### Opção 1: Via biblioteca oficial do Supabase (Recomendado para APIs/Auth)
A biblioteca `supabase-py` fornece um cliente HTTP para interagir com o Supabase via APIs REST geradas automaticamente pelo PostgREST.

**Instalação**:
```bash
pip install supabase
```

**Exemplo de uso**:
```python
import os
from supabase import create_client, Client

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Exemplo de inserção
response = supabase.table("leituras").insert({
    "silo_id": "silo_01",
    "data_saldo": "2026-06-17",
    "horario": "20:00:00",
    "valor_racao": 15200.5
}).execute()
```

### Opção 2: Conexão Direta ao PostgreSQL (Recomendado para o Scraper/Dashboard)
Para consultas complexas, inserções eficientes em lote e compatibilidade com o SQLite (usando a mesma sintaxe SQL), podemos utilizar o **Psycopg2** ou **asyncpg** para se conectar diretamente à porta do Postgres (`5432` ou `6543` para transaction pooler).

**Instalação**:
```bash
pip install psycopg2-binary
# ou
pip install sqlalchemy
```

**Exemplo de uso com SQLAlchemy**:
```python
import os
from sqlalchemy import create_engine

# A string de conexão é fornecida no painel do Supabase em Project Settings -> Database
db_url = os.environ.get("DATABASE_URL") # postgresql://postgres:[password]@db.[project-id].supabase.co:5432/postgres

engine = create_engine(db_url)

with engine.connect() as conn:
    result = conn.execute("SELECT * FROM produtores")
    for row in result:
        print(row)
```

---

## 🔒 Boas Práticas de Segurança

1. **Nunca comite chaves de API ou strings de conexão**: Mantenha chaves como `SUPABASE_KEY` e `DATABASE_URL` apenas no arquivo `.env`.
2. **Habilite Row Level Security (RLS)**: No painel do Supabase, sempre habilite RLS para as tabelas a fim de impedir acessos não autorizados se as chaves públicas forem vazadas.
3. **Use Transaction Pooling**: Como o scraper roda no cron a cada hora e o Telegram bot rodará constantemente, use a string de conexão do pooler de transação (porta `6543`) se houver problemas de limite de conexões no plano gratuito do Supabase.
