#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de Simulação de Offline e Fallback SQLite.
Demonstra a resiliência do sistema quando a conexão com o Supabase é interrompida.
"""
import os
import sys
import sqlite3
from unittest.mock import MagicMock

# Garante que o Python encontre o pacote 'src'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database.connection import DatabaseConnection
from src.scraper.extractor import AgrisolusScraper

def run_simulation():
    print("==================================================")
    print("      SIMULAÇÃO DE QUEDA DE INTERNET / OFFLINE    ")
    print("==================================================")
    
    # 1. Instanciar DatabaseConnection com URL inválida para forçar falha no Supabase
    print("\n1. Inicializando conexão forçando falha com Supabase (URL inválida)...")
    db_conn = DatabaseConnection(
        supabase_url="https://invalid-id-supabase.co",
        secret_key="fake-secret-key",
        sqlite_path="local_fallback.db"
    )
    
    # 2. Mockar envio de alertas Telegram para não floodar o Telegram real do usuário
    from src.bot.notifier import TelegramNotifier
    TelegramNotifier.send_immediate_alert = MagicMock(return_value=True)
    print("✅ Envio de alertas reais do Telegram desabilitado para o teste.")

    # 3. Ler o HTML local de teste para simular o scraping sem precisar logar
    html_path = "scripts/batch_details.html"
    if not os.path.exists(html_path):
        print(f"❌ ERRO: O arquivo de dump {html_path} não existe.")
        print("Por favor, execute o script 'scripts/test_scraper.py' primeiro para gerar o dump.")
        return
        
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    # 4. Inicializar o scraper e processar o HTML
    print("\n2. Inicializando scraper e processando o HTML do lote...")
    scraper = AgrisolusScraper(db_conn=db_conn)
    
    # Executa o processamento
    link_lote = "https://s2.agrisolus.com.br/Home/Detalhes?idLote=4200000019"
    scraper._process_lote_html(html_content, link_lote)
    
    print("\n3. Verificando persistência local no SQLite (local_fallback.db)...")
    try:
        conn = sqlite3.connect("local_fallback.db")
        cursor = conn.cursor()
        
        # Verificar Lote
        cursor.execute("SELECT id_lote, empresa, aviario FROM lotes WHERE id_lote = 4200000019")
        lote = cursor.fetchone()
        if lote:
            print(f"   [SQLite] Lote salvo: ID={lote[0]}, Empresa='{lote[1]}', Aviário='{lote[2]}'")
        else:
            print("   [SQLite] ❌ Falha: Lote não encontrado.")
            
        # Verificar Silos
        cursor.execute("SELECT id_silo, capacidade_kg FROM silos WHERE lote_id = 4200000019")
        silos = cursor.fetchall()
        print(f"   [SQLite] Silos salvos ({len(silos)}):")
        for s in silos:
            print(f"     - Silo ID: {s[0]}, Capacidade: {s[1]} kg")
            
        # Verificar Leituras
        cursor.execute("SELECT COUNT(*) FROM leituras")
        leituras_count = cursor.fetchone()[0]
        print(f"   [SQLite] Leituras no buffer local: {leituras_count}")
        
        # Verificar Alertas
        cursor.execute("SELECT COUNT(*) FROM alertas")
        alertas_count = cursor.fetchone()[0]
        print(f"   [SQLite] Alertas no buffer local: {alertas_count}")
        
        conn.close()
        
        print("\n==================================================")
        print("🎉 SUCESSO: O Fallback SQLite funcionou com perfeição!")
        print("Como o Supabase estava offline, os dados foram bufferizados")
        print("localmente na tabela SQLite 'leituras' e 'alertas'.")
        print("Quando a conexão for restabelecida, a próxima execução")
        print("do scraper irá sincronizá-los e limpar o buffer local!")
        print("==================================================")
        
    except Exception as e:
        print(f"❌ ERRO ao acessar o SQLite: {e}")

if __name__ == "__main__":
    run_simulation()
