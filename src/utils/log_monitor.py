import os
import re
from datetime import datetime, timedelta
from src.utils.logger import setup_logger
from src.utils.datetime_parser import parse_iso_datetime

logger = setup_logger(name="cron_log_monitor", log_file="test_run.log")

class CronLogMonitor:
    """
    Serviço de auditoria e monitoramento de logs do Cron e da Aplicação.
    Detecta se o cron parou de rodar e varre exceções/erros nas últimas 24h.
    """
    def __init__(self, project_dir=None):
        self.project_dir = project_dir or os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        self.cron_log_path = os.path.join(self.project_dir, 'cron_exec.log')
        self.app_log_path = os.path.join(self.project_dir, 'test_run.log')

    def analyze_logs(self, hours_back=24) -> dict:
        """
        Analisa os logs do cron_exec.log e test_run.log.
        Retorna um dicionário contendo:
            - 'cron_active': bool (se o cron executou nas últimas 2 horas)
            - 'last_execution_time': str (data/hora da última execução)
            - 'errors': list (lista de erros encontrados nas últimas X horas)
            - 'warnings': list (lista de avisos de login ou rede)
        """
        now = datetime.now()
        threshold_time = now - timedelta(hours=hours_back)
        cron_active_threshold = now - timedelta(hours=2) # Espera-se execução a cada hora (no minuto 30)
        
        errors = []
        warnings = []
        last_execution_dt = None
        
        # --- 1. Analisar test_run.log (Log estruturado da aplicação) ---
        if os.path.exists(self.app_log_path):
            try:
                with open(self.app_log_path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                
                current_line_dt = None
                temp_traceback = []
                in_traceback = False
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Tenta capturar o timestamp inicial da linha (ex: 2026-06-20 11:29:51)
                    match_dt = re.match(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line)
                    if match_dt:
                        # Se estávamos acumulando um traceback e mudou de linha com timestamp, processamos o anterior
                        if in_traceback and temp_traceback and current_line_dt and current_line_dt >= threshold_time:
                            errors.append("\n".join(temp_traceback))
                        in_traceback = False
                        temp_traceback = []
                        
                        try:
                            current_line_dt = datetime.strptime(match_dt.group(1), "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            current_line_dt = None
                            
                        # Verifica se é uma marcação de início de scraper para monitoramento de atividade
                        if "INICIANDO EXECUÇÃO DO SCRAPER" in line:
                            if not last_execution_dt or current_line_dt > last_execution_dt:
                                last_execution_dt = current_line_dt
                                
                        # Filtra erros/avisos se estiverem dentro da janela de tempo
                        if current_line_dt and current_line_dt >= threshold_time:
                            if "[ERROR]" in line or "[CRITICAL]" in line:
                                errors.append(line)
                            elif "[WARNING]" in line:
                                # Captura avisos importantes de login ou sincronização
                                if "Falha" in line or "inacessível" in line or "offline" in line:
                                    warnings.append(line)
                                    
                    else:
                        # Linha sem timestamp (provavelmente parte de um traceback ou log multi-linha)
                        if "Traceback" in line or "Exception" in line or in_traceback:
                            in_traceback = True
                            temp_traceback.append(line)
                            
                # Processa último traceback pendente no arquivo se necessário
                if in_traceback and temp_traceback and current_line_dt and current_line_dt >= threshold_time:
                    errors.append("\n".join(temp_traceback))
                    
            except Exception as e:
                logger.error(f"Erro ao ler test_run.log para auditoria: {e}")
                errors.append(f"Erro de sistema ao monitorar test_run.log: {e}")
        else:
            warnings.append("Arquivo test_run.log não encontrado.")

        # --- 2. Analisar cron_exec.log (Erros brutos de execução do bash/cron) ---
        if os.path.exists(self.cron_log_path):
            try:
                # O cron_log_path acumula saídas do stdout/stderr.
                # Como a maioria das linhas do stderr brutas não tem timestamp, 
                # vamos analisar as linhas e correlacionar erros recorrentes.
                with open(self.cron_log_path, "r", encoding="utf-8", errors="ignore") as f:
                    # Lê apenas as últimas 300 linhas do cron_exec.log para não sobrecarregar
                    cron_lines = f.readlines()[-300:]
                
                for line in cron_lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Ignora avisos conhecidos não-fatais do dotenv
                    if "python-dotenv" in line or "could not parse" in line:
                        continue
                        
                    # Filtra mensagens de erro do bash/python bruto
                    if any(term in line.lower() for term in ["permission denied", "command not found", "no such file", "error", "exception"]):
                        # Como não há timestamp na linha bruta, evitamos duplicar no relatório se já capturado
                        if line not in errors:
                            errors.append(f"[Cron/Stderr] {line}")
            except Exception as e:
                logger.error(f"Erro ao ler cron_exec.log para auditoria: {e}")
                errors.append(f"Erro de sistema ao monitorar cron_exec.log: {e}")
        else:
            warnings.append("Arquivo cron_exec.log não encontrado.")

        # --- 3. Consolidar status de atividade do Cron ---
        cron_active = False
        last_execution_str = "Nunca executado"
        if last_execution_dt:
            cron_active = last_execution_dt >= cron_active_threshold
            last_execution_str = last_execution_dt.strftime("%Y-%m-%d %H:%M:%S")
        else:
            # Caso não tenha lido o timestamp nos logs do dia, verifica a data de modificação física do log
            if os.path.exists(self.app_log_path):
                mtime = datetime.fromtimestamp(os.path.getmtime(self.app_log_path))
                cron_active = mtime >= cron_active_threshold
                last_execution_str = mtime.strftime("%Y-%m-%d %H:%M:%S")

        return {
            "cron_active": cron_active,
            "last_execution_time": last_execution_str,
            "errors": errors,
            "warnings": warnings
        }
