Repositorio destinado a fazer o scraping de dados dos lotes C.Vale com dispositivos Agrisolus


Stack tecnologica (hardware + software
- Raspberry 3b (alpine linux) 1Gb de ram
- SQLite local para fallback
- Supabase (postgres)
- Streamlit community
- Docker / Docker compose
- Telegram bot (aiogram)

# Premissas:
- O scraper (BeautifulSoup) deverá ser configurado pra rodar no cron a cada hora
- salvar as leituras no postgres no supabase, com salvamento incremental. Esperamos que o aviario mande dados de forma intermitente (problema com conexão de internet)
- construir um dashboard no streamlit community
Objetivo: Ver como está funcionando a célula de carga (silo) neste aviario.
- Criar um código de alertas se o silo ficar mais de 2 horas sem enviar dados novos na plataforma
- criar scripts de teste
- criar um bot telegram para me avisar quando ficar sem enviar dados por mais de 3 horas. As 6 da manhã, 11 da manhã, 13 da tarde e 16 da tarde. Resumindo as ocorrencias de quantas horas ficaram sem enviar dados
- enviar no telegram o SLA do silo do das 17h do dia anterior até as 17h do dia atual. Enviar as 18h. Enviar a curva de saldo de ração, o consumo de ração por silo

# Bibliotecas python sugeridas
- BeautifulSoup
- numpy
- mapplotlib
- streamlit
- aiogram

# O que deve ser salvo no banco de dados com o scrapper (gerar MER para contexto e documentação)

## Dados do produtor Marcelo Fumagalli (pegar dados do aviario no *.json a ser gerado conforme premissas do arquivo /docs/GerarJson.md)
- Nome Produtor
- Aviario
- Lote
- Linhagem
- O que for importante

## Dados do Silo
- Dados do silo
- idSilo
- DataSaldo
- Horario
- Valor de Ração no Silo
- registrar o consumo do silo

## Alertas
- Tipo
- Datetime (unique)
- Mensagem (not null)

## Calibrações
- Datetime (unique)
- Idade
- Serial
- Zona

# Tarefas adicionais
- Gerar tutorial de se conectar ao supabase (nunca usei)
- Criar pastas para os arquivos com base em computacao orientada a objetos
- Crie um arquivo de roadmap
- Crie um arquivo de completude do Roadmap
- Crie uma pasta de knowledge para conceitos a serem aprendidos durante a criação do codigo
- Crie um arquivo na pasta knowledge com o changelog, lições aprendidas, arquitetura, stack
- crie arquivo .gitignore para proteger nossos secrets antes de dar o primeiro commit
- crie uma pasta /tests para salvar os testes
- crie uma pasta /scripts para os scripts de comissionamento, manutenção e reparo

# Perfil
- liberado para commit no repositorio remoto após executar testes
