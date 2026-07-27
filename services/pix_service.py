import uuid
from datetime import datetime, timedelta
import qrcode
from io import BytesIO

class PixService:
    def __init__(self):
        pass
    
    def generate_pix_id(self):
        return uuid.uuid4().hex[:32]
    
    def generate_copy_paste(self):
        return f"00020101021226830014BR.GOV.BCB.PIX2561qrcodespix.sejaefi.com.br/v2/{uuid.uuid4().hex[:32]}5204000053039865802BR5905EFISA6008SAOPAULO62070503***6304{uuid.uuid4().hex[:4].upper()}"
    
    def get_expiration(self, minutes=15):
        return datetime.now() + timedelta(minutes=minutes)
    
    def generate_qr_image(self, copy_paste):
        qr = qrcode.QRCode(version=1, box_size=10, border=2)
        qr.add_data(copy_paste)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        bio = BytesIO()
        img.save(bio, 'PNG')
        bio.seek(0)
        return bio
