#!/bin/bash
# -----------------------------------------------------------------------------
# Script: 2_setup_env.sh
# Descrição: Configura o arquivo de variáveis de ambiente (.env).
# -----------------------------------------------------------------------------

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_DIR" || exit 1

echo "=================================================="
echo "      PASSO 2: CONFIGURAÇÃO DO ARQUIVO .ENV       "
echo "=================================================="

# 1. Verifica se o .env já existe
if [ -f ".env" ]; then
    echo "ℹ️ O arquivo '.env' já existe no diretório raiz."
    echo "Caso precise reconfigurar, você pode editar diretamente ou fazer backup deste."
else
    # 2. Copia .env.example para .env
    if [ -f ".env.example" ]; then
        echo "📝 Copiando '.env.example' para '.env'..."
        cp .env.example .env
        echo "✅ Arquivo '.env' criado!"
    else
        echo "❌ ERRO: .env.example não encontrado para copiar."
        exit 1
    fi
fi

echo ""
echo "👉 IMPORTANTE: Por favor, abra o arquivo '.env' e configure suas credenciais:"
echo "   - ID_USUARIO e SENHA do Portal Agrisolus"
echo "   - SUPABASE_API_URL e SECRET_KEY do seu Supabase"
echo "   - TELEGRAM_BOT_TOKEN e TELEGRAM_ALLOWED_USER_ID para receber os alertas"
echo ""
echo "Você pode abrir o editor rodando: nano .env"
echo "=================================================="
