# Arquitetura e Decisões Técnicas

Este documento descreve as decisões de arquitetura, a stack de tecnologia, o modelo de banco de dados (MER) e as lições aprendidas ao longo do desenvolvimento do Agrisolus Scraper.

---

## 🏗️ Arquitetura do Sistema

A solução foi projetada de forma modular e baseada em Programação Orientada a Objetos (POO), facilitando a manutenção e a extensibilidade de cada componente.

### Fluxo de Dados e Fallback Offline
1. **Scraper (BeautifulSoup)**: Executado periodicamente via `cron` (a cada 1 hora).
2. **Persistência Principal**: Tenta inserir os dados coletados diretamente no **Supabase (PostgreSQL)**.
3. **Fallback Offline**: Se a conexão de rede falhar (comum em ambientes rurais/aviários), os dados são salvos localmente em um banco de dados **SQLite** (`local_fallback.db`).
4. **Sincronizador (`SyncService`)**: A cada execução bem-sucedida com internet, verifica se existem registros pendentes no SQLite e faz o upload incremental para o Supabase.

---

## 🛠️ Stack Tecnológica

| Componente | Tecnologia | Racional de Escolha |
| :--- | :--- | :--- |
| **Ambiente de Execução** | Raspberry Pi 3B (Alpine Linux) | Baixo consumo de energia, ideal para ambiente físico (aviário), 1GB de RAM exige eficiência. |
| **Linguagem** | Python 3 | Excelente suporte para scraping, IA, bancos de dados e bots. |
| **Scraper** | BeautifulSoup4 / Requests | Leve e eficiente. Evitamos Selenium/Playwright devido ao limite de 1GB de RAM do Raspberry Pi. |
| **Banco Remoto** | Supabase (PostgreSQL) | Banco de dados relacional gratuito na nuvem, com ótima API e dashboards internos. |
| **Banco Local** | SQLite | Serverless, sem consumo de RAM adicional, embutido no Python, ideal para fallback local. |
| **Telegram Bot** | aiogram (v3) | Assíncrono, robusto, ideal para rodar em segundo plano sem travar a CPU. |
| **Dashboard** | Streamlit | Permite criar dashboards de dados dinâmicos de forma rápida e com ótima estética visual. |

---

## 📐 Modelo de Entidade e Relacionamento (MER)

O MER definitivo abaixo reflete de forma exata os campos disponíveis nos objetos coletados (`lotes`, `saldoRacao`, `alertas` e `calibracoes`). Ele garante compatibilidade estrutural tanto no Supabase quanto no SQLite local.

```mermaid
erDiagram
    LOTES ||--o{ SILOS : "contém"
    LOTES ||--o{ ALERTAS : "registra"
    LOTES ||--o{ CALIBRACOES : "possui"
    SILOS ||--o{ LEITURAS : "registra"

    LOTES {
        bigint id_lote PK
        string codigo_lote
        string empresa
        string estabelecimento
        string aviario
        string linhagem
        int qtd_alojamento
        timestamp data_alojamento
        int saldo_frangos
        timestamp updated_at
    }

    SILOS {
        string id_silo PK
        bigint lote_id FK
        numeric capacidade_kg
    }

    LEITURAS {
        serial id PK
        string silo_id FK
        timestamp data_leitura UK
        numeric valor_racao_g
        numeric valor_racao_kg
        numeric consumo_kg
        timestamp created_at
    }

    ALERTAS {
        serial id PK
        bigint lote_id FK
        int tipo_alerta
        string tipo_alerta_str
        timestamp data_alerta UK
        string mensagem
    }

    CALIBRACOES {
        serial id PK
        bigint lote_id FK
        string numero_serial
        int zona
        string zona_str
        timestamp data_calibracao UK
        int idade
    }
```


---

## 📝 Changelog

### v0.1.0 (2026-06-17)
- Inicialização do repositório Git.
- Configuração do `.gitignore` para proteção de credenciais (`.env`).
- Criação dos documentos `ROADMAP.md` e `COMPLETUDE.md` na raiz do projeto.
- Estruturação da pasta `knowledge/` com tutoriais e decisões arquiteturais.

---

## 💡 Lições Aprendidas
- *Alpine Linux no Raspberry Pi 3B*: Como o Alpine usa `musl` em vez de `glibc`, bibliotecas que dependem de C pré-compiladas (como `psycopg2` ou `cryptography`) podem precisar ser instaladas via gerenciador de pacotes do sistema (`apk`) ou compiladas localmente. Recomenda-se utilizar `psycopg2-binary` para desenvolvimento inicial ou SQLAlchemy.
