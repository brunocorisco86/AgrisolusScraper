# -*- coding: utf-8 -*-
"""
Script utilitário de Housekeeping para limpeza de logs antigos (> 45 dias).
"""
import os
import time
from datetime import datetime, timedelta
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.utils.logger import setup_logger

logger = setup_logger(name="housekeeper", log_file="test_run.log")

def run_housekeeping(max_age_days=45):
    logger.info(f"Iniciando housekeeping de logs. Limite de idade: {max_age_days} dias.")
    now = time.time()
    cutoff = now - (max_age_days * 86400)
    
    project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    cleaned_files = 0
    bytes_freed = 0
    
    # Caminhos para verificar logs
    for root, dirs, files in os.walk(project_dir):
        # Evita entrar na pasta env (virtualenv)
        if "env" in dirs:
            dirs.remove("env")
            
        for file in files:
            if file.endswith(".log"):
                file_path = os.path.join(root, file)
                try:
                    file_mtime = os.path.getmtime(file_path)
                    if file_mtime < cutoff:
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        cleaned_files += 1
                        bytes_freed += file_size
                        logger.info(f"Log removido (antigo): {file_path} (Tamanho: {file_size} bytes)")
                except Exception as e:
                    logger.error(f"Erro ao processar arquivo {file_path}: {e}")
                    
    logger.info(f"Housekeeping concluído. Arquivos limpos: {cleaned_files}. Espaço liberado: {bytes_freed} bytes.")

if __name__ == "__main__":
    run_housekeeping()
