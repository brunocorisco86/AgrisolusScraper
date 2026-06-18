# 🚀 Tutorial de Implantação: Streamlit Community Cloud

Este guia descreve o passo a passo para implantar o seu dashboard de monitoramento de silos na nuvem gratuita do **Streamlit Community Cloud** conectado ao seu banco do **Supabase**.

---

## 📋 Pré-requisitos
1. O repositório [AgrisolusScraper](https://github.com/brunocorisco86/AgrisolusScraper) deve estar público ou privado na sua conta do GitHub.
2. Seu banco de dados Supabase já deve estar com as tabelas criadas (conforme o [supabase_schema.sql](file:///media/brunoconter/DOCUMENTOS3/11_AGRISOLUS_SCRAPER/scripts/supabase_schema.sql)).
3. Ter em mãos as credenciais de acesso ao Supabase (`SUPABASE_API_URL` e `SECRET_KEY`).

---

## 🛠️ Passo a Passo de Implantação

### Passo 1: Criar/Acessar Conta no Streamlit Cloud
1. Acesse [Streamlit Community Cloud](https://share.streamlit.io/).
2. Clique em **"Sign in with GitHub"** (Entrar com GitHub) e autorize a conexão.

### Passo 2: Configurar o Deploy do App
1. No painel inicial do Streamlit, clique no botão **"New app"** (Novo aplicativo) no canto superior direito.
2. Preencha os campos de deploy com as informações do seu repositório:
   * **Repository:** `brunocorisco86/AgrisolusScraper`
   * **Branch:** `main`
   * **Main file path:** `src/dashboard/app.py`
   * **App URL:** Escolha um subdomínio personalizado (ex: `agrisolus-silo-819.streamlit.app`).

### Passo 3: Configurar os Segredos (Variáveis de Ambiente)
Como a nuvem do Streamlit não utiliza o arquivo `.env` local por questões de segurança, você deve configurar as variáveis de ambiente diretamente nas configurações de **Secrets** do painel do Streamlit:

1. Antes de clicar em "Deploy", clique no link **"Advanced settings..."** (Configurações Avançadas) ou, caso já tenha iniciado, vá em **App Settings -> Secrets**.
2. Cole o conteúdo de configuração no formato **TOML** (chave/valor padrão Python):

```toml
SUPABASE_API_URL = "https://iimootclvuiyzdwajptw.supabase.co"
SECRET_KEY = "sb_secret_sua_chave_secreta_supabase"
# Caminho padrão para fallback local do SQLite na nuvem (opcional)
SQLITE_PATH = "local_fallback.db"
```

> [!IMPORTANT]
> Certifique-se de usar a URL base do Supabase sem o sufixo `/rest/v1/` no Streamlit Cloud, pois a biblioteca `supabase-py` trata a resolução do endpoint automaticamente.

3. Clique em **"Save"** (Salvar).

### Passo 4: Finalizar Deploy
1. Clique em **"Deploy!"**.
2. O Streamlit Cloud iniciará a criação do container, instalará todas as dependências declaradas no arquivo [requirements.txt](file:///media/brunoconter/DOCUMENTOS3/11_AGRISOLUS_SCRAPER/requirements.txt) automaticamente e inicializará o dashboard.
3. Em 2 ou 3 minutos o seu painel estará online e disponível publicamente ou privadamente (conforme as configurações de compartilhamento que você escolher no painel).

---

## 🔍 Como testar o Comissionamento na Nuvem
Ao abrir a URL do seu aplicativo implantado:
1. Veja se o indicador no topo direito mostra o status **"Aviário 819"**.
2. Verifique na barra lateral (sidebar) o status do banco de dados: ele deve exibir **"Online (Supabase) 🟢"**.
3. Se os gráficos e KPIs carregarem os dados históricos do silo do seu lote 85, o comissionamento foi concluído com sucesso e está plenamente operacional na nuvem!
