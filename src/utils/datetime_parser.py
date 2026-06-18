# -*- coding: utf-8 -*-
from datetime import datetime

def parse_iso_datetime(dt_str: str) -> datetime:
    """
    Parseia datas em formato ISO (com/sem T, com/sem fuso horário) com robustez.
    Remove qualquer informação de fuso horário para permitir operações matemáticas
    com datetime.now() que é naive (ingênuo/sem fuso horário).
    """
    if not dt_str:
        raise ValueError("String de data vazia.")
        
    dt_str = dt_str.strip()
    
    # Padroniza terminação UTC 'Z' para '+00:00'
    if dt_str.endswith("Z"):
        dt_str = dt_str[:-1] + "+00:00"
        
    # Tenta utilizar o fromisoformat nativo do Python (muito eficiente no Python 3.11+)
    try:
        dt = datetime.fromisoformat(dt_str)
        if dt.tzinfo is not None:
            # Converte para naive (ignora fuso horário)
            dt = dt.replace(tzinfo=None)
        return dt
    except Exception:
        pass

    # Fallback para múltiplos formatos comuns se o fromisoformat falhar
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue
            
    raise ValueError(f"Formato de data desconhecido ou inválido: '{dt_str}'")
