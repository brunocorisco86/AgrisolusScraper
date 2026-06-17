import logging
import os

def setup_logger(name="agrisolus", log_file="test_run.log", level=logging.INFO):
    """
    Configura o sistema de logs.
    Grava os logs em um arquivo (sobrescrevendo a cada execução) e exibe no console.
    """
    # Garante que o diretório para o arquivo de log existe
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Se já existirem handlers configurados para esse logger, evita duplicidade
    if logger.handlers:
        return logger

    # Formato dos logs: Data/Hora [Nível] Nome: Mensagem
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')

    # Handler para o arquivo (mode='w' garante que o arquivo é sobrescrito a cada execução)
    file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Handler para o terminal (stdout)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger
