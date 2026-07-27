import requests
import json
import uuid
import qrcode
from io import BytesIO
from datetime import datetime, timedelta
from config.settings import MP_ACCESS_TOKEN

class MercadoPagoFull:
    def __init__(self):
        self.token = MP_ACCESS_TOKEN
        self.base_url = "https://api.mercadopago.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def criar_pagamento_pix(self, valor, descricao, email_cliente="cliente@bot.com", expiracao_minutos=15):
        """
        Cria um pagamento PIX no Mercado Pago
        Retorna: dict com dados do PIX
        """
        try:
            data_expiracao = (datetime.now() + timedelta(minutes=expiracao_minutos)).isoformat()
            
            payload = {
                "transaction_amount": float(valor),
                "description": descricao,
                "payment_method_id": "pix",
                "payer": {
                    "email": email_cliente,
                    "first_name": "Cliente",
                    "last_name": "Bot"
                },
                "date_of_expiration": data_expiracao,
                "notification_url": "https://SEU_DOMINIO.onrender.com/webhook/mp"
            }
            
            response = requests.post(
                f"{self.base_url}/payments",
                json=payload,
                headers=self.headers
            )
            
            if response.status_code in [200, 201]:
                dados = response.json()
                
                pix_info = {
                    "id": dados["id"],
                    "status": dados["status"],
                    "valor": dados["transaction_amount"],
                    "qr_code": dados["point_of_interaction"]["transaction_data"]["qr_code"],
                    "qr_code_base64": dados["point_of_interaction"]["transaction_data"]["qr_code_base64"],
                    "copia_cola": dados["point_of_interaction"]["transaction_data"]["qr_code"],
                    "data_expiracao": dados["date_of_expiration"],
                    "data_criacao": dados["date_created"],
                }
                
                return {"sucesso": True, "dados": pix_info}
            else:
                return {"sucesso": False, "erro": response.json()}
                
        except Exception as e:
            return {"sucesso": False, "erro": str(e)}
    
    def verificar_pagamento(self, payment_id):
        """
        Verifica o status de um pagamento
        """
        try:
            response = requests.get(
                f"{self.base_url}/payments/{payment_id}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                dados = response.json()
                return {
                    "sucesso": True,
                    "status": dados["status"],
                    "id": dados["id"],
                    "valor": dados["transaction_amount"],
                    "aprovado": dados["status"] == "approved",
                    "pendente": dados["status"] == "pending",
                    "rejeitado": dados["status"] == "rejected",
                    "expirado": dados["status"] == "cancelled",
                    "dados_completos": dados
                }
            else:
                return {"sucesso": False, "erro": "Pagamento nao encontrado"}
                
        except Exception as e:
            return {"sucesso": False, "erro": str(e)}
    
    def gerar_qr_code_imagem(self, qr_code_texto):
        """
        Gera uma imagem PNG do QR Code
        """
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_code_texto)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            
            return buffer
        except Exception as e:
            print(f"Erro ao gerar QR Code: {e}")
            return None
    
    def criar_webhook(self, url_webhook):
        """
        Configura webhook para notificacoes
        """
        try:
            payload = {
                "url": url_webhook,
                "topics": ["payment"]
            }
            
            response = requests.post(
                f"{self.base_url}/webhooks",
                json=payload,
                headers=self.headers
            )
            
            return response.status_code in [200, 201]
        except Exception as e:
            print(f"Erro ao criar webhook: {e}")
            return False
    
    def listar_webhooks(self):
        """
        Lista webhooks configurados
        """
        try:
            response = requests.get(
                f"{self.base_url}/webhooks",
                headers=self.headers
            )
            return response.json() if response.status_code == 200 else []
        except:
            return []
    
    def deletar_webhook(self, webhook_id):
        """
        Remove um webhook
        """
        try:
            response = requests.delete(
                f"{self.base_url}/webhooks/{webhook_id}",
                headers=self.headers
            )
            return response.status_code == 200
        except:
            return False
