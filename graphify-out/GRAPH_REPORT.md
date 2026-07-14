# Graph Report - .  (2026-07-14)

## Corpus Check
- Corpus is ~37,802 words - fits in a single context window. You may not need a graph.

## Summary
- 212 nodes · 328 edges · 33 communities (20 shown, 13 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 13 edges (avg confidence: 0.82)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Core Scraper Engine
- Execution Scripts Wrapper
- Commissioning Dashboard & Simulation
- System Architecture & Supabase
- Telegram Notification Services
- SQLite Syncing Service
- Cron Testing Suite
- SLA Metric & Deployment Config
- Development Architecture Learnings
- Project Roadmap & Completeness
- Cron Runner Script
- Daily Telegram Summary wrapper
- Log Monitoring script
- Periodic Summary script
- SLA Report script
- Parser Unit Tests
- Setup Environment scripts
- System Configuration setup
- Database Connection validation
- Cron Configuration deployment
- Offline Mode simulation
- Telegram Notification testing

## God Nodes (most connected - your core abstractions)
1. `DatabaseConnection` - 34 edges
2. `AgrisolusScraper` - 28 edges
3. `TelegramNotifier` - 19 edges
4. `parse_iso_datetime()` - 14 edges
5. `setup_logger()` - 14 edges
6. `SyncService` - 9 edges
7. `CronLogMonitor` - 8 edges
8. `Supabase Cloud Database` - 8 edges
9. `load_dashboard_data()` - 7 edges
10. `Scraper com BeautifulSoup4` - 7 edges

## Surprising Connections (you probably didn't know these)
- `test_db()` --calls--> `DatabaseConnection`  [EXTRACTED]
  tests/test_scraper.py → src/database/connection.py
- `test_db()` --calls--> `DatabaseConnection`  [EXTRACTED]
  tests/test_sync.py → src/database/connection.py
- `run_comissioning()` --calls--> `DatabaseConnection`  [EXTRACTED]
  scripts/comissioning.py → src/database/connection.py
- `main()` --calls--> `DatabaseConnection`  [EXTRACTED]
  scripts/run_daily_summary_telegram.py → src/database/connection.py
- `main()` --calls--> `DatabaseConnection`  [EXTRACTED]
  scripts/run_periodic_summary.py → src/database/connection.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Mecanismo de Persistência Híbrida e Fallback** — knowledge_architecture_sqlite_fallback, knowledge_architecture_supabase_cloud, knowledge_architecture_sync_service [EXTRACTED 1.00]
- **Métrica e Registro de SLA do Silo** — readme_sla_metric, knowledge_architecture_table_historico_scraping, knowledge_consideracoes_resolved_questions [EXTRACTED 1.00]
- **Estratégia de Baixo Consumo (Raspberry Pi 3B 1GB)** — knowledge_aprendizados_push_only_bot, knowledge_architecture_beautifulsoup_scraper, knowledge_architecture_cron_scheduler [INFERRED 0.95]

## Communities (33 total, 13 thin omitted)

### Community 0 - "Core Scraper Engine"
Cohesion: 0.08
Nodes (22): run(), AgrisolusScraper, Lê a lista de lotes configurados, executa o scraping detalhado de cada um,, Scraper oficial para o portal Agrisolus.     Realiza o login, navegação, extraçã, Faz o parse do HTML de detalhes do lote, extrai as variáveis JS         e decide, Realiza a autenticação no portal Agrisolus.         Retorna True se autenticado, Busca o último peso salvo para o silo localmente (ou remotamente se possível), Salva os dados extraídos no Supabase. Se falhar, faz o fallback para o SQLite lo (+14 more)

### Community 1 - "Execution Scripts Wrapper"
Cohesion: 0.16
Nodes (16): datetime, main(), main(), main(), main(), run_telegram_commissioning(), Serviço push-only para o Telegram utilizando o aiogram.     Envia alertas imedia, TelegramNotifier (+8 more)

### Community 2 - "Commissioning Dashboard & Simulation"
Cohesion: 0.09
Nodes (19): Client, Connection, Script de Comissionamento para validação em tempo real das credenciais e conexão, run_comissioning(), run_simulation(), load_dashboard_data(), main(), Carrega todos os dados do banco de dados (Supabase principal, fallback SQLite). (+11 more)

### Community 3 - "System Architecture & Supabase"
Cohesion: 0.11
Nodes (18): Mapeamento de Lotes, Scraper com BeautifulSoup4, Cron Scheduler, Fluxo de Dados, Modelo MER, SQLite Local Fallback, Streamlit Dashboard, Supabase Cloud Database (+10 more)

### Community 4 - "Telegram Notification Services"
Cohesion: 0.20
Nodes (5): Envia o relatório diário de SLA, Consumo e Saldo de ração às 18:00., Envia uma mensagem assincronamente e garante que a sessão do bot seja fechada., Envia uma mensagem de texto gerenciando o event loop de forma síncrona., Envia um alerta imediato de que o silo está sem enviar dados por mais de 2 horas, Envia um resumo de ocorrências de silos fora de envio por mais de 3 horas.

### Community 5 - "SQLite Syncing Service"
Cohesion: 0.28
Nodes (5): Executa o fluxo de sincronização do SQLite local para o Supabase.         Retorn, Sincroniza os dados coletados localmente no SQLite (durante falhas de internet), SyncService, test_db(), test_sync_process()

### Community 6 - "Cron Testing Suite"
Cohesion: 0.29
Nodes (6): Verifica se todos os scripts wrappers do cron existem no diretório scripts/., Verifica se os scripts wrappers do cron têm permissão de execução (+x)., Verifica se o script 4_setup_cron.sh aponta corretamente para os wrappers do cro, test_cron_wrappers_executable(), test_cron_wrappers_existence(), test_setup_cron_script_alignment()

### Community 7 - "SLA Metric & Deployment Config"
Cohesion: 0.33
Nodes (4): Tabela: HISTORICO_SCRAPING, Decisões e Considerações, Configuração do Cronie no Alpine Linux, Métrica do SLA

### Community 8 - "Development Architecture Learnings"
Cohesion: 0.40
Nodes (4): Configuração do PYTHONPATH no Cron, Estratégia Push-Only para Telegram Bot, Caminho Absoluto no SQLite, Conversor de Datas ISO sem Timezone

## Knowledge Gaps
- **23 isolated node(s):** `1_install_env.sh script`, `2_setup_env.sh script`, `3_test_db.sh script`, `4_setup_cron.sh script`, `5_test_offline.sh script` (+18 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **13 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `DatabaseConnection` connect `Commissioning Dashboard & Simulation` to `Core Scraper Engine`, `Execution Scripts Wrapper`, `SQLite Syncing Service`?**
  _High betweenness centrality (0.140) - this node is a cross-community bridge._
- **Why does `AgrisolusScraper` connect `Core Scraper Engine` to `Execution Scripts Wrapper`, `Commissioning Dashboard & Simulation`, `SQLite Syncing Service`?**
  _High betweenness centrality (0.137) - this node is a cross-community bridge._
- **Why does `TelegramNotifier` connect `Execution Scripts Wrapper` to `Commissioning Dashboard & Simulation`, `Telegram Notification Services`?**
  _High betweenness centrality (0.075) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `AgrisolusScraper` (e.g. with `DatabaseConnection` and `SyncService`) actually correct?**
  _`AgrisolusScraper` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `1_install_env.sh script`, `2_setup_env.sh script`, `3_test_db.sh script` to the rest of the system?**
  _23 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Core Scraper Engine` be split into smaller, more focused modules?**
  _Cohesion score 0.07539118065433854 - nodes in this community are weakly interconnected._
- **Should `Commissioning Dashboard & Simulation` be split into smaller, more focused modules?**
  _Cohesion score 0.09032258064516129 - nodes in this community are weakly interconnected._