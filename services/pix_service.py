from services.mercado_pago_full import MercadoPagoFull
from database.db_manager import DBManager
from datetime import datetime, timedelta

class PixService:
    def __init__(self):
        self.mp = MercadoPagoFull()
        self.db = DBManager()
    
    def gerar_pix(self, user_id, valor, descricao="Recarga de saldo"):
        """
        Gera um PIX completo para o usuario
        """
        expiracao = int(self.db.get_setting('pix_expiration', '15'))
        
        resultado = self.mp.criar_pagamento_pix(
            valor=valor,
            descricao=descricao,
            expiracao_minutos=expiracao
        )
        
        if not resultado['sucesso']:
            return {"sucesso": False, "erro": resultado.get('erro', 'Erro ao gerar PIX')}
        
        dados = resultado['dados']
        
        # Salvar no banco de dados
        self.db.create_pix(
            user_id=user_id,
            amount=valor,
            pix_id=dados['id'],
            qr_code=dados['qr_code_base64'],
            copy_paste=dados['copia_cola'],
            expires_at=datetime.now() + timedelta(minutes=expiracao)
        )
        
        # Gerar imagem do QR Code
        qr_image = self.mp.gerar_qr_code_imagem(dados['qr_code'])
        
        return {
            "sucesso": True,
            "pix_id": dados['id'],
            "valor": dados['valor'],
            "qr_code_texto": dados['qr_code'],
            "qr_code_base64": dados['qr_code_base64'],
            "qr_code_imagem": qr_image,
            "copia_cola": dados['copia_cola'],
            "data_expiracao": dados['data_expiracao'],
            "expiracao_minutos": expiracao
        }
    
    def verificar_pagamento(self, pix_id):
        """
        Verifica se o PIX foi pago
        """
        resultado = self.mp.verificar_pagamento(pix_id)
        
        if not resultado['sucesso']:
            return {"sucesso": False, "status": "erro"}
        
        if resultado['aprovado']:
            # Confirmar no banco de dados
            confirmado, total = self.db.confirm_pix(pix_id)
            if confirmado:
                return {
                    "sucesso": True,
                    "status": "approved",
                    "valor": resultado['valor'],
                    "total_creditado": total
                }
        
        return {
            "sucesso": True,
            "status": resultado['status'],
            "aprovado": resultado['aprovado'],
            "pendente": resultado['pendente'],
            "rejeitado": resultado['rejeitado'],
            "expirado": resultado['expirado']
        }
    
    def close(self):
        self.db.close()
