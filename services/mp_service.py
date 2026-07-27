import requests
from config.settings import MP_ACCESS_TOKEN

class MercadoPagoService:
    def __init__(self):
        self.token = MP_ACCESS_TOKEN
        self.base_url = "https://api.mercadopago.com/v1"
    
    def create_pix_payment(self, amount, description, expiration_date):
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "transaction_amount": amount,
            "description": description,
            "payment_method_id": "pix",
            "payer": {
                "email": "cliente@bot.com",
                "first_name": "Cliente"
            },
            "date_of_expiration": expiration_date.isoformat()
        }
        
        try:
            response = requests.post(f"{self.base_url}/payments", json=data, headers=headers)
            return response.json()
        except Exception as e:
            print(f"Erro Mercado Pago: {e}")
            return None
    
    def check_payment(self, payment_id):
        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            response = requests.get(f"{self.base_url}/payments/{payment_id}", headers=headers)
            return response.json()
        except:
            return None
