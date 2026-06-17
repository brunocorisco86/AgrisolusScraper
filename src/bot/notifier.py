"""
Módulo de Notificação do Telegram utilizando a biblioteca aiogram.
"""

class TelegramNotifier:
    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id

    async def send_alert(self, message):
        """Envia um alerta imediato de falta de dados no Telegram."""
        pass

    async def send_daily_sla_report(self, sla_data):
        """Envia o relatório diário de SLA com a curva de consumo às 18h."""
        pass

    async def send_summary(self, summary_data):
        """Envia os resumos periódicos das ocorrências."""
        pass
