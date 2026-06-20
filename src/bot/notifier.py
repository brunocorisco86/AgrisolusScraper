import os
import asyncio
from aiogram import Bot
from dotenv import load_dotenv
from src.utils.logger import setup_logger

logger = setup_logger(name="telegram_notifier", log_file="test_run.log")

class TelegramNotifier:
    """
    Serviço push-only para o Telegram utilizando o aiogram.
    Envia alertas imediatos, resumos periódicos e relatórios diários de SLA.
    """
    def __init__(self, token=None, chat_id=None):
        load_dotenv()
        self.token = token or os.getenv("TELEGRAM_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID") or os.getenv("TELEGRAM_ALLOWED_USER_ID")
        
        if not self.token or not self.chat_id:
            logger.warning("TELEGRAM_TOKEN/TELEGRAM_BOT_TOKEN ou TELEGRAM_CHAT_ID/TELEGRAM_ALLOWED_USER_ID ausentes no .env. Notificações do Telegram estarão desabilitadas.")

    async def _send_async_message(self, text: str) -> bool:
        """
        Envia uma mensagem assincronamente e garante que a sessão do bot seja fechada.
        """
        if not self.token or not self.chat_id:
            logger.warning("Ignorando envio de mensagem do Telegram devido a chaves ausentes no .env.")
            return False
            
        try:
            import aiohttp
            from aiogram.client.session.aiohttp import AiohttpSession
            
            # Define timeout curto (10 segundos) para evitar travamentos infinitos do processo
            timeout = aiohttp.ClientTimeout(total=10)
            session = AiohttpSession(timeout=timeout)
            
            bot = Bot(token=self.token, session=session)
            # parse_mode="HTML" permite formatações estilosas com <b>, <i>, etc.
            await bot.send_message(chat_id=self.chat_id, text=text, parse_mode="HTML")
            await bot.session.close()
            logger.info("Notificação enviada com sucesso ao Telegram!")
            return True
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem para o Telegram: {e}")
            return False

    def send_message(self, text: str) -> bool:
        """
        Envia uma mensagem de texto gerenciando o event loop de forma síncrona.
        Garante compatibilidade ao ser executado dentro de crons síncronos.
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        if loop.is_running():
            # Se o loop de eventos já estiver rodando (ex: testes pytest ou outra task)
            # cria uma corrotina e aguarda em thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self._send_async_message(text))
                return future.result()
        else:
            return loop.run_until_complete(self._send_async_message(text))

    def send_immediate_alert(self, silo_id: str, last_datetime_str: str, offline_hours: float) -> bool:
        """
        Envia um alerta imediato de que o silo está sem enviar dados por mais de 2 horas.
        """
        emoji = "⚠️"
        text = (
            f"<b>{emoji} ALERTA: SILO OFFLINE</b>\n\n"
            f"O <b>{silo_id}</b> está sem enviar dados novos há mais de <b>{offline_hours:.1f} horas</b>!\n"
            f"• <b>Último Envio:</b> {last_datetime_str}\n\n"
            f"<i>Pilares Agrisolus: Tecnologia Habilitadora & Processos Otimizados.</i>"
        )
        return self.send_message(text)

    def send_periodic_summary(self, occurrences: list) -> bool:
        """
        Envia um resumo de ocorrências de silos fora de envio por mais de 3 horas.
        Será agendado para 06h, 11h, 13h e 16h.
        """
        emoji = "📋"
        if not occurrences:
            text = (
                f"<b>{emoji} RESUMO DE OCORRÊNCIAS - SILOS</b>\n\n"
                f"Todos os silos estão operando normalmente nas últimas horas. Sem quedas de envio detectadas!\n\n"
                f"<i>SLA estável.</i>"
            )
        else:
            text = f"<b>{emoji} RESUMO DE OCORRÊNCIAS - SILOS</b>\n"
            text += "Silos que ficaram sem enviar dados por mais de 3 horas nas últimas execuções:\n\n"
            for occ in occurrences:
                text += (
                    f"• <b>{occ['silo_id']}</b>: Offline há <b>{occ['offline_hours']:.1f}h</b>\n"
                    f"  (Último envio: {occ['last_datetime_str']})\n"
                )
            text += "\n<i>Pilares Agrisolus: Comunicação Eficiente & Tecnologia Habilitadora.</i>"
            
        return self.send_message(text)

    def send_daily_sla_report(self, date_str: str, silos_sla: list) -> bool:
        """
        Envia o relatório diário de SLA, Consumo e Saldo de ração às 18:00.
        """
        emoji = "📊"
        text = f"<b>{emoji} RELATÓRIO DIÁRIO DE SLA & CONSUMO</b>\n"
        text += f"Período: das 17h de ontem às 17h de hoje ({date_str})\n\n"
        
        for item in silos_sla:
            sla = item.get('sla_percentage', 0.0)
            status_emoji = "🟢" if sla >= 95.0 else ("🟡" if sla >= 85.0 else "🔴")
            
            text += (
                f"🔋 <b>{item['silo_id']}</b>\n"
                f"• {status_emoji} <b>SLA de Conectividade:</b> {sla:.1f}%\n"
                f"• 📉 <b>Ração Consumida:</b> {item['total_consumed_kg']:.2f} kg\n"
                f"• 📦 <b>Saldo de Ração Atual:</b> {item['current_balance_kg']:.2f} kg\n\n"
            )
            
        text += "<i>Pilares Agrisolus: Comunicação Eficiente & Processos Otimizados.</i>"
        return self.send_message(text)
