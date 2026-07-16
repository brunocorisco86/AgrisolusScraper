# Graph Report - .  (2026-07-16)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 253 nodes · 386 edges · 38 communities (21 shown, 17 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 14 edges (avg confidence: 0.78)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `25b9a13a`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- AgrisolusScraper
- DatabaseConnection
- connection.py
- architecture.md
- TelegramNotifier
- main.py
- test_cron.py
- Métrica do SLA
- .get_sqlite_connection
- aprendizados.md
- Taxa de Conclusão do Projeto
- analyze_silos.sh
- run_api.sh
- run_audit_telegram.sh
- run_cron.sh
- run_daily_summary_telegram.sh
- run_log_monitor.sh
- run_periodic_summary.sh
- run_sla_report.sh
- 1_install_env.sh
- 2_setup_env.sh
- 3_test_db.sh
- 4_setup_cron.sh
- 5_test_offline.sh
- 6_test_telegram.sh
- post-receive
- Client

## God Nodes (most connected - your core abstractions)
1. `DatabaseConnection` - 45 edges
2. `AgrisolusScraper` - 29 edges
3. `SiloAnalyzer` - 19 edges
4. `TelegramNotifier` - 17 edges
5. `setup_logger()` - 10 edges
6. `parse_iso_datetime()` - 8 edges
7. `Supabase Cloud Database` - 8 edges
8. `Scraper com BeautifulSoup4` - 7 edges
9. `CronLogMonitor` - 6 edges
10. `load_dashboard_data()` - 6 edges

## Surprising Connections (you probably didn't know these)
- `setup_test_db()` --calls--> `DatabaseConnection`  [EXTRACTED]
  tests/test_periodic_scripts.py → src/database/connection.py
- `test_db()` --calls--> `DatabaseConnection`  [EXTRACTED]
  tests/test_scraper.py → src/database/connection.py
- `main()` --calls--> `TelegramNotifier`  [EXTRACTED]
  scripts/run_log_monitor.py → src/bot/notifier.py
- `main()` --calls--> `TelegramNotifier`  [EXTRACTED]
  scripts/run_periodic_summary.py → src/bot/notifier.py
- `main()` --calls--> `DatabaseConnection`  [EXTRACTED]
  scripts/run_periodic_summary.py → src/database/connection.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Mecanismo de Persistência Híbrida e Fallback** — knowledge_architecture_sqlite_fallback, knowledge_architecture_supabase_cloud, knowledge_architecture_sync_service [EXTRACTED 1.00]
- **Métrica e Registro de SLA do Silo** — readme_sla_metric, knowledge_architecture_table_historico_scraping, knowledge_consideracoes_resolved_questions [EXTRACTED 1.00]
- **Estratégia de Baixo Consumo (Raspberry Pi 3B 1GB)** — knowledge_aprendizados_push_only_bot, knowledge_architecture_beautifulsoup_scraper, knowledge_architecture_cron_scheduler [INFERRED 0.95]

## Communities (38 total, 17 thin omitted)

### Community 0 - "AgrisolusScraper"
Cohesion: 0.07
Nodes (24): run_comissioning(), run_simulation(), run(), AgrisolusScraper, Lê a lista de lotes configurados, executa o scraping detalhado de cada um,, Scraper oficial para o portal Agrisolus.     Realiza o login, navegação, extraçã, Faz o parse do HTML de detalhes do lote, extrai as variáveis JS         e decide, Realiza a autenticação no portal Agrisolus.         Retorna True se autenticado (+16 more)

### Community 1 - "DatabaseConnection"
Cohesion: 0.08
Nodes (25): analyze(), add_invoice(), get_telemetry_summary(), run(), Aplica média móvel simples na série temporal dos pesos dos silos para suavizar o, Analisa a série temporal do silo:         1. Suaviza a série temporal.         2, Objetivo Épico: Calcula o nível de acurácia do sensor comparando as         Nota, Insere os dados de uma nota fiscal de entrada de ração no banco local.         d (+17 more)

### Community 2 - "connection.py"
Cohesion: 0.12
Nodes (16): datetime, main(), main(), main(), main(), Ponto de entrada principal para a execução horária do scraper Agrisolus., parse_iso_datetime(), Parseia datas em formato ISO (com/sem T, com/sem fuso horário) com robustez. (+8 more)

### Community 3 - "architecture.md"
Cohesion: 0.11
Nodes (18): Mapeamento de Lotes, Scraper com BeautifulSoup4, Cron Scheduler, Fluxo de Dados, Modelo MER, SQLite Local Fallback, Streamlit Dashboard, Supabase Cloud Database (+10 more)

### Community 4 - "TelegramNotifier"
Cohesion: 0.18
Nodes (8): run_telegram_commissioning(), Serviço push-only para o Telegram utilizando o aiogram.     Envia alertas imedia, Envia o relatório diário de SLA, Consumo e Saldo de ração às 18:00., Envia uma mensagem assincronamente e garante que a sessão do bot seja fechada., Envia uma mensagem de texto gerenciando o event loop de forma síncrona., Envia um alerta imediato de que o silo está sem enviar dados por mais de 2 horas, Envia um resumo de ocorrências de silos fora de envio por mais de 3 horas., TelegramNotifier

### Community 5 - "main.py"
Cohesion: 0.18
Nodes (6): BaseModel, add_invoice(), get_dashboard_stats(), get_recent_alerts(), InvoiceCreate, Retorna o status geral de ocupação, taxas de esvaziamento, e forecasts para todo

### Community 6 - "test_cron.py"
Cohesion: 0.29
Nodes (6): Verifica se todos os scripts wrappers do cron existem no diretório scripts/., Verifica se os scripts wrappers do cron têm permissão de execução (+x)., Verifica se o script 4_setup_cron.sh aponta corretamente para os wrappers do cro, test_cron_wrappers_executable(), test_cron_wrappers_existence(), test_setup_cron_script_alignment()

### Community 7 - "Métrica do SLA"
Cohesion: 0.33
Nodes (4): Tabela: HISTORICO_SCRAPING, Decisões e Considerações, Configuração do Cronie no Alpine Linux, Métrica do SLA

### Community 8 - ".get_sqlite_connection"
Cohesion: 0.40
Nodes (3): Connection, Abre e retorna uma conexão com o SQLite local, garantindo que as tabelas estejam, Cria a estrutura de tabelas do MER definitivo no SQLite local.

### Community 9 - "aprendizados.md"
Cohesion: 0.40
Nodes (4): Configuração do PYTHONPATH no Cron, Estratégia Push-Only para Telegram Bot, Caminho Absoluto no SQLite, Conversor de Datas ISO sem Timezone

## Knowledge Gaps
- **29 isolated node(s):** `1_install_env.sh script`, `2_setup_env.sh script`, `3_test_db.sh script`, `5_test_offline.sh script`, `6_test_telegram.sh script` (+24 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **17 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `DatabaseConnection` connect `DatabaseConnection` to `AgrisolusScraper`, `.get_sqlite_connection`, `connection.py`, `main.py`?**
  _High betweenness centrality (0.191) - this node is a cross-community bridge._
- **Why does `AgrisolusScraper` connect `AgrisolusScraper` to `DatabaseConnection`, `connection.py`?**
  _High betweenness centrality (0.132) - this node is a cross-community bridge._
- **Why does `SiloAnalyzer` connect `DatabaseConnection` to `main.py`?**
  _High betweenness centrality (0.072) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `DatabaseConnection` (e.g. with `SiloAnalyzer` and `InvoiceCreate`) actually correct?**
  _`DatabaseConnection` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `SiloAnalyzer` (e.g. with `DatabaseConnection` and `InvoiceCreate`) actually correct?**
  _`SiloAnalyzer` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `1_install_env.sh script`, `2_setup_env.sh script`, `3_test_db.sh script` to the rest of the system?**
  _76 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `AgrisolusScraper` be split into smaller, more focused modules?**
  _Cohesion score 0.06976744186046512 - nodes in this community are weakly interconnected._