# 🌾 Agrisolus Silo Monitor & Scraper

[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/)
[![Database](https://img.shields.io/badge/database-Supabase%20%28Postgres%29%20%7C%20SQLite-green)](https://supabase.com/)
[![Dashboard](https://img.shields.io/badge/dashboard-Streamlit-FF4B4B)](https://streamlit.io/)
[![Status](https://img.shields.io/badge/SLA%20Target-95%25%2B-brightgreen)]()
[![Repository](https://img.shields.io/badge/Origin-GitHub-black)](https://github.com/brunocorisco86/AgrisolusScraper)

Este repositório contém a solução completa para o monitoramento de células de carga (silos) de ração do **Aviário 819** (Lote 85, C.Vale), baseando-se em três pilares:
1. **Comunicação Eficiente**: Notificações e relatórios periódicos integrados ao Telegram.
2. **Processos Otimizados**: Acompanhamento dinâmico de consumo e SLA.
3. **Tecnologia Habilitadora**: Scraper resiliente com persistência principal na nuvem (Supabase) e fallback offline automático local (SQLite) otimizado para o Raspberry Pi 3B (1GB RAM).

---

## 📂 Árvore de Arquivos e Funções

Abaixo está detalhada a estrutura do projeto com as respectivas funções de cada arquivo e diretório:

```
.
├── .env.example                # Template de configuração de variáveis de ambiente
├── requirements.txt            # Dependências Python instaladas no projeto
├── lotes_config.json           # Lista local configurada do lote monitorado (Aviário 819)
│
├── docs/                       # Requisitos, especificações e scripts de migração do banco
│   ├── GerarJson.md            # Regras originais para geração de mapeamento de lotes
│   └── create_historico_scraping.sql # Script SQL para criar a tabela de histórico no Supabase
│
├── knowledge/                  # Base de conhecimento, planejamento e logs do projeto
│   ├── COMPLETUDE.md           # Taxa de conclusão detalhada por fase (100% concluído)
│   ├── ROADMAP.md              # Metas e divisões em fases do desenvolvimento
│   ├── architecture.md         # Detalhes de arquitetura, stack de software e diagrama MER
│   ├── consideracoes.md        # Registro de decisões de desenvolvimento sanadas
│   ├── supabase_tutorial.md    # Guia de conectividade e CRUD usando o SDK oficial do Supabase
│   └── dashboard_community_deploy.md # Tutorial de publicação do dashboard no Streamlit Cloud
│
├── scripts/                    # Scripts auxiliares, testes manuais e rotinas de deploy
│   ├── comissioning.py         # Valida credenciais e insere/remove lote teste no Supabase
│   ├── simulate_offline.py     # Simula queda de rede forçando a persistência no SQLite
│   ├── test_telegram.py        # Testa envio de mensagem no chat de destino via Bot Telegram
│   ├── run_cron.sh             # Script executado de hora em hora pelo cron do host
│   ├── run_periodic_summary.py # Processo do cron para resumos de silos offline às 06, 11, 13 e 16h
│   ├── run_sla_report.py       # Processo do cron para relatório diário de SLA e Consumo às 18h
│   │
│   └── deploy/                 # Roteiro passo a passo interativo para implantação em produção
│       ├── 1_install_env.sh    # [Passo 1] Cria o ambiente virtual python 'env' e instala pacotes
│       ├── 2_setup_env.sh      # [Passo 2] Copia o .env.example e guia a configuração de senhas
│       ├── 3_test_db.sh        # [Passo 3] Dispara o teste de comunicação com o Supabase
│       ├── 4_setup_cron.sh     # [Passo 4] Adiciona regras cron locais no crontab do host
│       ├── 5_test_offline.sh   # [Passo 5] Executa a simulação offline salvando dados no SQLite
│       └── 6_test_telegram.sh  # [Passo 6] Dispara mensagem de teste no Telegram para comissionar
│
├── src/                        # Código-fonte principal estruturado em POO
│   ├── main.py                 # Ponto de entrada executado de hora em hora pelo cron
│   │
│   ├── bot/                    # Integração com o canal de comunicação do Telegram
│   │   └── notifier.py         # Classe wrapper do aiogram para envio de alertas/relatórios
│   │
│   ├── dashboard/              # Interface gráfica web do usuário
│   │   └── app.py              # Interface Streamlit com gráficos Plotly e tolerância a falhas
│   │
│   ├── database/               # Módulo responsável pela persistência de dados
│   │   ├── connection.py       # Gerencia instâncias do Supabase SDK e conexões SQLite local
│   │   └── sync.py             # Sincroniza dados temporários locais para a nuvem quando há rede
│   │
│   ├── scraper/                # Módulo coletor de dados
│   │   └── extractor.py        # Autentica, extrai variáveis via Regex do HTML e calcula o consumo
│   │
│   └── utils/                  # Ferramentas globais e auxiliares
│       ├── logger.py           # Configura logs com rotação/sobregravação por execução
│       └── datetime_parser.py  # Conversor de datas ISO robusto com remoção de timezone
│
└── tests/                      # Suíte de testes unitários e de integração (pytest)
    ├── test_basic.py           # Validação básica de estruturas de dados e datas
    ├── test_dashboard.py       # Testa a tolerância a falhas e carregamento do Streamlit
    ├── test_database.py        # Testa criação de tabelas SQLite e comportamento sem chaves
    ├── test_periodic_scripts.py# Testa lógica de cálculo de SLA e resumos de offline
    └── test_scraper.py         # Testa processamento de HTML e comportamento resiliente do Scraper
```

---

## 📈 Cálculo do SLA & Histórico de Scraping

A disponibilidade e a conectividade de transmissão de dados dos silos são aferidas de forma contínua:
1. **Registro de Tentativas**: A cada hora, o scraper grava na tabela `historico_scraping` uma nova linha por silo contendo:
   - `sucesso_conexao` (boolean): Se o scraper conseguiu efetuar o login e acessar o portal Agrisolus.
   - `achou_dados_novos` (boolean): Se a leitura atualizada no portal é diferente da última leitura registrada na base local.
   - `peso_kg` (numeric): O peso atualizado da ração no silo.
2. **Resiliência Offline**: Se houver falha de conexão com a internet ou o Supabase estiver fora do ar, o registro é salvo no SQLite local e enviado automaticamente para a nuvem (`historico_scraping` no Supabase) via `SyncService` no próximo ciclo com internet disponível.
3. **Métrica do SLA**: A conectividade e a transmissão ativa são avaliadas diretamente no dashboard Streamlit através da fórmula:
   $$\text{SLA} = \frac{\text{Tentativas com sucesso\_conexao = True} \land \text{achou\_dados\_novos = True}}{\text{Número de tentativas esperadas no período}}$$
   *Nota: O script SQL de migração para o Supabase pode ser encontrado em [docs/create_historico_scraping.sql](file:///media/brunoconter/DOCUMENTOS3/11_AGRISOLUS_SCRAPER/docs/create_historico_scraping.sql).*

---

## ⚡ Guia Rápido de Instalação (Raspberry Pi)

Para colocar o projeto de pé de forma nativa e extremamente leve (minimizando o consumo de RAM):

1. **Clone o repositório** e entre na pasta do projeto.
2. **Execute os scripts sequenciais de deploy** localizados em `scripts/deploy/`:

```bash
# 1. Instale o ambiente virtual python e pacotes
./scripts/deploy/1_install_env.sh

# 2. Crie e preencha suas variáveis de ambiente no .env
./scripts/deploy/2_setup_env.sh
nano .env

# 3. Teste o banco de dados Supabase
./scripts/deploy/3_test_db.sh

# 4. Instale os agendamentos no Cron do sistema
./scripts/deploy/4_setup_cron.sh

# 5. Valide a persistência offline do SQLite
./scripts/deploy/5_test_offline.sh

# 6. Teste o recebimento de mensagens no seu Telegram
./scripts/deploy/6_test_telegram.sh
```

---

## 📊 Executando o Dashboard Localmente
Para abrir a interface gráfica do Streamlit e visualizar o comportamento dos silos:
```bash
source env/bin/activate
streamlit run src/dashboard/app.py
```
Acesse no navegador: `http://localhost:8501`.

---

## 🧪 Rodando os Testes Automatizados
O projeto conta com 13 testes unitários e de integração estruturados. Para executá-los:
```bash
env/bin/pytest tests/
```
