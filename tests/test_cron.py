# -*- coding: utf-8 -*-
"""
Testes unitários para validar a existência, permissões e corretude dos scripts do agendador Cron.
"""
import os
import stat
import pytest

def test_cron_wrappers_existence():
    """
    Verifica se todos os scripts wrappers do cron existem no diretório scripts/.
    """
    wrappers = [
        "scripts/run_cron.sh",
        "scripts/run_periodic_summary.sh",
        "scripts/run_sla_report.sh"
    ]
    
    for wrapper in wrappers:
        assert os.path.exists(wrapper), f"O wrapper {wrapper} não foi encontrado no projeto."

def test_cron_wrappers_executable():
    """
    Verifica se os scripts wrappers do cron têm permissão de execução (+x).
    """
    wrappers = [
        "scripts/run_cron.sh",
        "scripts/run_periodic_summary.sh",
        "scripts/run_sla_report.sh"
    ]
    
    for wrapper in wrappers:
        # Pega as permissões do arquivo
        mode = os.stat(wrapper).st_mode
        # Verifica se o bit de execução para o usuário/grupo/outros está ativo
        is_executable = bool(mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH))
        assert is_executable, f"O wrapper {wrapper} não tem permissão de execução."

def test_setup_cron_script_alignment():
    """
    Verifica se o script 4_setup_cron.sh aponta corretamente para os wrappers do cron criados.
    """
    setup_script = "scripts/deploy/4_setup_cron.sh"
    assert os.path.exists(setup_script), f"O script de deploy {setup_script} não existe."
    
    with open(setup_script, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Verifica se o setup do cron está configurado para apontar para os wrappers bash
    assert "scripts/run_cron.sh" in content
    assert "scripts/run_periodic_summary.sh" in content
    assert "scripts/run_sla_report.sh" in content
    assert "/bin/bash" in content
