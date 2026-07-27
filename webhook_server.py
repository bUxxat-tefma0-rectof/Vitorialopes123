import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from handlers.webhook_handler import WebhookServer
from utils.logger import logger

if __name__ == '__main__':
    print("🔗 Iniciando servidor de Webhook...")
    
    webhook = WebhookServer()
    webhook.run(port=int(os.environ.get('PORT', 5000)))
    
    logger.info("Webhook iniciado na porta 5000")
    print("✅ Webhook pronto para receber notificacoes!")
    
    # Manter rodando
    import time
    while True:
        time.sleep(60)
