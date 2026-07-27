from database.db_manager import DBManager

class AffiliateService:
    def __init__(self):
        self.db = DBManager()
    
    def process_referral(self, referred_id, referral_code):
        from database.models import SessionLocal, User
        db = SessionLocal()
        
        referrer = db.query(User).filter_by(referral_code=referral_code).first()
        referred = db.query(User).filter_by(telegram_id=referred_id).first()
        
        if referrer and referred and referrer.id != referred.id:
            referred.referred_by = referrer.telegram_id
            db.commit()
            db.close()
            return True
        
        db.close()
        return False
    
    def add_commission_on_recharge(self, user_id, amount):
        from database.models import SessionLocal, User
        db = SessionLocal()
        
        user = db.query(User).filter_by(telegram_id=user_id).first()
        if user and user.referred_by:
            referrer = db.query(User).filter_by(telegram_id=user.referred_by).first()
            if referrer:
                commission_pct = float(self.db.get_setting('commission_percentage', '20'))
                commission = amount * (commission_pct / 100)
                referrer.commission_balance += commission
                referrer.total_referrals += 1
                
                points_per = int(self.db.get_setting('affiliate_points_per_recharge', '1'))
                user.affiliate_points += points_per
                
                db.commit()
                db.close()
                return True
        
        db.close()
        return False
    
    def convert_points_to_balance(self, user_id):
        from database.models import SessionLocal, User
        db = SessionLocal()
        
        user = db.query(User).filter_by(telegram_id=user_id).first()
        if not user:
            db.close()
            return False, 0
        
        min_points = int(self.db.get_setting('affiliate_min_points', '500'))
        multiplier = float(self.db.get_setting('affiliate_multiplier', '0.01'))
        
        if user.affiliate_points >= min_points:
            converted = user.affiliate_points * multiplier
            user.balance += converted
            user.affiliate_points = 0
            db.commit()
            db.close()
            return True, converted
        
        db.close()
        return False, 0
    
    def get_affiliate_stats(self, user_id):
        from database.models import SessionLocal, User
        db = SessionLocal()
        
        user = db.query(User).filter_by(telegram_id=user_id).first()
        if not user:
            db.close()
            return None
        
        referred_users = db.query(User).filter_by(referred_by=user_id).all()
        
        stats = {
            'total_referrals': len(referred_users),
            'commission_balance': user.commission_balance,
            'affiliate_points': user.affiliate_points,
            'referral_code': user.referral_code,
        }
        
        db.close()
        return stats
    
    def close(self):
        self.db.close()
