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
- [ ] Criar bot Telegram usando a biblioteca `aiogram`.
- [ ] Lógica de Alertas: Enviar notificação imediata se o silo estiver sem enviar dados por mais de **2 horas**.
- [ ] Lógica de Resumos: Enviar resumos de quedas nos horários **06:00, 11:00, 13:00 e 16:00** se houver mais de 3 horas sem dados.
- [ ] Lógica de SLA: Enviar às **18:00** o SLA do silo (das 17:00 do dia anterior às 17:00 do dia atual), consumo e curva de saldo.

### **Fase 5: Dashboard Streamlit**
- [ ] Criar interface visual interativa para acompanhamento do saldo do silo.
- [ ] Exibir gráficos de curva de consumo de ração.
- [ ] Exibir histórico de alertas e métricas de SLA do silo.

### **Fase 6: Dockerização e Testes**
- [ ] Criar testes unitários para a classe Scraper e classes de Banco de Dados na pasta `/tests`.
- [ ] Criar scripts de comissionamento e testes manuais na pasta `/scripts`.
- [ ] Configurar `Dockerfile` e `docker-compose.yml` otimizados para o Raspberry Pi 3B (Alpine Linux).
