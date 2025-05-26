from app.services.whatsapp_service import WhatsappService

_whatsapp_service_instance = None

def get_whatsapp_service() -> WhatsappService:
    global _whatsapp_service_instance
    if _whatsapp_service_instance is None:
        _whatsapp_service_instance = WhatsappService()
    return _whatsapp_service_instance