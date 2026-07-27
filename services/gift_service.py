import random
import string
from database.db_manager import DBManager

class GiftService:
    def __init__(self):
        self.db = DBManager()
    
    def generate_code(self, length=12):
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
    
    def create_gift(self, value):
        return self.db.create_gift_card(value)
    
    def create_multiple_gifts(self, value, quantity):
        gifts = []
        for _ in range(quantity):
            gifts.append(self.create_gift(value))
        return gifts
    
    def redeem(self, code, user_id):
        return self.db.redeem_gift(code, user_id)
    
    def list_unused(self):
        from database.models import SessionLocal, GiftCard
        db = SessionLocal()
        gifts = db.query(GiftCard).filter_by(is_used=False).all()
        db.close()
        return gifts
    
    def close(self):
        self.db.close()
