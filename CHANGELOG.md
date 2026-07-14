# Changelog - Agrisolus Silo Monitor

Todas as alterações significativas deste projeto serão documentadas neste arquivo.

---

## [1.1.0] - 2026-07-14

### Adicionado
- **API REST (FastAPI):** Servidor REST leve rodando na porta `8090` que fornece endpoints para consultas de status de ocupação, séries temporais, notas fiscais, alertas e acurácia.
- **Frontend SPA Integrado:** Interface web moderna e responsiva em HTML5/CSS/JS (com Chart.js) servida diretamente pela API na rota `/`. Possui tema escuro premium (glassmorphism), logotipos e favicon da C.Vale/Agrisolus.
- **Série Temporal Consolidada (Conjunto):** Lógica analítica e visual para agrupar e somar os pesos de todos os silos ativos utilizando alinhamento de data e preenchimento para frente (*forward fill*).
- **Console de Alertas Emulado:** Terminal de console retrô verde-limão integrado ao dashboard, acionado por botão, permitindo depurar os 20 alertas mais recentes diretamente na interface web.
- **Housekeeping de Logs:** Rotina automatizada em `scripts/housekeep_logs.py` e integrada ao cron para remover automaticamente arquivos `.log` com mais de 45 dias de idade.
- **Script de Inicialização:** Criado o utilitário `scripts/run_api.sh` para facilitar o startup do servidor.
- **Wrapper CLI para o Hermes:** Criado o utilitário `scripts/analyze_silos.sh` para simplificar chamadas de ferramentas (*tool calling*) pelo agente IA na VPS.

### Modificado
- **Migração de Banco de Dados:** Remoção completa da persistência na nuvem do Supabase, centralizando todas as operações no banco SQLite local (`local_fallback.db`).
- **Suíte de Testes:** Atualizada para rodar inteiramente no SQLite (100% de sucesso em 14 testes rodando com pytest).
- **Comissionamento do Sistema:** O script `scripts/comissioning.py` foi reescrito para testar a saúde do SQLite local, integridade de tabelas (incluindo `notas_fiscais`) e conexão de login com o portal Agrisolus.
- **Instalação do Cron:** Refinado o script `scripts/deploy/4_setup_cron.sh` para maior portabilidade (removendo caminhos absolutos do bash e integrando a tarefa de housekeeping).

---

## [1.0.0] - 2026-06-21

### Adicionado
- **Scraper Agrisolus:** Coleta automatizada de saldo de ração via BeautifulSoup e requisições HTTP simulando sessão no portal.
- **Banco Híbrido (Supabase + SQLite):** Lógica de persistência principal remota e cache/fallback local no SQLite.
- **Integração Telegram:** Notificações de queda de conectividade, resumos periódicos e relatórios diários de SLA às 18h.
- **Dashboard Streamlit:** Interface gráfica Streamlit para análise e visualização de consumo de ração.
- **Scripts de Deploy:** Passo a passo para comissionamento e agendamentos no Raspberry Pi 3B rodando Alpine Linux.
