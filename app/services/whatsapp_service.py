import logging
import re
from typing import Optional

from twilio.rest import Client # Importar o cliente Twilio
from twilio.base.exceptions import TwilioRestException # Para tratar erros da API

from app.core.config import settings # Suas configurações com as credenciais

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("WhatsappService")

E164_REGEX = r"^\+[1-9]\d{9,14}$" # Formato E.164

class WhatsappService:
    def __init__(self):
        if not all([settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN, settings.TWILIO_WHATSAPP_FROM_NUMBER]):
            logger.warning(
                "Credenciais do Twilio (ACCOUNT_SID, AUTH_TOKEN, WHATSAPP_FROM_NUMBER) não configuradas completamente. "
                "O envio de WhatsApp real será desabilitado, usando apenas logs."
            )
            self.client = None
        else:
            try:
                self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                logger.info("Cliente Twilio inicializado com sucesso.")
            except Exception as e:
                logger.error(f"Falha ao inicializar o cliente Twilio: {e}")
                self.client = None
        
        self.twilio_from_number_whatsapp = f"whatsapp:{settings.TWILIO_WHATSAPP_FROM_NUMBER}"

    async def send_message(self, to_phone_number: str, message_body: str) -> bool:
        if not self.client:
            logger.error("[WhatsApp Service] Cliente Twilio não inicializado. Mensagem não enviada. Verifique as credenciais.")
            return await self._simulate_send(to_phone_number, message_body, "Cliente Twilio não configurado")

        if not to_phone_number:
            logger.error("[WhatsApp Service] Tentativa de envio sem número de telefone de destino.")
            return False

        if not re.fullmatch(E164_REGEX, to_phone_number):
            logger.warning(
                f"[WhatsApp Service] Número de telefone do destinatário '{to_phone_number}' "
                f"não está no formato E.164 esperado. Tentando enviar mesmo assim."
            )

        try:
            logger.info(f"Tentando enviar mensagem via Twilio para: whatsapp:{to_phone_number} de {self.twilio_from_number_whatsapp}")
            message = self.client.messages.create(
                from_=self.twilio_from_number_whatsapp,
                body=message_body,
                to=f"whatsapp:{settings.TWILIO_WHATSAPP_TO_NUMBER}"  
            )
            logger.info(f"Mensagem WhatsApp enviada para {to_phone_number}. SID da mensagem: {message.sid}, Status: {message.status}")
            return True
        except TwilioRestException as e:
            logger.error(f"Erro da API Twilio ao enviar para {to_phone_number}: {e}")
            return False
        except Exception as e:
            logger.error(f"Erro inesperado ao enviar WhatsApp para {to_phone_number} via Twilio: {e}")
            return False

    async def _simulate_send(self, phone_number: str, message_body: str, reason: str) -> bool:
        """Método de simulação privado para fallback."""
        from datetime import datetime 
        log_message = (
            f"\n==============================================\n"
            f"📲 SIMULAÇÃO DE ENVIO DE WHATSAPP (Fallback: {reason}) 📲\n"
            f"----------------------------------------------\n"
            f"Para (To):         {phone_number}\n"
            f"Mensagem (Message): {message_body}\n"
            f"Status:            Mensagem registrada para simulação.\n"
            f"Timestamp:         {datetime.now().isoformat()}\n"
            f"=============================================="
        )
        logger.info(log_message)
        return True 
