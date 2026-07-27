import sys
import os
import json
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, request, jsonify
from database.db_manager import DBManager
from utils.logger import logger
from datetime import datetime

class WebhookServer:
    def __init__(self, bot=None):
        self.app = Flask(__name__)
        self.bot = bot
        self.db = DBManager()
        self.setup_routes()
    
    def setup_routes(self):
        @self.app.route('/', methods=['GET'])
        def home():
            return jsonify({
                "status": "online",
                "service": "Doguinha Store Webhook",
                "timestamp": datetime.now().isoformat()
            })
        
        @self.app.route('/health', methods=['GET'])
        def health():
            return jsonify({"status": "healthy"})
        
        @self.app.route('/webhook/mp', methods=['POST'])
        def webhook_mercadopago():
            """
            Recebe notificações do Mercado Pago
            """
            try:
                data = request.json
                logger.info(f"Webhook MP recebido: {data}")
                
                if data.get('action') == 'payment.updated':
                    payment_id = data.get('data', {}).get('id')
                    
                    if payment_id:
                        from services.pix_service import PixService
                        pix_service = PixService()
                        
                        resultado = pix_service.verificar_pagamento(payment_id)
                        
                        if resultado.get('status') == 'approved':
                            logger.transaction(payment_id, 'PIX_APROVADO_WEBHOOK', resultado.get('valor', 0))
                            
                            from database.models import SessionLocal, PixRecharge
                            db = SessionLocal()
                            recharge = db.query(PixRecharge).filter_by(pix_id=payment_id).first()
                            
                            if recharge and self.bot:
                                try:
                                    user = db.query(db.__class__).filter_by(id=recharge.user_id).first()
                                    from database.models import User
                                    user = db.query(User).filter_by(id=recharge.user_id).first()
                                    
                                    bonus_pct = float(self.db.get_setting('bonus_percentage', '0'))
                                    bonus_min = float(self.db.get_setting('bonus_min_value', '0'))
                                    bonus = recharge.amount * (bonus_pct/100) if recharge.amount >= bonus_min and bonus_pct > 0 else 0
                                    
                                    await self.bot.send_message(
                                        recharge.user_id,
                                        f"✅ *Pagamento Aprovado!*\n\n"
                                        f"💰 Valor: R$ {recharge.amount:.2f}\n"
                                        f"🎁 Bônus: R$ {bonus:.2f}\n"
                                        f"💵 Saldo atualizado!\n\n"
                                        f"Use /start para ver o menu."
                                    )
                                    
                                    if user and user.referred_by:
                                        from services.affiliate_service import AffiliateService
                                        aff = AffiliateService()
                                        aff.add_commission_on_recharge(user.id, recharge.amount + bonus)
                                        aff.close()
                                    
                                except Exception as e:
                                    logger.error(f"Erro ao notificar: {e}")
                            
                            db.close()
                            pix_service.close()
                
                return jsonify({"status": "ok"}), 200
                
            except Exception as e:
                logger.error(f"Erro no webhook: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
        
        @self.app.route('/webhook/telegram', methods=['POST'])
        def webhook_telegram():
            """
            Webhook para Telegram (modo alternativo ao polling)
            """
            return jsonify({"status": "ok"}), 200
    
    def run(self, port=5000):
        """
        Inicia o servidor Flask em uma thread separada
        """
        def start():
            self.app.run(
                host='0.0.0.0',
                port=port,
                debug=False,
                use_reloader=False
            )
        
        thread = threading.Thread(target=start, daemon=True)
        thread.start()
        print(f"🔗 Webhook rodando na porta {port}")

if __name__ == '__main__':
    print("🔗 Iniciando Webhook Server...")
    
    webhook = WebhookServer()
    port = int(os.environ.get('PORT', 5000))
    webhook.run(port=port)
    
    print(f"✅ Webhook pronto na porta {port}")
    print("📡 Aguardando notificações do Mercado Pago...")
    
    import time
    while True:
        time.sleep(60)
