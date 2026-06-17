import os
import re
import json
import pytest
from src.utils.logger import setup_logger

# Configura o logger para rodar nos testes. Grava em test_run.log e sobrescreve
logger = setup_logger(name="test_suite", log_file="test_run.log")

def extract_js_var(var_name, html):
    pattern = r'var\s+' + re.escape(var_name) + r'\s*=\s*([\[\{].*?[\]\}]);'
    match = re.search(pattern, html, re.DOTALL)
    if match:
        var_content = match.group(1)
        try:
            return json.loads(var_content)
        except Exception as e:
            logger.error(f"Falha ao decodificar JSON para a variável {var_name}: {e}")
            return None
    logger.warning(f"Variável JS '{var_name}' não encontrada no HTML.")
    return None

def test_offline_parser():
    logger.info("--- Iniciando teste offline do parser BeautifulSoup/Regex ---")
    
    html_path = "scripts/batch_details.html"
    assert os.path.exists(html_path), "O dump de teste scripts/batch_details.html não existe!"
    
    logger.info(f"Carregando arquivo de dump offline: {html_path}")
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    # 1. Testando extração de 'lotes'
    logger.info("Extraindo dados de 'lotes'...")
    lotes = extract_js_var("lotes", html_content)
    assert lotes is not None, "A variável 'lotes' não pôde ser extraída."
    assert len(lotes) > 0, "A lista de lotes está vazia."
    
    first_lote = lotes[0]
    logger.info(f"Lote extraído com sucesso: ID {first_lote.get('IdLote')} - Aviário {first_lote.get('Aviario')}")
    assert first_lote.get("IdLote") == 4200000019
    assert first_lote.get("Aviario") == "Aviário 819"
    assert first_lote.get("CodigoLote") == "85"

    # 2. Testando extração de 'saldoRacao'
    logger.info("Extraindo dados de 'saldoRacao'...")
    saldo_racao = extract_js_var("saldoRacao", html_content)
    assert saldo_racao is not None, "A variável 'saldoRacao' não pôde ser extraída."
    assert len(saldo_racao) == 2, f"Esperava 2 silos, obteve {len(saldo_racao)}."
    
    silo1 = saldo_racao[0]
    silo2 = saldo_racao[1]
    
    logger.info(f"Silo 1 extraído: Descrição={silo1.get('Descricao')}, Quantidade={silo1.get('Quantidade')}")
    logger.info(f"Silo 2 extraído: Descrição={silo2.get('Descricao')}, Quantidade={silo2.get('Quantidade')}")
    
    assert silo1.get("Descricao") == "Silo-819-01"
    assert silo1.get("Capacidade") == 18000.0
    assert silo2.get("Descricao") == "Silo-819-02"
    assert silo2.get("Capacidade") == 18000.0

    logger.info("--- Teste offline do parser concluído com sucesso ---")
