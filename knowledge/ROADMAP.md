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

### **Fase 7: Otimizações e Observabilidade (Melhorias de Produção)**
- [ ] **Mecanismo de Retries (Re-tentativas) no Scraper**: Adicionar re-tentativas de login/acesso (até 2 vezes com intervalo de 1 min) em caso de timeout temporário do portal Agrisolus, evitando falsos alertas no Telegram.
- [ ] **Rotação e Limpeza do SQLite Local**: Implementar rotina para expurgar leituras locais mais antigas que 90 dias no `local_fallback.db`, controlando o uso de espaço em disco e o desgaste do cartão SD do Raspberry Pi.
- [ ] **Monitoramento de Saúde do Raspberry Pi (Host)**: Incluir status de temperatura, uso de CPU e RAM nos relatórios das 18h no Telegram para prevenir travamentos de hardware em dias quentes no aviário.
- [ ] **Proteção do Dashboard (Autenticação Básica)**: Adicionar autenticação simples no Streamlit se a visualização for hospedada publicamente.
