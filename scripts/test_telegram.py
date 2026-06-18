#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de teste rápido para envio de notificações via Telegram.
Valida as chaves TELEGRAM_BOT_TOKEN e TELEGRAM_ALLOWED_USER_ID.
"""
import os
import sys

# Garante que o Python encontre o pacote 'src'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.bot.notifier import TelegramNotifier

def run_telegram_commissioning():
    print("==================================================")
    print("        TESTE DE COMISSIONAMENTO DO TELEGRAM      ")
    print("==================================================")
    
    notifier = TelegramNotifier()
    
    # Valida chaves
    if not notifier.token or not notifier.chat_id:
        print("\n❌ ERRO: Chaves do Telegram ausentes no .env.")
        print("Preencha TELEGRAM_BOT_TOKEN e TELEGRAM_ALLOWED_USER_ID no .env antes de rodar.")
        return
        
    print(f"Token do Bot: {notifier.token[:15]}...")
    print(f"Chat ID de Destino: {notifier.chat_id}")
    print("\nEnviando mensagem de teste...")
    
    test_msg = (
        "🔌 <b>Agrisolus Scraper: Teste de Conectividade</b>\n\n"
        "Parabéns! O comissionamento das notificações via Telegram foi concluído com sucesso.\n"
        "Este bot está pronto para enviar alertas imediatos de silos offline, resumos e relatórios diários de SLA!\n\n"
        "<i>Pilares: Comunicação Eficiente & Tecnologia Habilitadora.</i>"
    )
    
    success = notifier.send_message(test_msg)
    
    if success:
        print("\n✅ SUCESSO: Mensagem enviada com sucesso! Verifique seu aplicativo do Telegram.")
    else:
        print("\n❌ FALHA: Não foi possível enviar a mensagem para o Telegram.")
        print("\nDicas de diagnóstico:")
        print("1. Verifique se o seu TELEGRAM_BOT_TOKEN está correto.")
        print("2. Verifique se o seu TELEGRAM_ALLOWED_USER_ID (Chat ID) está correto.")
        print("3. IMPORTANTE: Você precisa abrir o seu bot no Telegram e clicar em /start (Iniciar) antes de receber mensagens dele.")
        print("4. Verifique a sua conexão com a internet.")
        
    print("==================================================")

if __name__ == "__main__":
    run_telegram_commissioning()
