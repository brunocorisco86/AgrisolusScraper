# Imagem base leve do Debian Slim para evitar compilações demoradas no Raspberry Pi 3B.
# Debian Slim possui wheels pré-compilados para ARM64/v7 para pacotes como cryptography, lxml, etc.
FROM python:3.12-slim

# Define o diretório de trabalho
WORKDIR /app

# Instala dependências do sistema necessárias (cron e tzdata para fuso horário correto)
RUN apt-get update && apt-get install -y --no-install-recommends \
    cron \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Copia a lista de dependências
COPY requirements.txt .

# Instala as dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código do projeto
COPY . .

# Configura as variáveis de ambiente necessárias
ENV PYTHONPATH=/app
ENV TZ=America/Sao_Paulo

# Cria o arquivo de log para o cron
RUN touch /app/cron.log

# Adiciona o arquivo de crontab
COPY docker-crontab /etc/cron.d/agrisolus-cron

# Dá permissão correta ao crontab e aos scripts
RUN chmod 0644 /etc/cron.d/agrisolus-cron && \
    crontab /etc/cron.d/agrisolus-cron

# Exporta as variáveis de ambiente para /etc/environment e inicia o cron em foreground
CMD ["sh", "-c", "printenv | grep -v 'no_proxy' >> /etc/environment && cron -f"]
