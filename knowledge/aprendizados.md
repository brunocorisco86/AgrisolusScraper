# 🧠 Aprendizados de Implantação e Produção

Este documento registra os principais aprendizados técnicos e de infraestrutura coletados durante o desenvolvimento e a implantação do monitor de silos no ambiente de produção (Raspberry Pi 3B rodando Alpine Linux).

---

## 1. Caminhos Absolutos no SQLite (`SQLITE_PATH`)
* **Problema:** Quando os scripts Python são executados via Cron do sistema operacional, o diretório de execução padrão (`cwd`) geralmente é o diretório `home` do usuário executando o cron (como `/root` ou `/home/bruno`), e não a pasta raiz do projeto. Isso fazia com que o SQLite criasse arquivos `local_fallback.db` em locais aleatórios e o Dashboard Streamlit não os encontrasse.
* **Solução:** Adicionamos e configuramos a variável `SQLITE_PATH` com caminho absoluto no arquivo `.env` remoto:
  ```env
  SQLITE_PATH=/home/bruno/AgrisolusScraper/local_fallback.db
  ```
* **Aprendizado:** Para qualquer serviço ou script executado via agendador cron, o uso de caminhos relativos para persistência é uma fonte de falhas. Caminhos de arquivos no `.env` devem ser sempre absolutos.

---

## 2. Sintaxe de Executores Cron e Shebangs
* **Problema 1:** O script de deploy `5_test_offline.sh` foi inicialmente escrito com o shebang `#!/bash` em vez de `#!/bin/bash`. No Alpine Linux, isso causava erro `not found` imediato.
* **Problema 2:** O import de arquivos de pacotes relativos (`from src.database...`) falhava sob o Cron devido à falta do diretório raiz no `sys.path`.
* **Soluções:**
  * Corrigido o shebang no script.
  * No Crontab, configuramos a inicialização declarando explicitamente a variável `PYTHONPATH` e apontando para o binário Python do ambiente virtual:
    ```cron
    30 * * * * cd /home/bruno/AgrisolusScraper && env PYTHONPATH=/home/bruno/AgrisolusScraper /home/bruno/AgrisolusScraper/env/bin/python /home/bruno/AgrisolusScraper/src/main.py >> /home/bruno/AgrisolusScraper/test_run.log 2>&1
    ```
* **Aprendizado:** Ambientes virtuais devem ser chamados de forma absoluta no cron (`/caminho/projeto/env/bin/python`) e as variáveis de caminho do Python (`PYTHONPATH`) devem ser declaradas inline para evitar problemas de resolução de pacotes.

---

## 3. Estratégia Push-Only para Limites de Hardware (1GB RAM)
* **Decisão de Arquitetura:** Para atender à restrição de memória física no Raspberry Pi 3B (1GB RAM) sem degradar o sistema com processos pesados em background, decidimos não rodar um Telegram Bot clássico baseado em escuta ativa (polling/getUpdates/webhook).
* **Resultado:** O bot do Telegram foi desenvolvido de forma push-only. O código do notifier inicializa, envia a mensagem e encerra em milissegundos. Toda a lógica de agendamento de relatórios e resumos foi delegada ao **Cron nativo do SO**.
* **Métricas:** Redução de consumo de RAM do bot de ~100MB (para execução constante em background) para **0% em modo de espera**.

---

## 4. Parser de Datas sem Fuso Horário (Timezone Naive vs Aware)
* **Problema:** O Supabase retorna datas no formato ISO-8601 com offsets de fuso horário (ex: `+00:00` ou `Z`), enquanto cálculos nativos com `datetime.now()` no Python geram datas ingênuas (naive). Fazer a diferença entre datas aware e naive gera exceções matemáticas de tipo.
* **Solução:** Criação de um utilitário específico em [datetime_parser.py](file:///media/brunoconter/DOCUMENTOS3/11_AGRISOLUS_SCRAPER/src/utils/datetime_parser.py) que remove as informações de fuso horário após a conversão, permitindo cálculos de SLAs, diferença de horas offline e consumos sem erros matemáticos.
