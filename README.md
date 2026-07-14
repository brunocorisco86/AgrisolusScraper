# 🌾 Agrisolus Silo Monitor & Scraper

[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/)
[![Database](https://img.shields.io/badge/database-SQLite%20Local-green)](https://sqlite.org/)
[![API & Dashboard](https://img.shields.io/badge/REST%20API-FastAPI-009688)](https://fastapi.tiangolo.com/)
[![Status](https://img.shields.io/badge/SLA%20Target-95%25%2B-brightgreen)]()
[![Repository](https://img.shields.io/badge/Origin-GitHub-black)](https://github.com/brunocorisco86/AgrisolusScraper)

Este repositório contém a solução completa para o monitoramento de células de carga (silos) de ração do **Aviário 819** (Lote 85, C.Vale), baseando-se em três pilares:
1. **Comunicação Eficiente**: Notificações e relatórios periódicos integrados ao Telegram, além de documentação e suporte para Tool Calling pelo agente **Hermes** na VPS.
2. **Processos Otimizados**: Acompanhamento dinâmico de consumo diário, detecção automática de carregamentos e auditoria de acurácia de sensores físicos comparados com notas fiscais.
3. **Tecnologia Habilitadora**: Scraper resiliente e API REST leve (FastAPI) com persistência principal local (SQLite) e dashboard interativo integrado, otimizados para rodar de forma leve na VPS ou no Raspberry Pi 3B (1GB RAM).

---

## 📂 Árvore de Arquivos e Funções

Abaixo está detalhada a estrutura do projeto com as respectivas funções de cada arquivo e diretório:

```
.
├── .env.example                # Template de configuração de variáveis de ambiente
├── requirements.txt            # Dependências Python instaladas no projeto
├── lotes_config.json           # Lista local configurada do lote monitorado (Aviário 819)
├── HERMES_AGENT.md             # Guia de tool calling e regras para o Agente Hermes na VPS
│
├── docs/                       # Requisitos, especificações e diagramas
│   └── GerarJson.md            # Regras originais para geração de mapeamento de lotes
│
├── knowledge/                  # Base de conhecimento, planejamento e logs do projeto
│   ├── COMPLETUDE.md           # Taxa de conclusão detalhada por fase (100% concluído)
│   ├── ROADMAP.md              # Metas e divisões em fases do desenvolvimento
│   ├── architecture.md         # Detalhes de arquitetura, stack de software e diagrama MER
│   ├── consideracoes.md        # Registro de decisões de desenvolvimento sanadas
│   └── dashboard_community_deploy.md # Tutorial antigo de publicação no Streamlit Cloud
│
├── scripts/                    # Scripts auxiliares, testes manuais e rotinas de deploy
│   ├── comissioning.py         # Valida credenciais do portal e integridade do banco SQLite local
│   ├── simulate_offline.py     # Simula queda de rede forçando a persistência no SQLite
│   ├── test_telegram.py        # Testa envio de mensagem no chat de destino via Bot Telegram
│   ├── run_cron.sh             # Script de coleta executado de hora em hora pelo cron do host
│   ├── run_periodic_summary.py # Processo do cron para resumos de silos offline às 06, 11, 13 e 16h
│   ├── run_sla_report.py       # Processo do cron para relatório diário de SLA e Consumo às 18h
│   ├── run_api.sh              # Wrapper para iniciar o servidor API/Dashboard na porta 8090
│   ├── analyze_silos.sh        # Wrapper CLI de análise de silos para tool calling do Hermes
│   ├── housekeep_logs.py       # Script utilitário para expurgar logs com mais de 45 dias
│   │
│   └── deploy/                 # Roteiro passo a passo interativo para implantação em produção
│       ├── 1_install_env.sh    # [Passo 1] Cria o ambiente virtual python 'env' e instala pacotes
│       ├── 2_setup_env.sh      # [Passo 2] Copia o .env.example e guia a configuração de senhas
│       ├── 3_test_db.sh        # [Passo 3] Dispara teste de integridade local do SQLite
│       ├── 4_setup_cron.sh     # [Passo 4] Adiciona regras cron locais no crontab do host
│       ├── 5_test_offline.sh   # [Passo 5] Executa a simulação offline salvando dados no SQLite
│       └── 6_test_telegram.sh  # [Passo 6] Dispara mensagem de teste no Telegram para comissionar
│
├── src/                        # Código-fonte principal estruturado em POO
│   ├── main.py                 # Ponto de entrada executado de hora em hora pelo cron
│   │
│   ├── analysis/               # Módulo de processamento matemático de série temporal
│   │   └── silo_analyzer.py    # Suavização de ruído, consumo diário, abastecimento e acurácia
│   │
│   ├── api/                    # Servidor REST API e arquivos estáticos do front-end
│   │   ├── main.py             # Rotas do FastAPI e montagem das pastas estáticas
│   │   └── static/
│   │       └── index.html      # Dashboard em HTML5/Vanilla CSS/Chart.js com console retro
│   │
│   ├── bot/                    # Integração com o canal de comunicação do Telegram
│   │   └── notifier.py         # Classe wrapper do aiogram para envio de alertas/relatórios
│   │
│   ├── dashboard/              # Interface Streamlit legada
│   │   └── app.py              # Interface Streamlit antiga para monitoramento de silos
│   │
│   ├── database/               # Módulo responsável pela persistência de dados
│   │   └── connection.py       # Gerencia conexões e inicialização das tabelas no SQLite local
│   │
│   ├── scraper/                # Módulo coletor de dados
│   │   └── extractor.py        # Autentica, extrai variáveis via Regex do HTML e calcula o consumo
│   │
│   └── utils/                  # Ferramentas globais e auxiliares
│       ├── logger.py           # Configura logs com rotação/sobregravação por execução
│       └── datetime_parser.py  # Conversor de datas ISO robusto com remoção de timezone
│
└── tests/                      # Suíte de testes unitários e de integração (pytest)
    ├── test_analyzer.py        # Testa suavização, detecção de cargas e cálculo de acurácia
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
2. **Resiliência Local**: O histórico de tentativas é armazenado diretamente no SQLite local (`local_fallback.db`).
3. **Métrica do SLA**: A conectividade e a transmissão ativa são avaliadas no dashboard através da fórmula:
   $$\text{SLA} = \frac{\text{Tentativas com sucesso\_conexao = True} \land \text{achou\_dados\_novos = True}}{\text{Número de tentativas esperadas no período}}$$

---

## ⚡ Guia Rápido de Instalação (Raspberry Pi & VPS)

Para colocar o projeto de pé de forma nativa e extremamente leve (minimizando o consumo de RAM):

1. **Clone o repositório** e entre na pasta do projeto.
2. **Execute os scripts sequenciais de deploy** localizados em `scripts/deploy/`:

```bash
# 1. Instale o ambiente virtual python e pacotes
./scripts/deploy/1_install_env.sh

# 2. Crie e preencha suas variáveis de ambiente no .env
./scripts/deploy/2_setup_env.sh
nano .env

# 3. Teste a integridade do banco SQLite local
./scripts/deploy/3_test_db.sh

# 4. Instale os agendamentos no Cron do sistema (inclui Scraper e Housekeeping)
./scripts/deploy/4_setup_cron.sh

# 5. Valide a persistência offline do SQLite
./scripts/deploy/5_test_offline.sh

# 6. Teste o recebimento de mensagens no seu Telegram
./scripts/deploy/6_test_telegram.sh
```

---

## 📊 Executando a API e o Dashboard Frontend

Para iniciar o servidor FastAPI que serve a API REST e a interface web estática (na porta **8090**):
```bash
./scripts/run_api.sh
```
Acesse no navegador: **`http://localhost:8090`**.

---

## 🧪 Rodando os Testes Automatizados

O projeto conta com **14 testes** unitários e de integração estruturados. Para executá-los:
```bash
env/bin/pytest tests/
```

---

## 🔧 Notas de Produção (Alpine Linux & Cron)

No ambiente de produção (Alpine Linux VM), deve-se atentar para a configuração do agendador de tarefas:
1. **Daemon Recomendado:** Use exclusivamente o daemon **`cronie`** (em vez do `crond` padrão do BusyBox) para garantir suporte a arquivos de spool e diretórios externos de cron.
2. **Conflito de Serviços:** Desative o serviço concorrente do BusyBox no OpenRC para evitar conflito de PID e escuta:
   ```bash
   rc-update del crond default || true
   rc-service crond stop || true
   rc-update add cronie default
   rc-service cronie start
   ```
3. **Parâmetros do Serviço:** Certifique-se de que o daemon do `cronie` não seja iniciado com a flag `-c` (muito usada em scripts padrões do BusyBox). No `cronie`, a flag `-c` ativa o "clustering support" e desativa a execução normal de tarefas locais. As opções no arquivo `/etc/conf.d/cronie` devem ser `CRON_OPTS=""`.
