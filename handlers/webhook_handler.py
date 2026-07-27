from flask import Flask, request, jsonify
from database.db_manager import DBManager
from services.pix_service import PixService
from services.affiliate_service import AffiliateService
from utils.logger import logger
import threading

class WebhookServer:
    def __init__(self, bot=None):
        self.app = Flask(__name__)
        self.bot = bot
        self.db = DBManager()
        self.pix = PixService()
        self.affiliate = AffiliateService()
        self.setup_routes()
    
    def setup_routes(self):
        @self.app.route('/webhook/mp', methods=['POST'])
        def webhook_mp():
            """
            Recebe notificacoes do Mercado Pago
            """
            try:
                data = request.json
                
                if data.get('action') == 'payment.updated':
                    payment_id = data.get('data', {}).get('id')
                    
                    if payment_id:
                        # Verificar pagamento
                        resultado = self.pix.verificar_pagamento(payment_id)
                        
                        if resultado.get('status') == 'approved':
                            logger.transaction(payment_id, 'PIX_APROVADO', resultado.get('valor', 0))
                            
                            # Notificar usuario
                            from database.models import SessionLocal, PixRecharge
                            db = SessionLocal()
                            recharge = db.query(PixRecharge).filter_by(pix_id=payment_id).first()
                            
                            if recharge and self.bot:
                                try:
                                    self.bot.send_message(
                                        recharge.user_id,
                                        f"✅ *Pagamento Aprovado!*\n\n"
                                        f"💰 Valor: R$ {resultado.get('valor', 0):.2f}\n"
                                        f"💵 Saldo creditado com sucesso!\n\n"
                                        f"Use /start para ver o menu."
                                    )
                                except Exception as e:
                                    logger.error(f"Erro ao notificar usuario: {e}")
                            
                            db.close()
                
                return jsonify({"status": "ok"}), 200
                
            except Exception as e:
                logger.error(f"Erro no webhook: {e}")
                return jsonify({"status": "error"}), 500
        
        @self.app.route('/webhook/status', methods=['GET'])
        def webhook_status():
            return jsonify({
                "status": "online",
                "webhook": "Mercado Pago",
                "timestamp": datetime.now().isoformat()
            })
    
    def run(self, port=5000):
        """
        Inicia o servidor de webhook
        """
        def start_server():
            self.app.run(host='0.0.0.0', port=port, debug=False)
        
        thread = threading.Thread(target=start_server)
        thread.daemon = True
        thread.start()
        print(f"🔗 Webhook rodando na porta {port}")

from datetime import datetime
