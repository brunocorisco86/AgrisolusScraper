# ROADMAP - Agrisolus Scraper

Este arquivo define o planejamento e as metas de desenvolvimento para a solução de monitoramento dos silos Agrisolus.

---

## 🗺️ Fases do Projeto

### **Fase 1: Infraestrutura Básica e Documentação**
- [x] Criar estrutura de pastas orientada a objetos (POO).
- [x] Desenvolver documentações iniciais na pasta `knowledge/`.
- [x] Definir o modelo de banco de dados (MER) para o Supabase.

### **Fase 2: Conectividade e Banco de Dados**
- [x] Implementar classe de conexão e migração do **Supabase (PostgreSQL)**.
- [x] Implementar persistência local **SQLite** (fallback para quedas de internet).
- [x] Desenvolver serviço de sincronização (`SyncService`) local-remoto.

### **Fase 3: Módulo Scraper (BeautifulSoup)**
- [x] Criar script utilitário para gerar o `lotes_config.json` conforme `docs/GerarJson.md`.
- [x] Implementar classe `AgrisolusScraper` para login, navegação e extração de dados de saldo de ração.
- [x] Adicionar lógica de tratamento de falhas e logs detalhados.
- [x] Configurar agendamento (cron) para rodar o scraper a cada hora.

### **Fase 4: Alertas e Notificações (Telegram Bot - aiogram)**
- [x] Criar bot Telegram usando a biblioteca `aiogram` em modo push (Option B para 0% de overhead de RAM).
- [x] Lógica de Alertas: Enviar notificação imediata se o silo estiver sem enviar dados por mais de **2 horas**.
- [x] Lógica de Resumos: Enviar resumos de quedas nos horários **06:00, 11:00, 13:00 e 16:00** se houver mais de 3 horas sem dados.
- [x] Lógica de SLA: Enviar às **18:00** o SLA do silo (das 17:00 do dia anterior às 17:00 do dia atual), consumo e curva de saldo.

### **Fase 5: Dashboard Streamlit**
- [x] Criar interface visual interativa para acompanhamento do saldo do silo.
- [x] Exibir gráficos de curva de consumo de ração (usando Plotly).
- [x] Exibir histórico de alertas e métricas de SLA do silo.

### **Fase 6: Agendamento Local, Testes e Otimizações de Recursos**
- [x] Criar testes unitários para a classe Scraper e classes de Banco de Dados na pasta `/tests`.
- [x] Criar scripts de comissionamento e testes manuais na pasta `/scripts`.
- [x] Configurar scripts cron locais na máquina host (economia máxima de memória no Raspberry Pi 3B).
- [x] Decidir pela execução nativa no host (venv) no Raspberry Pi, removendo os arquivos Docker (`Dockerfile`, `docker-compose.yml`, `docker-crontab`) para poupar RAM e disco.

### **Fase 7: Otimizações, API REST e Painel Frontend**
- [x] **Rotação e Limpeza do SQLite Local**: Desenvolver utilitário de Housekeeping para expurgar logs com mais de 45 dias.
- [x] **API REST Integrada**: Criar API REST com FastAPI servindo endpoints estruturados para o Hermes Agent e para o front-end na porta 8090.
- [x] **Dashboard SPA Premium**: Desenvolver Dashboard SPA dinâmico em HTML5/CSS/JS (Chart.js) com estética glassmorphism dark-mode e logotipos C.Vale/Agrisolus.
- [x] **Série Temporal de Conjunto**: Implementar visualização consolidada do somatório dos silos, ordenando a linha do tempo cronologicamente da esquerda para a direita.
- [x] **Console de Alertas Emulado**: Criar mini-terminal retrô interativo no dashboard para depuração dos logs e alertas do sistema.

### **Fase 8: Estabilização e Alta Disponibilidade (Keepalive & Watchdog na VPS)**
- [ ] **Script de Watchdog (Cão de Guarda)**: Desenvolver um script leve (ex: cron a cada 5 mins) para testar o endpoint `/api/health`. Se a API não responder, reiniciar o processo uvicorn.
- [ ] **Configuração do Keepalive (Serviço Systemd/OpenRC)**: Criar o template de arquivo service para Systemd (VPS Ubuntu/Debian) ou OpenRC (Alpine Linux) para garantir a persistência em background pós-boot da máquina.
- [ ] **Monitoramento de Hardware do Host**: Incluir dados de consumo de CPU e RAM do Raspberry Pi / VPS nos relatórios diários de produção.
